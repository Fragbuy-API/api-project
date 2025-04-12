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

# Check if the API is accessible
def check_api_health():
    print_test("API Health Check")
    return make_api_call("health", method="GET")

def check_replenishment_health():
    print_test("Replenishment API Health Check")
    return make_api_call("replenishment-health", method="GET")

# Test ro_get_orders API
def test_ro_get_orders():
    print_test("Get Active Replenishment Orders")
    return make_api_call("ro_get_orders", method="GET")

# Verify response data from ro_get_orders
def verify_ro_get_orders_response(response_data):
    print_test("Verifying Replenishment Orders Response")
    
    # Check if we have the expected keys in the response
    expected_keys = ["status", "message", "orders", "count", "timestamp"]
    has_all_keys = all(key in response_data for key in expected_keys)
    print_result(has_all_keys, "Response contains all expected keys")
    
    # Check if there are orders in the response
    has_orders = "orders" in response_data and isinstance(response_data["orders"], list)
    print_result(has_orders, "Response contains orders list")
    
    if not has_orders or len(response_data["orders"]) == 0:
        print_result(True, "No orders to verify")
        return True
    
    # Check if the count matches the number of orders
    count_matches = response_data["count"] == len(response_data["orders"])
    print_result(count_matches, f"Count ({response_data['count']}) matches number of orders ({len(response_data['orders'])})")
    
    # Check if each order has the expected fields
    order_fields = ["ro_id", "ro_date_created", "ro_status", "destination", "skus_in_order"]
    all_orders_valid = True
    
    for i, order in enumerate(response_data["orders"]):
        order_valid = all(field in order for field in order_fields)
        if not order_valid:
            all_orders_valid = False
            print_result(False, f"Order {i+1} is missing some required fields")
    
    print_result(all_orders_valid, "All orders have the required fields")
    
    # Check that all returned orders are not "Completed"
    no_completed_orders = True
    for i, order in enumerate(response_data["orders"]):
        if order.get("ro_status") == "Completed":
            no_completed_orders = False
            print_result(False, f"Order {order.get('ro_id')} has 'Completed' status but should not be returned")
    
    print_result(no_completed_orders, "No 'Completed' orders were returned as expected")
    
    return has_all_keys and has_orders and count_matches and all_orders_valid and no_completed_orders


if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING REPLENISHMENT ORDER GET API ================={Colors.ENDC}")
    
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
    
    # Run the test for ro_get_orders
    success, response_data = test_ro_get_orders()
    
    # If the API call was successful, verify the response content
    if success:
        response_valid = verify_ro_get_orders_response(response_data)
    else:
        response_valid = False
    
    # Print test summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"API call successful: {'✓' if success else '✗'}")
    print(f"Response data valid: {'✓' if success and response_valid else '✗'}")
    
    if success and response_valid:
        print(f"{Colors.GREEN}✓ All tests passed! ro_get_orders API is working correctly.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")