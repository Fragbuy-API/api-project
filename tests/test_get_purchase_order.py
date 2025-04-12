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

# Test scenarios for get_purchase_order API
def test_get_existing_po():
    print_test("Get Existing Purchase Order")
    data = {
        "po_number": "SVPO2000300015"  # Actual PO from poLines.csv with 8 line items
    }
    success, response = make_api_call("get_purchase_order", data)
    if success:
        # Check that the response contains expected fields
        has_items = "items" in response
        has_total = "total_quantity" in response
        items_count = len(response.get("items", []))
        expected_count = 8  # This PO has 8 line items according to the data
        
        print_result(has_items, "Response contains items array")
        print_result(has_total, "Response contains total_quantity")
        print_result(items_count == expected_count, f"Contains expected number of items (found: {items_count}, expected: {expected_count})")
        
        return has_items and has_total and (items_count == expected_count), response
    return success, response

def test_get_nonexistent_po():
    print_test("Get Non-existent Purchase Order")
    data = {
        "po_number": "NONEXISTENT-PO-123456789"
    }
    return make_api_call("get_purchase_order", data, expect_success=False)

def test_missing_po_number():
    print_test("Missing PO Number")
    data = {}
    return make_api_call("get_purchase_order", data, expect_success=False)

def test_empty_po_number():
    print_test("Empty PO Number")
    data = {
        "po_number": ""
    }
    return make_api_call("get_purchase_order", data, expect_success=False)

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING GET PURCHASE ORDER API ================={Colors.ENDC}")
    
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
        "get_existing_po": test_get_existing_po()[0],
        "get_nonexistent_po": test_get_nonexistent_po()[0],
        "missing_po_number": test_missing_po_number()[0],
        "empty_po_number": test_empty_po_number()[0]
    }
    
    # Print summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Tests passed: {sum(1 for success in results.values() if success)}/{len(results)}")
    
    if all(results.values()):
        print(f"{Colors.GREEN}✓ All tests passed! Get Purchase Order API is working.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")