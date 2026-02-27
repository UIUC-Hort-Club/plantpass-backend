"""
Comprehensive tests for TransactionHandler Lambda
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from decimal import Decimal
import sys
import os

# Mock AWS dependencies FIRST
sys.modules['boto3'] = MagicMock()
sys.modules['botocore'] = MagicMock()
sys.modules['botocore.exceptions'] = MagicMock()

# Clear any cached lambda_handler imports
if 'lambda_handler' in sys.modules:
    del sys.modules['lambda_handler']

# Add TransactionHandler to path FIRST (before any other handler)
transaction_handler_path = os.path.join(os.path.dirname(__file__), '../TransactionHandler')
# Remove any existing handler paths
sys.path = [p for p in sys.path if 'Handler' not in p or p == transaction_handler_path]
sys.path.insert(0, transaction_handler_path)


@pytest.fixture
def transaction_handler():
    """Import and return the transaction handler"""
    from lambda_handler import lambda_handler
    return lambda_handler


@pytest.fixture
def mock_database():
    """Mock all database operations"""
    with patch('lambda_handler.create_transaction') as create, \
         patch('lambda_handler.read_transaction') as read, \
         patch('lambda_handler.update_transaction') as update, \
         patch('lambda_handler.delete_transaction') as delete, \
         patch('lambda_handler.get_recent_unpaid_transactions') as recent:
        yield {
            'create': create,
            'read': read,
            'update': update,
            'delete': delete,
            'recent': recent,
        }


@pytest.fixture
def mock_websocket():
    """Mock WebSocket notifications"""
    with patch('lambda_handler.notify_transaction_update') as notify:
        yield notify


@pytest.fixture
def mock_auth():
    """Mock authentication"""
    with patch('auth_middleware.extract_token') as extract, \
         patch('auth_middleware.verify_token') as verify, \
         patch('lambda_handler.is_public_endpoint') as is_public:
        verify.return_value = {'role': 'staff', 'user_id': 'test-user'}
        is_public.return_value = False  # Default to protected endpoints
        yield {'extract': extract, 'verify': verify, 'is_public': is_public}


@pytest.fixture
def mock_public_endpoint():
    """Mock public endpoint check"""
    with patch('lambda_handler.is_public_endpoint') as is_public:
        is_public.return_value = True
        yield is_public


class TestCreateTransaction:
    def test_create_transaction_success(self, transaction_handler, mock_database, mock_websocket, mock_auth, api_gateway_event, sample_transaction_data):
        """Test successful transaction creation"""
        mock_transaction = {
            'purchase_id': 'ABC-DEF',
            'receipt': {'subtotal': 21.98, 'discount': 0, 'total': 21.98}
        }
        mock_database['create'].return_value = mock_transaction
        
        event = api_gateway_event.copy()
        event['routeKey'] = 'POST /transactions'
        event['body'] = json.dumps(sample_transaction_data)
        event['headers']['Authorization'] = 'Bearer test-token'
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        assert body['message'] == 'Transaction created successfully'
        assert body['transaction']['purchase_id'] == 'ABC-DEF'
        mock_database['create'].assert_called_once()
        mock_websocket.assert_called_once_with('created', mock_transaction)
    
    def test_create_transaction_validation_error(self, transaction_handler, mock_auth, api_gateway_event):
        """Test transaction creation with invalid data"""
        invalid_data = {
            'timestamp': 1640000000000,
            'items': [],  # Empty items should fail
            'discounts': [],
            'voucher': 0,
        }
        
        event = api_gateway_event.copy()
        event['routeKey'] = 'POST /transactions'
        event['body'] = json.dumps(invalid_data)
        event['headers']['Authorization'] = 'Bearer test-token'
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid transaction data' in body['message']
        assert 'errors' in body
    
    def test_create_transaction_websocket_failure(self, transaction_handler, mock_database, mock_websocket, mock_auth, api_gateway_event, sample_transaction_data):
        """Test transaction creation succeeds even if WebSocket fails"""
        mock_transaction = {'purchase_id': 'ABC-DEF'}
        mock_database['create'].return_value = mock_transaction
        mock_websocket.side_effect = Exception('WebSocket error')
        
        event = api_gateway_event.copy()
        event['routeKey'] = 'POST /transactions'
        event['body'] = json.dumps(sample_transaction_data)
        event['headers']['Authorization'] = 'Bearer test-token'
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 201  # Should still succeed


class TestReadTransaction:
    def test_read_transaction_success(self, transaction_handler, mock_database, mock_public_endpoint, api_gateway_event):
        """Test successful transaction retrieval"""
        mock_transaction = {
            'purchase_id': 'ABC-DEF',
            'timestamp': 1640000000000,
            'items': [],
            'receipt': {'total': 10.00}
        }
        mock_database['read'].return_value = mock_transaction
        
        event = api_gateway_event.copy()
        event['routeKey'] = 'GET /transactions/{purchase_id}'
        event['pathParameters'] = {'purchase_id': 'ABC-DEF'}
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['purchase_id'] == 'ABC-DEF'
        mock_database['read'].assert_called_once_with('ABC-DEF')
    
    def test_read_transaction_not_found(self, transaction_handler, mock_database, mock_public_endpoint, api_gateway_event):
        """Test reading non-existent transaction"""
        mock_database['read'].return_value = None
        
        event = api_gateway_event.copy()
        event['routeKey'] = 'GET /transactions/{purchase_id}'
        event['pathParameters'] = {'purchase_id': 'ABC-DEF'}
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'not found' in body['message'].lower()
    
    def test_read_transaction_invalid_id_format(self, transaction_handler, mock_public_endpoint, api_gateway_event):
        """Test reading transaction with invalid ID format"""
        event = api_gateway_event.copy()
        event['routeKey'] = 'GET /transactions/{purchase_id}'
        event['pathParameters'] = {'purchase_id': 'invalid-id'}
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid order ID format' in body['message']
    
    def test_read_transaction_missing_id(self, transaction_handler, mock_public_endpoint, api_gateway_event):
        """Test reading transaction without ID"""
        event = api_gateway_event.copy()
        event['routeKey'] = 'GET /transactions/{purchase_id}'
        event['pathParameters'] = {}
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 400


class TestUpdateTransaction:
    def test_update_transaction_payment(self, transaction_handler, mock_database, mock_websocket, mock_auth, api_gateway_event):
        """Test updating transaction payment status"""
        updated_transaction = {
            'purchase_id': 'ABC-DEF',
            'payment': {'method': 'Cash', 'paid': True}
        }
        mock_database['update'].return_value = updated_transaction
        
        event = api_gateway_event.copy()
        event['routeKey'] = 'PUT /transactions/{purchase_id}'
        event['pathParameters'] = {'purchase_id': 'ABC-DEF'}
        event['body'] = json.dumps({'payment': {'method': 'Cash', 'paid': True}})
        event['headers']['Authorization'] = 'Bearer test-token'
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['transaction']['purchase_id'] == 'ABC-DEF'
        mock_websocket.assert_called_once_with('updated', updated_transaction)
    
    def test_update_transaction_invalid_id(self, transaction_handler, mock_auth, api_gateway_event):
        """Test updating transaction with invalid ID"""
        event = api_gateway_event.copy()
        event['routeKey'] = 'PUT /transactions/{purchase_id}'
        event['pathParameters'] = {'purchase_id': 'bad-format'}
        event['body'] = json.dumps({'payment': {'paid': True}})
        event['headers']['Authorization'] = 'Bearer test-token'
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 400


class TestDeleteTransaction:
    def test_delete_transaction_success(self, transaction_handler, mock_database, mock_websocket, mock_auth, api_gateway_event):
        """Test successful transaction deletion"""
        event = api_gateway_event.copy()
        event['routeKey'] = 'DELETE /transactions/{purchase_id}'
        event['pathParameters'] = {'purchase_id': 'ABC-DEF'}
        event['headers']['Authorization'] = 'Bearer test-token'
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 204
        mock_database['delete'].assert_called_once_with('ABC-DEF')
        mock_websocket.assert_called_once()


class TestRecentUnpaidTransactions:
    def test_get_recent_unpaid_default_limit(self, transaction_handler, mock_database, mock_auth, api_gateway_event):
        """Test getting recent unpaid transactions with default limit"""
        mock_transactions = [
            {'purchase_id': 'ABC-DEF', 'total': 10.00},
            {'purchase_id': 'XYZ-QRS', 'total': 20.00},
        ]
        mock_database['recent'].return_value = mock_transactions
        
        event = api_gateway_event.copy()
        event['routeKey'] = 'GET /transactions/recent-unpaid'
        event['headers']['Authorization'] = 'Bearer test-token'
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['transactions']) == 2
        mock_database['recent'].assert_called_once_with(5)  # Default limit
    
    def test_get_recent_unpaid_custom_limit(self, transaction_handler, mock_database, mock_auth, api_gateway_event):
        """Test getting recent unpaid transactions with custom limit"""
        mock_database['recent'].return_value = []
        
        event = api_gateway_event.copy()
        event['routeKey'] = 'GET /transactions/recent-unpaid'
        event['queryStringParameters'] = {'limit': '10'}
        event['headers']['Authorization'] = 'Bearer test-token'
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 200
        mock_database['recent'].assert_called_once_with(10)


class TestSalesAnalytics:
    def test_get_sales_analytics(self, transaction_handler, api_gateway_event, mock_auth):
        """Test getting sales analytics"""
        with patch('lambda_handler.compute_sales_analytics') as mock_analytics:
            mock_analytics.return_value = {
                'total_sales': 1000.00,
                'transaction_count': 50,
                'average_transaction': 20.00
            }
            
            event = api_gateway_event.copy()
            event['routeKey'] = 'GET /transactions/sales-analytics'
            event['headers']['Authorization'] = 'Bearer token'
            
            response = transaction_handler(event, {})
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['total_sales'] == 1000.00
            assert body['transaction_count'] == 50


class TestExportData:
    def test_export_transaction_data_admin_only(self, transaction_handler, api_gateway_event):
        """Test that export requires admin role"""
        with patch('auth_middleware.extract_token') as extract, \
             patch('auth_middleware.verify_token') as verify, \
             patch('lambda_handler.is_public_endpoint') as is_public:
            verify.return_value = {'role': 'staff', 'user_id': 'test'}
            is_public.return_value = False
            
            event = api_gateway_event.copy()
            event['routeKey'] = 'GET /transactions/export-data'
            event['headers']['Authorization'] = 'Bearer token'
            
            response = transaction_handler(event, {})
            
            assert response['statusCode'] == 403
    
    def test_export_transaction_data_success(self, transaction_handler, api_gateway_event):
        """Test successful data export"""
        with patch('auth_middleware.extract_token') as extract, \
             patch('auth_middleware.verify_token') as verify, \
             patch('lambda_handler.is_public_endpoint') as is_public, \
             patch('lambda_handler.export_transaction_data') as mock_export, \
             patch('lambda_handler.generate_csv_export') as mock_csv:
            verify.return_value = {'role': 'admin', 'user_id': 'admin'}
            is_public.return_value = False
            mock_export.return_value = []
            mock_csv.return_value = {
                'filename': 'transactions.csv',
                'content': 'data',
                'content_type': 'text/csv'
            }
            
            event = api_gateway_event.copy()
            event['routeKey'] = 'GET /transactions/export-data'
            event['headers']['Authorization'] = 'Bearer token'
            
            response = transaction_handler(event, {})
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'filename' in body
            assert 'content' in body


class TestClearAllTransactions:
    def test_clear_all_admin_only(self, transaction_handler, api_gateway_event):
        """Test that clear all requires admin role"""
        with patch('auth_middleware.extract_token') as extract, \
             patch('auth_middleware.verify_token') as verify, \
             patch('lambda_handler.is_public_endpoint') as is_public:
            verify.return_value = {'role': 'staff', 'user_id': 'test'}
            is_public.return_value = False
            
            event = api_gateway_event.copy()
            event['routeKey'] = 'DELETE /transactions/clear-all'
            event['headers']['Authorization'] = 'Bearer token'
            
            response = transaction_handler(event, {})
            
            assert response['statusCode'] == 403
    
    def test_clear_all_success(self, transaction_handler, api_gateway_event, mock_websocket):
        """Test successful clear all transactions"""
        with patch('auth_middleware.extract_token') as extract, \
             patch('auth_middleware.verify_token') as verify, \
             patch('lambda_handler.is_public_endpoint') as is_public, \
             patch('lambda_handler.clear_all_transactions') as mock_clear:
            verify.return_value = {'role': 'admin', 'user_id': 'admin'}
            is_public.return_value = False
            mock_clear.return_value = 25
            
            event = api_gateway_event.copy()
            event['routeKey'] = 'DELETE /transactions/clear-all'
            event['headers']['Authorization'] = 'Bearer token'
            
            response = transaction_handler(event, {})
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['cleared_count'] == 25
            mock_websocket.assert_called_once()


class TestErrorHandling:
    def test_route_not_found(self, transaction_handler, mock_auth, api_gateway_event):
        """Test handling of unknown routes"""
        event = api_gateway_event.copy()
        event['routeKey'] = 'GET /unknown-route'
        event['headers']['Authorization'] = 'Bearer test-token'
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'Route not found' in body['message']
    
    def test_internal_server_error(self, transaction_handler, mock_database, mock_auth, api_gateway_event, sample_transaction_data):
        """Test handling of unexpected errors"""
        mock_database['create'].side_effect = Exception('Database error')
        
        event = api_gateway_event.copy()
        event['routeKey'] = 'POST /transactions'
        event['body'] = json.dumps(sample_transaction_data)
        event['headers']['Authorization'] = 'Bearer test-token'
        
        response = transaction_handler(event, {})
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'message' in body
