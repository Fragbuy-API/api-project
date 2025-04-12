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

# ======== PRODUCT SEARCH TESTS ========

def test_product_search_by_known_sku():
    print_test("Search Product by Known SKU")
    
    # Use a known SKU that exists in the database
    test_sku = "4711M-50B"
    print(f"Using known SKU: {test_sku}")
    
    data = {
        "sku": test_sku,
        "limit": 10
    }
    
    return make_api_call("product_search", data)

def test_product_search_by_description_fragment():
    print_test("Search Product by Description Fragment")
    
    # Use a fragment from the known product description
    test_name = "Kolnisch"
    print(f"Using description fragment: {test_name}")
    
    data = {
        "name": test_name,
        "limit": 10
    }
    
    return make_api_call("product_search", data)

def test_product_search_by_nonexistent_sku():
    print_test("Search Product by Non-existent SKU")
    
    # This SKU shouldn't exist in the database
    test_sku = "NONEXISTENT-SKU-12345"
    print(f"Using non-existent SKU: {test_sku}")
    
    data = {
        "sku": test_sku,
        "limit": 10
    }
    
    # We expect a 200 OK but with an empty products array
    return make_api_call("product_search", data)

def test_product_search_invalid_input():
    print_test("Search with Invalid Input (No SKU or Name)")
    
    data = {
        "limit": 10  # Missing both sku and name
    }
    
    # We expect validation error
    return make_api_call("product_search", data, expect_success=False)

def run_tests():
    """Run the tests to verify the product search API"""
    print(f"{Colors.BLUE}================= TESTING PRODUCT SEARCH API ================={Colors.ENDC}")
    
    # Check if API is running
    api_healthy, _ = check_api_health()
    if not api_healthy:
        print(f"{Colors.RED}API health check failed. Cannot proceed with tests.{Colors.ENDC}")
        return
    
    # Run the tests
    results = {
        "search_by_known_sku": test_product_search_by_known_sku()[0],
        "search_by_description_fragment": test_product_search_by_description_fragment()[0],
        "search_by_nonexistent_sku": test_product_search_by_nonexistent_sku()[0],
        "search_invalid_input": test_product_search_invalid_input()[0]
    }
    
    # Show results
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Tests passed: {sum(1 for success in results.values() if success)}/{len(results)}")
    
    if all(results.values()):
        print(f"{Colors.GREEN}✓ All tests passed! Product search API is working.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")

if __name__ == "__main__":
    run_tests()