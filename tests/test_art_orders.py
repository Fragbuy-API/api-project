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

def check_art_orders_health():
    print_test("ART Orders API Health Check")
    return make_api_call("art-orders-health", {}, method="GET")

# Test scenarios for ART API
def test_add_operation():
    print_test("Add Operation")
    data = {
        "type": "Add",
        "sku": "4711M-50B",  # Using an SKU known to exist in the products table
        "quantity": 50,
        "to_location": "RACK-A1-01",
        "reason": "Restocking"
    }
    return make_api_call("art_order", data)

def test_remove_operation():
    print_test("Remove Operation")
    data = {
        "type": "Remove",
        "sku": "4711M-50B",
        "quantity": 20,
        "from_location": "RACK-A1-01",
        "reason": "Damaged goods"
    }
    return make_api_call("art_order", data)

def test_transfer_operation():
    print_test("Transfer Operation")
    data = {
        "type": "Transfer",
        "sku": "4711M-50B",
        "quantity": 30,
        "from_location": "RACK-A1-01",
        "to_location": "RACK-B2-02",
        "reason": "Reorganizing inventory"
    }
    return make_api_call("art_order", data)

def test_insufficient_stock():
    print_test("Insufficient Stock (Simulated)")
    data = {
        "type": "Remove",
        "sku": "4711M-50B",
        "quantity": 100,
        "from_location": "RACK-A1-01",
        "reason": "Testing insufficient stock",
        "sufficient_stock": False  # Simulate insufficient stock
    }
    return make_api_call("art_order", data, expect_success=False)

def test_invalid_sku():
    print_test("Invalid SKU")
    data = {
        "type": "Add",
        "sku": "NONEXISTENT-SKU",
        "quantity": 50,
        "to_location": "RACK-A1-01"
    }
    return make_api_call("art_order", data, expect_success=False)

def test_missing_from_location():
    print_test("Missing from_location in Remove Operation")
    data = {
        "type": "Remove",
        "sku": "4711M-50B",
        "quantity": 20
    }
    return make_api_call("art_order", data, expect_success=False)

def test_missing_to_location():
    print_test("Missing to_location in Add Operation")
    data = {
        "type": "Add",
        "sku": "4711M-50B",
        "quantity": 50
    }
    return make_api_call("art_order", data, expect_success=False)

def test_invalid_location_format():
    print_test("Invalid Location Format")
    data = {
        "type": "Add",
        "sku": "4711M-50B",
        "quantity": 50,
        "to_location": "INVALID-LOCATION-FORMAT"
    }
    return make_api_call("art_order", data, expect_success=False)

def test_same_locations_for_transfer():
    print_test("Same Locations for Transfer")
    data = {
        "type": "Transfer",
        "sku": "4711M-50B",
        "quantity": 30,
        "from_location": "RACK-A1-01",
        "to_location": "RACK-A1-01",
        "reason": "This should fail"
    }
    return make_api_call("art_order", data, expect_success=False)

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING ART ORDERS API ================={Colors.ENDC}")
    
    # Check API health
    api_healthy, _ = check_api_health()
    if not api_healthy:
        print(f"{Colors.RED}Main API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    art_api_healthy, _ = check_art_orders_health()
    if not art_api_healthy:
        print(f"{Colors.RED}ART Orders API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    # Run the tests
    results = {
        "add_operation": test_add_operation()[0],
        "remove_operation": test_remove_operation()[0],
        "transfer_operation": test_transfer_operation()[0],
        "insufficient_stock": test_insufficient_stock()[0],
        "invalid_sku": test_invalid_sku()[0],
        "missing_from_location": test_missing_from_location()[0],
        "missing_to_location": test_missing_to_location()[0],
        "invalid_location_format": test_invalid_location_format()[0],
        "same_locations_for_transfer": test_same_locations_for_transfer()[0]
    }
    
    # Print summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Tests passed: {sum(1 for success in results.values() if success)}/{len(results)}")
    
    if all(results.values()):
        print(f"{Colors.GREEN}✓ All tests passed! ART Orders API is working.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")