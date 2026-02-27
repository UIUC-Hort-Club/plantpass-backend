import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from utils import generate_random_id

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Transaction:
    
    def __init__(self, data=None, source="json"):
        self.data = data or {}
        self.source = source
        
        if source == "json":
            self._initialize_from_json()
        elif source == "db":
            self._initialize_from_db()
    
    def _initialize_from_json(self):
        self.purchase_id = generate_random_id()
        self.timestamp = self.data.get("timestamp", int(datetime.now(timezone.utc).timestamp()))
        self.items = self.data.get("items", [])
        self.input_discounts = self.data.get("discounts", [])
        self.club_voucher = self.data.get("voucher", 0)
        self.customer_email = self.data.get("email", "")
        
        self.payment = {
            "method": "",
            "paid": False
        }
        
        # Add payment_status for GSI
        self.payment_status = "unpaid"
        
        self._process_discounts()
        self._calculate_receipt()
    
    def _initialize_from_db(self):
        self.purchase_id = self.data.get("purchase_id")
        self.timestamp = self.data.get("timestamp")
        self.items = self.data.get("items", [])
        self.discounts = self.data.get("discounts", [])
        self.club_voucher = self.data.get("club_voucher", 0)
        self.customer_email = self.data.get("customer_email", "")
        self.payment = self.data.get("payment", {"method": "", "paid": False})
        self.receipt = self.data.get("receipt", {})
        
        # Set payment_status based on payment.paid
        self.payment_status = "paid" if self.payment.get("paid") else "unpaid"
    
    def _process_discounts(self):
        subtotal = self.get_subtotal()
        self.discounts = []
        
        for discount in self.input_discounts:
            discount_type = discount.get("type")
            selected = discount.get("selected", False)
            discount_value = discount.get("value", 0)
            
            discount_record = {
                "name": discount.get("name"),
                "type": discount_type,
                "value": discount_value
            }
            
            if selected:
                if discount_type == "dollar":
                    discount_record["amount_off"] = discount_value
                else:
                    discount_amount = (subtotal * discount_value) / 100
                    discount_record["amount_off"] = discount_amount
            else:
                discount_record["amount_off"] = 0
            
            self.discounts.append(discount_record)
    
    def _calculate_receipt(self):
        subtotal = self.get_subtotal()
        total_discount = self.get_total_discount()
        total = max(subtotal - total_discount, 0)
        
        self.receipt = {
            "subtotal": subtotal,
            "discount": total_discount,
            "total": total
        }
    
    def get_subtotal(self):
        return sum(item["quantity"] * item["price_ea"] for item in self.items)
    
    def get_total_discount(self):
        discount_amount = sum(discount.get("amount_off", 0) for discount in self.discounts)
        return discount_amount + self.club_voucher
    
    def update_items(self, new_items):
        preserved_items = []
        for updated_item in new_items:
            sku = updated_item["SKU"]
            original_item = next((item for item in self.items if item["SKU"] == sku), None)
            
            if original_item:
                preserved_item = {
                    "SKU": sku,
                    "item": original_item["item"],
                    "quantity": updated_item["quantity"],
                    "price_ea": original_item["price_ea"]
                }
                preserved_items.append(preserved_item)
            else:
                preserved_items.append(updated_item)
        
        self.items = preserved_items
        self._recalculate_discounts_and_receipt()
    
    def update_discounts(self, new_discounts):
        preserved_discounts = []
        subtotal = self.get_subtotal()
        
        for updated_discount in new_discounts:
            discount_name = updated_discount["name"]
            original_discount = next((d for d in self.discounts if d["name"] == discount_name), None)
            
            if original_discount:
                discount_record = {
                    "name": discount_name,
                    "type": original_discount["type"],
                    "value": original_discount["value"]
                }
                
                selected = updated_discount.get("selected", False)
                
                if selected:
                    if original_discount["type"] == "dollar":
                        discount_record["amount_off"] = original_discount["value"]
                    else:
                        discount_amount = (subtotal * original_discount["value"]) / 100
                        discount_record["amount_off"] = discount_amount
                else:
                    discount_record["amount_off"] = 0
                
                preserved_discounts.append(discount_record)
            else:
                preserved_discounts.append(updated_discount)
        
        self.discounts = preserved_discounts
        self._calculate_receipt()
    
    def update_voucher(self, voucher_amount):
        self.club_voucher = voucher_amount
        self._calculate_receipt()
    
    def update_payment(self, payment_info):
        self.payment.update(payment_info)
        
        # Update payment_status field for GSI
        if payment_info.get('paid'):
            self.payment_status = 'paid'
        else:
            self.payment_status = 'unpaid'
    
    def _recalculate_discounts_and_receipt(self):
        subtotal = self.get_subtotal()
        
        for discount in self.discounts:
            if discount.get("amount_off", 0) > 0 and discount["type"] == "percent":
                discount_amount = (subtotal * discount["value"]) / 100
                discount["amount_off"] = discount_amount
        
        self._calculate_receipt()
    
    def to_dict(self):
        return {
            "purchase_id": self.purchase_id,
            "timestamp": self.timestamp,
            "items": self.items,
            "discounts": self.discounts,
            "club_voucher": self.club_voucher,
            "customer_email": self.customer_email,
            "payment": self.payment,
            "payment_status": self.payment_status,  # For GSI
            "receipt": self.receipt
        }
    
    def to_db_record(self):
        transaction_dict = self.to_dict()
        return json.loads(json.dumps(transaction_dict), parse_float=Decimal)
    
    @classmethod
    def from_json(cls, json_data):
        return cls(json_data, source="json")
    
    @classmethod
    def from_db_record(cls, db_record):
        return cls(db_record, source="db")
    
    def get_summary(self):
        return {
            "purchase_id": self.purchase_id,
            "timestamp": self.timestamp,
            "total_quantity": sum(item.get("quantity", 0) for item in self.items),
            "grand_total": self.receipt.get("total", 0),
            "paid": self.payment.get("paid", False)
        }
