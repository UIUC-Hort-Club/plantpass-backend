import logging
import os
from botocore.exceptions import ClientError
from decimal import Decimal
from dynamodb_client import get_table

logger = logging.getLogger()
logger.setLevel(logging.INFO)

table = get_table('DISCOUNTS_TABLE', 'discounts')

def get_all_discounts():
    try:
        response = table.scan()
        discounts = response.get('Items', [])
        
        for discount in discounts:
            if 'value' in discount and isinstance(discount['value'], Decimal):
                discount['value'] = float(discount['value'])
            
            if 'sort_order' in discount and isinstance(discount['sort_order'], Decimal):
                discount['sort_order'] = int(discount['sort_order'])
        
        discounts.sort(key=lambda x: x.get('sort_order', 0))
        return discounts
    except ClientError as e:
        logger.error(f"Error retrieving discounts: {e}")
        raise Exception(f"Failed to retrieve discounts: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in get_all_discounts: {e}")
        raise Exception(f"Failed to retrieve discounts: {e}")

def replace_all_discounts(discounts_data):
    try:
        existing_discounts = get_all_discounts()
        
        with table.batch_writer() as batch:
            for discount in existing_discounts:
                batch.delete_item(Key={'name': discount['name']})
        
        created_count = 0
        with table.batch_writer() as batch:
            for discount_data in discounts_data:
                if 'name' not in discount_data or 'type' not in discount_data:
                    logger.warning(f"Skipping invalid discount data: {discount_data}")
                    continue
                
                if discount_data['type'] not in ['percent', 'dollar']:
                    logger.warning(f"Skipping discount with invalid type: {discount_data}")
                    continue
                
                item = {
                    'name': discount_data['name'],
                    'type': discount_data['type'],
                    'value': Decimal(str(discount_data.get('value', 0))),
                    'sort_order': int(discount_data.get('sort_order', 0))
                }
                
                batch.put_item(Item=item)
                created_count += 1
        
        return {"deleted": len(existing_discounts), "created": created_count}
        
    except ClientError as e:
        logger.error(f"DynamoDB error replacing discounts: {e}")
        raise Exception(f"Failed to replace discounts: {e}")
    except Exception as e:
        logger.error(f"Error replacing discounts: {e}")
        raise Exception(f"Failed to replace discounts: {e}")