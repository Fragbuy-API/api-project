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

# Test scenarios for enhanced find_purchase_order API
def test_find_by_po_number():
    print_test("Find Purchase Order by PO Number")
    data = {
        "po_number": "SVPO2000300"  # Partial PO number pattern
    }
    success, response = make_api_call("find_purchase_order", data)
    if success:
        found_pos = len(response.get("results", []))
        print_result(found_pos > 0, f"Found {found_pos} purchase orders matching the PO number pattern")
    return success, response

def test_find_by_specific_po_number():
    print_test("Find Purchase Order by Specific PO Number")
    data = {
        "po_number": "SVPO2000300015"  # Exact match for a known PO
    }
    success, response = make_api_call("find_purchase_order", data)
    if success:
        found_pos = len(response.get("results", []))
        print_result(found_pos > 0, f"Found {found_pos} purchase orders with the exact PO number")
    return success, response

def test_find_by_supplier_name():
    print_test("Find Purchase Order by Supplier Name")
    data = {
        "po_number": "Hussein"  # Part of supplier name "Al Hussein"
    }
    success, response = make_api_call("find_purchase_order", data)
    if success:
        found_pos = len(response.get("results", []))
        has_supplier = False
        if found_pos > 0:
            # Check if any of the returned POs are from the expected supplier
            for po in response.get("results", []):
                if "Hussein" in po.get("supplier_name", ""):
                    has_supplier = True
                    break
        print_result(has_supplier, "Found purchase orders from the specified supplier")
    return success, response

def test_find_by_barcode():
    print_test("Find Purchase Order by Barcode")
    # Use a barcode that should map to a SKU in a known PO
    # This might need to be updated with a valid barcode from your system
    data = {
        "barcode": "1234567890123"
    }
    return make_api_call("find_purchase_order", data)

def test_find_by_multiple_barcodes():
    print_test("Find Purchase Order by Multiple Barcodes")
    # Use barcodes that should map to SKUs in a known PO
    # This might need to be updated with valid barcodes from your system
    data = {
        "barcode": ["1234567890123", "9876543210987"]
    }
    return make_api_call("find_purchase_order", data)

def test_find_by_nonexistent_text():
    print_test("Find Purchase Order by Non-existent Text")
    data = {
        "po_number": "NONEXISTENTTEXT123456789"
    }
    success, response = make_api_call("find_purchase_order", data)
    if success:
        # Should return success but with empty results
        empty_results = len(response.get("results", [None])) == 0
        print_result(empty_results, "Returned empty results for non-existent text as expected")
        return empty_results, response
    return success, response

def test_find_by_invalid_barcode_list():
    print_test("Find Purchase Order by Invalid Barcode List")
    data = {
        "barcode": ["1234567890123", "123"]  # Second barcode is invalid
    }
    return make_api_call("find_purchase_order", data, expect_success=False)

def test_invalid_request_missing_fields():
    print_test("Invalid Request - Missing Fields")
    data = {}  # No search parameters provided
    return make_api_call("find_purchase_order", data, expect_success=False)

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING ENHANCED PURCHASE ORDER SEARCH API ================={Colors.ENDC}")
    
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
        "find_by_po_number": test_find_by_po_number()[0],
        "find_by_specific_po_number": test_find_by_specific_po_number()[0],
        "find_by_supplier_name": test_find_by_supplier_name()[0],
        "find_by_nonexistent_text": test_find_by_nonexistent_text()[0],
        "invalid_request_missing_fields": test_invalid_request_missing_fields()[0]
    }
    
    # Optionally run tests that require valid barcodes if they are available
    # Update this section with valid barcodes or comment out if not applicable
    try:
        results["find_by_barcode"] = test_find_by_barcode()[0]
        results["find_by_multiple_barcodes"] = test_find_by_multiple_barcodes()[0]
        results["find_by_invalid_barcode_list"] = test_find_by_invalid_barcode_list()[0]
    except Exception as e:
        print(f"{Colors.YELLOW}Skipped barcode tests - ensure valid barcodes are used: {str(e)}{Colors.ENDC}")
    
    # Print summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Tests passed: {sum(1 for success in results.values() if success)}/{len(results)}")
    
    if all(results.values()):
        print(f"{Colors.GREEN}✓ All tests passed! Enhanced Purchase Order Search API is working.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")