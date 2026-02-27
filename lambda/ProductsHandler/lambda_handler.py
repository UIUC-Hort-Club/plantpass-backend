import json
import logging
from response_utils import create_response
from database_interface import (
    get_all_products,
    replace_all_products
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
                
                # PUT /products requires admin role
                if route_key == "PUT /products" and decoded.get("role") != "admin":
                    return create_response(403, {"message": "Admin access required"})
                    
            except AuthError as e:
                return create_response(e.status_code, {"error": e.message})
        
        body = json.loads(event.get("body", "{}")) if event.get("body") else {}

        if route_key == "GET /products":
            products = get_all_products()
            return create_response(200, products)

        elif route_key == "PUT /products":
            if not isinstance(body, list):
                return create_response(400, {"message": "Request body must be a list of products"})
            
            result = replace_all_products(body)
            return create_response(200, {"message": "Products replaced successfully", "result": result})

        else:
            return create_response(404, {"message": "Route not found"})

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return create_response(500, {"message": str(e)})
