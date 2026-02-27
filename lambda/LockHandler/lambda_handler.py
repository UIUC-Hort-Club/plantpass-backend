import json
import os
import logging
from dynamodb_client import get_dynamodb_client
from response_utils import create_response
from auth_middleware import extract_token, verify_token, AuthError

LOCK_TABLE_NAME = os.environ.get('LOCK_TABLE_NAME', 'PlantPass-Locks')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Handle lock state operations for admin resources
    """
    try:
        # All lock operations require admin authentication
        try:
            token = extract_token(event)
            decoded = verify_token(token)
            
            if decoded.get("role") != "admin":
                return create_response(403, {"message": "Admin access required"})
                
            event["auth"] = decoded
        except AuthError as e:
            return create_response(e.status_code, {"error": e.message})
        
        route_key = event.get('routeKey', '')
        path_parameters = event.get('pathParameters', {})
        resource_type = path_parameters.get('resourceType', '')
        
        logger.info(f"Route Key: {route_key}, Resource Type: {resource_type}")
        
        if not resource_type:
            return create_response(400, {'message': 'Resource type is required'})
        
        # Validate resource type
        valid_resources = ['products', 'discounts', 'payment_methods']
        if resource_type not in valid_resources:
            return create_response(400, {'message': f'Invalid resource type. Must be one of: {", ".join(valid_resources)}'})
        
        # Match route pattern
        if route_key.startswith('GET /lock/'):
            return get_lock_state(resource_type)
        elif route_key.startswith('PUT /lock/'):
            body = json.loads(event.get('body', '{}'))
            return set_lock_state(resource_type, body)
        else:
            return create_response(404, {'message': f'Route not found: {route_key}'})
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        return create_response(500, {'message': 'Internal server error'})


def get_lock_state(resource_type):
    """
    Get the current lock state for a resource
    """
    try:
        dynamodb = get_dynamodb_client()
        table = dynamodb.Table(LOCK_TABLE_NAME)
        
        response = table.get_item(
            Key={'resource_type': resource_type}
        )
        
        item = response.get('Item', {})
        is_locked = item.get('is_locked', False)
        
        return create_response(200, {
            'resourceType': resource_type,
            'isLocked': is_locked
        })
        
    except Exception as e:
        print(f"Error getting lock state: {str(e)}")
        return create_response(500, {'message': 'Error retrieving lock state'})


def set_lock_state(resource_type, body):
    """
    Set the lock state for a resource
    """
    try:
        is_locked = body.get('isLocked')
        
        if is_locked is None:
            return create_response(400, {'message': 'isLocked field is required'})
        
        if not isinstance(is_locked, bool):
            return create_response(400, {'message': 'isLocked must be a boolean'})
        
        dynamodb = get_dynamodb_client()
        table = dynamodb.Table(LOCK_TABLE_NAME)
        
        table.put_item(
            Item={
                'resource_type': resource_type,
                'is_locked': is_locked
            }
        )
        
        return create_response(200, {
            'resourceType': resource_type,
            'isLocked': is_locked,
            'message': f'Lock state updated successfully'
        })
        
    except Exception as e:
        print(f"Error setting lock state: {str(e)}")
        return create_response(500, {'message': 'Error updating lock state'})
