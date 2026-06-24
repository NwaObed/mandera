
import os
from datetime import datetime, timezone

from config import env  # noqa: F401


# Data generation settings
CUSTOMERS_MIN = 10
CUSTOMERS_MAX = 20
ORDERS_MIN = 2000
ORDERS_MAX = 5000
PRODUCTS_MIN = 5
PRODUCTS_MAX = 10

REGIONS = ["North America", "Europe", "Asia", "South America", "Africa", "Oceania"]
PAYMENT_METHODS = ["Credit Card", "PayPal", "Bank Transfer", "Cash on Delivery"]
ORDER_STATUSES = ["Pending", "Shipped", "Delivered", "Cancelled"]
PAYMENT_STATUSES = ["Pending", "Completed", "Failed", "Refunded"]

PRODUCT_CATEGORIES = {
    "Electronics": [
        "Smartphone", "Laptop", "Tablet", "Headphones", "Smartwatch",
        "Bluetooth Speaker", "Gaming Console", "Digital Camera", "Drone", "Monitor",
        "Keyboard", "Mouse", "Printer", "Router", "External Hard Drive",
        "Power Bank", "E-Reader", "Webcam", "Projector", "VR Headset",
    ],
    "Home Appliances": [
        "Refrigerator", "Microwave", "Washing Machine", "Air Conditioner", "Vacuum Cleaner",
        "Dishwasher", "Electric Kettle", "Coffee Maker", "Blender", "Toaster",
        "Rice Cooker", "Air Fryer", "Food Processor", "Water Dispenser", "Ceiling Fan",
        "Space Heater", "Iron", "Humidifier", "Dehumidifier", "Sewing Machine",
    ],
    "Clothing": [
        "T-Shirt", "Jeans", "Jacket", "Dress", "Shoes",
        "Sweater", "Hoodie", "Skirt", "Shorts", "Blazer",
        "Coat", "Socks", "Scarf", "Hat", "Belt",
        "Polo Shirt", "Cardigan", "Leggings", "Suit", "Sandals",
    ],
    "Books": [
        "Fiction", "Non-Fiction", "Science Fiction", "Biography", "Self-Help",
        "Mystery", "Fantasy", "Romance", "History", "Poetry",
        "Cookbook", "Travel Guide", "Graphic Novel", "Business", "Children's Book",
        "Young Adult", "Thriller", "Memoir", "Health", "Education",
    ],
    "Sports": [
        "Football", "Basketball", "Tennis Racket", "Running Shoes", "Yoga Mat",
        "Baseball Glove", "Golf Clubs", "Swimming Goggles", "Cycling Helmet", "Dumbbells",
        "Resistance Bands", "Boxing Gloves", "Soccer Cleats", "Cricket Bat", "Hiking Backpack",
        "Skipping Rope", "Exercise Bike", "Treadmill", "Water Bottle", "Fitness Tracker",
    ],
    "Beauty": [
        "Lipstick", "Foundation", "Mascara", "Perfume", "Skincare Set",
        "Moisturizer", "Cleanser", "Toner", "Sunscreen", "Face Serum",
        "Eyeliner", "Eyeshadow Palette", "Blush", "Concealer", "Nail Polish",
        "Hair Dryer", "Shampoo", "Conditioner", "Body Lotion", "Makeup Brushes",
    ],
    "Toys": [
        "Action Figure", "Puzzle", "Board Game", "Doll", "Building Blocks",
        "Toy Car", "Stuffed Animal", "Remote Control Car", "Science Kit", "Art Set",
        "Play Kitchen", "Train Set", "Kite", "Yo-Yo", "Water Gun",
        "Musical Toy", "Card Game", "Robot Toy", "Scooter", "Jump Rope",
    ],
    "Automotive": [
        "Car Battery", "Tire", "Car Cover", "GPS Navigator", "Car Vacuum Cleaner",
        "Engine Oil", "Brake Pads", "Windshield Wipers", "Seat Covers", "Dash Cam",
        "Jump Starter", "Floor Mats", "Air Freshener", "Car Charger", "Roof Rack",
        "Spark Plugs", "Tool Kit", "Pressure Gauge", "Coolant", "Headlight Bulb",
    ],
    "Grocery": [
        "Organic Vegetables", "Dairy Products", "Snacks", "Beverages", "Canned Goods",
        "Fresh Fruits", "Bread", "Rice", "Pasta", "Breakfast Cereal",
        "Cooking Oil", "Spices", "Frozen Foods", "Tea", "Coffee",
        "Chocolate", "Nuts", "Seafood", "Meat", "Baby Food",
    ],
}


# ── Batch scheduling ───────────────────────────────────────────
NUMBER_OF_BATCHES = int(os.getenv("NUMBER_OF_BATCHES", "1"))

# Scheduled run hours (UTC) — must match .github/workflows/generate_data.yml cron
BATCH_SCHEDULE_HOURS = [7, 15]

def generate_batch_id() -> str:
    """
    Auto-generate batch ID: 2026_03_23_07_batch_01

    date_part: YYYY_MM_DD
    hour: HH (24-hour format)
    batch_number: 1 or 2 based on which scheduled hour is closest (7 or 15 UTC)

    Determines the batch number based on which scheduled hour slot
    the current time falls closest to. Falls back to sequential
    numbering if the hour doesn't match a known schedule.
    """
    now = datetime.now(timezone.utc)
    date_part = now.strftime("%Y_%m_%d")
    hour = now.hour

    # Find the closest scheduled hour to determine batch number
    batch_number = 1
    for i, scheduled_hour in enumerate(BATCH_SCHEDULE_HOURS):
        if abs(hour - scheduled_hour) <= 1:
            batch_number = i + 1
            break
    else:
        # Manual run outside scheduled hours — assign based on AM/PM
        batch_number = 1 if hour < 12 else 2

    return f"{date_part}_{hour:02d}_batch_0{batch_number}"