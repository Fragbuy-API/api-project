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

def make_api_call(endpoint, data=None, method="POST", expect_success=True):
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
    return make_api_call("health", method="GET")

def check_replenishment_health():
    print_test("Replenishment API Health Check")
    return make_api_call("replenishment-health", method="GET")

# Test ro_retrieve_order API with valid order ID
def test_retrieve_valid_order():
    print_test("Retrieve Valid Replenishment Order")
    
    # First get a list of active orders to use a valid ID
    success, response = make_api_call("ro_get_orders", method="GET")
    
    if not success or "orders" not in response or len(response["orders"]) == 0:
        print_result(False, "Could not get a valid order ID for testing")
        return False, None
    
    # Use the first order from the list
    test_ro_id = response["orders"][0]["ro_id"]
    print(f"Using replenishment order ID: {test_ro_id}")
    
    # Print exactly what we're sending
    print(f"Making POST request to {BASE_URL}/ro_retrieve_order with data: {{'ro_id': '{test_ro_id}'}}")
    
    # Now test retrieving this order
    return make_api_call("ro_retrieve_order", {"ro_id": test_ro_id})

# Test ro_retrieve_order API with invalid order ID
def test_retrieve_invalid_order():
    print_test("Retrieve Invalid Replenishment Order")
    return make_api_call("ro_retrieve_order", {"ro_id": "NONEXISTENT-RO"}, expect_success=False)

# Test ro_retrieve_order API with empty order ID
def test_retrieve_empty_order_id():
    print_test("Retrieve with Empty Order ID")
    return make_api_call("ro_retrieve_order", {"ro_id": ""}, expect_success=False)

# Verify response data from ro_retrieve_order
def verify_order_response(response_data):
    print_test("Verifying Order Response")
    
    # Check if we have the expected keys in the response
    expected_keys = ["status", "message", "order", "timestamp"]
    has_all_keys = all(key in response_data for key in expected_keys)
    print_result(has_all_keys, "Response contains all expected keys")
    
    if not has_all_keys:
        return False
    
    # Check if order has the expected structure
    order = response_data.get("order", {})
    order_keys = ["ro_id", "ro_date_created", "ro_status", "destination", "items", "item_count"]
    has_order_keys = all(key in order for key in order_keys)
    print_result(has_order_keys, "Order contains all expected keys")
    
    # Check if items exist and match the item_count
    items = order.get("items", [])
    count_matches = len(items) == order.get("item_count", 0)
    print_result(count_matches, f"Item count ({order.get('item_count', 0)}) matches number of items ({len(items)})")
    
    # Check if each item has the expected fields
    if items:
        item_keys = ["id", "sku", "description", "qty", "qty_picked", "created_at", "rack_location"]
        all_items_valid = True
        
        for i, item in enumerate(items):
            item_valid = all(key in item for key in item_keys)
            if not item_valid:
                missing_keys = [key for key in item_keys if key not in item]
                all_items_valid = False
                print_result(False, f"Item {i+1} is missing some required fields: {missing_keys}")
        
        print_result(all_items_valid, "All items have the required fields")
    else:
        print_result(True, "No items to verify")
        all_items_valid = True
    
    return has_all_keys and has_order_keys and count_matches and all_items_valid

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING REPLENISHMENT ORDER RETRIEVE API ================={Colors.ENDC}")
    
    # Check main API health
    api_healthy, _ = check_api_health()
    if not api_healthy:
        print(f"{Colors.RED}Main API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    # Check replenishment API health
    replen_api_healthy, _ = check_replenishment_health()
    if not replen_api_healthy:
        print(f"{Colors.RED}Replenishment API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    # Run the tests
    test_results = {}
    
    # Test with valid order ID
    success, response_data = test_retrieve_valid_order()
    test_results["valid_order"] = success
    
    # If the API call was successful, verify the response content
    if success:
        test_results["valid_order_response"] = verify_order_response(response_data)
    else:
        test_results["valid_order_response"] = False
    
    # Test with invalid order ID
    test_results["invalid_order"] = test_retrieve_invalid_order()[0]
    
    # Test with empty order ID
    test_results["empty_order_id"] = test_retrieve_empty_order_id()[0]
    
    # Print test summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"API health check: {'✓' if api_healthy else '✗'}")
    print(f"Retrieve valid order: {'✓' if test_results['valid_order'] else '✗'}")
    print(f"Valid order response structure: {'✓' if test_results['valid_order_response'] else '✗'}")
    print(f"Retrieve invalid order (should fail): {'✓' if test_results['invalid_order'] else '✗'}")
    print(f"Retrieve with empty order ID (should fail): {'✓' if test_results['empty_order_id'] else '✗'}")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print(f"{Colors.GREEN}✓ All tests passed! ro_retrieve_order API is working correctly.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")