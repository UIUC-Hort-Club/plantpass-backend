import json
import os
import logging
from dynamodb_client import get_dynamodb_client
from response_utils import create_response
from auth_middleware import is_public_endpoint, extract_token, verify_token, AuthError

FEATURE_TOGGLES_TABLE_NAME = os.environ.get('FEATURE_TOGGLES_TABLE_NAME', 'PlantPass-FeatureToggles')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Default feature toggle values
DEFAULT_FEATURES = {
    'collectEmailAddresses': True,
    'passwordProtectAdmin': True,
    'protectPlantPassAccess': False
}

def lambda_handler(event, context):
    """
    Handle feature toggle operations
    """
    try:
        route_key = event.get('routeKey', '')
        
        logger.info(f"Route Key: {route_key}")
        
        # Check if endpoint requires authentication
        if not is_public_endpoint(route_key):
            try:
                token = extract_token(event)
                decoded = verify_token(token)
                event["auth"] = decoded
                
                # PUT /feature-toggles requires admin role
                if route_key == "PUT /feature-toggles" and decoded.get("role") != "admin":
                    return create_response(403, {"message": "Admin access required"})
                    
            except AuthError as e:
                return create_response(e.status_code, {"error": e.message})
        
        if route_key == 'GET /feature-toggles':
            return get_feature_toggles()
        elif route_key == 'PUT /feature-toggles':
            body = json.loads(event.get('body', '{}'))
            return set_feature_toggles(body)
        else:
            return create_response(404, {'message': f'Route not found: {route_key}'})
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        return create_response(500, {'message': 'Internal server error'})


def get_feature_toggles():
    """
    Get the current feature toggle settings
    """
    try:
        dynamodb = get_dynamodb_client()
        table = dynamodb.Table(FEATURE_TOGGLES_TABLE_NAME)
        
        response = table.get_item(
            Key={'config_id': 'feature_toggles'}
        )
        
        item = response.get('Item', {})
        
        # Return stored features or defaults
        features = {
            'collectEmailAddresses': item.get('collectEmailAddresses', DEFAULT_FEATURES['collectEmailAddresses']),
            'passwordProtectAdmin': item.get('passwordProtectAdmin', DEFAULT_FEATURES['passwordProtectAdmin']),
            'protectPlantPassAccess': item.get('protectPlantPassAccess', DEFAULT_FEATURES['protectPlantPassAccess'])
        }
        
        return create_response(200, features)
        
    except Exception as e:
        logger.error(f"Error getting feature toggles: {str(e)}", exc_info=True)
        return create_response(500, {'message': 'Error retrieving feature toggles'})


def set_feature_toggles(body):
    """
    Set the feature toggle settings
    """
    try:
        collect_email = body.get('collectEmailAddresses')
        password_protect = body.get('passwordProtectAdmin')
        protect_plantpass = body.get('protectPlantPassAccess')
        
        # Validate required fields
        if collect_email is None or password_protect is None or protect_plantpass is None:
            return create_response(400, {
                'message': 'All feature toggle fields are required'
            })
        
        # Validate types
        if not isinstance(collect_email, bool) or not isinstance(password_protect, bool) or not isinstance(protect_plantpass, bool):
            return create_response(400, {
                'message': 'Feature toggle values must be boolean'
            })
        
        dynamodb = get_dynamodb_client()
        table = dynamodb.Table(FEATURE_TOGGLES_TABLE_NAME)
        
        table.put_item(
            Item={
                'config_id': 'feature_toggles',
                'collectEmailAddresses': collect_email,
                'passwordProtectAdmin': password_protect,
                'protectPlantPassAccess': protect_plantpass
            }
        )
        
        return create_response(200, {
            'collectEmailAddresses': collect_email,
            'passwordProtectAdmin': password_protect,
            'protectPlantPassAccess': protect_plantpass,
            'message': 'Feature toggles updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error setting feature toggles: {str(e)}", exc_info=True)
        return create_response(500, {'message': 'Error updating feature toggles'})
