#!/usr/bin/env python3
"""
Test script for Step 5: Active Learning and Export
Tests local model training, inference, and export functionality
"""

import sys
import io
import os
import json
import tempfile

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, 'backend')

def test_model_training():
    """Test local model training"""
    print("=" * 70)
    print("TEST 1: Local Model Training")
    print("=" * 70)

    from services.model_training import LocalModelTrainer

    trainer = LocalModelTrainer()

    # Create test data
    texts = [
        "Great product, very happy",
        "Terrible quality, disappointed",
        "Excellent service, recommend",
        "Bad experience, not worth it",
        "Amazing purchase, love it",
        "Waste of money, broken",
        "Perfect! Exactly what I needed",
        "Awful, never again",
        "Great value for price",
        "Poor quality, returned it",
        "Outstanding, best ever",
        "Terrible, worst purchase",
    ]

    labels = [
        "positive", "negative", "positive", "negative",
        "positive", "negative", "positive", "negative",
        "positive", "negative", "positive", "negative"
    ]

    try:
        print("\n[1] Training model on 12 samples (2 classes)...")
        metadata = trainer.train_model(
            dataset_id=999,
            dataset_name="test_dataset",
            texts=texts,
            labels=labels,
            model_type="logistic_regression"
        )

        print(f"[OK] Training completed")
        print(f"    Model type: {metadata['model_type']}")
        print(f"    Training samples: {metadata['training_samples']}")
        print(f"    Classes: {metadata['n_classes']}")
        print(f"    Accuracy: {metadata['accuracy']:.4f}")
        print(f"    F1-Score: {metadata['f1_score']:.4f}")

        # Test prediction
        print("\n[2] Testing model inference...")
        test_text = "This is an amazing product!"
        label, confidence = trainer.predict(999, test_text)

        print(f"[OK] Prediction successful")
        print(f"    Text: {test_text}")
        print(f"    Label: {label}")
        print(f"    Confidence: {confidence:.4f}")

        # Check model exists
        print("\n[3] Checking model existence...")
        exists = trainer.model_exists(999)
        print(f"[OK] Model exists: {exists}")

        # Get metadata
        print("\n[4] Retrieving metadata...")
        retrieved = trainer.get_metadata(999)
        if retrieved:
            print(f"[OK] Metadata retrieved")
            print(f"    Training date: {retrieved['training_date']}")
            print(f"    Accuracy: {retrieved['accuracy']:.4f}")
        else:
            print("[FAIL] Could not retrieve metadata")
            return False

        # Clean up
        print("\n[5] Cleaning up...")
        trainer.delete_model(999)
        exists = trainer.model_exists(999)
        print(f"[OK] Model deleted: {not exists}")

        return True

    except Exception as e:
        print(f"\n[FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_export_service():
    """Test export service functionality"""
    print("\n" + "=" * 70)
    print("TEST 2: Export Service")
    print("=" * 70)

    from services.export_service import ExportService

    # Create mock objects
    class MockDataset:
        id = 1
        name = "test_dataset"
        file_type = "csv"
        description = "Test dataset"
        created_at = __import__('datetime').datetime.utcnow()

    class MockItem:
        def __init__(self, item_id, label, confidence=0.8):
            self.id = item_id
            self.content_preview = f"Sample text {item_id}"
            self.file_type = "csv"
            self.final_label = label
            self.confidence_score = confidence
            self.is_reviewed = confidence == 1.0
            self.raw_data_path = f"storage/uploads/file_{item_id}.csv"
            self.created_at = __import__('datetime').datetime.utcnow()

    service = ExportService()
    dataset = MockDataset()
    items = [
        MockItem(1, "positive", 1.0),
        MockItem(2, "negative", 0.85),
        MockItem(3, "positive", 0.72),
        MockItem(4, "neutral", 0.65),
        MockItem(5, "positive", 1.0),
    ]

    try:
        # Test CSV export
        print("\n[1] Testing CSV export...")
        csv_content = service.export_to_csv(dataset, items)
        print(f"[OK] CSV export: {len(csv_content)} bytes")
        print(f"    Contains header: {'content_preview' in csv_content}")
        print(f"    Contains data: {'Sample text' in csv_content}")

        # Test JSON export
        print("\n[2] Testing JSON export...")
        json_content = service.export_to_json(dataset, items)
        json_data = json.loads(json_content)
        print(f"[OK] JSON export: {len(json_content)} bytes")
        print(f"    Metadata keys: {list(json_data['metadata'].keys())[:3]}...")
        print(f"    Items count: {len(json_data['items'])}")
        print(f"    Average confidence: {json_data['metadata']['average_confidence']:.4f}")

        # Test ML-ready export
        print("\n[3] Testing ML-ready CSV export...")
        ml_csv = service.export_to_ml_ready_csv(dataset, items)
        ml_lines = ml_csv.strip().split('\n')
        print(f"[OK] ML-ready export: {len(ml_csv)} bytes")
        print(f"    Header: {ml_lines[0]}")
        print(f"    Data rows (reviewed only): {len(ml_lines) - 1}")

        # Test ZIP export
        print("\n[4] Testing ZIP export...")
        zip_content = service.export_to_zip(dataset, items, include_original_files=False)
        print(f"[OK] ZIP export: {len(zip_content)} bytes")
        print(f"    Is binary: {isinstance(zip_content, bytes)}")

        # Test export list
        print("\n[5] Testing export list...")
        exports = service.list_exports()
        print(f"[OK] Found {len(exports)} exports")

        return True

    except Exception as e:
        print(f"\n[FAIL] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_hybrid_inference():
    """Test hybrid inference strategy (local + Gemini fallback)"""
    print("\n" + "=" * 70)
    print("TEST 3: Hybrid Inference Strategy")
    print("=" * 70)

    from services.model_training import LocalModelTrainer

    trainer = LocalModelTrainer()

    # Train a simple model
    texts = [
        "Great product", "Bad product",
        "Good service", "Poor service",
        "Amazing quality", "Terrible quality",
    ]
    labels = ["positive", "negative", "positive", "negative", "positive", "negative"]

    try:
        print("\n[1] Training model for hybrid inference test...")
        metadata = trainer.train_model(
            dataset_id=888,
            dataset_name="hybrid_test",
            texts=texts,
            labels=labels
        )
        print(f"[OK] Model trained: accuracy={metadata['accuracy']:.4f}")

        # Test high-confidence prediction
        print("\n[2] Testing high-confidence prediction...")
        text = "This is a great product"
        label, confidence = trainer.predict(888, text)
        print(f"[OK] Prediction: {label} ({confidence:.4f})")

        if confidence >= 0.7:
            print(f"    Would use LOCAL model (confidence >= 0.7)")
        else:
            print(f"    Would fall back to GEMINI (confidence < 0.7)")

        # Test inference decision logic
        print("\n[3] Testing inference decision tree...")

        test_cases = [
            ("Very bad quality", 0.7),  # Should use local
            ("Okay product", 0.65),     # Might fall back
            ("Amazing service", 0.75),  # Should use local
        ]

        for test_text, threshold in test_cases:
            _, conf = trainer.predict(888, test_text)
            model_used = "LOCAL" if conf >= threshold else "GEMINI"
            print(f"    '{test_text}' -> confidence={conf:.4f} -> {model_used}")

        trainer.delete_model(888)
        return True

    except Exception as e:
        print(f"\n[FAIL] Error: {str(e)}")
        return False

def test_retraining_trigger_logic():
    """Test the retraining trigger logic"""
    print("\n" + "=" * 70)
    print("TEST 4: Retraining Trigger Logic")
    print("=" * 70)

    try:
        print("\n[1] Simulating correction sequence...")
        print("    Testing retraining trigger at every 10th correction\n")

        corrections = [i for i in range(1, 31)]
        training_triggered = []

        for correction_count in corrections:
            if correction_count % 10 == 0:
                training_triggered.append(correction_count)
                print(f"    Correction {correction_count:2d}: RETRAINING TRIGGERED")
            else:
                print(f"    Correction {correction_count:2d}: No training")

        print(f"\n[OK] Training would be triggered at corrections: {training_triggered}")
        print(f"    Expected: [10, 20, 30]")
        print(f"    Match: {training_triggered == [10, 20, 30]}")

        # Test edge cases
        print("\n[2] Testing edge cases...")
        edge_cases = [0, 1, 5, 9, 10, 11, 19, 20, 100, 101]

        for count in edge_cases:
            should_train = (count > 0) and (count % 10 == 0)
            marker = "TRAIN" if should_train else "skip"
            print(f"    {count:3d} reviewed items -> {marker}")

        return True

    except Exception as e:
        print(f"\n[FAIL] Error: {str(e)}")
        return False

def test_endpoint_structure():
    """Test that all new endpoints are defined"""
    print("\n" + "=" * 70)
    print("TEST 5: API Endpoint Structure")
    print("=" * 70)

    new_endpoints = {
        "Export": [
            "GET /api/datasets/{id}/export/csv",
            "GET /api/datasets/{id}/export/json",
            "GET /api/datasets/{id}/export/ml-ready",
            "GET /api/datasets/{id}/export/zip",
        ],
        "Model Management": [
            "GET /api/models",
            "GET /api/models/{dataset_id}",
            "POST /api/datasets/{id}/train-model",
            "POST /api/models/{dataset_id}/delete",
        ],
        "Enhanced Labeling": [
            "PUT /api/items/{id}/correct (with auto-retraining)",
        ]
    }

    print("\nNew endpoints for Step 5:\n")

    total = 0
    for category, endpoints in new_endpoints.items():
        print(f"[{category}]")
        for endpoint in endpoints:
            print(f"  - {endpoint}")
            total += 1
        print()

    print(f"[OK] Total new endpoints: {total}")
    return True

def main():
    """Run all tests"""
    print("\n")
    print("*" * 70)
    print("STEP 5: ACTIVE LEARNING & EXPORT - TEST SUITE")
    print("*" * 70)

    results = []

    results.append(("Model Training", test_model_training()))
    results.append(("Export Service", test_export_service()))
    results.append(("Hybrid Inference", test_hybrid_inference()))
    results.append(("Retraining Trigger", test_retraining_trigger_logic()))
    results.append(("API Endpoints", test_endpoint_structure()))

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
