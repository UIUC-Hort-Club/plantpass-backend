import json
import logging
from response_utils import create_response
from database_interface import (
    create_transaction,
    read_transaction,
    update_transaction,
    delete_transaction,
    get_recent_unpaid_transactions
)
from sales_analytics import (
    compute_sales_analytics,
    export_transaction_data,
    clear_all_transactions
)
from csv_export import generate_csv_export
from websocket_notifier import notify_transaction_update
from auth_middleware import require_auth, is_public_endpoint

# Import validation from Lambda Layer
try:
    from shared_utils.validation import validate_transaction_data, validate_order_id
except ImportError:
    # Fallback for local development
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../layers/python'))
    from shared_utils.validation import validate_transaction_data, validate_order_id

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        route_key = event.get("routeKey", "")
        
        # Check if endpoint requires authentication
        if not is_public_endpoint(route_key):
            # Apply authentication check
            from auth_middleware import extract_token, verify_token, AuthError
            try:
                token = extract_token(event)
                decoded = verify_token(token)
                event["auth"] = decoded
                
                # Check role-based permissions for admin-only operations
                admin_only_routes = [
                    "DELETE /transactions/clear-all",
                    "GET /transactions/export-data",
                ]
                
                if route_key in admin_only_routes:
                    if decoded.get("role") != "admin":
                        return create_response(403, {"message": "Admin access required"})
                        
            except AuthError as e:
                return create_response(e.status_code, {"error": e.message})
        
        path_params = event.get("pathParameters") or {}
        body = json.loads(event.get("body") or "{}")

        if route_key == "POST /transactions":
            # Validate transaction data
            is_valid, validation_errors = validate_transaction_data(body)
            if not is_valid:
                logger.warning(f"Transaction validation failed: {validation_errors}")
                return create_response(400, {
                    "message": "Invalid transaction data",
                    "errors": validation_errors
                })
            
            transaction = create_transaction(body)
            
            try:
                notify_transaction_update('created', transaction)
            except Exception as notify_error:
                logger.error(f"Failed to send WebSocket notification: {notify_error}")
            
            return create_response(201, {"message": "Transaction created successfully", "transaction": transaction})

        elif route_key == "GET /transactions/{purchase_id}":
            purchase_id = path_params.get("purchase_id")
            if not purchase_id:
                return create_response(400, {"message": "purchase_id required"})
            
            # Validate order ID format
            if not validate_order_id(purchase_id):
                return create_response(400, {"message": "Invalid order ID format. Expected format: ABC-DEF"})
            
            transaction = read_transaction(purchase_id)
            if not transaction:
                return create_response(404, {"message": "Transaction not found"})
            
            return create_response(200, transaction)
        
        elif route_key == "GET /transactions/recent-unpaid":
            query_params = event.get("queryStringParameters") or {}
            limit = int(query_params.get("limit", 5))
            
            recent_transactions = get_recent_unpaid_transactions(limit)
            return create_response(200, {"transactions": recent_transactions})

        elif route_key == "PUT /transactions/{purchase_id}":
            purchase_id = path_params.get("purchase_id")
            if not purchase_id:
                return create_response(400, {"message": "purchase_id required"})
            
            # Validate order ID format
            if not validate_order_id(purchase_id):
                return create_response(400, {"message": "Invalid order ID format. Expected format: ABC-DEF"})
            
            # Validate update data (partial validation - only validate provided fields)
            if 'items' in body or 'discounts' in body or 'voucher' in body:
                is_valid, validation_errors = validate_transaction_data(body)
                if not is_valid:
                    logger.warning(f"Transaction update validation failed: {validation_errors}")
                    return create_response(400, {
                        "message": "Invalid transaction data",
                        "errors": validation_errors
                    })
            
            updated_transaction = update_transaction(purchase_id, body)
            
            try:
                notify_transaction_update('updated', updated_transaction)
            except Exception as notify_error:
                logger.error(f"Failed to send WebSocket notification: {notify_error}")
            
            return create_response(200, {"transaction": updated_transaction})

        elif route_key == "DELETE /transactions/{purchase_id}":
            purchase_id = path_params.get("purchase_id")
            if not purchase_id:
                return create_response(400, {"message": "purchase_id required"})
            
            delete_transaction(purchase_id)
            
            try:
                notify_transaction_update('deleted', {'purchase_id': purchase_id})
            except Exception as notify_error:
                logger.error(f"Failed to send WebSocket notification: {notify_error}")
            
            return create_response(204, {})
        
        elif route_key == "GET /transactions/sales-analytics":
            analytics = compute_sales_analytics()
            return create_response(200, analytics)

        elif route_key == "GET /transactions/export-data":
            transactions = export_transaction_data()
            csv_export = generate_csv_export(transactions)
            
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type,Authorization",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "filename": csv_export['filename'],
                    "content": csv_export['content'],
                    "content_type": csv_export['content_type']
                })
            }

        elif route_key == "DELETE /transactions/clear-all":
            cleared_count = clear_all_transactions()
            
            try:
                notify_transaction_update('cleared', {'cleared_count': cleared_count})
            except Exception as notify_error:
                logger.error(f"Failed to send WebSocket notification: {notify_error}")
            
            return create_response(200, {"message": f"Successfully cleared {cleared_count} transactions", "cleared_count": cleared_count})

        else:
            return create_response(404, {"message": "Route not found"})

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return create_response(500, {"message": str(e)})
