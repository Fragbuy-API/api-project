import sys
print(f"Python path: {sys.executable}")
print(f"Path: {sys.path}")

import requests
import json
import time
import random
import sqlalchemy
from sqlalchemy import create_engine, text



# API base URL for the main API
BASE_URL = "http://localhost:8000/api/v1"

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
    print_test("Lookup Existing Barcode")
    
    # Get a valid SKU from the products table
    valid_skus = get_valid_skus()
    if not valid_skus:
        print(f"{Colors.RED}No valid SKUs found in the products table. Cannot proceed.{Colors.ENDC}")
        return False, {"error": "No valid SKUs found"}
    
    test_sku = valid_skus[0]
    test_barcode = get_random_barcode()
    
    print(f"Using SKU: {test_sku} and Barcode: {test_barcode}")
    
    # Add the barcode
    add_data = {
        "sku": test_sku,
        "barcode": test_barcode
    }
    
    success, _ = make_api_call("addNewBarcode", add_data, method="POST")
    
    if not success:
        print(f"{Colors.RED}Failed to create test barcode for lookup test{Colors.ENDC}")
    
    # Now look it up
    lookup_data = {
        "barcode": test_barcode
    }
    
    return make_api_call("barcodeLookup", lookup_data, method="POST")

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

# ======== ADD BARCODE TESTS ========

def test_add_new_barcode_for_new_sku():
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

def run_tests():
    """Run a subset of tests to verify the API is working"""
    print(f"{Colors.BLUE}================= TESTING MAIN API BARCODE ENDPOINTS ================={Colors.ENDC}")
    
    # Check if API is running
    api_healthy, _ = check_api_health()
    if not api_healthy:
        print(f"{Colors.RED}Main API health check failed. Cannot proceed with tests.{Colors.ENDC}")
        return
    
    # Run a few basic tests
    results = {
        "barcode_lookup": test_barcode_lookup_existing()[0],
        "add_barcode": test_add_new_barcode_for_new_sku()[0]
    }
    
    # Show results
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Tests passed: {sum(1 for success in results.values() if success)}/{len(results)}")
    
    if all(results.values()):
        print(f"{Colors.GREEN}✓ All tests passed! Main API barcode endpoints are working.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")

if __name__ == "__main__":
    run_tests()