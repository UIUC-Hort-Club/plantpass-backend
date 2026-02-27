"""
Pytest configuration and shared fixtures for Lambda tests
"""
import pytest
import sys
import os
from decimal import Decimal
from typing import Dict, Any

# Add shared directories to path (but NOT handler-specific directories)
# Each test file will add its own handler directory to avoid conflicts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../layers/python'))


@pytest.fixture
def mock_context():
    """Mock Lambda context object"""
    class MockContext:
        function_name = 'test-function'
        function_version = '$LATEST'
        invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-function'
        memory_limit_in_mb = 128
        aws_request_id = 'test-request-id'
        log_group_name = '/aws/lambda/test-function'
        log_stream_name = '2024/01/01/[$LATEST]test'
        
        @staticmethod
        def get_remaining_time_in_millis():
            return 30000
    
    return MockContext()


@pytest.fixture
def api_gateway_event() -> Dict[str, Any]:
    """Base API Gateway event structure"""
    return {
        'routeKey': '',
        'headers': {
            'Content-Type': 'application/json',
        },
        'requestContext': {
            'requestId': 'test-request-id',
            'apiId': 'test-api-id',
        },
        'body': None,
        'pathParameters': None,
        'queryStringParameters': None,
    }


@pytest.fixture
def sample_transaction_data() -> Dict[str, Any]:
    """Sample valid transaction data"""
    return {
        'timestamp': 1640000000000,
        'items': [
            {
                'SKU': 'TEST-001',
                'item': 'Test Product',
                'quantity': 2,
                'price_ea': 10.99,
            },
            {
                'SKU': 'TEST-002',
                'item': 'Another Product',
                'quantity': 1,
                'price_ea': 5.50,
            },
        ],
        'discounts': [
            {
                'name': '10% Off',
                'type': 'percent',
                'value': 10,
                'selected': True,
            }
        ],
        'voucher': 5.00,
        'email': 'test@example.com',
    }


@pytest.fixture
def sample_product_data() -> list:
    """Sample valid product data"""
    return [
        {
            'SKU': 'PROD-001',
            'item': 'Product 1',
            'price_ea': 10.99,
            'sort_order': 1,
        },
        {
            'SKU': 'PROD-002',
            'item': 'Product 2',
            'price_ea': 25.50,
            'sort_order': 2,
        },
    ]


@pytest.fixture
def sample_discount_data() -> list:
    """Sample valid discount data"""
    return [
        {
            'name': '10% Off',
            'type': 'percent',
            'value': 10,
            'sort_order': 1,
        },
        {
            'name': '$5 Off',
            'type': 'dollar',
            'value': 5,
            'sort_order': 2,
        },
    ]


@pytest.fixture
def auth_token() -> str:
    """Mock authentication token"""
    return 'Bearer mock-jwt-token'


@pytest.fixture
def admin_auth_event(api_gateway_event, auth_token) -> Dict[str, Any]:
    """API Gateway event with admin authentication"""
    event = api_gateway_event.copy()
    event['headers']['Authorization'] = auth_token
    event['auth'] = {
        'role': 'admin',
        'user_id': 'test-admin',
    }
    return event


@pytest.fixture
def staff_auth_event(api_gateway_event, auth_token) -> Dict[str, Any]:
    """API Gateway event with staff authentication"""
    event = api_gateway_event.copy()
    event['headers']['Authorization'] = auth_token
    event['auth'] = {
        'role': 'staff',
        'user_id': 'test-staff',
    }
    return event
