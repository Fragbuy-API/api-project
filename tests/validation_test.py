import requests
import json
import time

# API base URL
BASE_URL = "http://155.138.159.75/api/v1"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    ENDC = '\033[0m'

def print_test(test_name):
    """Print a test name header"""
    print(f"\n{Colors.BLUE}======== Testing: {test_name} ========{Colors.ENDC}")

def print_result(result, message):
    """Print the test result with appropriate color"""
    if result:
        print(f"{Colors.GREEN}✓ PASS: {message}{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ FAIL: {message}{Colors.ENDC}")
    return result

def print_json(data):
    """Print JSON data with yellow color"""
    print(f"{Colors.YELLOW}{json.dumps(data, indent=2)}{Colors.ENDC}")

def make_api_call(endpoint, data, expect_success=True):
    """Make an API call and verify the result"""
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        response = requests.post(url, json=data)
        status_code = response.status_code
        
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            response_json = {"error": "Invalid JSON response"}
        
        if expect_success:
            success = status_code == 200
            result_msg = "Request succeeded as expected" if success else f"Expected success but got status {status_code}"
        else:
            success = status_code != 200
            result_msg = f"Request failed as expected with status {status_code}" if success else "Expected failure but request succeeded"
        
        print_result(success, result_msg)
        print_json(response_json)
        return success, response_json
    
    except Exception as e:
        print_result(False, f"Exception occurred: {str(e)}")
        return False, {"error": str(e)}

# ======== PUTAWAY ORDER TESTS ========

def test_putaway_order_valid():
    print_test("Valid Putaway Order")
    
    data = {
        "tote": "TOTE123ABC",
        "items": [
            {
                "sku": "SKU-001",
                "name": "Test Product 1",
                "barcode": "12345678901",
                "quantity": 5
            },
            {
                "sku": "SKU-002",
                "name": "Test Product 2",
                "barcode": "98765432109",
                "quantity": 3
            }
        ]
    }
    
    return make_api_call("putawayOrder", data)

def test_putaway_order_invalid_tote():
    print_test("Invalid Tote Format")
    
    data = {
        "tote": "INVALID_TOTE_FORMAT", # Should start with TOTE
        "items": [
            {
                "sku": "SKU-001",
                "name": "Test Product 1",
                "barcode": "12345678901",
                "quantity": 5
            }
        ]
    }
    
    return make_api_call("putawayOrder", data, expect_success=False)

def test_putaway_order_invalid_barcode():
    print_test("Invalid Barcode")
    
    data = {
        "tote": "TOTE123ABC",
        "items": [
            {
                "sku": "SKU-001",
                "name": "Test Product 1",
                "barcode": "123", # Too short
                "quantity": 5
            }
        ]
    }
    
    return make_api_call("putawayOrder", data, expect_success=False)

def test_putaway_order_duplicate_skus():
    print_test("Duplicate SKUs")
    
    data = {
        "tote": "TOTE123ABC",
        "items": [
            {
                "sku": "SKU-001",
                "name": "Test Product 1",
                "barcode": "12345678901",
                "quantity": 5
            },
            {
                "sku": "SKU-001", # Duplicate SKU
                "name": "Test Product 2",
                "barcode": "98765432109",
                "quantity": 3
            }
        ]
    }
    
    return make_api_call("putawayOrder", data, expect_success=False)

def test_putaway_order_invalid_quantity():
    print_test("Invalid Quantity")
    
    data = {
        "tote": "TOTE123ABC",
        "items": [
            {
                "sku": "SKU-001",
                "name": "Test Product 1",
                "barcode": "12345678901",
                "quantity": -5 # Negative quantity
            }
        ]
    }
    
    return make_api_call("putawayOrder", data, expect_success=False)

# ======== BULK STORAGE TESTS ========

def test_bulk_storage_valid():
    print_test("Valid Bulk Storage")
    
    data = {
        "location": "RACK-A1-01",
        "items": [
            {
                "sku": "BULK-001",
                "name": "Bulk Product 1",
                "barcode": "12345678901",
                "quantity": 100
            },
            {
                "sku": "BULK-002",
                "name": "Bulk Product 2",
                "barcode": "98765432109",
                "quantity": 50
            }
        ]
    }
    
    return make_api_call("bulkStorage", data)

def test_bulk_storage_invalid_location():
    print_test("Invalid Location Format")
    
    data = {
        "location": "INVALID-LOCATION", # Wrong format
        "items": [
            {
                "sku": "BULK-001",
                "name": "Bulk Product 1",
                "barcode": "12345678901",
                "quantity": 100
            }
        ]
    }
    
    return make_api_call("bulkStorage", data, expect_success=False)

