import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ses = boto3.client('ses', region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))

SENDER_EMAIL = os.environ['SENDER_EMAIL']
UIUC_HORT_CLUB_EMAIL = os.environ.get('UIUC_HORT_CLUB_EMAIL', 'hortclub@example.com')

def create_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }

def send_receipt_email(recipient_email, transaction_data):
    """Send receipt email to customer"""
    try:
        receipt = transaction_data.get('receipt', {})
        items = transaction_data.get('items', [])
        discounts = transaction_data.get('discounts', [])
        purchase_id = transaction_data.get('purchase_id', 'N/A')
        
        # Build items list
        items_html = ""
        for item in items:
            item_name = item.get('item') or item.get('name', 'N/A')
            quantity = int(item.get('quantity', 0))
            price_ea = float(item.get('price_ea', 0))
            items_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{item_name}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">{quantity}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">${price_ea:.2f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">${quantity * price_ea:.2f}</td>
            </tr>
            """
        
        # Build discounts list
        discounts_html = ""
        for discount in discounts:
            if discount.get('amount_off', 0) > 0:
                discounts_html += f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;" colspan="3">{discount.get('name', 'Discount')}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right; color: green;">-${discount.get('amount_off', 0):.2f}</td>
                </tr>
                """
        
        html_body = f"""
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2e7d32;">PlantPass Receipt</h1>
                <p style="color: #666;">Order ID: {purchase_id}</p>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #f5f5f5;">
                        <th style="padding: 12px 8px; text-align: left; border-bottom: 2px solid #ddd;">Item</th>
                        <th style="padding: 12px 8px; text-align: center; border-bottom: 2px solid #ddd;">Qty</th>
                        <th style="padding: 12px 8px; text-align: right; border-bottom: 2px solid #ddd;">Price</th>
                        <th style="padding: 12px 8px; text-align: right; border-bottom: 2px solid #ddd;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
            
            {f'<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;"><tbody>{discounts_html}</tbody></table>' if discounts_html else ''}
            
            <div style="text-align: right; margin-top: 20px; padding-top: 20px; border-top: 2px solid #333;">
                <p style="font-size: 14px; margin: 5px 0;"><strong>Subtotal:</strong> ${receipt.get('subtotal', 0):.2f}</p>
                {f'<p style="font-size: 14px; margin: 5px 0; color: green;"><strong>Discount:</strong> -${receipt.get("discount", 0):.2f}</p>' if receipt.get('discount', 0) > 0 else ''}
                <p style="font-size: 18px; margin: 10px 0;"><strong>Total:</strong> ${receipt.get('total', 0):.2f}</p>
            </div>
            
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666; font-size: 12px;">
                <p>Thank you for your purchase!</p>
                <p>UIUC Horticulture Club</p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
Spring Plant Fair 2026 Receipt
Order ID: {purchase_id}

Items:
"""
        for item in items:
            item_name = item.get('item') or item.get('name', 'N/A')
            quantity = int(item.get('quantity', 0))
            price_ea = float(item.get('price_ea', 0))
            text_body += f"{item_name} x{quantity} @ ${price_ea:.2f} = ${quantity * price_ea:.2f}\n"
        
        text_body += f"\nSubtotal: ${receipt.get('subtotal', 0):.2f}\n"
        if receipt.get('discount', 0) > 0:
            text_body += f"Discount: -${receipt.get('discount', 0):.2f}\n"
        text_body += f"Total: ${receipt.get('total', 0):.2f}\n\nThank you for your purchase!\nUIUC Horticulture Club"
        
        response = ses.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [recipient_email]},
            Message={
                'Subject': {'Data': f'PlantPass Receipt - Order {purchase_id}'},
                'Body': {
                    'Text': {'Data': text_body},
                    'Html': {'Data': html_body}
                }
            }
        )
        
        logger.info(f"Receipt email sent to {recipient_email}, MessageId: {response['MessageId']}")
        return True
        
    except ClientError as e:
        logger.error(f"Failed to send receipt email: {e}")
        raise

def send_password_reset_email(temp_password):
    """Send temporary password to UIUC Hort Club email"""
    try:
        html_body = f"""
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2e7d32;">PlantPass Admin Password Reset</h1>
            </div>
            
            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0 0 10px 0;">Your temporary password is:</p>
                <p style="font-size: 24px; font-weight: bold; color: #2e7d32; margin: 10px 0; font-family: monospace;">{temp_password}</p>
            </div>
            
            <p style="color: #666; margin-top: 20px;">Please use this temporary password to log in to the admin console. You will be required to change your password after logging in.</p>
            
            <p style="color: #d32f2f; margin-top: 20px;"><strong>Important:</strong> This temporary password will expire in 15 minutes.</p>
            
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666; font-size: 12px;">
                <p>If you did not request this password reset, please contact your system administrator.</p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
PlantPass Admin Password Reset

Your temporary password is: {temp_password}

Please use this temporary password to log in to the admin console. You will be required to change your password after logging in.

Important: This temporary password will expire in 15 minutes.

If you did not request this password reset, please contact your system administrator.
        """
        
        response = ses.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [UIUC_HORT_CLUB_EMAIL]},
            Message={
                'Subject': {'Data': 'PlantPass Admin Password Reset'},
                'Body': {
                    'Text': {'Data': text_body},
                    'Html': {'Data': html_body}
                }
            }
        )
        
        logger.info(f"Password reset email sent to {UIUC_HORT_CLUB_EMAIL}, MessageId: {response['MessageId']}")
        return True
        
    except ClientError as e:
        logger.error(f"Failed to send password reset email: {e}")
        raise

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        route_key = event.get("routeKey", "")
        
        if route_key == "POST /email/receipt":
            recipient_email = body.get('email')
            transaction_data = body.get('transaction')
            
            if not recipient_email or not transaction_data:
                return create_response(400, {"message": "Email and transaction data required"})
            
            send_receipt_email(recipient_email, transaction_data)
            return create_response(200, {"message": "Receipt email sent successfully"})
        
        elif route_key == "POST /email/password-reset":
            temp_password = body.get('temp_password')
            
            if not temp_password:
                return create_response(400, {"message": "Temporary password required"})
            
            send_password_reset_email(temp_password)
            return create_response(200, {"message": "Password reset email sent successfully"})
        
        else:
            return create_response(404, {"message": "Route not found"})
    
    except Exception as e:
        logger.error(f"Error in email handler: {e}", exc_info=True)
        return create_response(500, {"message": f"Internal server error: {str(e)}"})
