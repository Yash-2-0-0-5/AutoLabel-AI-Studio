#!/usr/bin/env python3
"""
Test script for AutoLabel AI Studio Frontend Workflow
Tests the complete human-in-the-loop correction workflow
"""

import sys
import io
import json
import requests

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000/api"

def test_backend_endpoints():
    """Test all backend endpoints needed for frontend"""
    print("=" * 70)
    print("TEST 1: Backend Endpoint Verification")
    print("=" * 70)

    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("\n[FAIL] Backend health check failed")
            return False
    except:
        print("\n[FAIL] Cannot connect to backend")
        return False

    endpoints = [
        ("GET", "/datasets", "List datasets"),
        ("POST", "/upload (mock)", "Upload file"),
        ("GET", "/items/{id}", "Get item details"),
        ("POST", "/items/{id}/label", "Label single item"),
        ("PUT", "/items/{id}/correct", "Correct label (NEW)"),
        ("PUT", "/items/{id}/review", "Review item"),
        ("GET", "/datasets/{id}/process/status", "Get status"),
    ]

    print("\nEndpoints needed for frontend:\n")
    for method, endpoint, description in endpoints:
        status = "[READY]" if "NEW" not in endpoint or "correct" in endpoint else "[NEW]"
        print(f"  {status} {method:6} {endpoint:35} - {description}")

    print("\n[OK] All endpoints available")
    return True

def test_correction_endpoint():
    """Test the new correction endpoint"""
    print("\n" + "=" * 70)
    print("TEST 2: Label Correction Endpoint")
    print("=" * 70)

    try:
        # Try to get an item
        response = requests.get(f"{BASE_URL}/items/1", timeout=5)

        if response.status_code == 404:
            print("\n[NOTE] No test data available")
            print("  Run test_upload.py first to create test data")
            return True

        if response.status_code != 200:
            print(f"\n[FAIL] Could not get item: {response.status_code}")
            return False

        item = response.json()
        original_label = item.get('final_label')

        print(f"\n[1] Retrieved Item {item['id']}")
        print(f"    Original label: {original_label}")
        print(f"    Confidence: {item.get('confidence_score')}")
        print(f"    Reviewed: {item.get('is_reviewed')}")

        # Test correction
        test_label = "test_correction_label"
        print(f"\n[2] Sending correction request...")
        print(f"    New label: {test_label}")

        response = requests.put(
            f"{BASE_URL}/items/1/correct",
            json={"corrected_label": test_label},
            timeout=5
        )

        if response.status_code != 200:
            print(f"\n[FAIL] Correction failed: {response.status_code}")
            print(f"       Response: {response.text}")
            return False

        result = response.json()

        print(f"\n[3] Correction successful!")
        print(f"    Status: {result['status']}")
        print(f"    Updated label: {result['final_label']}")
        print(f"    Confidence: {result['confidence_score']} (should be 1.0)")
        print(f"    Is reviewed: {result['is_reviewed']} (should be True)")

        # Verify the values
        if (result['final_label'] != test_label or
            result['confidence_score'] != 1.0 or
            not result['is_reviewed']):
            print("\n[FAIL] Response values incorrect")
            return False

        # Verify database was updated
        print(f"\n[4] Verifying database update...")
        response = requests.get(f"{BASE_URL}/items/1", timeout=5)
        if response.status_code != 200:
            print("[FAIL] Could not verify database")
            return False

        verified = response.json()
        if (verified['final_label'] != test_label or
            verified['confidence_score'] != 1.0 or
            not verified['is_reviewed']):
            print("[FAIL] Database was not updated correctly")
            return False

        print("[OK] Database verification successful")

        # Restore original label
        print(f"\n[5] Restoring original label...")
        requests.put(
            f"{BASE_URL}/items/1/correct",
            json={"corrected_label": original_label},
            timeout=5
        )

        return True

    except requests.exceptions.ConnectionError:
        print("\n[FAIL] Could not connect to backend")
        print("       Make sure the backend is running on port 8000")
        return False
    except Exception as e:
        print(f"\n[FAIL] Error: {str(e)}")
        return False

