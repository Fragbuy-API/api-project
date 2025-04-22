import requests
import json
import random
import string

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

# Generate a random tote ID for testing
def generate_tote_id():
    """Generate a random tote ID that follows the required format"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"TOTE{suffix}"

# Generate a valid test order
def generate_test_order():
    """Generate a valid test putaway order"""
    return {
        "tote": generate_tote_id(),
        "items": [
            {
                "sku": "TEST-SKU-001",
                "name": "Test Product 1",
                "barcode": "12345678901",
                "quantity": 5
            },
            {
                "sku": "TEST-SKU-002",
                "name": "Test Product 2",
                "barcode": "98765432109",
                "quantity": 3
            }
        ]
    }

# Test normal putaway order creation (should succeed)
def test_normal_putaway():
    print_test("Normal Putaway Order Creation")
    
    test_order = generate_test_order()
    print(f"Using tote ID: {test_order['tote']}")
    
    return make_api_call("putawayOrder", test_order)

# Test putaway order with insufficient stock (should fail)
def test_insufficient_stock():
    print_test("Putaway Order with Insufficient Stock")
    
    test_order = generate_test_order()
    # Add the test flag
    test_order["test_insufficient_stock"] = True
    print(f"Using tote ID: {test_order['tote']} with insufficient stock flag")
    
    return make_api_call("putawayOrder", test_order, expect_success=False)

# Test duplicate tote (should fail)
def test_duplicate_tote():
    print_test("Duplicate Tote ID")
    
    # First create an order with a specific tote
    test_order = generate_test_order()
    tote_id = test_order["tote"]
    
    success, _ = make_api_call("putawayOrder", test_order)
    if not success:
        print_result(False, "Could not create initial test order")
        return False, None
    
    # Now try to create another order with the same tote
    second_order = generate_test_order()
    second_order["tote"] = tote_id
    print(f"Using duplicate tote ID: {tote_id}")
    
    return make_api_call("putawayOrder", second_order, expect_success=False)

# Test invalid tote format (should fail)
def test_invalid_tote_format():
    print_test("Invalid Tote Format")
    
    test_order = generate_test_order()
    test_order["tote"] = "INVALID-TOTE"  # Doesn't start with TOTE
    
    return make_api_call("putawayOrder", test_order, expect_success=False)

# Test invalid barcode (should fail)
def test_invalid_barcode():
    print_test("Invalid Barcode")
    
    test_order = generate_test_order()
    test_order["items"][0]["barcode"] = "123"  # Too short
    
    return make_api_call("putawayOrder", test_order, expect_success=False)

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING PUTAWAY WORKFLOW ================={Colors.ENDC}")
    
    # Check API health
    api_healthy, _ = check_api_health()
    if not api_healthy:
        print(f"{Colors.RED}API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    # Run the tests
    test_results = {}
    
    # Test normal putaway
    test_results["normal_putaway"] = test_normal_putaway()[0]
    
    # Test insufficient stock
    test_results["insufficient_stock"] = test_insufficient_stock()[0]
    
    # Test duplicate tote
    test_results["duplicate_tote"] = test_duplicate_tote()[0]
    
    # Test invalid tote format
    test_results["invalid_tote_format"] = test_invalid_tote_format()[0]
    
    # Test invalid barcode
    test_results["invalid_barcode"] = test_invalid_barcode()[0]
    
    # Print test summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"API health check: {'✓' if api_healthy else '✗'}")
    print(f"Normal putaway order: {'✓' if test_results['normal_putaway'] else '✗'}")
    print(f"Insufficient stock test: {'✓' if test_results['insufficient_stock'] else '✗'}")
    print(f"Duplicate tote rejection: {'✓' if test_results['duplicate_tote'] else '✗'}")
    print(f"Invalid tote format rejection: {'✓' if test_results['invalid_tote_format'] else '✗'}")
    print(f"Invalid barcode rejection: {'✓' if test_results['invalid_barcode'] else '✗'}")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print(f"{Colors.GREEN}✓ All tests passed! Putaway workflow is working correctly.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")