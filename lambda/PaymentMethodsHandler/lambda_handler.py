import json
import logging
from response_utils import create_response
from database_interface import (
    get_all_payment_methods,
    replace_all_payment_methods
)
from auth_middleware import is_public_endpoint, extract_token, verify_token, AuthError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        route_key = event.get("routeKey", "")
        
        # Check if endpoint requires authentication
        if not is_public_endpoint(route_key):
            try:
                token = extract_token(event)
                decoded = verify_token(token)
                event["auth"] = decoded
                
                # PUT /payment-methods requires admin role
                if route_key == "PUT /payment-methods" and decoded.get("role") != "admin":
                    return create_response(403, {"message": "Admin access required"})
                    
            except AuthError as e:
                return create_response(e.status_code, {"error": e.message})
        
        body = json.loads(event.get("body", "{}")) if event.get("body") else {}

        if route_key == "GET /payment-methods":
            payment_methods = get_all_payment_methods()
            return create_response(200, payment_methods)

        elif route_key == "PUT /payment-methods":
            if not isinstance(body, list):
                return create_response(400, {"message": "Request body must be a list of payment methods"})
            
            result = replace_all_payment_methods(body)
            return create_response(200, {"message": "Payment methods replaced successfully", "result": result})

        else:
            return create_response(404, {"message": "Route not found"})

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return create_response(500, {"message": str(e)})
