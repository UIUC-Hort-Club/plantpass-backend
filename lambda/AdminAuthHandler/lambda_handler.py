import json
import logging
import os
import boto3
import bcrypt
import jwt
import datetime
from response_utils import create_response
from temp_password_manager import (
    generate_temp_password,
    store_temp_password,
    get_temp_password_hash,
    delete_temp_password
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
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

def lambda_handler(event, context):
    try:
        logger.info(f"=== Lambda Invoked ===")
        logger.info(f"Event: {json.dumps(event)}")
        
        body = json.loads(event.get("body", "{}"))
        route_key = event.get("routeKey", "")
        
        logger.info(f"Route: {route_key}")
        logger.info(f"Body keys: {list(body.keys())}")

        if route_key == "POST /admin/login":
            logger.info("=== Admin Login Attempt ===")
            pw_hash = get_password_hash()
            password = body.get("password", "")
            
            logger.info(f"Password length: {len(password)}")
            logger.info(f"Password hash from S3 exists: {bool(pw_hash)}")

            # Check regular password first
            logger.info("Checking regular password...")
            regular_match = bcrypt.checkpw(password.encode(), pw_hash)
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
                temp_match = bcrypt.checkpw(password.encode(), temp_hash.encode())
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

            old_pw = body.get("old_password", "")
            new_pw = body.get("new_password", "")

            # If using temp token, skip old password check
            if not is_temp:
                pw_hash = get_password_hash()
                if not bcrypt.checkpw(old_pw.encode(), pw_hash):
                    return create_response(401, {"error": "Invalid current password"})

            new_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt())
            set_password_hash(new_hash)
            return create_response(200, {"success": True})

        if route_key == "POST /admin/forgot-password":
            logger.info("=== Forgot Password Request ===")
            # Generate temporary password
            temp_password = generate_temp_password()
            logger.info(f"Generated temp password length: {len(temp_password)}")
            
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
