import logging
from botocore.exceptions import ClientError
from dynamodb_client import get_table

logger = logging.getLogger()
logger.setLevel(logging.INFO)

table = get_table('PAYMENT_METHODS_TABLE', 'payment_methods')

def get_all_payment_methods():
    try:
        response = table.scan()
        payment_methods = response.get('Items', [])
        
        for method in payment_methods:
            if 'sort_order' in method:
                method['sort_order'] = int(method['sort_order'])
        
        payment_methods.sort(key=lambda x: x.get('sort_order', 0))
        return payment_methods
    except ClientError as e:
        logger.error(f"Error retrieving payment methods: {e}")
        raise Exception(f"Failed to retrieve payment methods: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in get_all_payment_methods: {e}")
        raise Exception(f"Failed to retrieve payment methods: {e}")

def replace_all_payment_methods(payment_methods_data):
    try:
        existing_methods = get_all_payment_methods()
        
        with table.batch_writer() as batch:
            for method in existing_methods:
                batch.delete_item(Key={'name': method['name']})
        
        created_count = 0
        with table.batch_writer() as batch:
            for method_data in payment_methods_data:
                if 'name' not in method_data or not method_data['name'].strip():
                    logger.warning(f"Skipping invalid payment method data: {method_data}")
                    continue
                
                item = {
                    'name': method_data['name'].strip(),
                    'sort_order': int(method_data.get('sort_order', 0))
                }
                
                batch.put_item(Item=item)
                created_count += 1
        
        return {"deleted": len(existing_methods), "created": created_count}
        
    except ClientError as e:
        logger.error(f"DynamoDB error replacing payment methods: {e}")
        raise Exception(f"Failed to replace payment methods: {e}")
    except Exception as e:
        logger.error(f"Error replacing payment methods: {e}")
        raise Exception(f"Failed to replace payment methods: {e}")
