#!/usr/bin/env python3
"""
Test script for Gemini Labeling Service
Tests JSON parsing, validation, and error handling
"""

import sys
import io
import json

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, 'backend')

def test_json_parsing():
    """Test the JSON parsing and validation logic"""
    from services.gemini_service import GeminiLabelingService

    print("=" * 70)
    print("TEST 1: JSON Parsing and Validation")
    print("=" * 70)

    # We'll test the private methods directly
    service = object.__new__(GeminiLabelingService)

    test_cases = [
        {
            "name": "Valid JSON",
            "response": '{"label": "electronics", "confidence_score": 0.95}',
            "should_pass": True
        },
        {
            "name": "JSON with Markdown (common format)",
            "response": '```json\n{"label": "clothing", "confidence_score": 0.87}\n```',
            "should_pass": True
        },
        {
            "name": "JSON with extra text",
            "response": 'Based on the data, I classify this as:\n{"label": "furniture", "confidence_score": 0.72}',
            "should_pass": True
        },
        {
            "name": "JSON with newlines",
            "response": '{\n  "label": "food",\n  "confidence_score": 0.91\n}',
            "should_pass": True
        },
        {
            "name": "Missing confidence_score",
            "response": '{"label": "electronics"}',
            "should_pass": False,
            "error": "missing required fields"
        },
        {
            "name": "Invalid confidence (out of range)",
            "response": '{"label": "test", "confidence_score": 1.5}',
            "should_pass": False,
            "error": "must be between 0.0 and 1.0"
        },
        {
            "name": "Invalid confidence (wrong type)",
            "response": '{"label": "test", "confidence_score": "high"}',
            "should_pass": False,
            "error": "must be a number"
        },
        {
            "name": "Label too long",
            "response": '{"label": "' + 'x' * 60 + '", "confidence_score": 0.5}',
            "should_pass": False,
            "error": "1-50 characters"
        }
    ]

    passed = 0
    failed = 0

    for test in test_cases:
        try:
            result = service._parse_json_response(test["response"])
            validation = service._validate_response(result)

            if test["should_pass"]:
                print(f"\n[PASS] {test['name']}")
                print(f"  Label: {validation['label']}")
                print(f"  Confidence: {validation['confidence_score']}")
                passed += 1
            else:
                print(f"\n[FAIL] {test['name']}")
                print(f"  Expected error but got: {validation}")
                failed += 1

        except (ValueError, json.JSONDecodeError) as e:
            if not test["should_pass"]:
                if test.get("error") and test["error"] in str(e):
                    print(f"\n[PASS] {test['name']}")
                    print(f"  Expected error: {str(e)[:60]}...")
                    passed += 1
                else:
                    print(f"\n[FAIL] {test['name']}")
                    print(f"  Got error but wrong type: {str(e)}")
                    failed += 1
            else:
                print(f"\n[FAIL] {test['name']}")
                print(f"  Unexpected error: {str(e)}")
                failed += 1

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0

def test_prompt_generation():
    """Test prompt generation for different data types"""
    from services.gemini_service import GeminiLabelingService

    print("\n" + "=" * 70)
    print("TEST 2: Prompt Generation")
    print("=" * 70)

    service = object.__new__(GeminiLabelingService)

    # Test tabular prompt
    print("\n[1] Tabular Data Prompt (CSV):")
    print("-" * 70)
    sample_csv = "{'text': 'Great product!', 'category': 'electronics'}"
    prompt = service._create_tabular_prompt(sample_csv, "csv")
    print(prompt[:300] + "...")

    # Test image prompt
    print("\n[2] Image Data Prompt:")
    print("-" * 70)
    prompt = service._create_image_prompt()
    print(prompt[:300] + "...")

    # Test audio prompt
    print("\n[3] Audio Data Prompt:")
    print("-" * 70)
    sample_audio = {"duration": 2.5, "sample_rate": 44100}
    prompt = service._create_audio_prompt().format(content=json.dumps(sample_audio))
    print(prompt[:300] + "...")

    print("\n" + "=" * 70)
    print("All prompts generated successfully!")
    print("=" * 70)

    return True

