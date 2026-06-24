import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timezone
from typing import List, Dict

from faker import Faker

fake = Faker()
from config.settings import CUSTOMERS_MAX, CUSTOMERS_MIN


def introduce_bad_data(customer: Dict[str, any]) -> Dict[str, any]:
    """Randomly introduce bad data into the customer record to simulate real-world scenarios.
    """

    # Introduce some bad data with a 10% chance
    if random.random() < 0.1:
        customer["email"] = "invalid-email"
    if random.random() < 0.1:
        customer["phone"] = "12345"
    if random.random() < 0.1:
        customer["address"] = ""
    return customer


def generate_customers(batch_id: str) -> List[Dict]:
    count = random.randint(CUSTOMERS_MIN, CUSTOMERS_MAX)
    customers = []

    for _ in range(count):
        new_customer = {
            "customer_id": f"CUST{random.randint(10000, 99999)}",
            "name": fake.name(),
            "email": fake.email(),
            "address": fake.address(),
            "phone": fake.phone_number(),
            "created_at": datetime.now(timezone.utc),
            "city": fake.city(),
            "country": fake.country(),
            "batch_id": batch_id,
        }

        bad_customer = introduce_bad_data(new_customer)
        customers.append(bad_customer)

    return customers

print(generate_customers(f"{datetime.now(timezone.utc).strftime}"))

