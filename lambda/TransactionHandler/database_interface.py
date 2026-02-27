import os
import json
import logging
import boto3
from decimal import Decimal
from botocore.exceptions import ClientError
from decimal_utils import decimal_to_float
from dynamodb_client import get_table
from transaction import Transaction

logger = logging.getLogger()
logger.setLevel(logging.INFO)

table = get_table('TRANSACTIONS_TABLE', 'transactions')
lambda_client = boto3.client('lambda')
EMAIL_LAMBDA_ARN = os.environ.get('EMAIL_LAMBDA_ARN')

def create_transaction(transaction_data):
    max_retries = 5
    
    for attempt in range(max_retries):
        try:
            transaction = Transaction.from_json(transaction_data)
            
            db_item = transaction.to_db_record()
            table.put_item(
                Item=db_item,
                ConditionExpression='attribute_not_exists(purchase_id)'
            )
            
            return transaction.to_dict()
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                if attempt == max_retries - 1:
                    raise Exception("Failed to generate unique transaction ID after multiple attempts")
                continue
            else:
                logger.error(f"DynamoDB error creating transaction: {e}", exc_info=True)
                raise Exception(f"Failed to create transaction: {e}")
        except Exception as e:
            logger.error(f"Error creating transaction: {e}", exc_info=True)
            raise Exception(f"Failed to create transaction: {e}")

def read_transaction(transaction_id):
    try:
        response = table.get_item(Key={'purchase_id': transaction_id})
        
        if 'Item' not in response:
            return None
            
        transaction = decimal_to_float(response['Item'])
        return transaction
        
    except ClientError as e:
        logger.error(f"DynamoDB error reading transaction {transaction_id}: {e}")
        raise Exception(f"Failed to read transaction: {e}")
    except Exception as e:
        logger.error(f"Error reading transaction {transaction_id}: {e}")
        raise Exception(f"Failed to read transaction: {e}")

def update_transaction(transaction_id, updated_data):
    try:
        existing_data = read_transaction(transaction_id)
        if not existing_data:
            raise Exception(f"Transaction {transaction_id} not found")
        
        transaction = Transaction.from_db_record(existing_data)
        
        # Track if payment status changed to paid
        was_paid = transaction.payment.get('paid', False)
        
        if "items" in updated_data:
            transaction.update_items(updated_data["items"])
            
        if "discounts" in updated_data:
            transaction.update_discounts(updated_data["discounts"])
            
        if "voucher" in updated_data:
            transaction.update_voucher(updated_data["voucher"])
            
        if "payment" in updated_data:
            transaction.update_payment(updated_data["payment"])
        
        db_item = transaction.to_db_record()
        table.put_item(Item=db_item)
        
        transaction_dict = transaction.to_dict()
        
        # Send receipt email if order just completed and email provided
        is_now_paid = transaction.payment.get('paid', False)
        if not was_paid and is_now_paid and transaction.customer_email and EMAIL_LAMBDA_ARN:
            try:
                email_payload = {
                    "routeKey": "POST /email/receipt",
                    "body": json.dumps({
                        "email": transaction.customer_email,
                        "transaction": transaction_dict
                    })
                }
                
                lambda_client.invoke(
                    FunctionName=EMAIL_LAMBDA_ARN,
                    InvocationType='Event',
                    Payload=json.dumps(email_payload)
                )
                
                logger.info(f"Receipt email triggered for {transaction.customer_email}")
            except Exception as e:
                logger.error(f"Failed to trigger receipt email: {e}")
        
        return transaction_dict
        
    except ClientError as e:
        logger.error(f"DynamoDB error updating transaction {transaction_id}: {e}")
        raise Exception(f"Failed to update transaction: {e}")
    except Exception as e:
        logger.error(f"Error updating transaction {transaction_id}: {e}")
        raise Exception(f"Failed to update transaction: {e}")

def delete_transaction(transaction_id):
    try:
        table.delete_item(Key={'purchase_id': transaction_id})
        
    except ClientError as e:
        logger.error(f"DynamoDB error deleting transaction {transaction_id}: {e}")
        raise Exception(f"Failed to delete transaction: {e}")
    except Exception as e:
        logger.error(f"Error deleting transaction {transaction_id}: {e}")
        raise Exception(f"Failed to delete transaction: {e}")

def get_recent_unpaid_transactions(limit=5):
    """
    Get recent unpaid transactions using GSI for optimal performance.
    Falls back to scan if GSI is not available.
    """
    try:
        # Try to use GSI for better performance
        try:
            response = table.query(
                IndexName='payment-status-timestamp-index',
                KeyConditionExpression='payment_status = :status',
                ExpressionAttributeValues={
                    ':status': 'unpaid'
                },
                ScanIndexForward=False,  # Sort descending (newest first)
                Limit=limit
            )
            
            transactions = response['Items']
            result = decimal_to_float(transactions)
            logger.info(f"Retrieved {len(result)} unpaid transactions using GSI")
            return result
            
        except ClientError as gsi_error:
            # GSI might not exist yet, fall back to scan
            if gsi_error.response['Error']['Code'] == 'ValidationException':
                logger.warning("GSI not found, falling back to table scan")
            else:
                raise
        
        # Fallback: Use table scan (original implementation)
        response = table.scan()
        transactions = response['Items']
        
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            transactions.extend(response['Items'])
        
        unpaid_transactions = [
            t for t in transactions 
            if not t.get('payment', {}).get('paid', False)
        ]
        
        unpaid_transactions.sort(
            key=lambda x: x.get('timestamp', 0), 
            reverse=True
        )
        
        limited_transactions = unpaid_transactions[:limit]
        result = decimal_to_float(limited_transactions)
        logger.info(f"Retrieved {len(result)} unpaid transactions using table scan")
        return result
        
    except ClientError as e:
        logger.error(f"DynamoDB error getting recent unpaid transactions: {e}")
        raise Exception(f"Failed to get recent unpaid transactions: {e}")
    except Exception as e:
        logger.error(f"Error getting recent unpaid transactions: {e}")
        raise Exception(f"Failed to get recent unpaid transactions: {e}")