def test_service_initialization():
    """Test service initialization with and without API key"""
    import os
    from services.gemini_service import GeminiLabelingService

    print("\n" + "=" * 70)
    print("TEST 3: Service Initialization")
    print("=" * 70)

    # Test 1: Without API key
    print("\n[1] Initialization without API key:")
    original_key = os.environ.get("GEMINI_API_KEY")
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]

    try:
        service = GeminiLabelingService()
        print("[FAIL] Should have raised ValueError for missing API key")
        result1 = False
    except ValueError as e:
        print(f"[PASS] Correctly raised error: {str(e)[:60]}...")
        result1 = True
    finally:
        if original_key:
            os.environ["GEMINI_API_KEY"] = original_key

    # Test 2: With API key (mock)
    print("\n[2] Initialization with API key:")
    os.environ["GEMINI_API_KEY"] = "test-api-key-12345"

    try:
        service = GeminiLabelingService()
        print("[PASS] Service initialized successfully")
        print(f"  Model: {service.model}")
        result2 = True
    except Exception as e:
        # google-generativeai might not be installed, that's ok
        if "google-generativeai" in str(e):
            print(f"[NOTE] google-generativeai not installed: {str(e)[:40]}...")
            result2 = True
        else:
            print(f"[FAIL] Unexpected error: {str(e)}")
            result2 = False

    # Restore original key
    if original_key:
        os.environ["GEMINI_API_KEY"] = original_key
    elif "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]

    print("\n" + "=" * 70)
    print("Initialization tests completed!")
    print("=" * 70)

    return result1 and result2

def test_error_handling():
    """Test robust error handling"""
    from services.gemini_service import GeminiLabelingService

    print("\n" + "=" * 70)
    print("TEST 4: Error Handling")
    print("=" * 70)

    service = object.__new__(GeminiLabelingService)
    test_cases = [
        {
            "name": "Empty response",
            "response": "",
            "error_type": "JSONDecodeError"
        },
        {
            "name": "Invalid JSON",
            "response": "{invalid json}",
            "error_type": "JSONDecodeError"
        },
        {
            "name": "Non-dict response",
            "response": '["label", "confidence"]',
            "error_type": "ValueError"
        },
        {
            "name": "Null values",
            "response": '{"label": null, "confidence_score": 0.5}',
            "error_type": "ValueError"
        }
    ]

    passed = 0

    for test in test_cases:
        try:
            result = service._parse_json_response(test["response"])
            print(f"\n[FAIL] {test['name']} - should have raised error")
        except Exception as e:
            print(f"\n[PASS] {test['name']}")
            print(f"  Error: {str(e)[:70]}...")
            passed += 1

    print("\n" + "=" * 70)
    print(f"Error handling: {passed}/{len(test_cases)} tests passed")
    print("=" * 70)

    return passed == len(test_cases)

def test_database_integration():
    """Test integration with database models"""
    import os
    from pathlib import Path

    print("\n" + "=" * 70)
    print("TEST 5: Database Integration")
    print("=" * 70)

    # Check if database exists
    db_path = Path("backend/autolabel.db")

    if db_path.exists():
        print(f"\n[OK] Database found: {db_path}")

        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            print(f"\n[OK] Tables found:")
            for table in tables:
                print(f"  - {table[0]}")

            # Check data items
            cursor.execute("SELECT COUNT(*) FROM data_items")
            count = cursor.fetchone()[0]
            print(f"\n[OK] Data items in database: {count}")

            # Sample items
            cursor.execute(
                "SELECT id, file_type, final_label, confidence_score FROM data_items LIMIT 3"
            )
            items = cursor.fetchall()

            print(f"\n[OK] Sample items:")
            for item in items:
                labeled = "Yes" if item[2] else "No"
                print(f"  - ID: {item[0]}, Type: {item[1]}, Labeled: {labeled}")

            conn.close()
            return True

        except Exception as e:
            print(f"\n[ERROR] Database check failed: {str(e)}")
            return False
    else:
        print(f"\n[NOTE] Database not found at {db_path}")
        print("  Run test_upload.py first to create test data")
        return True

def main():
    """Run all tests"""
    print("\n")
    print("*" * 70)
    print("GEMINI LABELING SERVICE - CORE IMPLEMENTATION TEST")
    print("*" * 70)

    results = []

    results.append(("JSON Parsing", test_json_parsing()))
    results.append(("Prompt Generation", test_prompt_generation()))
    results.append(("Service Initialization", test_service_initialization()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("Database Integration", test_database_integration()))

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

if __name__ == "__main__":
    main()
