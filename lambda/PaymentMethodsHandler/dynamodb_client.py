import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')

def get_table(env_var_name, default_table_name):
    table_name = os.environ.get(env_var_name, default_table_name)
    logger.info(f"Using DynamoDB table: {table_name}")
    return dynamodb.Table(table_name)
