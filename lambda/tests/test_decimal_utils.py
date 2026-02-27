"""
Tests for decimal utilities
"""
import pytest
from decimal import Decimal
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../shared'))

from decimal_utils import decimal_to_float


class TestDecimalToFloat:
    """Test decimal to float conversion"""
    
    def test_converts_decimal_to_float(self):
        """Test basic decimal to float conversion"""
        result = decimal_to_float(Decimal('10.99'))
        assert result == 10.99
        assert isinstance(result, float)
    
    def test_handles_dict_with_decimals(self):
        """Test conversion of dict containing decimals"""
        data = {
            'price': Decimal('10.99'),
            'quantity': Decimal('5'),
        }
        result = decimal_to_float(data)
        assert result == {'price': 10.99, 'quantity': 5.0}
    
    def test_handles_list_with_decimals(self):
        """Test conversion of list containing decimals"""
        data = [Decimal('10.99'), Decimal('5.50')]
        result = decimal_to_float(data)
        assert result == [10.99, 5.50]
    
    def test_handles_nested_structures(self):
        """Test conversion of nested dicts and lists"""
        data = {
            'items': [
                {'price': Decimal('10.99'), 'qty': Decimal('2')},
                {'price': Decimal('5.50'), 'qty': Decimal('1')},
            ],
            'total': Decimal('27.48'),
        }
        result = decimal_to_float(data)
        assert result['total'] == 27.48
        assert result['items'][0]['price'] == 10.99
    
    def test_handles_non_decimal_values(self):
        """Test that non-decimal values pass through unchanged"""
        assert decimal_to_float('string') == 'string'
        assert decimal_to_float(42) == 42
        assert decimal_to_float(None) is None
        assert decimal_to_float(True) is True
