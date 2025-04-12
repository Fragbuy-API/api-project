import requests
import json

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

# Check if the API is accessible
def check_api_health():
    print_test("API Health Check")
    return make_api_call("health", {}, method="GET")

def check_purchase_orders_health():
    print_test("Purchase Orders API Health Check")
    return make_api_call("purchase-orders-health", {}, method="GET")

# Test scenarios for check_sku_against_po API
def test_sku_in_po():
    print_test("Check SKU In PO (Should return True)")
    data = {
        "po_number": "PO-TEST-001",
        "barcode": "1234567890123"  # This barcode should map to SKU 4711M-50B which is in PO-TEST-001
    }
    success, response = make_api_call("check_sku_against_po", data)
    if success:
        # Check that the result is true
        result_check = response.get("result") == True
        print_result(result_check, "API returned TRUE as expected")
        return result_check, response
    return success, response

def test_sku_not_in_po():
    print_test("Check SKU Not In PO (Should return False)")
    data = {
        "po_number": "PO-TEST-003",
        "barcode": "1234567890123"  # This barcode should map to SKU 4711M-50B which isn't in PO-TEST-003
    }
    success, response = make_api_call("check_sku_against_po", data)
    if success:
        # Check that the result is false
        result_check = response.get("result") == False
        print_result(result_check, "API returned FALSE as expected")
        return result_check, response
    return success, response

def test_barcode_not_found():
    print_test("Check SKU with Non-existent Barcode")
    data = {
        "po_number": "PO-TEST-001",
        "barcode": "9999999999999"  # This barcode should not exist
    }
    return make_api_call("check_sku_against_po", data, expect_success=False)

def test_missing_po_number():
    print_test("Missing PO Number")
    data = {
        "barcode": "1234567890123"
    }
    return make_api_call("check_sku_against_po", data, expect_success=False)

def test_missing_barcode():
    print_test("Missing Barcode")
    data = {
        "po_number": "PO-TEST-001"
    }
    return make_api_call("check_sku_against_po", data, expect_success=False)

def test_invalid_barcode_format():
    print_test("Invalid Barcode Format")
    data = {
        "po_number": "PO-TEST-001",
        "barcode": "123"  # Too short
    }
    return make_api_call("check_sku_against_po", data, expect_success=False)

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING CHECK SKU AGAINST PO API ================={Colors.ENDC}")
    
    # Check API health
    api_healthy, _ = check_api_health()
    if not api_healthy:
        print(f"{Colors.RED}Main API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    po_api_healthy, _ = check_purchase_orders_health()
    if not po_api_healthy:
        print(f"{Colors.RED}Purchase Orders API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    # Run the tests
    results = {
        "sku_in_po": test_sku_in_po()[0],
        "sku_not_in_po": test_sku_not_in_po()[0],
        "barcode_not_found": test_barcode_not_found()[0],
        "missing_po_number": test_missing_po_number()[0],
        "missing_barcode": test_missing_barcode()[0],
        "invalid_barcode_format": test_invalid_barcode_format()[0]
    }
    
    # Print summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Tests passed: {sum(1 for success in results.values() if success)}/{len(results)}")
    
    if all(results.values()):
        print(f"{Colors.GREEN}✓ All tests passed! Check SKU Against PO API is working.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")