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

# Find an order with "In Process" status
def find_in_process_order():
    print_test("Finding an In Process order")
    success, response = make_api_call("ro_get_orders", method="GET")
    
    if not success or "orders" not in response or len(response["orders"]) == 0:
        print_result(False, "Could not get orders list for testing")
        return None
    
    # Look for an "In Process" order
    in_process_orders = [order for order in response["orders"] if order["ro_status"] == "In Process"]
    
    if not in_process_orders:
        print_result(False, "No 'In Process' orders found for testing")
        return None
    
    order_id = in_process_orders[0]["ro_id"]
    print_result(True, f"Found In Process order: {order_id}")
    return order_id

# Test cancellation of a valid "In Process" order
def test_cancel_valid_order():
    print_test("Cancel Valid In Process Order")
    
    # First find an "In Process" order
    ro_id = find_in_process_order()
    if not ro_id:
        print_result(False, "Could not find a valid order for testing")
        return False, None
    
    # Try to cancel the order
    success, response = make_api_call("ro_pick_cancelled", {"ro_id": ro_id})
    
    if success:
        # Verify the order is now "Unassigned"
        verify_success, verify_response = make_api_call("ro_retrieve_order", {"ro_id": ro_id})
        
        if verify_success and "order" in verify_response and verify_response["order"]["ro_status"] == "Unassigned":
            print_result(True, f"Order {ro_id} successfully changed to Unassigned status")
            
            # Check if all qty_picked values were reset to 0
            all_reset = all(item["qty_picked"] == 0 for item in verify_response["order"]["items"])
            print_result(all_reset, "All qty_picked values reset to 0")
            
            return success and all_reset, response
        else:
            print_result(False, f"Order status was not updated to Unassigned")
            return False, response
    
    return success, response

# Test with invalid order ID
def test_cancel_invalid_order():
    print_test("Cancel Invalid Order ID")
    return make_api_call("ro_pick_cancelled", {"ro_id": "NONEXISTENT-RO"}, expect_success=False)

# Test with empty order ID
def test_cancel_empty_order_id():
    print_test("Cancel with Empty Order ID")
    return make_api_call("ro_pick_cancelled", {"ro_id": ""}, expect_success=False)

# Test with an Unassigned order (which should fail)
def test_cancel_unassigned_order():
    print_test("Cancel Unassigned Order")
    
    # Get a list of orders
    success, response = make_api_call("ro_get_orders", method="GET")
    
    if not success or "orders" not in response or len(response["orders"]) == 0:
        print_result(False, "Could not get orders list for testing")
        return False, None
    
    # Look for an "Unassigned" order
    unassigned_orders = [order for order in response["orders"] if order["ro_status"] == "Unassigned"]
    
    if not unassigned_orders:
        print_result(False, "No 'Unassigned' orders found for testing")
        return False, None
    
    order_id = unassigned_orders[0]["ro_id"]
    print(f"Found Unassigned order: {order_id}")
    
    # Try to cancel the unassigned order (should fail)
    return make_api_call("ro_pick_cancelled", {"ro_id": order_id}, expect_success=False)

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING REPLENISHMENT PICK CANCELLED API ================={Colors.ENDC}")
    
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
    
    # Test with invalid order ID
    test_results["invalid_order"] = test_cancel_invalid_order()[0]
    
    # Test with empty order ID
    test_results["empty_order_id"] = test_cancel_empty_order_id()[0]
    
    # Test with Unassigned order (should fail)
    test_results["unassigned_order"] = test_cancel_unassigned_order()[0]
    
    # Test with valid order last (as it changes the database)
    test_results["valid_order"] = test_cancel_valid_order()[0]
    
    # Print test summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"API health check: {'✓' if api_healthy else '✗'}")
    print(f"Cancel with invalid order ID: {'✓' if test_results['invalid_order'] else '✗'}")
    print(f"Cancel with empty order ID: {'✓' if test_results['empty_order_id'] else '✗'}")
    print(f"Cancel Unassigned order (should fail): {'✓' if test_results['unassigned_order'] else '✗'}")
    print(f"Cancel valid In Process order: {'✓' if test_results['valid_order'] else '✗'}")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print(f"{Colors.GREEN}✓ All tests passed! ro_pick_cancelled API is working correctly.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")