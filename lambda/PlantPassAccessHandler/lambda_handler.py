import json
import os
import logging
import jwt
import datetime
from dynamodb_client import get_dynamodb_client
from response_utils import create_response

PLANTPASS_ACCESS_TABLE_NAME = os.environ.get('PLANTPASS_ACCESS_TABLE_NAME', 'PlantPass-Access')
JWT_SECRET = os.environ.get("JWT_SECRET")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Handle PlantPass access passphrase operations
    """
    try:
        route_key = event.get('routeKey', '')
        
        logger.info(f"Route Key: {route_key}")
        
        # GET and PUT require admin authentication
        if route_key in ['GET /plantpass-access', 'PUT /plantpass-access']:
            from auth_middleware import extract_token, verify_token, AuthError
            try:
                token = extract_token(event)
                decoded = verify_token(token)
                
                if decoded.get("role") != "admin":
                    return create_response(403, {"message": "Admin access required"})
                    
                event["auth"] = decoded
            except AuthError as e:
                return create_response(e.status_code, {"error": e.message})
        
        if route_key == 'GET /plantpass-access':
            return get_passphrase()
        elif route_key == 'PUT /plantpass-access':
            body = json.loads(event.get('body', '{}'))
            return set_passphrase(body)
        elif route_key == 'POST /plantpass-access/verify':
            body = json.loads(event.get('body', '{}'))
            return verify_passphrase(body)
        else:
            return create_response(404, {'message': f'Route not found: {route_key}'})
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        return create_response(500, {'message': 'Internal server error'})


def get_passphrase():
    """
    Get the current PlantPass access passphrase
    """
    try:
        dynamodb = get_dynamodb_client()
        table = dynamodb.Table(PLANTPASS_ACCESS_TABLE_NAME)
        
        response = table.get_item(
            Key={'config_id': 'plantpass_access'}
        )
        
        item = response.get('Item', {})
        passphrase = item.get('passphrase', '')
        
        return create_response(200, {'passphrase': passphrase})
        
    except Exception as e:
        logger.error(f"Error getting passphrase: {str(e)}", exc_info=True)
        return create_response(500, {'message': 'Error retrieving passphrase'})


def set_passphrase(body):
    """
    Set the PlantPass access passphrase
    """
    try:
        passphrase = body.get('passphrase')
        
        if passphrase is None:
            return create_response(400, {'message': 'Passphrase is required'})
        
        if not isinstance(passphrase, str):
            return create_response(400, {'message': 'Passphrase must be a string'})
        
        dynamodb = get_dynamodb_client()
        table = dynamodb.Table(PLANTPASS_ACCESS_TABLE_NAME)
        
        table.put_item(
            Item={
                'config_id': 'plantpass_access',
                'passphrase': passphrase
            }
        )
        
        return create_response(200, {
            'message': 'Passphrase updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error setting passphrase: {str(e)}", exc_info=True)
        return create_response(500, {'message': 'Error updating passphrase'})


def verify_passphrase(body):
    """
    Verify the provided passphrase against the stored one.
    Returns a JWT token with 'staff' role on success.
    """
    try:
        provided_passphrase = body.get('passphrase')
        
        if not provided_passphrase:
            return create_response(400, {'message': 'Passphrase is required'})
        
        dynamodb = get_dynamodb_client()
        table = dynamodb.Table(PLANTPASS_ACCESS_TABLE_NAME)
        
        response = table.get_item(
            Key={'config_id': 'plantpass_access'}
        )
        
        item = response.get('Item', {})
        stored_passphrase = item.get('passphrase', '')
        
        if provided_passphrase == stored_passphrase:
            # Generate JWT token with staff role
            if not JWT_SECRET:
                logger.error("JWT_SECRET not configured")
                return create_response(500, {'message': 'Server configuration error'})
            
            token = jwt.encode(
                {
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
                    "role": "staff",
                    "iat": datetime.datetime.utcnow()
                },
                JWT_SECRET,
                algorithm="HS256"
            )
            
            return create_response(200, {
                'message': 'Passphrase verified',
                'token': token
            })
        else:
            return create_response(401, {'message': 'Incorrect passphrase'})
        
    except Exception as e:
        logger.error(f"Error verifying passphrase: {str(e)}", exc_info=True)
        return create_response(500, {'message': 'Error verifying passphrase'})
