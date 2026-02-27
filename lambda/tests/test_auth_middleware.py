"""
Tests for authentication middleware
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Mock AWS dependencies before importing
sys.modules['boto3'] = MagicMock()
sys.modules['botocore'] = MagicMock()
sys.modules['botocore.exceptions'] = MagicMock()

# Add handler to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../TransactionHandler'))


@pytest.fixture
def auth_middleware():
    """Import and return auth middleware"""
    from auth_middleware import (
        extract_token,
        verify_token,
        require_auth,
        is_public_endpoint,
        AuthError
    )
    return {
        'extract_token': extract_token,
        'verify_token': verify_token,
        'require_auth': require_auth,
        'is_public_endpoint': is_public_endpoint,
        'AuthError': AuthError,
    }


@pytest.fixture
def jwt_secret():
    """Set JWT secret for testing"""
    secret = 'test-secret-key'
    with patch.dict(os.environ, {'JWT_SECRET': secret}):
        yield secret


class TestExtractToken:
    def test_extract_token_success(self, auth_middleware):
        """Test successful token extraction"""
        event = {
            'headers': {
                'Authorization': 'Bearer test-token-123'
            }
        }
        
        token = auth_middleware['extract_token'](event)
        assert token == 'test-token-123'
    
    def test_extract_token_case_insensitive(self, auth_middleware):
        """Test token extraction with case-insensitive header"""
        event = {
            'headers': {
                'authorization': 'Bearer test-token-123'
            }
        }
        
        token = auth_middleware['extract_token'](event)
        assert token == 'test-token-123'
    
    def test_extract_token_missing_header(self, auth_middleware):
        """Test extraction fails when Authorization header is missing"""
        event = {'headers': {}}
        
        with pytest.raises(auth_middleware['AuthError']) as exc_info:
            auth_middleware['extract_token'](event)
        
        assert exc_info.value.status_code == 401
        assert 'Missing Authorization header' in exc_info.value.message
    
    def test_extract_token_invalid_format(self, auth_middleware):
        """Test extraction fails with invalid header format"""
        event = {
            'headers': {
                'Authorization': 'InvalidFormat token'
            }
        }
        
        with pytest.raises(auth_middleware['AuthError']) as exc_info:
            auth_middleware['extract_token'](event)
        
        assert exc_info.value.status_code == 401
        assert 'Invalid Authorization header format' in exc_info.value.message


class TestVerifyToken:
    def test_verify_valid_token(self, auth_middleware, jwt_secret):
        """Test verification of valid token"""
        # Mock jwt.decode to return a valid payload
        with patch('auth_middleware.JWT_SECRET', jwt_secret), \
             patch('auth_middleware.jwt.decode') as mock_decode:
            mock_decode.return_value = {'user_id': 'test-user', 'role': 'staff'}
            
            decoded = auth_middleware['verify_token']('valid-token')
            
            assert decoded['user_id'] == 'test-user'
            assert decoded['role'] == 'staff'
            mock_decode.assert_called_once()
    
    def test_verify_expired_token(self, auth_middleware, jwt_secret):
        """Test verification fails for expired token"""
        import jwt as jwt_lib
        
        with patch('auth_middleware.JWT_SECRET', jwt_secret), \
             patch('auth_middleware.jwt.decode') as mock_decode:
            mock_decode.side_effect = jwt_lib.ExpiredSignatureError()
            
            with pytest.raises(auth_middleware['AuthError']) as exc_info:
                auth_middleware['verify_token']('expired-token')
            
            assert exc_info.value.status_code == 401
            assert 'Token expired' in exc_info.value.message
    
    def test_verify_invalid_token(self, auth_middleware, jwt_secret):
        """Test verification fails for invalid token"""
        import jwt as jwt_lib
        
        with patch('auth_middleware.JWT_SECRET', jwt_secret), \
             patch('auth_middleware.jwt.decode') as mock_decode:
            mock_decode.side_effect = jwt_lib.InvalidTokenError()
            
            with pytest.raises(auth_middleware['AuthError']) as exc_info:
                auth_middleware['verify_token']('invalid-token')
            
            assert exc_info.value.status_code == 401
            assert 'Invalid token' in exc_info.value.message
    
    def test_verify_token_no_secret_configured(self, auth_middleware):
        """Test verification fails when JWT_SECRET not configured"""
        with patch('auth_middleware.JWT_SECRET', None):
            with pytest.raises(auth_middleware['AuthError']) as exc_info:
                auth_middleware['verify_token']('any-token')
            
            assert exc_info.value.status_code == 500
            assert 'Server configuration error' in exc_info.value.message


class TestRequireAuth:
    def test_require_auth_success(self, auth_middleware, jwt_secret):
        """Test successful authentication"""
        @auth_middleware['require_auth']()
        def test_handler(event, context):
            return {'statusCode': 200, 'body': 'Success'}
        
        with patch('auth_middleware.JWT_SECRET', jwt_secret), \
             patch('auth_middleware.jwt.decode') as mock_decode:
            mock_decode.return_value = {'user_id': 'test-user', 'role': 'staff'}
            
            event = {
                'headers': {'Authorization': 'Bearer valid-token'}
            }
            
            response = test_handler(event, {})
            assert response['statusCode'] == 200
            assert 'auth' in event
            assert event['auth']['user_id'] == 'test-user'
    
    def test_require_auth_missing_token(self, auth_middleware):
        """Test authentication fails without token"""
        @auth_middleware['require_auth']()
        def test_handler(event, context):
            return {'statusCode': 200}
        
        event = {'headers': {}}
        
        response = test_handler(event, {})
        assert response['statusCode'] == 401
    
    def test_require_admin_role(self, auth_middleware, jwt_secret):
        """Test admin role requirement"""
        @auth_middleware['require_auth'](role='admin')
        def test_handler(event, context):
            return {'statusCode': 200}
        
        with patch('auth_middleware.JWT_SECRET', jwt_secret), \
             patch('auth_middleware.jwt.decode') as mock_decode:
            mock_decode.return_value = {'user_id': 'admin-user', 'role': 'admin'}
            
            event = {
                'headers': {'Authorization': 'Bearer admin-token'}
            }
            
            response = test_handler(event, {})
            assert response['statusCode'] == 200
    
    def test_require_admin_role_insufficient_permissions(self, auth_middleware, jwt_secret):
        """Test admin role requirement fails for staff user"""
        @auth_middleware['require_auth'](role='admin')
        def test_handler(event, context):
            return {'statusCode': 200}
        
        with patch('auth_middleware.JWT_SECRET', jwt_secret), \
             patch('auth_middleware.jwt.decode') as mock_decode:
            mock_decode.return_value = {'user_id': 'test-user', 'role': 'staff'}
            
            event = {
                'headers': {'Authorization': 'Bearer staff-token'}
            }
            
            response = test_handler(event, {})
            assert response['statusCode'] == 403


class TestIsPublicEndpoint:
    def test_public_endpoints(self, auth_middleware):
        """Test that public endpoints are correctly identified"""
        public_routes = [
            'GET /transactions/{purchase_id}',
            'POST /admin/login',
            'POST /admin/forgot-password',
            'GET /products',
            'GET /discounts',
            'GET /payment-methods',
            'GET /feature-toggles',
        ]
        
        for route in public_routes:
            assert auth_middleware['is_public_endpoint'](route) is True
    
    def test_protected_endpoints(self, auth_middleware):
        """Test that protected endpoints are correctly identified"""
        protected_routes = [
            'POST /transactions',
            'PUT /transactions/{purchase_id}',
            'DELETE /transactions/{purchase_id}',
            'PUT /products',
            'PUT /discounts',
            'GET /transactions/sales-analytics',
        ]
        
        for route in protected_routes:
            assert auth_middleware['is_public_endpoint'](route) is False


class TestAuthError:
    def test_auth_error_default_status(self, auth_middleware):
        """Test AuthError with default status code"""
        error = auth_middleware['AuthError']('Test error')
        assert error.message == 'Test error'
        assert error.status_code == 401
    
    def test_auth_error_custom_status(self, auth_middleware):
        """Test AuthError with custom status code"""
        error = auth_middleware['AuthError']('Forbidden', 403)
        assert error.message == 'Forbidden'
        assert error.status_code == 403