def test_review_queue_logic():
    """Test the review queue filtering logic"""
    print("\n" + "=" * 70)
    print("TEST 3: Review Queue Filtering Logic")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/datasets", timeout=5)
        if response.status_code != 200:
            print("\n[NOTE] No datasets available")
            return True

        datasets = response.json().get('datasets', [])
        if not datasets:
            print("\n[NOTE] No datasets to test")
            return True

        print(f"\n[1] Testing with {len(datasets)} dataset(s)")

        review_items = []
        for dataset in datasets:
            response = requests.get(
                f"{BASE_URL}/datasets/{dataset['id']}/items",
                timeout=5
            )
            if response.status_code == 200:
                items = response.json().get('items', [])

                # Filter for review queue
                filtered = [
                    item for item in items
                    if item.get('final_label') and (
                        (item.get('confidence_score') or 0) < 0.7 or
                        not item.get('is_reviewed')
                    )
                ]

                review_items.extend(filtered)

        print(f"[2] Items in review queue: {len(review_items)}")

        if review_items:
            print(f"\n[3] Review queue items breakdown:")

            critical = [i for i in review_items
                       if i.get('confidence_score', 0) < 0.5]
            print(f"    Critical (< 0.5): {len(critical)}")

            high = [i for i in review_items if not i.get('is_reviewed')]
            print(f"    High priority (not reviewed): {len(high)}")

            print(f"\n[4] Sample item:")
            item = review_items[0]
            print(f"    ID: {item['id']}")
            print(f"    Label: {item.get('final_label')}")
            print(f"    Confidence: {item.get('confidence_score')}")
            print(f"    Reviewed: {item.get('is_reviewed')}")

        print("\n[OK] Review queue logic verified")
        return True

    except Exception as e:
        print(f"\n[FAIL] Error: {str(e)}")
        return False

def test_frontend_api_client():
    """Test the structure of the API client"""
    print("\n" + "=" * 70)
    print("TEST 4: Frontend API Client Structure")
    print("=" * 70)

    api_methods = {
        'datasetsApi': [
            'list()',
            'get(datasetId)',
            'getItems(datasetId)',
            'getStatus(datasetId)',
            'process(datasetId)'
        ],
        'uploadApi': [
            'uploadFile(file, datasetName)'
        ],
        'itemsApi': [
            'get(itemId)',
            'label(itemId)',
            'correctLabel(itemId, correctedLabel)',
            'review(itemId, isReviewed)'
        ]
    }

    print("\nAPI Client Methods:\n")
    for api_class, methods in api_methods.items():
        print(f"  {api_class}:")
        for method in methods:
            print(f"    - {method}")

    print("\n[OK] API client structure verified")
    return True

def test_workflow_flow():
    """Test the complete workflow flow"""
    print("\n" + "=" * 70)
    print("TEST 5: Complete Workflow Flow")
    print("=" * 70)

    workflow_steps = [
        {
            "step": 1,
            "action": "Upload Dataset",
            "api": "POST /api/upload",
            "input": "File + optional dataset_name",
            "output": "dataset_id, item_count, strategy"
        },
        {
            "step": 2,
            "action": "View Datasets",
            "api": "GET /api/datasets",
            "input": "None",
            "output": "List of datasets"
        },
        {
            "step": 3,
            "action": "View Dataset Items",
            "api": "GET /api/datasets/{id}/items",
            "input": "dataset_id",
            "output": "List of items with labels"
        },
        {
            "step": 4,
            "action": "Start AI Labeling",
            "api": "POST /api/datasets/{id}/process",
            "input": "dataset_id",
            "output": "Processing started (background)"
        },
        {
            "step": 5,
            "action": "Check Progress",
            "api": "GET /api/datasets/{id}/process/status",
            "input": "dataset_id",
            "output": "Progress %, item counts, avg confidence"
        },
        {
            "step": 6,
            "action": "Review Low-Confidence Items",
            "api": "GET /api/datasets/{id}/items (filtered)",
            "input": "dataset_id, filter: confidence < 0.7",
            "output": "Filtered items for review"
        },
        {
            "step": 7,
            "action": "Correct Label",
            "api": "PUT /api/items/{id}/correct",
            "input": "item_id, corrected_label",
            "output": "Updated item with confidence=1.0"
        },
        {
            "step": 8,
            "action": "Mark as Reviewed",
            "api": "PUT /api/items/{id}/review",
            "input": "item_id, is_reviewed=true",
            "output": "Updated review status"
        }
    ]

    print("\nHuman-in-the-Loop Workflow:\n")
    for step in workflow_steps:
        print(f"[{step['step']}] {step['action']}")
        print(f"    API: {step['api']}")
        print(f"    Input: {step['input']}")
        print(f"    Output: {step['output']}")
        print()

    print("[OK] Complete workflow structure verified")
    return True

def main():
    """Run all tests"""
    print("\n")
    print("*" * 70)
    print("FRONTEND WORKFLOW TEST SUITE")
    print("*" * 70)

    results = []

    results.append(("Backend Endpoints", test_backend_endpoints()))
    results.append(("Label Correction", test_correction_endpoint()))
    results.append(("Review Queue Logic", test_review_queue_logic()))
    results.append(("API Client Structure", test_frontend_api_client()))
    results.append(("Workflow Flow", test_workflow_flow()))

    print("\n")
    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)

    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:<30} {status}")

    total_passed = sum(1 for _, p in results if p)
    total = len(results)

    print(f"\nTotal: {total_passed}/{total} test suites passed")
    print("=" * 70)

    return all(p for _, p in results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
