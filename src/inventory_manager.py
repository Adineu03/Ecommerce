import json
import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
INVENTORY_FILE = os.path.join(DATA_DIR, 'inventory.json')

def load_inventory():
    # Ensure data folder exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # If the inventory file does not exist, create one with 25 predefined products
    if not os.path.exists(INVENTORY_FILE):
        # Create 25 default products (example list below).
        default_inventory = [
            {"id": 1,  "name": "Laptop",                     "price": 1200, "stock": 30, "popularity": 90},
            {"id": 2,  "name": "Smartphone",                 "price": 800,  "stock": 50, "popularity": 85},
            {"id": 3,  "name": "Tablet",                     "price": 500,  "stock": 20, "popularity": 70},
            {"id": 4,  "name": "Desktop PC",                 "price": 1500, "stock": 10, "popularity": 88},
            {"id": 5,  "name": "Gaming Console",             "price": 400,  "stock": 15, "popularity": 80},
            {"id": 6,  "name": "Smart Watch",                "price": 250,  "stock": 40, "popularity": 65},
            {"id": 7,  "name": "Headphones",                 "price": 120,  "stock": 60, "popularity": 72},
            {"id": 8,  "name": "Wireless Earbuds",           "price": 180,  "stock": 35, "popularity": 78},
            {"id": 9,  "name": "Bluetooth Speaker",          "price": 220,  "stock": 25, "popularity": 83},
            {"id": 10, "name": "External Hard Drive",        "price": 90,   "stock": 40, "popularity": 70},
            {"id": 11, "name": "USB Flash Drive (128GB)",    "price": 35,   "stock": 100,"popularity": 60},
            {"id": 12, "name": "Wireless Keyboard",          "price": 70,   "stock": 30, "popularity": 75},
            {"id": 13, "name": "Wireless Mouse",             "price": 40,   "stock": 45, "popularity": 68},
            {"id": 14, "name": "Webcam",                     "price": 60,   "stock": 20, "popularity": 65},
            {"id": 15, "name": "HDMI Cable",                 "price": 15,   "stock": 70, "popularity": 50},
            {"id": 16, "name": "Ethernet Cable (10 ft)",     "price": 10,   "stock": 80, "popularity": 52},
            {"id": 17, "name": "Smart Home Hub",             "price": 300,  "stock": 10, "popularity": 74},
            {"id": 18, "name": "Drone",                      "price": 600,  "stock": 5,  "popularity": 85},
            {"id": 19, "name": "DSLR Camera",                "price": 1000, "stock": 8,  "popularity": 80},
            {"id": 20, "name": "Action Camera",              "price": 250,  "stock": 12, "popularity": 66},
            {"id": 21, "name": "Portable Charger (10000mAh)","price": 25,   "stock": 50, "popularity": 60},
            {"id": 22, "name": "E-Reader",                   "price": 130,  "stock": 15, "popularity": 72},
            {"id": 23, "name": "Wireless Router",            "price": 90,   "stock": 25, "popularity": 67},
            {"id": 24, "name": "Bluetooth Tracker",          "price": 35,   "stock": 40, "popularity": 58},
            {"id": 25, "name": "USB-C Hub",                  "price": 45,   "stock": 30, "popularity": 65},
        ]
        # Convert to DataFrame and save
        save_inventory(pd.DataFrame(default_inventory))

    # Load the JSON file into a DataFrame
    with open(INVENTORY_FILE, 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)

def save_inventory(df):
    data = df.to_dict(orient='records')
    with open(INVENTORY_FILE, 'w') as f:
        json.dump(data, f, indent=4)
