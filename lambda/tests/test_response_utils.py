"""
Tests for shared response utilities
"""
import pytest
import json
from response_utils import create_response


class TestCreateResponse:
    """Test create_response utility"""
    
    def test_creates_response_with_status_code(self):
        """Test response includes correct status code"""
        response = create_response(200, {'message': 'Success'})
        assert response['statusCode'] == 200
    
    def test_creates_response_with_body(self):
        """Test response includes JSON body"""
        body = {'message': 'Success', 'data': [1, 2, 3]}
        response = create_response(200, body)
        assert json.loads(response['body']) == body
    
    def test_includes_cors_headers(self):
        """Test response includes CORS headers"""
        response = create_response(200, {})
        headers = response['headers']
        assert headers['Access-Control-Allow-Origin'] == '*'
        assert 'GET' in headers['Access-Control-Allow-Methods']
        assert 'POST' in headers['Access-Control-Allow-Methods']
        assert 'Content-Type' in headers['Access-Control-Allow-Headers']
        assert 'Authorization' in headers['Access-Control-Allow-Headers']
    
    def test_handles_error_responses(self):
        """Test error response creation"""
        response = create_response(400, {'error': 'Bad request'})
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Bad request'
    
    def test_handles_empty_body(self):
        """Test response with empty body"""
        response = create_response(204, {})
        assert response['statusCode'] == 204
        assert json.loads(response['body']) == {}
    
    def test_handles_complex_body(self):
        """Test response with nested data structures"""
        body = {
            'transaction': {
                'id': 'ABC-DEF',
                'items': [
                    {'sku': 'TEST-001', 'quantity': 2},
                ],
                'total': 100.50,
            }
        }
        response = create_response(201, body)
        assert json.loads(response['body']) == body
