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

# Prepare a test order: find an In Process order, pick all items
def prepare_test_order():
    print_test("Preparing an order for completion")
    
    # Find an In Process order
    success, response = make_api_call("ro_get_orders", method="GET")
    
    if not success or "orders" not in response or len(response["orders"]) == 0:
        print_result(False, "Could not get orders list for testing")
        return None
    
    # Try to find an In Process order
    in_process_orders = [order for order in response["orders"] if order["ro_status"] == "In Process"]
    
    # If no In Process orders, try to use an Unassigned order
    if not in_process_orders:
        unassigned_orders = [order for order in response["orders"] if order["ro_status"] == "Unassigned"]
        
        if not unassigned_orders:
            print_result(False, "No suitable orders found for testing")
            return None
        
        test_ro_id = unassigned_orders[0]["ro_id"]
        print(f"Using Unassigned order: {test_ro_id}")
    else:
        test_ro_id = in_process_orders[0]["ro_id"]
        print(f"Using In Process order: {test_ro_id}")
    
    # Get items for this order
    success, order_response = make_api_call("ro_retrieve_order", {"ro_id": test_ro_id})
    
    if not success or "order" not in order_response or "items" not in order_response["order"]:
        print_result(False, "Could not get items for the order")
        return None
    
    # Check if any items need to be picked
    items = order_response["order"]["items"]
    unpicked_items = [item for item in items if item["qty_picked"] == 0]
    
    if unpicked_items:
        print(f"Picking {len(unpicked_items)} items for order {test_ro_id}")
        
        # Pick all unpicked items
        for item in unpicked_items:
            make_api_call("ro_item_picked", {
                "ro_id": test_ro_id,
                "sku": item["sku"],
                "qty_picked": item["qty"]  # Pick the full quantity
            })
    else:
        print("All items already picked")
    
    print_result(True, f"Order {test_ro_id} prepared for completion testing")
    return test_ro_id

# Test ro_complete with a fully picked order
def test_complete_valid_order():
    print_test("Complete Valid Order (all items picked)")
    
    # First prepare a test order
    ro_id = prepare_test_order()
    if not ro_id:
        print_result(False, "Could not prepare a test order")
        return False, None
    
    # Mark the order as complete
    return make_api_call("ro_complete", {"ro_id": ro_id})

# Test ro_complete with an invalid order ID
def test_complete_invalid_order():
    print_test("Complete Invalid Order ID")
    return make_api_call("ro_complete", {"ro_id": "NONEXISTENT-RO"}, expect_success=False)

# Test ro_complete with an empty order ID
def test_complete_empty_order_id():
    print_test("Complete with Empty Order ID")
    return make_api_call("ro_complete", {"ro_id": ""}, expect_success=False)

# Test ro_complete with an already completed order
def test_complete_already_completed():
    print_test("Complete Already Completed Order")
    
    # Find a completed order or create one
    success, response = make_api_call("ro_get_orders", method="GET")
    
    if not success:
        print_result(False, "Could not get orders list")
        return False, None
    
    # First complete a test order
    already_complete_id = None
    
    # Prepare and complete an order
    ro_id = prepare_test_order()
    if ro_id:
        success, _ = make_api_call("ro_complete", {"ro_id": ro_id})
        if success:
            already_complete_id = ro_id
    
    if not already_complete_id:
        print_result(False, "Could not prepare a completed order for testing")
        return False, None
    
    # Try to complete it again
    print(f"Testing with already completed order: {already_complete_id}")
    return make_api_call("ro_complete", {"ro_id": already_complete_id})

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING REPLENISHMENT COMPLETE API ================={Colors.ENDC}")
    
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
    test_results["invalid_order"] = test_complete_invalid_order()[0]
    
    # Test with empty order ID
    test_results["empty_order_id"] = test_complete_empty_order_id()[0]
    
    # Test with valid order
    test_results["valid_order"] = test_complete_valid_order()[0]
    
    # Test with already completed order
    test_results["already_completed"] = test_complete_already_completed()[0]
    
    # Print test summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"API health check: {'✓' if api_healthy else '✗'}")
    print(f"Complete with invalid order ID: {'✓' if test_results['invalid_order'] else '✗'}")
    print(f"Complete with empty order ID: {'✓' if test_results['empty_order_id'] else '✗'}")
    print(f"Complete valid order: {'✓' if test_results['valid_order'] else '✗'}")
    print(f"Complete already completed order: {'✓' if test_results['already_completed'] else '✗'}")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print(f"{Colors.GREEN}✓ All tests passed! ro_complete API is working correctly.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")