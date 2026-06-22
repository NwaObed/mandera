"""Generates synthetic order records."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timezone

from typing import List, Dict

from config.settings import ORDERS_MIN, ORDERS_MAX, REGIONS, PAYMENT_STATUSES


# ── Source generation settings (used by generator/) ────────────

def introduce_bad_order_data(order: Dict[str, any]) -> Dict[str, any]:
    """Introduce common order data quality issues in a simple, explainable way."""
    if random.random() < 0.08:  # 8% missing customer reference
        order["customer_id"] = None

    if random.random() < 0.08:  # 8% missing product reference
        order["product_id"] = None

    if random.random() < 0.06:  # 6% invalid amount values
        order["amount"] = "NaN"

    if random.random() < 0.05:  # 5% negative amount bug
        if isinstance(order["amount"], (int, float)):
            order["amount"] = -abs(order["amount"])

    if random.random() < 0.05:  # 5% invalid status values
        order["payment_status"] = "UNKNOWN_STATUS"

    return order


def generate_orders(customer_ids: List[int], product_ids: List[int], batch_id: str) -> List[Dict[str, any]]:
    count = random.randint(ORDERS_MIN, ORDERS_MAX)
    orders_data = []

    for _ in range(count):
        new_order = {
            "order_id": f"ORD{random.randint(10000, 99999)}",
            "customer_id": random.choice(customer_ids),
            "product_id": random.choice(product_ids),
            "region": random.choice(REGIONS),
            "quantity": random.randint(1, 5),
            "amount": round(random.uniform(1000, 3000), 2), # questionable. Should be product price * quantity, but we want to test amount-related issues too
            "payment_status": random.choice(PAYMENT_STATUSES),
            "batch_id": batch_id,
            "created_at": datetime.now(timezone.utc),
        }

        bad_order_data = introduce_bad_order_data(new_order)
        orders_data.append(bad_order_data)

    return orders_data

if __name__ == "__main__":
    print(generate_orders([34, 23], [45, 23], "batch_001"))  # Example usage