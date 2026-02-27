import boto3

_dynamodb_resource = None

def get_dynamodb_client():
    """
    Returns a singleton DynamoDB resource
    """
    global _dynamodb_resource
    if _dynamodb_resource is None:
        _dynamodb_resource = boto3.resource('dynamodb')
    return _dynamodb_resource