def test_bulk_storage_duplicate_skus():
    print_test("Duplicate SKUs in Bulk Storage")
    
    data = {
        "location": "RACK-A1-01",
        "items": [
            {
                "sku": "BULK-001",
                "name": "Bulk Product 1",
                "barcode": "12345678901",
                "quantity": 100
            },
            {
                "sku": "BULK-001", # Duplicate SKU
                "name": "Bulk Product 2",
                "barcode": "98765432109",
                "quantity": 50
            }
        ]
    }
    
    return make_api_call("bulkStorage", data, expect_success=False)

# ======== MEASUREMENT TESTS ========

def test_measurement_valid():
    print_test("Valid Measurement")
    
    data = {
        "timestamp": "2025-02-18T22:30:00.000Z",
        "l": 187,
        "w": 102,
        "h": 58,
        "weight": 560,
        "barcode": "860003782507",
        "shape": "Cuboidal",
        "device": "FH0402211700010",
        "note": "Test measurement",
        "attributes": {
            "ovpk": "false",
            "batt": "true",
            "hazmat": "false",
            "qty": "5",
            "sku": "TEST-SKU-001"
        },
        "image": "test_image_data"
    }
    
    return make_api_call("measurement", data)

def test_measurement_invalid_barcode():
    print_test("Invalid Measurement Barcode")
    
    data = {
        "timestamp": "2025-02-18T22:30:00.000Z",
        "l": 187,
        "w": 102,
        "h": 58,
        "weight": 560,
        "barcode": "123", # Too short
        "shape": "Cuboidal",
        "device": "FH0402211700010",
        "note": "Test measurement",
        "attributes": {
            "ovpk": "false",
            "batt": "true",
            "hazmat": "false",
            "qty": "5"
        },
        "image": "test_image_data"
    }
    
    return make_api_call("measurement", data, expect_success=False)

def test_measurement_invalid_attributes():
    print_test("Missing Required Attributes")
    
    data = {
        "timestamp": "2025-02-18T22:30:00.000Z",
        "l": 187,
        "w": 102,
        "h": 58,
        "weight": 560,
        "barcode": "860003782507",
        "shape": "Cuboidal",
        "device": "FH0402211700010",
        "note": "Test measurement",
        "attributes": {
            # Missing required attributes
            "ovpk": "false",
            "batt": "true"
            # Missing hazmat and qty
        },
        "image": "test_image_data"
    }
    
    return make_api_call("measurement", data, expect_success=False)

def test_measurement_invalid_dimensions():
    print_test("Invalid Dimensions")
    
    data = {
        "timestamp": "2025-02-18T22:30:00.000Z",
        "l": -187, # Negative dimension
        "w": 102,
        "h": 58,
        "weight": 560,
        "barcode": "860003782507",
        "shape": "Cuboidal",
        "device": "FH0402211700010",
        "note": "Test measurement",
        "attributes": {
            "ovpk": "false",
            "batt": "true",
            "hazmat": "false",
            "qty": "5"
        },
        "image": "test_image_data"
    }
    
    return make_api_call("measurement", data, expect_success=False)

# ======== RUN ALL TESTS ========

def run_all_tests():
    """Run all validation tests"""
    print(f"{Colors.BLUE}================= STARTING VALIDATION TESTS ================={Colors.ENDC}")
    
    test_results = {
        "putaway_order": {
            "valid": test_putaway_order_valid()[0],
            "invalid_tote": test_putaway_order_invalid_tote()[0],
            "invalid_barcode": test_putaway_order_invalid_barcode()[0],
            "duplicate_skus": test_putaway_order_duplicate_skus()[0],
            "invalid_quantity": test_putaway_order_invalid_quantity()[0]
        },
        "bulk_storage": {
            "valid": test_bulk_storage_valid()[0],
            "invalid_location": test_bulk_storage_invalid_location()[0],
            "duplicate_skus": test_bulk_storage_duplicate_skus()[0]
        },
        "measurement": {
            "valid": test_measurement_valid()[0],
            "invalid_barcode": test_measurement_invalid_barcode()[0],
            "invalid_attributes": test_measurement_invalid_attributes()[0],
            "invalid_dimensions": test_measurement_invalid_dimensions()[0]
        }
    }
    
    # Calculate test results
    tests_passed = sum(1 for category in test_results.values() for test_success in category.values() if test_success)
    total_tests = sum(len(category) for category in test_results.values())
    
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Total tests: {total_tests}")
    print(f"Tests passed: {tests_passed}")
    print(f"Success rate: {(tests_passed / total_tests) * 100:.1f}%")
    
    # Check if all tests passed as expected
    all_passed = True
    for category, tests in test_results.items():
        for test_name, success in tests.items():
            expected_success = "valid" in test_name
            if success != expected_success:
                all_passed = False
                print(f"{Colors.RED}✗ Test issue: {category} - {test_name} - {'Success' if success else 'Failure'} was unexpected{Colors.ENDC}")
    
    if all_passed:
        print(f"{Colors.GREEN}✓ All tests produced expected results{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests did not produce expected results{Colors.ENDC}")

if __name__ == "__main__":
    run_all_tests()