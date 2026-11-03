"""Eligibility logic for refunds."""
from datetime import datetime, timedelta

def validate_ownership(order: dict, customer_id: str) -> bool:
    """REQ-001: Customer can only request a refund for their own order."""
    return order.get("customer_id") == customer_id

def validate_window(order_date: datetime, request_date: datetime) -> bool:
    """REQ-002: Refund requests must be within 30 days of purchase."""
    return (request_date - order_date) <= timedelta(days=30)
