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

# Find an active replenishment order for testing
def find_test_order():
    print_test("Finding a Test Order")
    
    # Get a list of active orders
    success, response = make_api_call("ro_get_orders", method="GET")
    
    if not success or "orders" not in response or len(response["orders"]) == 0:
        print_result(False, "Could not find any active orders for testing")
        return None, None, None
    
    # Use the first order
    test_ro_id = response["orders"][0]["ro_id"]
    
    # Get the details of this order
    success, order_response = make_api_call("ro_retrieve_order", {"ro_id": test_ro_id})
    
    if not success or "order" not in order_response or "items" not in order_response["order"] or len(order_response["order"]["items"]) == 0:
        print_result(False, "Could not get order details for testing")
        return None, None, None
    
    # Use the first item
    test_item = order_response["order"]["items"][0]
    test_sku = test_item["sku"]
    test_rack_location = test_item.get("rack_location", "UNKNOWN")
    
    print_result(True, f"Found order {test_ro_id} with SKU {test_sku} at location {test_rack_location}")
    return test_ro_id, test_sku, test_rack_location

# Test normal item picking (should succeed)
def test_normal_item_picking():
    print_test("Normal Item Picking")
    
    ro_id, sku, rack_location = find_test_order()
    if not ro_id:
        return False, None
    
    data = {
        "ro_id": ro_id,
        "sku": sku,
        "rack_location": rack_location,
        "qty_picked": 5,
        "note": "Test picking with note"
    }
    
    return make_api_call("ro_item_picked", data)

# Test item picking with insufficient stock flag (should fail)
def test_insufficient_stock():
    print_test("Simulated Insufficient Stock")
    
    ro_id, sku, rack_location = find_test_order()
    if not ro_id:
        return False, None
    
    data = {
        "ro_id": ro_id,
        "sku": sku,
        "rack_location": rack_location,
        "qty_picked": 10,
        "test_insufficient_stock": True
    }
    
    return make_api_call("ro_item_picked", data, expect_success=False)

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING REPLENISHMENT ITEM PICKED WITH INVENTORY TEST ================={Colors.ENDC}")
    
    # Check API health
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
    
    # Test normal picking
    test_results["normal_picking"] = test_normal_item_picking()[0]
    
    # Test insufficient stock
    test_results["insufficient_stock"] = test_insufficient_stock()[0]
    
    # Print test summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"API health check: {'✓' if api_healthy else '✗'}")
    print(f"Normal item picking: {'✓' if test_results['normal_picking'] else '✗'}")
    print(f"Insufficient stock test: {'✓' if test_results['insufficient_stock'] else '✗'}")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print(f"{Colors.GREEN}✓ All tests passed! Inventory check testing is working correctly.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")