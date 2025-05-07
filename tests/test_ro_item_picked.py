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

# Test ro_item_picked API with valid data
def test_item_picked_valid():
    print_test("Update Item Picked - Valid Data")
    
    # First get a valid RO and item
    success, response = make_api_call("ro_get_orders", method="GET")
    
    if not success or "orders" not in response or len(response["orders"]) == 0:
        print_result(False, "Could not get a valid order ID for testing")
        return False, None
    
    # Use the first order's ID
    test_ro_id = response["orders"][0]["ro_id"]
    
    # Now get the items in this order
    success, order_response = make_api_call("ro_retrieve_order", {"ro_id": test_ro_id})
    
    if not success or "order" not in order_response or "items" not in order_response["order"] or len(order_response["order"]["items"]) == 0:
        print_result(False, "Could not get valid items for testing")
        return False, None
    
    # Use the first item's SKU
    test_sku = order_response["order"]["items"][0]["sku"]
    test_qty = order_response["order"]["items"][0]["qty"]
    
    # Update with a partial quantity (not marking the whole order as complete)
    test_qty_picked = max(1, test_qty // 2)  # Use half the requested quantity
    
    print(f"Using RO={test_ro_id}, SKU={test_sku}, Qty_Picked={test_qty_picked}")
    
    # Test partial item picking
    return make_api_call("ro_item_picked", {
        "ro_id": test_ro_id,
        "sku": test_sku,
        "qty_picked": test_qty_picked,
        "rack_location": "123-456-789"
    })

# Test ro_item_picked API with invalid order ID
def test_item_picked_invalid_ro():
    print_test("Update Item Picked - Invalid RO ID")
    return make_api_call("ro_item_picked", {
        "ro_id": "NONEXISTENT-RO",
        "sku": "212SM-50B",
        "qty_picked": 5,
        "rack_location": "123-456-789"
    }, expect_success=False)

# Test ro_item_picked API with invalid SKU
def test_item_picked_invalid_sku():
    print_test("Update Item Picked - Invalid SKU")
    
    # First get a valid order ID
    success, response = make_api_call("ro_get_orders", method="GET")
    
    if not success or "orders" not in response or len(response["orders"]) == 0:
        print_result(False, "Could not get a valid order ID for testing")
        return False, None
    
    test_ro_id = response["orders"][0]["ro_id"]
    
    return make_api_call("ro_item_picked", {
        "ro_id": test_ro_id,
        "sku": "NONEXISTENT-SKU",
        "qty_picked": 5,
        "rack_location": "123-456-789"
    }, expect_success=False)

# Test ro_item_picked API with negative quantity
def test_item_picked_negative_qty():
    print_test("Update Item Picked - Negative Quantity")
    
    # First get a valid RO and item
    success, response = make_api_call("ro_get_orders", method="GET")
    
    if not success or "orders" not in response or len(response["orders"]) == 0:
        print_result(False, "Could not get a valid order ID for testing")
        return False, None
    
    test_ro_id = response["orders"][0]["ro_id"]
    
    # Now get the items in this order
    success, order_response = make_api_call("ro_retrieve_order", {"ro_id": test_ro_id})
    
    if not success or "order" not in order_response or "items" not in order_response["order"] or len(order_response["order"]["items"]) == 0:
        print_result(False, "Could not get valid items for testing")
        return False, None
    
    test_sku = order_response["order"]["items"][0]["sku"]
    
    return make_api_call("ro_item_picked", {
        "ro_id": test_ro_id,
        "sku": test_sku,
        "qty_picked": -5,
        "rack_location": "123-456-789"
    }, expect_success=False)

# Test marking all items in an order as picked
def test_complete_order():
    print_test("Complete Entire Order")
    
    # Find an order with status not Completed
    success, response = make_api_call("ro_get_orders", method="GET")
    
    if not success or "orders" not in response or len(response["orders"]) == 0:
        print_result(False, "Could not get a valid order ID for testing")
        return False, None
    
    # Use the last order in the list (least likely to be used in other tests)
    test_ro_id = response["orders"][-1]["ro_id"]
    
    # Get all items in this order
    success, order_response = make_api_call("ro_retrieve_order", {"ro_id": test_ro_id})
    
    if not success or "order" not in order_response or "items" not in order_response["order"] or len(order_response["order"]["items"]) == 0:
        print_result(False, "Could not get valid items for testing")
        return False, None
    
    items = order_response["order"]["items"]
    
    # Mark each item as fully picked
    results = []
    for item in items:
        success, pick_response = make_api_call("ro_item_picked", {
            "ro_id": test_ro_id,
            "sku": item["sku"],
            "qty_picked": item["qty"],  # Set to full qty requested
            "rack_location": "123-456-789"
        })
        results.append(success)
        
        # If the last item was updated, check the message
        if item == items[-1]:
            if success and "message" in pick_response:
                if pick_response["message"] == "Data Added; RO Complete":
                    print_result(True, "Order correctly marked as Complete")
                else:
                    print_result(False, f"Expected 'Data Added; RO Complete' but got '{pick_response['message']}'")
    
    return all(results), None

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING REPLENISHMENT ITEM PICKED API ================={Colors.ENDC}")
    
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
    
    # Test with valid data
    test_results["valid_data"] = test_item_picked_valid()[0]
    
    # Test with invalid RO ID
    test_results["invalid_ro"] = test_item_picked_invalid_ro()[0]
    
    # Test with invalid SKU
    test_results["invalid_sku"] = test_item_picked_invalid_sku()[0]
    
    # Test with negative quantity
    test_results["negative_qty"] = test_item_picked_negative_qty()[0]
    
    # Test complete order
    # Note: This will modify data and mark an order as complete
    test_results["complete_order"] = test_complete_order()[0]
    
    # Print test summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"API health check: {'✓' if api_healthy else '✗'}")
    print(f"Update with valid data: {'✓' if test_results['valid_data'] else '✗'}")
    print(f"Update with invalid RO ID: {'✓' if test_results['invalid_ro'] else '✗'}")
    print(f"Update with invalid SKU: {'✓' if test_results['invalid_sku'] else '✗'}")
    print(f"Update with negative quantity: {'✓' if test_results['negative_qty'] else '✗'}")
    print(f"Complete entire order: {'✓' if test_results['complete_order'] else '✗'}")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print(f"{Colors.GREEN}✓ All tests passed! ro_item_picked API is working correctly.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")