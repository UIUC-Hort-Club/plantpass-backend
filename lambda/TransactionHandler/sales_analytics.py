import os
import logging
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError
from decimal_utils import decimal_to_float
from dynamodb_client import get_table
from transaction import Transaction

CST = timezone(timedelta(hours=-6))

logger = logging.getLogger()
logger.setLevel(logging.INFO)

table = get_table('TRANSACTIONS_TABLE', 'transactions')


def compute_sales_analytics():
    """
    Compute sales analytics such as total sales, average order value, etc.
    
    Analytics (cards and graph) only include PAID transactions.
    Transaction table includes all transactions regardless of payment status.
    
    Returns analytics grouped into 30-minute time blocks aligned to clock boundaries.
    """
    try:
        response = table.scan()
        transactions = response['Items']
        
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            transactions.extend(response['Items'])
        
        if not transactions:
            return {
                "total_sales": 0.0,
                "total_orders": 0,
                "total_units_sold": 0,
                "average_items_per_order": 0.0,
                "average_order_value": 0.0,
                "sales_over_time": {},
                "transactions": []
            }
        
        transactions = decimal_to_float(transactions)
        
        paid_transactions = []
        total_sales = 0.0
        total_units_sold = 0
        sales_by_time_bucket = {}
        transaction_summaries = []
        
        for transaction_data in transactions:
            # Create Transaction object to get summary
            transaction = Transaction.from_db_record(transaction_data)
            summary = transaction.get_summary()
            
            transaction_summaries.append(summary)
            
            is_paid = summary.get("paid", False)
            if is_paid is True or is_paid == "true" or str(is_paid).lower() == "true":
                paid_transactions.append(transaction)
                total_sales += summary["grand_total"]
                total_units_sold += summary["total_quantity"]
                
                timestamp = transaction.timestamp
                if timestamp:
                    dt = datetime.fromtimestamp(timestamp, tz=CST)
                    minute = 0 if dt.minute < 30 else 30
                    bucket_time = dt.replace(minute=minute, second=0, microsecond=0)
                    bucket_key = bucket_time.strftime("%m-%d-%Y %I:%M %p")
                    
                    if bucket_key not in sales_by_time_bucket:
                        sales_by_time_bucket[bucket_key] = 0.0
                    sales_by_time_bucket[bucket_key] += summary["grand_total"]
        
        total_orders = len(paid_transactions)
        
        average_items_per_order = total_units_sold / total_orders if total_orders > 0 else 0.0
        average_order_value = total_sales / total_orders if total_orders > 0 else 0.0
        
        if paid_transactions:
            timestamps = [t.timestamp for t in paid_transactions if t.timestamp]
            if timestamps:
                min_time = min(timestamps)
                max_time = max(timestamps)
                
                current_time = datetime.fromtimestamp(min_time, tz=CST)
                end_time = datetime.fromtimestamp(max_time, tz=CST)
                
                while current_time <= end_time:
                    minute = 0 if current_time.minute < 30 else 30
                    bucket_time = current_time.replace(minute=minute, second=0, microsecond=0)
                    bucket_key = bucket_time.strftime("%m-%d-%Y %I:%M %p")
                    
                    if bucket_key not in sales_by_time_bucket:
                        sales_by_time_bucket[bucket_key] = 0.0
                    
                    current_time += timedelta(minutes=30)
        
        analytics = {
            "total_sales": round(total_sales, 2),
            "total_orders": total_orders,
            "total_units_sold": total_units_sold,
            "average_items_per_order": round(average_items_per_order, 2),
            "average_order_value": round(average_order_value, 2),
            "sales_over_time": sales_by_time_bucket,
            "transactions": transaction_summaries
        }
        
        logger.info(f"Analytics computed for {total_orders} transactions")
        return analytics
        
    except ClientError as e:
        logger.error(f"DynamoDB error computing analytics: {e}")
        raise Exception(f"Failed to compute analytics: {e}")
    except Exception as e:
        logger.error(f"Error computing analytics: {e}")
        raise Exception(f"Failed to compute analytics: {e}")


def export_transaction_data():
    """
    Export all transaction data in a format suitable for export (e.g., CSV, JSON).
    Note: For MVP, returning JSON data directly. For production, consider S3 + presigned URLs.
    """
    try:
        response = table.scan()
        transactions = response['Items']
        
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            transactions.extend(response['Items'])
        
        transactions = decimal_to_float(transactions)
        
        logger.info(f"Exported {len(transactions)} transactions")
        return transactions
        
    except ClientError as e:
        logger.error(f"DynamoDB error exporting data: {e}")
        raise Exception(f"Failed to export data: {e}")
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise Exception(f"Failed to export data: {e}")


def clear_all_transactions():
    """
    Clear all transactions from the database.
    
    Returns the number of transactions that were deleted.
    """
    try:
        response = table.scan()
        transactions = response['Items']
        
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            transactions.extend(response['Items'])
        
        if not transactions:
            logger.info("No transactions found to clear")
            return 0
        
        with table.batch_writer() as batch:
            for transaction in transactions:
                batch.delete_item(Key={'purchase_id': transaction['purchase_id']})
        
        cleared_count = len(transactions)
        logger.info(f"Successfully cleared {cleared_count} transactions")
        return cleared_count
        
    except ClientError as e:
        logger.error(f"DynamoDB error clearing transactions: {e}")
        raise Exception(f"Failed to clear transactions: {e}")
    except Exception as e:
        logger.error(f"Error clearing transactions: {e}")
        raise Exception(f"Failed to clear transactions: {e}")