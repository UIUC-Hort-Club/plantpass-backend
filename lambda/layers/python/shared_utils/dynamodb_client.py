import boto3
import os

_dynamodb = None

def get_dynamodb_resource():
    """Get or create DynamoDB resource (singleton pattern)."""
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource('dynamodb')
    return _dynamodb

def get_table(table_env_var, default_name):
    """Get DynamoDB table by environment variable or default name."""
    dynamodb = get_dynamodb_resource()
    table_name = os.environ.get(table_env_var, default_name)
    return dynamodb.Table(table_name)
