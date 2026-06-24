"""
Orchestrates synthetic data generation → MongoDB Atlas.

Calls each faker module, inserts the results into MongoDB,
and logs what was generated. Designed to be called by GitHub Actions.

Usage:
    python -m generator.data_generator
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient

from config.settings import generate_batch_id
from config.mongo_settings import MONGO_URI, MONGO_DB, MONGO_COLLECTIONS

from generator import faker_customers, faker_products, faker_orders



def run():
    """Generate customers → products → orders and insert into MongoDB."""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]

    # Generate batch_id once so all records in this run share the same ID
    batch_id = generate_batch_id()
    print(f"  Batch ID: {batch_id}\n")

    try:
        # Generate and insert customers
        customers = faker_customers.generate_customers(batch_id)
        db[MONGO_COLLECTIONS["customers"]].insert_many(customers)
        print(f"  ✓ Inserted {len(customers)} customers")

        # Generate and insert products
        products = faker_products.generate_products(batch_id)
        db[MONGO_COLLECTIONS["products"]].insert_many(products)
        print(f"  ✓ Inserted {len(products)} products")

        # Get ALL customer/product IDs so orders reference the full pool
        all_customer_ids = db[MONGO_COLLECTIONS["customers"]].distinct("customer_id")
        all_product_ids = db[MONGO_COLLECTIONS["products"]].distinct("product_id")

        # Generate and insert orders
        orders = faker_orders.generate_orders(all_customer_ids, all_product_ids, batch_id)
        db[MONGO_COLLECTIONS["orders"]].insert_many(orders)
        print(f"  ✓ Inserted {len(orders)} orders")

        client.close()

    finally:
        client.close()

    print("\n✓ Data generation complete.")


if __name__ == "__main__":
    run()