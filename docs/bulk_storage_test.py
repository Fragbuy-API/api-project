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

# Generate a random rack location for testing
def generate_rack_location():
    """Generate a random rack location that follows the required format"""
    section = random.choice(string.ascii_uppercase)
    aisle = random.randint(1, 9)
    position = random.randint(1, 99)
    return f"RACK-{section}{aisle}-{position:02d}"

# Generate a valid test order
def generate_test_order():
    """Generate a valid test bulk storage order"""
    return {
        "location": generate_rack_location(),
        "items": [
            {
                "sku": "BULK-SKU-001",
                "name": "Bulk Product 1",
                "barcode": "12345678901",
                "quantity": 50
            },
            {
                "sku": "BULK-SKU-002",
                "name": "Bulk Product 2",
                "barcode": "98765432109",
                "quantity": 25
            }
        ]
    }

# Test normal bulk storage order creation (should succeed)
def test_normal_bulk_storage():
    print_test("Normal Bulk Storage Order Creation")
    
    test_order = generate_test_order()
    print(f"Using location: {test_order['location']}")
    
    return make_api_call("bulkStorage", test_order)

# Test bulk storage order with insufficient stock (should fail)
def test_insufficient_stock():
    print_test("Bulk Storage Order with Insufficient Stock")
    
    test_order = generate_test_order()
    # Add the test flag
    test_order["test_insufficient_stock"] = True
    print(f"Using location: {test_order['location']} with insufficient stock flag")
    
    return make_api_call("bulkStorage", test_order, expect_success=False)

# Test duplicate location (should fail)
def test_duplicate_location():
    print_test("Duplicate Location")
    
    # First create an order with a specific location
    test_order = generate_test_order()
    location = test_order["location"]
    
    success, _ = make_api_call("bulkStorage", test_order)
    if not success:
        print_result(False, "Could not create initial test order")
        return False, None
    
    # Now try to create another order with the same location
    second_order = generate_test_order()
    second_order["location"] = location
    print(f"Using duplicate location: {location}")
    
    return make_api_call("bulkStorage", second_order, expect_success=False)

# Test invalid location format (should fail)
def test_invalid_location_format():
    print_test("Invalid Location Format")
    
    test_order = generate_test_order()
    test_order["location"] = "INVALID-LOCATION"  # Wrong format
    
    return make_api_call("bulkStorage", test_order, expect_success=False)

# Test invalid barcode (should fail)
def test_invalid_barcode():
    print_test("Invalid Barcode")
    
    test_order = generate_test_order()
    test_order["items"][0]["barcode"] = "123"  # Too short
    
    return make_api_call("bulkStorage", test_order, expect_success=False)

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING BULK STORAGE WORKFLOW ================={Colors.ENDC}")
    
    # Check API health
    api_healthy, _ = check_api_health()
    if not api_healthy:
        print(f"{Colors.RED}API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    # Run the tests
    test_results = {}
    
    # Test normal bulk storage
    test_results["normal_bulk_storage"] = test_normal_bulk_storage()[0]
    
    # Test insufficient stock
    test_results["insufficient_stock"] = test_insufficient_stock()[0]
    
    # Test duplicate location
    test_results["duplicate_location"] = test_duplicate_location()[0]
    
    # Test invalid location format
    test_results["invalid_location_format"] = test_invalid_location_format()[0]
    
    # Test invalid barcode
    test_results["invalid_barcode"] = test_invalid_barcode()[0]
    
    # Print test summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"API health check: {'✓' if api_healthy else '✗'}")
    print(f"Normal bulk storage order: {'✓' if test_results['normal_bulk_storage'] else '✗'}")
    print(f"Insufficient stock test: {'✓' if test_results['insufficient_stock'] else '✗'}")
    print(f"Duplicate location rejection: {'✓' if test_results['duplicate_location'] else '✗'}")
    print(f"Invalid location format rejection: {'✓' if test_results['invalid_location_format'] else '✗'}")
    print(f"Invalid barcode rejection: {'✓' if test_results['invalid_barcode'] else '✗'}")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        print(f"{Colors.GREEN}✓ All tests passed! Bulk storage workflow is working correctly.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")