import json
import logging
import os
import boto3
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')

def get_connections_table():
    """Get the connections table, with error handling."""
    table_name = os.environ.get('CONNECTIONS_TABLE')
    if not table_name:
        raise ValueError("CONNECTIONS_TABLE environment variable not set")
    return dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Handle WebSocket connections, disconnections, and default messages.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    route_key = event.get('requestContext', {}).get('routeKey')
    connection_id = event.get('requestContext', {}).get('connectionId')
    
    try:
        if route_key == '$connect':
            return handle_connect(connection_id)
        elif route_key == '$disconnect':
            return handle_disconnect(connection_id)
        elif route_key == '$default':
            return handle_default(connection_id, event)
        else:
            logger.warning(f"Unknown route: {route_key}")
            return {'statusCode': 400, 'body': 'Unknown route'}
    
    except Exception as e:
        logger.error(f"Error handling WebSocket event: {e}", exc_info=True)
        return {'statusCode': 500, 'body': str(e)}


def handle_connect(connection_id):
    """
    Store connection ID in DynamoDB when client connects.
    """
    try:
        connections_table = get_connections_table()
        
        # TTL set to 2 hours from now (in case disconnect doesn't fire)
        ttl = int((datetime.now() + timedelta(hours=2)).timestamp())
        
        connections_table.put_item(
            Item={
                'connectionId': connection_id,
                'connectedAt': int(datetime.now().timestamp()),
                'ttl': ttl
            }
        )
        
        logger.info(f"Connection stored: {connection_id}")
        return {'statusCode': 200, 'body': 'Connected'}
    
    except Exception as e:
        logger.error(f"Error storing connection: {e}", exc_info=True)
        return {'statusCode': 500, 'body': str(e)}


def handle_disconnect(connection_id):
    """
    Remove connection ID from DynamoDB when client disconnects.
    """
    try:
        connections_table = get_connections_table()
        
        connections_table.delete_item(
            Key={'connectionId': connection_id}
        )
        
        logger.info(f"Connection removed: {connection_id}")
        return {'statusCode': 200, 'body': 'Disconnected'}
    
    except Exception as e:
        logger.error(f"Error removing connection: {e}", exc_info=True)
        return {'statusCode': 500, 'body': str(e)}


def handle_default(connection_id, event):
    """
    Handle any other messages (ping/pong, etc).
    """
    logger.info(f"Default route called for connection: {connection_id}")
    return {'statusCode': 200, 'body': 'Message received'}
