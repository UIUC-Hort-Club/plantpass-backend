"""
Tests for shared validation utilities
"""
import pytest
from decimal import Decimal
from shared_utils.validation import (
    validate_quantity,
    validate_price,
    validate_email,
    validate_order_id,
    validate_sku,
    sanitize_string,
    validate_discount_value,
    validate_transaction_items,
    validate_discounts,
    validate_payment_method,
    validate_boolean,
    clamp_number,
    validate_transaction_data,
)


class TestValidateQuantity:
    def test_valid_positive_integer(self):
        assert validate_quantity(5) == 5
        assert validate_quantity('10') == 10
    
    def test_zero_quantity(self):
        assert validate_quantity(0) == 0
    
    def test_negative_quantity_returns_zero(self):
        assert validate_quantity(-5) == 0
    
    def test_invalid_input_returns_zero(self):
        assert validate_quantity('invalid') == 0
        assert validate_quantity(None) == 0
        assert validate_quantity([]) == 0


class TestValidatePrice:
    def test_valid_price(self):
        assert validate_price(10.99) == Decimal('10.99')
        assert validate_price('25.50') == Decimal('25.50')
    
    def test_rounds_to_two_decimals(self):
        assert validate_price(10.999) == Decimal('11.00')
        assert validate_price(10.994) == Decimal('10.99')
    
    def test_negative_price_returns_zero(self):
        assert validate_price(-10) == Decimal('0.00')
    
    def test_invalid_input_returns_zero(self):
        assert validate_price('invalid') == Decimal('0.00')
        assert validate_price(None) == Decimal('0.00')


class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email('test@example.com') is True
        assert validate_email('user.name+tag@domain.co.uk') is True
    
    def test_invalid_email(self):
        assert validate_email('invalid') is False
        assert validate_email('test@') is False
        assert validate_email('@example.com') is False
        assert validate_email('') is False
        assert validate_email(None) is False


class TestValidateOrderId:
    def test_valid_order_id(self):
        assert validate_order_id('ABC-DEF') is True
        assert validate_order_id('XYZ-QRS') is True
    
    def test_invalid_order_id(self):
        assert validate_order_id('abc-def') is False  # lowercase
        assert validate_order_id('AB-DEF') is False   # too short
        assert validate_order_id('ABCD-DEF') is False # too long
        assert validate_order_id('ABC_DEF') is False  # wrong separator
        assert validate_order_id('') is False
        assert validate_order_id(None) is False


class TestValidateSku:
    def test_valid_sku(self):
        assert validate_sku('PROD-001') is True
        assert validate_sku('TEST_SKU') is True
        assert validate_sku('ABC123') is True
    
    def test_invalid_sku(self):
        assert validate_sku('') is False
        assert validate_sku(None) is False
        assert validate_sku('   ') is False


class TestSanitizeString:
    def test_removes_html_tags(self):
        assert sanitize_string('<script>alert("xss")</script>') == 'alert("xss")'
        assert sanitize_string('<b>Bold</b> text') == 'Bold text'
    
    def test_trims_whitespace(self):
        assert sanitize_string('  test  ') == 'test'
    
    def test_limits_length(self):
        long_string = 'a' * 300
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_handles_invalid_input(self):
        assert sanitize_string(None) == ''
        assert sanitize_string('') == ''


class TestValidateDiscountValue:
    def test_percent_discount_clamped_to_100(self):
        assert validate_discount_value(150, 'percent') == Decimal('100.00')
        assert validate_discount_value(50, 'percent') == Decimal('50.00')
    
    def test_dollar_discount_non_negative(self):
        assert validate_discount_value(10, 'dollar') == Decimal('10.00')
        assert validate_discount_value(-5, 'dollar') == Decimal('0.00')


