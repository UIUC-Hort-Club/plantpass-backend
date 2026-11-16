import json
import logging
import os
from decimal import Decimal
import boto3
import bcrypt
import jwt
import datetime
from response_utils import create_response
from dynamodb_client import get_table
from temp_password_manager import (
    generate_temp_password,
    store_temp_password,
    get_temp_password_hash,
    delete_temp_password,
    seconds_since_temp_password_issued
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FEATURE_TOGGLES_TABLE_ENV = "FEATURE_TOGGLES_TABLE_NAME"
DEFAULT_PASSWORD_PROTECT_ADMIN = True
# Login tries are slowed down at the API (terraform/apigateway.tf), never locked
# out, so a long password is what makes guessing useless.
MIN_ADMIN_PASSWORD_LENGTH = 12
FORGOT_PASSWORD_COOLDOWN_SECONDS = 60

s3 = boto3.client("s3")


def _dynamo_bool(item, key, default):
    """Normalize DynamoDB boolean fields (BOOL, legacy strings, or Decimal)."""
    if key not in item:
        return default
    value = item[key]
    if isinstance(value, bool):
        return value
    if isinstance(value, Decimal):
        return value != 0
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ('true', '1', 'yes')
    return default
bucket = os.environ["PASSWORD_BUCKET"]
key = os.environ["PASSWORD_KEY"]

JWT_SECRET = os.environ["JWT_SECRET"]
EMAIL_LAMBDA_ARN = os.environ.get("EMAIL_LAMBDA_ARN")

lambda_client = boto3.client('lambda')

def get_password_hash():
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = json.loads(obj["Body"].read())
    return data["admin_password_hash"].encode()

def set_password_hash(new_hash):
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps({"admin_password_hash": new_hash.decode()})
    )


def password_matches(candidate, pw_hash):
    """False, never an error, for a value bcrypt cannot compare (it refuses more than 72 bytes)."""
    return (
        isinstance(candidate, str)
        and len(candidate.encode()) <= 72
        and bcrypt.checkpw(candidate.encode(), pw_hash)
    )


def is_password_protect_admin_enabled():
    """
    Read feature toggle from DynamoDB. On error or missing item, default to True (require password).
    """
    try:
        table = get_table(FEATURE_TOGGLES_TABLE_ENV, "PlantPass-FeatureToggles")
        response = table.get_item(Key={"config_id": "feature_toggles"})
        item = response.get("Item", {})
        return _dynamo_bool(item, "passwordProtectAdmin", DEFAULT_PASSWORD_PROTECT_ADMIN)
    except Exception as e:
        logger.warning("Could not read passwordProtectAdmin from DynamoDB: %s", e)
        return True


