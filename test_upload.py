#!/usr/bin/env python3
"""
Test script for AutoLabel AI Studio - Data Ingestion Layer
Tests the upload endpoint and database functionality
"""

import sys
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
import pandas as pd
import json
import os
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
TEST_DATA_DIR = "test_data"

def create_test_files():
    """Create test files for uploading"""
    os.makedirs(TEST_DATA_DIR, exist_ok=True)

    # Create test CSV
    csv_data = {
        'text': [
            'This is a positive review about the product',
            'Terrible quality, very disappointed',
            'Amazing service, highly recommend',
            'Not worth the money',
            'Best purchase I made this year'
        ],
        'category': ['electronics', 'clothing', 'electronics', 'furniture', 'electronics']
    }
    df = pd.DataFrame(csv_data)
    csv_path = os.path.join(TEST_DATA_DIR, "reviews.csv")
    df.to_csv(csv_path, index=False)
    print(f"✓ Created test CSV: {csv_path}")

    # Create test Excel
    excel_path = os.path.join(TEST_DATA_DIR, "products.xlsx")
    df.to_excel(excel_path, index=False, sheet_name="Data")
    print(f"✓ Created test Excel: {excel_path}")

    # Create test JSON
    json_data = [
        {"id": 1, "title": "Product A", "price": 29.99, "tags": ["electronics", "gadget"]},
        {"id": 2, "title": "Product B", "price": 49.99, "tags": ["electronics", "accessory"]},
        {"id": 3, "title": "Product C", "price": 199.99, "tags": ["electronics", "premium"]},
    ]
    json_path = os.path.join(TEST_DATA_DIR, "products.json")
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"✓ Created test JSON: {json_path}")

    return csv_path, excel_path, json_path

def upload_file(file_path, dataset_name=None):
    """Upload a file to the backend"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            params = {}
            if dataset_name:
                params['dataset_name'] = dataset_name

            print(f"\n📤 Uploading: {os.path.basename(file_path)}")
            response = requests.post(
                f"{BASE_URL}/api/upload",
                files=files,
                params=params,
                timeout=10
            )

        response.raise_for_status()
        result = response.json()

        print(f"✓ Upload successful!")
        print(f"  Dataset ID: {result['dataset_id']}")
        print(f"  Dataset Name: {result['dataset_name']}")
        print(f"  File Type: {result['file_type']}")
        print(f"  Item Count: {result['item_count']}")
        print(f"  Recommended Strategy: {result['recommended_strategy']}")
        print(f"  Message: {result['message']}")
        if result.get('preview'):
            print(f"  Preview: {json.dumps(result['preview'], indent=2)}")

        return result['dataset_id']

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend at {BASE_URL}")
        print("   Make sure the backend is running: python -m uvicorn backend.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Upload failed: {str(e)}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response.text}")
        return None

def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
        return True
    except:
        return False

def get_datasets():
    """Fetch and display all datasets"""
    try:
        response = requests.get(f"{BASE_URL}/api/datasets", timeout=10)
        response.raise_for_status()
        result = response.json()

        print(f"\n📊 Datasets in Database:")
        print(f"   Total datasets: {result['total']}")

        for dataset in result['datasets']:
            print(f"\n   Dataset: {dataset['name']}")
            print(f"   ID: {dataset['id']}")
            print(f"   Type: {dataset['file_type']}")
            print(f"   Created: {dataset['created_at']}")

        return result['datasets']

    except Exception as e:
        print(f"❌ Failed to fetch datasets: {str(e)}")
        return None

def get_dataset_items(dataset_id):
    """Fetch and display items in a dataset"""
    try:
        response = requests.get(f"{BASE_URL}/api/datasets/{dataset_id}/items", timeout=10)
        response.raise_for_status()
        result = response.json()

        print(f"\n📋 Items in Dataset {dataset_id}:")
        print(f"   Total items: {result['item_count']}")

        for idx, item in enumerate(result['items'][:3], 1):  # Show first 3
            print(f"\n   Item {idx}:")
            print(f"   ID: {item['id']}")
            print(f"   Type: {item['file_type']}")
            print(f"   Preview: {item['content_preview'][:100]}...")
            print(f"   Reviewed: {item['is_reviewed']}")

        if result['item_count'] > 3:
            print(f"\n   ... and {result['item_count'] - 3} more items")

    except Exception as e:
        print(f"❌ Failed to fetch items: {str(e)}")

def main():
    """Run the test"""
    print("=" * 60)
    print("🧪 AutoLabel AI Studio - Data Ingestion Test")
    print("=" * 60)

    # Check if backend is running
    print("\n🔍 Checking backend status...")
    if not check_backend():
        print("❌ Backend is not running!")
        print("   Start it with: cd backend && python -m uvicorn main:app --reload")
        sys.exit(1)
    print("✓ Backend is running!")

    # Create test files
    print("\n📝 Creating test files...")
    csv_path, excel_path, json_path = create_test_files()

    # Upload CSV
    print("\n" + "=" * 60)
    csv_dataset_id = upload_file(csv_path, dataset_name="test_reviews_csv")
    if csv_dataset_id:
        get_dataset_items(csv_dataset_id)

    # Upload Excel
    print("\n" + "=" * 60)
    excel_dataset_id = upload_file(excel_path, dataset_name="test_products_excel")
    if excel_dataset_id:
        get_dataset_items(excel_dataset_id)

    # Upload JSON
    print("\n" + "=" * 60)
    json_dataset_id = upload_file(json_path, dataset_name="test_products_json")
    if json_dataset_id:
        get_dataset_items(json_dataset_id)

    # Show all datasets
    print("\n" + "=" * 60)
    datasets = get_datasets()

    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
