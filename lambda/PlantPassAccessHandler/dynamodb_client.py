import boto3
import os

def get_dynamodb_client():
    """
    Get DynamoDB client
    """
    region = os.environ.get('AWS_REGION', 'us-east-1')
    return boto3.resource('dynamodb', region_name=region)
