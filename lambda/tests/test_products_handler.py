"""
Tests for ProductsHandler Lambda
"""
import pytest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Mock AWS dependencies FIRST
sys.modules['boto3'] = MagicMock()
sys.modules['botocore'] = MagicMock()
sys.modules['botocore.exceptions'] = MagicMock()

# Clear any cached lambda_handler imports to ensure we get the right one
for module_name in list(sys.modules.keys()):
    if 'lambda_handler' in module_name:
        del sys.modules[module_name]

# Add ProductsHandler to path FIRST (before any other handler)
products_handler_path = os.path.join(os.path.dirname(__file__), '../ProductsHandler')
# Remove any existing handler paths from sys.path
sys.path = [p for p in sys.path if not any(h in p for h in ['TransactionHandler', 'DiscountsHandler', 'EmailHandler']) or p == products_handler_path]
sys.path.insert(0, products_handler_path)

# Now import - this should get ProductsHandler's lambda_handler
import lambda_handler as products_lambda_module


@pytest.fixture
def products_handler():
    """Import and return the products handler with mocked dependencies"""
    return products_lambda_module.lambda_handler


@pytest.fixture
def mock_database():
    """Mock database operations"""
    with patch.object(products_lambda_module, 'get_all_products') as get_all, \
         patch.object(products_lambda_module, 'replace_all_products') as replace:
        yield {'get_all': get_all, 'replace': replace}


@pytest.fixture
def mock_auth():
    """Mock authentication"""
    with patch('auth_middleware.JWT_SECRET', 'test-secret-key'), \
         patch.object(products_lambda_module, 'extract_token') as extract, \
         patch.object(products_lambda_module, 'verify_token') as verify, \
         patch.object(products_lambda_module, 'is_public_endpoint') as is_public:
        verify.return_value = {'role': 'admin', 'user_id': 'test-admin'}
        is_public.return_value = False  # Default to protected endpoints
        yield {'extract': extract, 'verify': verify, 'is_public': is_public}


@pytest.fixture
def mock_public_endpoint():
    """Mock public endpoint check"""
    with patch.object(products_lambda_module, 'is_public_endpoint') as is_public:
        is_public.return_value = True
        yield is_public


class TestGetProducts:
    def test_get_all_products_success(self, products_handler, mock_database, mock_public_endpoint, api_gateway_event, sample_product_data):
        """Test successful retrieval of all products"""
        mock_database['get_all'].return_value = sample_product_data
        
        event = api_gateway_event.copy()
        event['routeKey'] = 'GET /products'
        
        response = products_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body) == 2
        assert body[0]['SKU'] == 'PROD-001'
        mock_database['get_all'].assert_called_once()
    
    def test_get_all_products_empty(self, products_handler, mock_database, mock_public_endpoint, api_gateway_event):
        """Test getting products when none exist"""
        mock_database['get_all'].return_value = []
        
        event = api_gateway_event.copy()
        event['routeKey'] = 'GET /products'
        
        response = products_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body == []


class TestReplaceProducts:
    def test_replace_products_success(self, products_handler, mock_database, mock_auth, api_gateway_event, sample_product_data):
        """Test successful product replacement"""
        mock_database['replace'].return_value = {'replaced': 2}
        
        event = api_gateway_event.copy()
        event['routeKey'] = 'PUT /products'
        event['headers']['Authorization'] = 'Bearer token'
        event['body'] = json.dumps(sample_product_data)
        
        response = products_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'Products replaced successfully' in body['message']
        mock_database['replace'].assert_called_once_with(sample_product_data)
    
    def test_replace_products_requires_admin(self, products_handler, api_gateway_event):
        """Test that replace products requires admin role"""
        with patch('auth_middleware.JWT_SECRET', 'test-secret-key'), \
             patch.object(products_lambda_module, 'extract_token') as extract, \
             patch.object(products_lambda_module, 'verify_token') as verify, \
             patch.object(products_lambda_module, 'is_public_endpoint') as is_public:
            verify.return_value = {'role': 'staff', 'user_id': 'test'}
            is_public.return_value = False
            
            event = api_gateway_event.copy()
            event['routeKey'] = 'PUT /products'
            event['headers']['Authorization'] = 'Bearer token'
            event['body'] = json.dumps([])
            
            response = products_handler(event, {})
            
            assert response['statusCode'] == 403
            body = json.loads(response['body'])
            assert 'Admin access required' in body['message']
    
    def test_replace_products_invalid_body(self, products_handler, mock_auth, api_gateway_event):
        """Test replace products with non-list body"""
        event = api_gateway_event.copy()
        event['routeKey'] = 'PUT /products'
        event['headers']['Authorization'] = 'Bearer token'
        event['body'] = json.dumps({'not': 'a list'})
        
        response = products_handler(event, {})
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'must be a list' in body['message']


class TestErrorHandling:
    def test_route_not_found(self, products_handler, api_gateway_event):
        """Test handling of unknown routes"""
        with patch('auth_middleware.JWT_SECRET', 'test-secret-key'), \
             patch.object(products_lambda_module, 'extract_token') as mock_extract, \
             patch.object(products_lambda_module, 'verify_token') as mock_verify, \
             patch.object(products_lambda_module, 'is_public_endpoint') as is_public:
            mock_verify.return_value = {'role': 'admin', 'user_id': 'test'}
            is_public.return_value = False
            
            event = api_gateway_event.copy()
            event['routeKey'] = 'DELETE /products'
            event['headers']['Authorization'] = 'Bearer token'
            
            response = products_handler(event, {})
            
            assert response['statusCode'] == 404
    
    def test_database_error(self, products_handler, mock_database, mock_public_endpoint, api_gateway_event):
        """Test handling of database errors"""
        mock_database['get_all'].side_effect = Exception('Database connection failed')
        
        event = api_gateway_event.copy()
        event['routeKey'] = 'GET /products'
        
        response = products_handler(event, {})
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'message' in body
