import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()

# Initialize clients
dynamodb = boto3.resource('dynamodb')
apigateway_management = None  # Will be initialized when needed

def get_api_gateway_client():
    """
    Lazy initialization of API Gateway Management API client.
    """
    global apigateway_management
    
    if apigateway_management is None:
        # Get WebSocket endpoint from environment
        websocket_endpoint = os.environ.get('WEBSOCKET_ENDPOINT')
        if not websocket_endpoint:
            logger.warning("WEBSOCKET_ENDPOINT not configured, notifications disabled")
            return None
        
        apigateway_management = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=websocket_endpoint
        )
    
    return apigateway_management


def notify_transaction_update(event_type, transaction_data):
    """
    Broadcast transaction update to all connected WebSocket clients.
    
    Args:
        event_type: Type of event ('created', 'updated', 'deleted', 'cleared')
        transaction_data: Transaction data to send
    """
    try:
        client = get_api_gateway_client()
        if not client:
            logger.info("WebSocket notifications disabled")
            return
        
        connections_table_name = os.environ.get('CONNECTIONS_TABLE')
        if not connections_table_name:
            logger.warning("CONNECTIONS_TABLE not configured")
            return
        
        connections_table = dynamodb.Table(connections_table_name)
        
        # Get all active connections
        response = connections_table.scan()
        connections = response.get('Items', [])
        
        if not connections:
            logger.info("No active WebSocket connections")
            return
        
        # Prepare message
        message = {
            'type': 'transaction_update',
            'event': event_type,
            'data': transaction_data,
            'timestamp': transaction_data.get('timestamp') if isinstance(transaction_data, dict) else None
        }
        
        message_data = json.dumps(message).encode('utf-8')
        
        # Send to all connections
        stale_connections = []
        successful_sends = 0
        
        for connection in connections:
            connection_id = connection['connectionId']
            
            try:
                client.post_to_connection(
                    ConnectionId=connection_id,
                    Data=message_data
                )
                successful_sends += 1
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                
                if error_code == 'GoneException':
                    # Connection is stale, mark for removal
                    logger.info(f"Stale connection found: {connection_id}")
                    stale_connections.append(connection_id)
                else:
                    logger.error(f"Error sending to {connection_id}: {e}")
        
        # Clean up stale connections
        for connection_id in stale_connections:
            try:
                connections_table.delete_item(
                    Key={'connectionId': connection_id}
                )
                logger.info(f"Removed stale connection: {connection_id}")
            except Exception as e:
                logger.error(f"Error removing stale connection {connection_id}: {e}")
        
        logger.info(f"Sent {event_type} notification to {successful_sends} clients, removed {len(stale_connections)} stale connections")
    
    except Exception as e:
        logger.error(f"Error broadcasting WebSocket notification: {e}", exc_info=True)