class TestValidateTransactionItems:
    def test_valid_items(self):
        items = [
            {
                'SKU': 'TEST-001',
                'item': 'Test Product',
                'quantity': 2,
                'price_ea': 10.99,
            }
        ]
        is_valid, errors = validate_transaction_items(items)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_empty_items_array(self):
        is_valid, errors = validate_transaction_items([])
        assert is_valid is False
        assert 'At least one item is required' in errors
    
    def test_items_not_array(self):
        is_valid, errors = validate_transaction_items('not an array')
        assert is_valid is False
        assert 'Items must be an array' in errors
    
    def test_invalid_sku(self):
        items = [
            {
                'SKU': '',
                'item': 'Test',
                'quantity': 1,
                'price_ea': 10,
            }
        ]
        is_valid, errors = validate_transaction_items(items)
        assert is_valid is False
        assert any('Invalid SKU' in e for e in errors)
    
    def test_zero_price(self):
        items = [
            {
                'SKU': 'TEST-001',
                'item': 'Test',
                'quantity': 1,
                'price_ea': 0,
            }
        ]
        is_valid, errors = validate_transaction_items(items)
        assert is_valid is False
        assert any('Price must be greater than 0' in e for e in errors)
    
    def test_all_zero_quantities(self):
        items = [
            {
                'SKU': 'TEST-001',
                'item': 'Test',
                'quantity': 0,
                'price_ea': 10,
            }
        ]
        is_valid, errors = validate_transaction_items(items)
        assert is_valid is False
        assert any('quantity greater than 0' in e for e in errors)


class TestValidateDiscounts:
    def test_valid_discounts(self):
        discounts = [
            {
                'name': '10% Off',
                'type': 'percent',
                'value': 10,
            }
        ]
        is_valid, errors = validate_discounts(discounts)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_empty_discounts_array(self):
        is_valid, errors = validate_discounts([])
        assert is_valid is True  # Empty discounts is valid
    
    def test_invalid_discount_type(self):
        discounts = [
            {
                'name': 'Invalid',
                'type': 'invalid_type',
                'value': 10,
            }
        ]
        is_valid, errors = validate_discounts(discounts)
        assert is_valid is False
        assert any('Type must be' in e for e in errors)
    
    def test_negative_discount_value(self):
        """Test that negative discount values are handled (converted to 0)"""
        discounts = [
            {
                'name': 'Negative',
                'type': 'dollar',
                'value': -10,
            }
        ]
        is_valid, errors = validate_discounts(discounts)
        # Negative values are converted to 0, so validation passes
        assert is_valid is True


class TestValidatePaymentMethod:
    def test_valid_payment_method(self):
        assert validate_payment_method('Cash') is True
        assert validate_payment_method('Credit Card') is True
    
    def test_invalid_payment_method(self):
        assert validate_payment_method('') is False
        assert validate_payment_method(None) is False
        assert validate_payment_method('   ') is False


class TestValidateBoolean:
    def test_boolean_values(self):
        assert validate_boolean(True) is True
        assert validate_boolean(False) is False
    
    def test_string_values(self):
        assert validate_boolean('true') is True
        assert validate_boolean('1') is True
        assert validate_boolean('yes') is True
        assert validate_boolean('false') is False
        assert validate_boolean('0') is False
    
    def test_numeric_values(self):
        assert validate_boolean(1) is True
        assert validate_boolean(0) is False


class TestClampNumber:
    def test_clamps_to_range(self):
        assert clamp_number(5, 0, 10) == 5
        assert clamp_number(-5, 0, 10) == 0
        assert clamp_number(15, 0, 10) == 10
    
    def test_handles_invalid_input(self):
        assert clamp_number('invalid', 0, 10) == 0
        assert clamp_number(None, 5, 10) == 5


class TestValidateTransactionData:
    def test_valid_transaction_data(self):
        data = {
            'items': [
                {
                    'SKU': 'TEST-001',
                    'item': 'Test',
                    'quantity': 1,
                    'price_ea': 10,
                }
            ],
            'discounts': [],
            'voucher': 0,
        }
        is_valid, errors = validate_transaction_data(data)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_email(self):
        data = {
            'items': [
                {
                    'SKU': 'TEST-001',
                    'item': 'Test',
                    'quantity': 1,
                    'price_ea': 10,
                }
            ],
            'discounts': [],
            'voucher': 0,
            'email': 'invalid-email',
        }
        is_valid, errors = validate_transaction_data(data)
        assert is_valid is False
        assert any('email' in e.lower() for e in errors)
    
    def test_multiple_validation_errors(self):
        data = {
            'items': [],
            'discounts': [
                {
                    'name': 'Bad',
                    'type': 'invalid',
                    'value': -10,
                }
            ],
            'voucher': -5,
        }
        is_valid, errors = validate_transaction_data(data)
        assert is_valid is False
        assert len(errors) > 1
