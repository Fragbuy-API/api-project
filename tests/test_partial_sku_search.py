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

# Test partial SKU search
def test_partial_sku_search():
    print_test("Search by Partial SKU")
    
    # Use a partial SKU
    test_sku = "4711M"  # This should find multiple 4711M products
    print(f"Using partial SKU: {test_sku}")
    
    data = {
        "sku": test_sku,
        "limit": 10
    }
    
    success, response = make_api_call("product_search", data)
    
    # Verify that we got multiple results
    if success and response.get("count", 0) > 1:
        print(f"{Colors.GREEN}✓ Successfully found multiple products with partial SKU search{Colors.ENDC}")
        print(f"Found {response.get('count', 0)} products matching '{test_sku}'")
    else:
        print(f"{Colors.RED}✗ Failed to find multiple products with partial SKU search{Colors.ENDC}")
    
    return success and response.get("count", 0) > 1

if __name__ == "__main__":
    # Run the health check first
    api_healthy, _ = check_api_health()
    
    if not api_healthy:
        print(f"{Colors.RED}API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    # Test partial SKU search
    partial_sku_test = test_partial_sku_search()
    
    # Print summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    if partial_sku_test:
        print(f"{Colors.GREEN}✓ Partial SKU search is working correctly!{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Partial SKU search test failed.{Colors.ENDC}")