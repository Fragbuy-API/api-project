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

def check_proship_health():
    print_test("ProShip API Health Check")
    return make_api_call("proship-health", method="GET")

# Test updating parent orders
def test_update_parent_orders():
    print_test("Update Parent Orders")
    data = {
        "items": [
            {
                "orderId": "1288592238",
                "parentOrderId": "1288590000"
            },
            {
                "orderId": "1288592239",
                "parentOrderId": "1288590000"
            }
        ]
    }
    return make_api_call("update_parent_orders", data)

# Test with invalid order ID
def test_invalid_order_id():
    print_test("Update with Invalid Order ID")
    data = {
        "items": [
            {
                "orderId": "NONEXISTENT-ORDER",
                "parentOrderId": "1288590000"
            }
        ]
    }
    return make_api_call("update_parent_orders", data)

# Test with empty request
def test_empty_request():
    print_test("Empty Request")
    data = {
        "items": []
    }
    return make_api_call("update_parent_orders", data, expect_success=False)

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING PROSHIP PARENT ORDER API ================={Colors.ENDC}")
    
    # Check API health
    api_healthy, _ = check_api_health()
    if not api_healthy:
        print(f"{Colors.RED}Main API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    proship_api_healthy, _ = check_proship_health()
    if not proship_api_healthy:
        print(f"{Colors.RED}ProShip API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    # Run the tests
    results = {
        "update_parent_orders": test_update_parent_orders()[0],
        "invalid_order_id": test_invalid_order_id()[0],
        "empty_request": test_empty_request()[0]
    }
    
    # Print summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Tests passed: {sum(1 for success in results.values() if success)}/{len(results)}")
    
    if all(results.values()):
        print(f"{Colors.GREEN}✓ All tests passed! ProShip Parent Order API is working correctly.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")