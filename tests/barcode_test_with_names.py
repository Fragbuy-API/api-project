import requests
import json
import time
import random
import sqlalchemy
from sqlalchemy import create_engine, text

# API base URL for the main API
BASE_URL = "http://155.138.159.75/api/v1"

# Database connection for getting valid SKUs
DATABASE_URL = "mysql+pymysql://Qboid:JY8xM2ch5#Q[@155.138.159.75/products"

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

def make_api_call(endpoint, data=None, method="GET", expect_success=True):
    """Make an API call and verify the result"""
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=data)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        status_code = response.status_code
        
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            response_json = {"error": "Invalid JSON response", "raw": response.text[:500]}
        
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

def get_valid_skus(limit=10):
    """Get some valid SKUs from the products table"""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT sku FROM products LIMIT :limit"), {"limit": limit})
            skus = [str(row[0]) for row in result if row[0] is not None]  # Convert to string
            return skus
    except Exception as e:
        print(f"{Colors.RED}Error fetching SKUs: {str(e)}{Colors.ENDC}")
        return []

def get_sku_with_description(sku):
    """Get the description for a specific SKU"""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT description FROM products WHERE sku = :sku"), {"sku": sku})
            row = result.fetchone()
            return str(row[0]) if row and row[0] else ""
    except Exception as e:
        print(f"{Colors.RED}Error fetching description for SKU {sku}: {str(e)}{Colors.ENDC}")
        return ""

def get_random_barcode():
    """Generate a random valid barcode (8-14 digits)"""
    barcode_length = random.randint(8, 14)
    return ''.join(random.choice('0123456789') for _ in range(barcode_length))

# First check if the API is accessible
def check_api_health():
    print_test("API Health Check")
    return make_api_call("health")

# ======== BARCODE LOOKUP TESTS ========

def test_barcode_lookup_existing():
    print_test("Lookup Existing Barcode (with Name Field)")
    
    # Get a valid SKU from the products table
    valid_skus = get_valid_skus()
    if not valid_skus:
        print(f"{Colors.RED}No valid SKUs found in the products table. Cannot proceed.{Colors.ENDC}")
        return False, {"error": "No valid SKUs found"}
    
    test_sku = valid_skus[0]
    test_barcode = get_random_barcode()
    expected_name = get_sku_with_description(test_sku)
    
    print(f"Using SKU: {test_sku}, Barcode: {test_barcode}, Expected Name: {expected_name}")
    
    # Add the barcode first
    add_data = {
        "sku": test_sku,
        "barcode": test_barcode
    }
    
    success, _ = make_api_call("addNewBarcode", add_data, method="POST")
    
    if not success:
        print(f"{Colors.RED}Failed to create test barcode for lookup test{Colors.ENDC}")
        return False, {"error": "Failed to create test barcode"}
    
    # Now look it up
    lookup_data = {
        "barcode": test_barcode
    }
    
    success, response = make_api_call("barcodeLookup", lookup_data, method="POST")
    
    if success:
        # Validate the response structure and name field
        required_fields = ["status", "barcode", "sku", "name", "alternate", "timestamp"]
        fields_present = all(field in response for field in required_fields)
        print_result(fields_present, f"All required fields present: {required_fields}")
        
        # Validate the name field specifically
        name_valid = "name" in response and isinstance(response["name"], str)
        print_result(name_valid, f"Name field present and is string: '{response.get('name', 'NOT_FOUND')}'")
        
        # Check if name matches expected (if we have an expected name)
        if expected_name:
            name_matches = response.get("name") == expected_name
            print_result(name_matches, f"Name matches expected: '{expected_name}'")
            success = success and name_matches
        
        # Validate other core fields
        sku_matches = response.get("sku") == test_sku
        barcode_matches = response.get("barcode") == test_barcode
        print_result(sku_matches, f"SKU matches: {test_sku}")
        print_result(barcode_matches, f"Barcode matches: {test_barcode}")
        
        return success and fields_present and name_valid and sku_matches and barcode_matches, response
    
    return success, response