def lambda_handler(event, context):
    try:
        logger.info(f"=== Lambda Invoked ===")
        
        body = json.loads(event.get("body", "{}"))
        route_key = event.get("routeKey", "")
        
        logger.info(f"Route: {route_key}")
        logger.info(f"Body keys: {list(body.keys())}")

        if route_key == "POST /admin/login":
            logger.info("=== Admin Login Attempt ===")
            if not is_password_protect_admin_enabled():
                logger.info("Password protection disabled; issuing admin token without password check")
                token = jwt.encode(
                    {
                        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
                        "role": "admin",
                        "iat": datetime.datetime.utcnow()
                    },
                    JWT_SECRET,
                    algorithm="HS256"
                )
                return create_response(200, {"token": token, "requires_password_change": False})

            pw_hash = get_password_hash()
            password = body.get("password", "")
            
            logger.info(f"Password hash from S3 exists: {bool(pw_hash)}")

            # Check regular password first
            logger.info("Checking regular password...")
            regular_match = password_matches(password, pw_hash)
            logger.info(f"Regular password match: {regular_match}")
            
            if regular_match:
                token = jwt.encode(
                    {
                        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
                        "role": "admin",
                        "iat": datetime.datetime.utcnow()
                    },
                    JWT_SECRET,
                    algorithm="HS256"
                )
                logger.info("Regular password authenticated successfully")
                return create_response(200, {"token": token, "requires_password_change": False})
            
            # If regular password didn't match, check temp password
            logger.info("Regular password failed, checking temporary password...")
            temp_hash = get_temp_password_hash()
            logger.info(f"Temp password hash exists: {bool(temp_hash)}")
            
            if temp_hash:
                temp_match = password_matches(password, temp_hash.encode())
                logger.info(f"Temp password match: {temp_match}")
                
                if temp_match:
                    # Generate token but require password change
                    token = jwt.encode(
                        {
                            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
                            "temp": True,
                            "role": "admin",
                            "iat": datetime.datetime.utcnow()
                        },
                        JWT_SECRET,
                        algorithm="HS256"
                    )
                    delete_temp_password()
                    logger.info("Temp password authenticated successfully")
                    return create_response(200, {"token": token, "requires_password_change": True})
            else:
                logger.info("No temp password hash found in DynamoDB")
            
            logger.warning("Authentication failed - no password matched")
            return create_response(401, {"error": "Invalid password"})
        
        if route_key == "POST /admin/change-password":
            headers = event.get("headers", {})
            authorization = headers.get("authorization", "")
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else ""

            try:
                decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                is_temp = decoded.get("temp", False)
            except jwt.ExpiredSignatureError:
                return create_response(401, {"error": "Token expired"})
            except:
                return create_response(401, {"error": "Invalid token"})

            # Staff tokens are signed with the same key; only an admin's may
            # change the admin password.
            if decoded.get("role") != "admin":
                return create_response(403, {"error": "Admin access required"})

            old_pw = body.get("old_password", "")
            new_pw = body.get("new_password", "")

            if not isinstance(new_pw, str) or len(new_pw) < MIN_ADMIN_PASSWORD_LENGTH:
                return create_response(400, {
                    "error": f"New password must be at least {MIN_ADMIN_PASSWORD_LENGTH} characters"
                })
            # bcrypt reads only the first 72 bytes; refuse rather than cut silently
            if len(new_pw.encode()) > 72:
                return create_response(400, {"error": "New password is too long (72 bytes at most)"})

            # If using temp token, skip old password check
            if not is_temp:
                pw_hash = get_password_hash()
                if not password_matches(old_pw, pw_hash):
                    return create_response(401, {"error": "Invalid current password"})

            new_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt())
            set_password_hash(new_hash)
            return create_response(200, {"success": True})

        if route_key == "POST /admin/forgot-password":
            logger.info("=== Forgot Password Request ===")
            # No login is needed to ask, and each request emails the club, so
            # one request a minute.
            waited = seconds_since_temp_password_issued()
            if waited is not None and waited < FORGOT_PASSWORD_COOLDOWN_SECONDS:
                return create_response(429, {
                    "error": "A reset email was just sent. Please wait a minute before asking again."
                })
            # Generate temporary password
            temp_password = generate_temp_password()
            
            temp_hash = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()
            logger.info("Temp password hashed successfully")
            
            # Store temp password hash
            store_temp_password(temp_hash)
            logger.info("Temp password stored in DynamoDB")
            
            # Send email via Email Lambda
            if EMAIL_LAMBDA_ARN:
                try:
                    email_payload = {
                        "routeKey": "POST /email/password-reset",
                        "body": json.dumps({"temp_password": temp_password})
                    }
                    
                    lambda_client.invoke(
                        FunctionName=EMAIL_LAMBDA_ARN,
                        InvocationType='Event',
                        Payload=json.dumps(email_payload)
                    )
                    
                    logger.info("Password reset email triggered successfully")
                except Exception as e:
                    logger.error(f"Failed to trigger email: {e}")
                    return create_response(500, {"error": "Failed to send email"})
            else:
                logger.warning("EMAIL_LAMBDA_ARN not configured")
            
            return create_response(200, {"message": "Temporary password sent to registered email"})

        return create_response(404, {"error": "Route not found"})

    except:
        logger.exception("Error processing request")
        return create_response(500, {"error": "Internal server error"})
