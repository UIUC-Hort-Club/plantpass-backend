import boto3

_dynamodb_resource = None

def get_dynamodb_client():
    """
    Get or create a DynamoDB resource client (singleton pattern)
    """
    global _dynamodb_resource
    if _dynamodb_resource is None:
        _dynamodb_resource = boto3.resource('dynamodb')
    return _dynamodb_resource
