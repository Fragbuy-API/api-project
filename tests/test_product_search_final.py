import requests
import json
import re

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

def check_product_health():
    print_test("Product API Health Check")
    return make_api_call("product-health", {}, method="GET")

# Test basic search functionality
def test_basic_search():
    print_test("Basic Product Search")
    data = {
        "query": "Kolnisch",
        "limit": 5
    }
    success, response = make_api_call("product_search", data)
    
    if success and response["status"] == "success":
        # Additional validation
        products_found = response.get("count", 0) > 0
        print_result(products_found, f"Found {response.get('count', 0)} products")
        
        if not products_found:
            # If no products found, skip further validation
            return success, response
        
        # Validate response format
        required_fields = ["status", "message", "search_criteria", "count", "products", "timestamp"]
        all_fields_present = all(field in response for field in required_fields)
        print_result(all_fields_present, "All required response fields are present")
        
        # Validate products array
        products_valid = True
        for product in response["products"]:
            if not all(field in product for field in ["sku", "name"]):
                products_valid = False
                break
        print_result(products_valid, "Products have required fields (sku, name)")
        
        return success and all_fields_present and products_valid, response
    
    return success, response

# Test image URL presence in results
def test_image_url_presence():
    print_test("Image URL Presence")
    data = {
        "query": "4711M",
        "limit": 10
    }
    success, response = make_api_call("product_search", data)
    
    if success and response["status"] == "success" and response.get("count", 0) > 0:
        # Check if any products have image_url
        products_with_image_url = [p for p in response["products"] if "image_url" in p]
        image_url_presence = len(products_with_image_url) > 0
        
        print_result(image_url_presence, 
                    f"{len(products_with_image_url)} out of {len(response['products'])} products have image_url")
        
        # Check if image URLs are valid URLs
        valid_urls = True
        invalid_urls = []
        url_pattern = re.compile(r'^https?://\S+\.\S+$')
        
        for product in products_with_image_url:
            if not url_pattern.match(product["image_url"]):
                valid_urls = False
                invalid_urls.append(product["image_url"])
        
        print_result(valid_urls, "All image URLs are valid formats" if valid_urls else f"Invalid URLs: {invalid_urls}")
        
        return success and image_url_presence and valid_urls, response
    
    if success and response.get("count", 0) == 0:
        print_result(False, "No products found to test image URLs")
    
    return success, response

# Test finalurl is used as image_url when available
def test_finalurl_priority():
    print_test("finalurl Priority for image_url")
    data = {
        "query": "4711M",
        "limit": 10
    }
    success, response = make_api_call("product_search", data)
    
    if success and response["status"] == "success" and response.get("count", 0) > 0:
        # Check if any products have both finalurl and image_url
        products_with_both = [p for p in response["products"] if "finalurl" in p and "image_url" in p]
        
        if len(products_with_both) == 0:
            print_result(False, "No products found with both finalurl and image_url to test priority")
            return success, response
        
        # Check if finalurl is used as image_url
        correct_priority = True
        for product in products_with_both:
            if product["finalurl"] != product["image_url"]:
                correct_priority = False
                break
        
        print_result(correct_priority, 
                    "finalurl is correctly used as image_url" if correct_priority 
                    else "finalurl is not used as image_url in some products")
        
        return success and correct_priority, response
    
    if success and response.get("count", 0) == 0:
        print_result(False, "No products found to test finalurl priority")
    
    return success, response

# Test fallback to other image fields when finalurl is not available
def test_image_fallback():
    print_test("Image URL Fallback Logic")
    data = {
        "query": "4711M",
        "limit": 10
    }
    success, response = make_api_call("product_search", data)
    
    if success and response["status"] == "success" and response.get("count", 0) > 0:
        # Look for products without finalurl but with image_url
        products_with_fallback = [p for p in response["products"] 
                               if ("finalurl" not in p or not p["finalurl"]) and "image_url" in p]
        
        if len(products_with_fallback) == 0:
            print_result(True, "No products found needing fallback logic (all have finalurl or none have image_url)")
            return success, response
        
        # Check if fallback worked correctly - image_url should match one of the other image fields
        correct_fallback = True
        for product in products_with_fallback:
            other_image_fields = ["photo_url_live", "photo_url_raw", "pictures"]
            matched = False
            for field in other_image_fields:
                if field in product and product[field] == product["image_url"]:
                    matched = True
                    break
            if not matched:
                correct_fallback = False
                break
        
        print_result(correct_fallback, 
                   f"Fallback logic worked correctly for {len(products_with_fallback)} products" if correct_fallback 
                   else "Fallback logic failed for some products")
        
        return success and correct_fallback, response
    
    if success and response.get("count", 0) == 0:
        print_result(False, "No products found to test image fallback")
    
    return success, response

# Test limit parameter with a small value
def test_limit_parameter():
    print_test("Limit Parameter")
    small_limit = 2
    data = {
        "query": "Kolnisch",
        "limit": small_limit
    }
    success, response = make_api_call("product_search", data)
    
    if success and response["status"] == "success":
        # Check if limit was respected
        respects_limit = len(response["products"]) <= small_limit
        print_result(respects_limit, 
                    f"Response respects limit parameter ({len(response['products'])} ≤ {small_limit})")
        
        return success and respects_limit, response
    
    return success, response

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING PRODUCT SEARCH API WITH IMAGES ================={Colors.ENDC}")
    
    # Check API health
    api_healthy, _ = check_api_health()
    if not api_healthy:
        print(f"{Colors.RED}Main API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    product_api_healthy, _ = check_product_health()
    if not product_api_healthy:
        print(f"{Colors.RED}Product API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    # Run the tests
    results = {
        "basic_search": test_basic_search()[0],
        "image_url_presence": test_image_url_presence()[0],
        "finalurl_priority": test_finalurl_priority()[0],
        "image_fallback": test_image_fallback()[0],
        "limit_parameter": test_limit_parameter()[0]
    }
    
    # Print summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Tests passed: {sum(1 for success in results.values() if success)}/{len(results)}")
    
    if all(results.values()):
        print(f"{Colors.GREEN}✓ All tests passed! Product Search API with images is working.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")