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

# Test scenarios for update_po_status API
def test_update_to_complete():
    print_test("Update PO Status to Complete")
    data = {
        "po_number": "PO-TEST-001",
        "status": "Complete"
    }
    return make_api_call("update_po_status", data)

def test_update_to_incomplete():
    print_test("Update PO Status to Incomplete")
    data = {
        "po_number": "PO-TEST-002",
        "status": "Incomplete"
    }
    return make_api_call("update_po_status", data)

def test_nonexistent_po():
    print_test("Update Non-existent PO")
    data = {
        "po_number": "NONEXISTENT-PO",
        "status": "Complete"
    }
    return make_api_call("update_po_status", data, expect_success=False)

def test_missing_status():
    print_test("Missing Status")
    data = {
        "po_number": "PO-TEST-001"
    }
    return make_api_call("update_po_status", data, expect_success=False)

def test_missing_po_number():
    print_test("Missing PO Number")
    data = {
        "status": "Complete"
    }
    return make_api_call("update_po_status", data, expect_success=False)

def test_invalid_status():
    print_test("Invalid Status")
    data = {
        "po_number": "PO-TEST-001",
        "status": "Invalid"
    }
    return make_api_call("update_po_status", data, expect_success=False)

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING UPDATE PO STATUS API ================={Colors.ENDC}")
    
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
        "update_to_complete": test_update_to_complete()[0],
        "update_to_incomplete": test_update_to_incomplete()[0],
        "nonexistent_po": test_nonexistent_po()[0],
        "missing_status": test_missing_status()[0],
        "missing_po_number": test_missing_po_number()[0],
        "invalid_status": test_invalid_status()[0]
    }
    
    # Print summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Tests passed: {sum(1 for success in results.values() if success)}/{len(results)}")
    
    if all(results.values()):
        print(f"{Colors.GREEN}✓ All tests passed! Update PO Status API is working.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")