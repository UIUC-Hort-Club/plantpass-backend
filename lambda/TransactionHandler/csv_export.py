import csv
import io
import zipfile
import base64
from datetime import datetime
from decimal import Decimal


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj


def generate_csv_export(transactions):
    """
    Generate 3 CSV files from transaction data and return as a base64-encoded zip file.
    
    Returns:
        dict: Contains base64-encoded zip file and filename
    """
    transactions = decimal_to_float(transactions)
    
    # Create in-memory buffers for CSV files
    transactions_csv = io.StringIO()
    items_csv = io.StringIO()
    discounts_csv = io.StringIO()
    
    # Writers
    transactions_writer = csv.writer(transactions_csv)
    items_writer = csv.writer(items_csv)
    discounts_writer = csv.writer(discounts_csv)
    
    # Write headers
    transactions_writer.writerow([
        'purchase_id', 'timestamp', 'subtotal', 'discount_total', 
        'club_voucher', 'grand_total', 'payment_method', 'paid'
    ])
    
    items_writer.writerow([
        'purchase_id', 'timestamp', 'item_name', 'sku', 
        'quantity', 'price_ea', 'line_total'
    ])
    
    discounts_writer.writerow([
        'purchase_id', 'timestamp', 'discount_name', 'discount_type', 
        'discount_value', 'amount_off'
    ])
    
    # Process each transaction
    for transaction in transactions:
        purchase_id = transaction.get('purchase_id', '')
        timestamp = transaction.get('timestamp', 0)
        receipt = transaction.get('receipt', {})
        payment = transaction.get('payment', {})
        
        subtotal = receipt.get('subtotal', 0)
        discount_total = receipt.get('discount', 0)
        grand_total = receipt.get('total', 0)
        club_voucher = transaction.get('club_voucher', 0)
        payment_method = payment.get('method', '')
        paid = payment.get('paid', False)
        
        # Write transaction row
        transactions_writer.writerow([
            purchase_id,
            timestamp,
            f"{subtotal:.2f}",
            f"{discount_total:.2f}",
            club_voucher,
            f"{grand_total:.2f}",
            payment_method,
            paid
        ])
        
        # Write item rows (only items with quantity > 0)
        items = transaction.get('items', [])
        for item in items:
            quantity = item.get('quantity', 0)
            if quantity > 0:  # Only export items that were actually purchased
                item_name = item.get('item', '')
                sku = item.get('SKU', '')
                price_ea = item.get('price_ea', 0)
                line_total = quantity * price_ea
                
                items_writer.writerow([
                    purchase_id,
                    timestamp,
                    item_name,
                    sku,
                    quantity,
                    f"{price_ea:.2f}",
                    f"{line_total:.2f}"
                ])
        
        # Write discount rows (only discounts with amount_off > 0)
        discounts = transaction.get('discounts', [])
        for discount in discounts:
            amount_off = discount.get('amount_off', 0)
            if amount_off > 0:  # Only export discounts that were actually applied
                discount_name = discount.get('name', '')
                discount_type = discount.get('type', '')
                discount_value = discount.get('value', 0)
                
                discounts_writer.writerow([
                    purchase_id,
                    timestamp,
                    discount_name,
                    discount_type,
                    discount_value,
                    f"{amount_off:.2f}"
                ])
    
    # Create zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add CSV files to zip
        zip_file.writestr('transactions.csv', transactions_csv.getvalue())
        zip_file.writestr('transaction_items.csv', items_csv.getvalue())
        zip_file.writestr('transaction_discounts.csv', discounts_csv.getvalue())
    
    # Get zip content and encode as base64
    zip_buffer.seek(0)
    zip_content = zip_buffer.read()
    zip_base64 = base64.b64encode(zip_content).decode('utf-8')
    
    # Generate filename with current date-time
    now = datetime.now()
    filename = f"plantpass_data_export_{now.strftime('%Y%m%d_%H%M%S')}.zip"
    
    return {
        'filename': filename,
        'content': zip_base64,
        'content_type': 'application/zip'
    }
