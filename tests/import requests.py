import requests
import json
import time
import random

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

def make_api_call(endpoint, data, method="POST", expect_success=True):
    """Make an API call and verify the result"""
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        else:
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

def generate_random_barcode():
    """Generate a random valid barcode (8-14 digits)"""
    length = random.randint(8, 14)
    return ''.join(random.choice('0123456789') for _ in range(length))

# ======== BARCODE API TESTS ========

def test_barcode_health():
    print_test("Barcode API Health Check")
    return make_api_call("barcode-health", {}, method="GET")

def test_barcode_lookup_valid():
    print_test("Valid Barcode Lookup")
    
    # Use a barcode that is known to exist in your system
    # Replace with a valid barcode from your database
    data = {
        "barcode": "12345678901"  # Example barcode - replace with a valid one
    }
    
    return make_api_call("barcodeLookup", data)

def test_barcode_lookup_invalid_format():
    print_test("Invalid Barcode Format Lookup")
    
    data = {
        "barcode": "123"  # Too short, should fail validation
    }
    
    return make_api_call("barcodeLookup", data, expect_success=False)

def test_barcode_lookup_nonexistent():
    print_test("Non-existent Barcode Lookup")
    
    # Create a random barcode that's unlikely to exist
    # (This assumes your system doesn't have every possible barcode already)
    data = {
        "barcode": "99999999999"
    }
    
    return make_api_call("barcodeLookup", data, expect_success=False)

def test_add_barcode_valid():
    print_test("Add Valid Barcode")
    
    # Replace with a valid SKU that exists in your products table
    # And a barcode that doesn't exist yet
    data = {
        "sku": "TEST-SKU-001",  # Replace with valid SKU
        "barcode": generate_random_barcode()
    }
    
    print(f"Using SKU: {data['sku']} and Barcode: {data['barcode']}")
    return make_api_call("addNewBarcode", data)

def test_add_barcode_invalid_sku():
    print_test("Add Barcode with Invalid SKU Format")
    
    data = {
        "sku": "INVALID SKU WITH SPACES", # Invalid SKU format
        "barcode": generate_random_barcode()
    }
    
    return make_api_call("addNewBarcode", data, expect_success=False)

def test_add_barcode_nonexistent_sku():
    print_test("Add Barcode with Non-existent SKU")
    
    data = {
        "sku": "NONEXISTENT-SKU-999999",  # SKU that doesn't exist in products table
        "barcode": generate_random_barcode()
    }
    
    return make_api_call("addNewBarcode", data, expect_success=False)

def test_add_barcode_invalid_barcode():
    print_test("Add Invalid Barcode Format")
    
    # Replace with a valid SKU
    data = {
        "sku": "TEST-SKU-001",  # Replace with valid SKU
        "barcode": "123"  # Too short, invalid format
    }
    
    return make_api_call("addNewBarcode", data, expect_success=False)

def test_add_duplicate_barcode():
    print_test("Add Duplicate Barcode")
    
    # First add a barcode
    barcode = generate_random_barcode()
    first_data = {
        "sku": "TEST-SKU-001",  # Replace with valid SKU
        "barcode": barcode
    }
    
    success, _ = make_api_call("addNewBarcode", first_data)
    if not success:
        print(f"{Colors.RED}Failed to add first barcode for duplicate test{Colors.ENDC}")
        return False, {"error": "First barcode addition failed"}
    
    # Now try to add the same barcode again
    second_data = {
        "sku": "TEST-SKU-002",  # Different SKU
        "barcode": barcode  # Same barcode
    }
    
    return make_api_call("addNewBarcode", second_data, expect_success=False)

def run_all_tests():
    """Run all barcode API tests with a summary at the end"""
    print(f"{Colors.BLUE}================= STARTING BARCODE API TESTS ================={Colors.ENDC}")
    
    # First check if API is healthy
    health_success, _ = test_barcode_health()
    if not health_success:
        print(f"{Colors.RED}Barcode API health check failed. Cannot proceed with tests.{Colors.ENDC}")
        return
    
    test_results = {
        "barcode_lookup_valid": test_barcode_lookup_valid()[0],
        "barcode_lookup_invalid_format": test_barcode_lookup_invalid_format()[0],
        "barcode_lookup_nonexistent": test_barcode_lookup_nonexistent()[0],
        "add_barcode_valid": test_add_barcode_valid()[0],
        "add_barcode_invalid_sku": test_add_barcode_invalid_sku()[0],
        "add_barcode_nonexistent_sku": test_add_barcode_nonexistent_sku()[0],
        "add_barcode_invalid_barcode": test_add_barcode_invalid_barcode()[0],
        "add_duplicate_barcode": test_add_duplicate_barcode()[0]
    }
    
    # Calculate test results
    tests_passed = sum(1 for test_success in test_results.values() if test_success)
    total_tests = len(test_results)
    
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Total tests: {total_tests}")
    print(f"Tests passed: {tests_passed}")
    print(f"Success rate: {(tests_passed / total_tests) * 100:.1f}%")
    
    # Check if all tests passed as expected (failed where they should fail, passed where they should pass)
    all_passed = (
        test_results["barcode_lookup_valid"] and
        test_results["barcode_lookup_invalid_format"] and
        test_results["barcode_lookup_nonexistent"] and
        test_results["add_barcode_valid"] and
        test_results["add_barcode_invalid_sku"] and
        test_results["add_barcode_nonexistent_sku"] and
        test_results["add_barcode_invalid_barcode"] and
        test_results["add_duplicate_barcode"]
    )
    
    if all_passed:
        print(f"{Colors.GREEN}✓ All tests produced expected results{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests did not produce expected results{Colors.ENDC}")
        
    print(f"\n{Colors.BLUE}================= IMPORTANT NOTES ================={Colors.ENDC}")
    print(f"{Colors.YELLOW}Before running this test script on your system:{Colors.ENDC}")
    print(f"1. Replace 'TEST-SKU-001' and 'TEST-SKU-002' with actual SKUs from your products table")
    print(f"2. Replace '12345678901' with a barcode that actually exists in your system")
    print(f"3. Adjust the base URL if you're testing in a different environment")

if __name__ == "__main__":
    run_all_tests()