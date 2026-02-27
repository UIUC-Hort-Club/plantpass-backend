import json
import logging
import os
import boto3
import secrets
import string
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TEMP_PASSWORD_TABLE', 'temp_passwords')
table = dynamodb.Table(table_name)

def generate_temp_password(length=12):
    """Generate a secure random temporary password"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def store_temp_password(temp_password_hash):
    """Store temporary password hash with 15-minute expiration"""
    expiration_time = int((datetime.utcnow() + timedelta(minutes=15)).timestamp())
    
    logger.info(f"Storing temp password in table: {table_name}")
    logger.info(f"Expiration timestamp: {expiration_time}")
    
    table.put_item(
        Item={
            'id': 'temp_password',
            'password_hash': temp_password_hash,
            'expiration': expiration_time
        }
    )
    
    logger.info(f"Temporary password stored successfully, expires at {expiration_time}")

def get_temp_password_hash():
    """Retrieve temporary password hash if not expired"""
    try:
        logger.info(f"Retrieving temp password from table: {table_name}")
        response = table.get_item(Key={'id': 'temp_password'})
        
        if 'Item' not in response:
            logger.info("No temp password found in DynamoDB")
            return None
        
        item = response['Item']
        expiration = int(item.get('expiration', 0))  # Convert Decimal to int
        current_time = int(datetime.utcnow().timestamp())  # Convert to int
        
        logger.info(f"Current timestamp: {current_time}")
        logger.info(f"Expiration timestamp: {expiration}")
        logger.info(f"Time remaining: {expiration - current_time} seconds")
        
        if current_time > expiration:
            logger.info("Temporary password has expired")
            delete_temp_password()
            return None
        
        logger.info("Temp password retrieved successfully and not expired")
        return item.get('password_hash')
    
    except Exception as e:
        logger.error(f"Error retrieving temp password: {e}", exc_info=True)
        return None

def delete_temp_password():
    """Delete temporary password from storage"""
    try:
        table.delete_item(Key={'id': 'temp_password'})
        logger.info("Temporary password deleted")
    except Exception as e:
        logger.error(f"Error deleting temp password: {e}")
