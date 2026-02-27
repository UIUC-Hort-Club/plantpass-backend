"""
Authentication and authorization middleware for Lambda functions.
Validates JWT tokens and enforces role-based access control.
"""
import os
import jwt
import logging
from functools import wraps
from response_utils import create_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)

JWT_SECRET = os.environ.get("JWT_SECRET")

class AuthError(Exception):
    """Custom exception for authentication errors"""
    def __init__(self, message, status_code=401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def extract_token(event):
    """Extract JWT token from Authorization header"""
    headers = event.get("headers", {})
    
    # Handle case-insensitive headers
    auth_header = None
    for key, value in headers.items():
        if key.lower() == "authorization":
            auth_header = value
            break
    
    if not auth_header:
        raise AuthError("Missing Authorization header", 401)
    
    if not auth_header.startswith("Bearer "):
        raise AuthError("Invalid Authorization header format", 401)
    
    return auth_header.replace("Bearer ", "")


def verify_token(token):
    """Verify JWT token and return decoded payload"""
    if not JWT_SECRET:
        logger.error("JWT_SECRET not configured")
        raise AuthError("Server configuration error", 500)
    
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired", 401)
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise AuthError("Invalid token", 401)


def require_auth(role=None):
    """
    Decorator to require authentication for Lambda handlers.
    
    Args:
        role: Optional role requirement ('admin' or 'staff'). 
              If None, any authenticated user is allowed.
    """
    def decorator(handler_func):
        @wraps(handler_func)
        def wrapper(event, context):
            try:
                # Extract and verify token
                token = extract_token(event)
                decoded = verify_token(token)
                
                # Check role if specified
                if role:
                    token_role = decoded.get("role", "staff")
                    
                    # Admin can access everything
                    if token_role != "admin" and role == "admin":
                        raise AuthError("Insufficient permissions", 403)
                
                # Add decoded token to event for handler to use
                event["auth"] = decoded
                
                # Call the actual handler
                return handler_func(event, context)
                
            except AuthError as e:
                logger.warning(f"Authentication error: {e.message}")
                return create_response(e.status_code, {"error": e.message})
            except Exception as e:
                logger.error(f"Unexpected auth error: {e}", exc_info=True)
                return create_response(500, {"error": "Internal server error"})
        
        return wrapper
    return decorator


def is_public_endpoint(route_key):
    """
    Check if an endpoint should be publicly accessible.
    """
    public_endpoints = [
        "GET /transactions/{purchase_id}",  # Customer order lookup
        "POST /admin/login",  # Login endpoint
        "POST /admin/forgot-password",  # Password reset
        "POST /plantpass-access/verify",  # PlantPass passphrase verification
        "GET /feature-toggles",  # Feature toggles (needed for UI)
        "GET /products",  # Products list (needed for order entry)
        "GET /discounts",  # Discounts list (needed for order entry)
        "GET /payment-methods",  # Payment methods (needed for checkout)
    ]
    
    return route_key in public_endpoints


def require_staff_auth(handler_func):
    """Require staff-level authentication"""
    return require_auth(role="staff")(handler_func)


def require_admin_auth(handler_func):
    """Require admin-level authentication"""
    return require_auth(role="admin")(handler_func)