def test_barcode_lookup_nonexistent():
    print_test("Lookup Non-Existent Barcode")
    
    # This should be a valid format but non-existent barcode
    # Make sure it's not one we generated earlier
    nonexistent_barcode = ''.join(random.choice('0123456789') for _ in range(10))
    
    data = {
        "barcode": nonexistent_barcode
    }
    
    # We expect a 404 Not Found
    return make_api_call("barcodeLookup", data, method="POST", expect_success=False)

def test_barcode_lookup_invalid_format():
    print_test("Lookup Barcode with Invalid Format")
    
    data = {
        "barcode": "123"  # Too short, should fail validation
    }
    
    # We expect a 422 Validation Error
    return make_api_call("barcodeLookup", data, method="POST", expect_success=False)

# ======== ADD BARCODE TESTS ========

def test_add_new_barcode_for_existing_sku():
    print_test("Add New Barcode for Existing SKU")
    
    # Get a valid SKU from the products table
    valid_skus = get_valid_skus()
    if not valid_skus:
        print(f"{Colors.RED}No valid SKUs found in the products table. Cannot proceed.{Colors.ENDC}")
        return False, {"error": "No valid SKUs found"}
    
    test_sku = valid_skus[0]
    test_barcode = get_random_barcode()
    
    print(f"Using SKU: {test_sku} and Barcode: {test_barcode}")
    
    data = {
        "sku": test_sku,
        "barcode": test_barcode
    }
    
    return make_api_call("addNewBarcode", data, method="POST")

def test_add_barcode_duplicate():
    print_test("Add Duplicate Barcode (Should Fail)")
    
    # Get a valid SKU from the products table
    valid_skus = get_valid_skus()
    if not valid_skus:
        print(f"{Colors.RED}No valid SKUs found in the products table. Cannot proceed.{Colors.ENDC}")
        return False, {"error": "No valid SKUs found"}
    
    test_sku = valid_skus[0]
    test_barcode = get_random_barcode()
    
    data = {
        "sku": test_sku,
        "barcode": test_barcode
    }
    
    # Add the barcode first
    success, _ = make_api_call("addNewBarcode", data, method="POST")
    
    if not success:
        print(f"{Colors.RED}Failed to create initial barcode for duplicate test{Colors.ENDC}")
        return False, {"error": "Failed to create initial barcode"}
    
    # Try to add the same barcode again (should fail)
    return make_api_call("addNewBarcode", data, method="POST", expect_success=False)

def test_add_barcode_invalid_sku():
    print_test("Add Barcode for Invalid SKU (Should Fail)")
    
    data = {
        "sku": "NONEXISTENT-SKU-12345",
        "barcode": get_random_barcode()
    }
    
    # Should fail because SKU doesn't exist in products table
    return make_api_call("addNewBarcode", data, method="POST", expect_success=False)

def run_tests():
    """Run comprehensive barcode API tests"""
    print(f"{Colors.BLUE}================= TESTING BARCODE API WITH NAME FIELD ================={Colors.ENDC}")
    
    # Check if API is running
    api_healthy, _ = check_api_health()
    if not api_healthy:
        print(f"{Colors.RED}Main API health check failed. Cannot proceed with tests.{Colors.ENDC}")
        return
    
    # Run all tests
    results = {
        "barcode_lookup_existing": test_barcode_lookup_existing()[0],
        "barcode_lookup_nonexistent": test_barcode_lookup_nonexistent()[0],
        "barcode_lookup_invalid_format": test_barcode_lookup_invalid_format()[0],
        "add_barcode_existing_sku": test_add_new_barcode_for_existing_sku()[0],
        "add_barcode_duplicate": test_add_barcode_duplicate()[0],
        "add_barcode_invalid_sku": test_add_barcode_invalid_sku()[0]
    }
    
    # Show results
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Tests passed: {sum(1 for success in results.values() if success)}/{len(results)}")
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        color = Colors.GREEN if passed else Colors.RED
        print(f"{color}{status}: {test_name.replace('_', ' ').title()}{Colors.ENDC}")
    
    if all(results.values()):
        print(f"\n{Colors.GREEN}✓ All tests passed! Barcode API with name field is working correctly.{Colors.ENDC}")
    else:
        print(f"\n{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")

if __name__ == "__main__":
    run_tests()