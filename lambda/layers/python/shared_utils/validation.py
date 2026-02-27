"""
Input validation utilities for Lambda functions
Prevents invalid data from corrupting the database
"""
import re
from decimal import Decimal
from typing import Any, Dict, List, Tuple


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def validate_quantity(value: Any) -> int:
    """
    Validate and sanitize quantity input
    Returns non-negative integer
    """
    try:
        num = int(value)
        if num < 0:
            return 0
        return num
    except (ValueError, TypeError):
        return 0


def validate_price(value: Any) -> Decimal:
    """
    Validate and sanitize price input
    Returns non-negative Decimal with 2 decimal places
    """
    try:
        price = Decimal(str(value))
        if price < 0:
            return Decimal('0.00')
        return price.quantize(Decimal('0.01'))
    except (ValueError, TypeError, ArithmeticError):
        return Decimal('0.00')


def validate_email(email: str) -> bool:
    """
    Validate email format
    Returns True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # RFC 5322 simplified regex
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return bool(re.match(email_regex, email.strip()))


def validate_order_id(order_id: str) -> bool:
    """
    Validate order ID format (ABC-DEF)
    Returns True if valid, False otherwise
    """
    if not order_id or not isinstance(order_id, str):
        return False
    
    order_id_regex = r'^[A-Z]{3}-[A-Z]{3}$'
    return bool(re.match(order_id_regex, order_id.strip()))


def validate_sku(sku: str) -> bool:
    """
    Validate SKU format
    Returns True if valid, False otherwise
    """
    if not sku or not isinstance(sku, str):
        return False
    
    # Alphanumeric with optional hyphens/underscores
    sku_regex = r'^[A-Za-z0-9_-]+$'
    return bool(re.match(sku_regex, sku.strip())) and len(sku.strip()) > 0


def sanitize_string(input_str: str, max_length: int = 255) -> str:
    """
    Sanitize string input
    Removes HTML tags and limits length
    """
    if not input_str or not isinstance(input_str, str):
        return ''
    
    # Remove HTML tags
    sanitized = re.sub(r'<[^>]*>', '', input_str)
    
    # Trim and limit length
    return sanitized.strip()[:max_length]


def validate_discount_value(value: Any, discount_type: str) -> Decimal:
    """
    Validate discount value based on type
    Returns valid Decimal value
    """
    price = validate_price(value)
    
    if discount_type == "percent":
        # Percentage should be 0-100
        if price > 100:
            return Decimal('100.00')
        return price
    
    # Dollar amount should be non-negative
    return price


def validate_transaction_items(items: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate transaction items array
    Returns (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(items, list):
        return False, ['Items must be an array']
    
    if len(items) == 0:
        return False, ['At least one item is required']
    
    has_valid_items = False
    
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f'Item {idx + 1}: Must be an object')
            continue
        
        # Validate SKU
        sku = item.get('SKU', '')
        if not validate_sku(sku):
            errors.append(f'Item {idx + 1}: Invalid SKU')
        
        # Validate item name
        item_name = item.get('item', '')
        if not item_name or not isinstance(item_name, str):
            errors.append(f'Item {idx + 1}: Invalid item name')
        
        # Validate price
        price = validate_price(item.get('price_ea', 0))
        if price <= 0:
            errors.append(f'Item {idx + 1}: Price must be greater than 0')
        
        # Validate quantity
        quantity = validate_quantity(item.get('quantity', 0))
        if quantity > 0:
            has_valid_items = True
    
    if not has_valid_items:
        errors.append('At least one item must have a quantity greater than 0')
    
    return len(errors) == 0, errors


def validate_discounts(discounts: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate discounts array
    Returns (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(discounts, list):
        return False, ['Discounts must be an array']
    
    for idx, discount in enumerate(discounts):
        if not isinstance(discount, dict):
            errors.append(f'Discount {idx + 1}: Must be an object')
            continue
        
        # Validate name
        name = discount.get('name', '')
        if not name or not isinstance(name, str):
            errors.append(f'Discount {idx + 1}: Invalid name')
        
        # Validate type
        discount_type = discount.get('type', '')
        if discount_type not in ['percent', 'dollar']:
            errors.append(f'Discount {idx + 1}: Type must be "percent" or "dollar"')
        
        # Validate value
        value = discount.get('value', 0)
        validated_value = validate_discount_value(value, discount_type)
        if validated_value < 0:
            errors.append(f'Discount {idx + 1}: Value must be non-negative')
    
    return len(errors) == 0, errors


def validate_payment_method(method: str) -> bool:
    """
    Validate payment method
    Returns True if valid, False otherwise
    """
    if not method or not isinstance(method, str):
        return False
    
    # Payment method should be non-empty string
    return len(method.strip()) > 0


def validate_boolean(value: Any) -> bool:
    """
    Validate and coerce boolean value
    Returns boolean
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes']
    
    return bool(value)


def clamp_number(value: Any, min_val: float = 0, max_val: float = float('inf')) -> float:
    """
    Validate and clamp number to range
    Returns clamped value
    """
    try:
        num = float(value)
        if not (-float('inf') < num < float('inf')):  # Check for NaN/Inf
            return min_val
        return max(min_val, min(max_val, num))
    except (ValueError, TypeError):
        return min_val


def validate_transaction_data(data: Dict) -> Tuple[bool, List[str]]:
    """
    Comprehensive validation for transaction data
    Returns (is_valid, error_messages)
    """
    errors = []
    
    # Validate items
    items = data.get('items', [])
    items_valid, items_errors = validate_transaction_items(items)
    if not items_valid:
        errors.extend(items_errors)
    
    # Validate discounts
    discounts = data.get('discounts', [])
    discounts_valid, discounts_errors = validate_discounts(discounts)
    if not discounts_valid:
        errors.extend(discounts_errors)
    
    # Validate voucher
    voucher = data.get('voucher', 0)
    if validate_price(voucher) < 0:
        errors.append('Voucher amount must be non-negative')
    
    # Validate email if provided
    email = data.get('email', '')
    if email and not validate_email(email):
        errors.append('Invalid email format')
    
    return len(errors) == 0, errors
