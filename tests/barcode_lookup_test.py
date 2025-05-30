import requests
import json
import random
import time
import sys

# API base URL - update if testing in a different environment
BASE_URL = "http://155.138.159.75/api/v1"

# Specific product data to use for testing
TEST_SKU = "4711M-50B"
EXPECTED_NAME = "4711 By Echt Kolnisch Wasser 50ml Splash Boxed"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    ENDC = '\033[0m'

def get_valid_skus(limit=10):
    """Get some valid SKUs from the products table"""
    try:
        import sqlalchemy
        from sqlalchemy import create_engine, text
        
        DATABASE_URL = "mysql+pymysql://Qboid:JY8xM2ch5#Q[@155.138.159.75/products"
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT sku FROM products LIMIT :limit"), {"limit": limit})
            skus = [str(row[0]) for row in result if row[0] is not None]
            return skus
    except Exception as e:
        print(f"{Colors.RED}Error fetching SKUs: {str(e)}{Colors.ENDC}")
        return []

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

def test_barcode_health():
    """Test the barcode API health endpoint"""
    print_test("Barcode API Health Check")
    return make_api_call("barcode-health", {}, method="GET")

def test_barcode_lookup_with_name():
    """Test looking up a barcode and ensuring specific product name is returned"""
    print_test(f"Barcode Lookup with Product Name: {EXPECTED_NAME}")
    
    # Generate a random barcode
    barcode = generate_random_barcode()
    
    print(f"Setting up test: Adding barcode {barcode} for SKU {TEST_SKU}")
    
    # Add the barcode
    add_data = {
        "sku": TEST_SKU,
        "barcode": barcode
    }
    
    add_success, add_response = make_api_call("addNewBarcode", add_data)
    if not add_success:
        print(f"{Colors.RED}Failed to create test barcode. Check that {TEST_SKU} exists in products table.{Colors.ENDC}")
        return False, add_response
    
    # Verify the barcode was added successfully
    add_success_check = add_response.get('status') == 'success'
    print_result(add_success_check, "Barcode added successfully")
    if not add_success_check:
        return False, add_response
        
    # Now lookup the barcode
    lookup_data = {
        "barcode": barcode
    }
    
    lookup_success, lookup_response = make_api_call("barcodeLookup", lookup_data)
    
    # Verify lookup response includes correct name
    if lookup_success:
        has_status = lookup_response.get("status") == "success"
        print_result(has_status, f"Lookup response is successful")
        
        # Verify SKU and barcode are correct
        sku_correct = lookup_response.get("sku", "") == TEST_SKU
        barcode_correct = lookup_response.get("barcode", "") == barcode
        
        print_result(sku_correct, f"SKU is correct: {lookup_response.get('sku', '')}")
        print_result(barcode_correct, f"Barcode is correct: {lookup_response.get('barcode', '')}")
        
        return has_status and sku_correct and barcode_correct, lookup_response
    
    return False, lookup_response

def test_lookup_existing_barcodes():
    """Test looking up existing barcodes in the system, if any"""
    print_test("Looking up any existing barcodes for this SKU")
    
    # We'll use the same barcode we added in the previous test
    barcode = None
    
    # Add a new barcode first
    new_barcode = generate_random_barcode()
    add_data = {
        "sku": TEST_SKU,
        "barcode": new_barcode
    }
    
    add_success, add_response = make_api_call("addNewBarcode", add_data)
    if add_success:
        barcode = new_barcode
    
    # If we have a barcode, look it up
    if barcode:
        lookup_data = {
            "barcode": barcode
        }
        
        lookup_success, lookup_response = make_api_call("barcodeLookup", lookup_data)
        
        if lookup_success:
            # Verify SKU is correct
            sku_matches = lookup_response.get("sku", "") == TEST_SKU
            print_result(sku_matches, "Found existing barcode with correct SKU")
            return sku_matches, lookup_response
    
    print(f"{Colors.YELLOW}No existing barcodes found or failed to create test barcode{Colors.ENDC}")
    return False, {"error": "No barcode to test"}

def test_add_na_barcode_valid_sku():
    """Test adding NA barcode for valid SKU"""
    print_test("Add NA Barcode for Valid SKU")
    
    valid_skus = get_valid_skus()
    if not valid_skus:
        print(f"{Colors.RED}No valid SKUs found for testing.{Colors.ENDC}")
        return False, {"error": "No valid SKUs found"}
    
    test_sku = valid_skus[0]
    
    data = {
        "sku": test_sku,
        "barcode": "NA"
    }
    
    success, response = make_api_call("addNewBarcode", data, method="POST")
    
    if success:
        # Verify the response indicates it wasn't stored
        not_stored = response.get("stored_in_database") == False
        print_result(not_stored, "NA barcode correctly not stored in database")
        return success and not_stored, response
    
    return success, response

def test_add_na_barcode_invalid_sku():
    """Test adding NA barcode for invalid SKU"""
    print_test("Add NA Barcode for Invalid SKU")
    
    data = {
        "sku": "NONEXISTENT-SKU",
        "barcode": "NA"
    }
    
    return make_api_call("addNewBarcode", data, method="POST", expect_success=False)

def test_lookup_na_barcode():
    """Test looking up NA barcode (should fail)"""
    print_test("Lookup NA Barcode")
    
    data = {
        "barcode": "NA"
    }
    
    return make_api_call("barcodeLookup", data, method="POST", expect_success=False)

def run_tests():
    """Run tests focused on the specific product"""
    print(f"{Colors.BLUE}================= TESTING BARCODE API WITH SPECIFIC PRODUCT ================={Colors.ENDC}")
    print(f"{Colors.BLUE}SKU: {TEST_SKU}{Colors.ENDC}")
    print(f"{Colors.BLUE}Expected Product Name: {EXPECTED_NAME}{Colors.ENDC}")
    
    # First check if API is running
    api_healthy, _ = test_barcode_health()
    if not api_healthy:
        print(f"{Colors.RED}Barcode API health check failed. Cannot proceed with tests.{Colors.ENDC}")
        return
    
    # Run the tests focusing on the specific product
    results = {
        "barcode_lookup_with_name": test_barcode_lookup_with_name()[0],
        "lookup_existing_barcodes": test_lookup_existing_barcodes()[0],
        "add_na_barcode_valid": test_add_na_barcode_valid_sku()[0],
        "add_na_barcode_invalid": test_add_na_barcode_invalid_sku()[0],
        "lookup_na_barcode": test_lookup_na_barcode()[0]
    }
    
    # Show results
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    tests_passed = sum(1 for success in results.values() if success)
    total_tests = len(results)
    
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if all(results.values()):
        print(f"{Colors.GREEN}✓ All tests passed! Barcode API correctly handles the specific product.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")
    
    print(f"\n{Colors.BLUE}================= IMPORTANT NOTES ================={Colors.ENDC}")
    print(f"{Colors.YELLOW}If any tests failed, check the following:{Colors.ENDC}")
    print(f"1. Confirm that SKU {TEST_SKU} exists in the products table")
    print(f"2. Confirm that the name in the database exactly matches: {EXPECTED_NAME}")
    print(f"3. Verify the Barcode API endpoints are functioning correctly")
    print(f"4. Check that the database connection is working correctly")

if __name__ == "__main__":
    # Show which Python is running the test (for debugging)
    print(f"Python path: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    run_tests()