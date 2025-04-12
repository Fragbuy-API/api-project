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

# Test various search scenarios with unified search
def test_search_by_sku():
    print_test("Search by SKU Pattern")
    data = {
        "query": "4711M",
        "limit": 5
    }
    return make_api_call("product_search", data)

def test_search_by_description():
    print_test("Search by Description")
    data = {
        "query": "Kolnisch",
        "limit": 5
    }
    return make_api_call("product_search", data)

def test_search_by_size():
    print_test("Search by Size (50ml)")
    data = {
        "query": "50ml",
        "limit": 5
    }
    return make_api_call("product_search", data)

def test_search_nonexistent():
    print_test("Search for Non-Existent Product")
    data = {
        "query": "NonExistentProduct12345",
        "limit": 5
    }
    return make_api_call("product_search", data)

def test_empty_query():
    print_test("Search with Empty Query")
    data = {
        "query": "",
        "limit": 5
    }
    return make_api_call("product_search", data, expect_success=False)

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING UNIFIED PRODUCT SEARCH API ================={Colors.ENDC}")
    
    # Check API health
    api_healthy, _ = check_api_health()
    if not api_healthy:
        print(f"{Colors.RED}API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    # Run the tests
    results = {
        "search_by_sku": test_search_by_sku()[0],
        "search_by_description": test_search_by_description()[0],
        "search_by_size": test_search_by_size()[0],
        "search_nonexistent": test_search_nonexistent()[0],
        "empty_query": test_empty_query()[0]
    }
    
    # Print summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Tests passed: {sum(1 for success in results.values() if success)}/{len(results)}")
    
    if all(results.values()):
        print(f"{Colors.GREEN}✓ All tests passed! Unified product search API is working.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")