import requests
import json
import time

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

def check_api_health():
    print_test("API Health Check")
    return make_api_call("health", {}, method="GET")

def test_enhanced_measurement_processing():
    """Test the enhanced measurement processing with known barcode"""
    print_test("Enhanced Measurement Processing - Basic Test")
    
    # Use a known barcode that should exist in the barcodes table
    # This is a test with new attributes format
    test_data = {
        "timestamp": "2025-06-02T19:30:00.000000",
        "l": 150,  # 150mm length
        "w": 50,   # 50mm width  
        "h": 200,  # 200mm height
        "weight": 450,  # 450g weight
        "barcode": "1234567890123",  # Known test barcode
        "shape": "rectangular",
        "device": "qboid-scanner-01",
        "note": "Enhanced processing test",
        "attributes": {
            "cap-tstr": "true",
            "origin": "germany", 
            "cello": "false",
            "origin2": "uk"
        }
    }
    
    success, response = make_api_call("measurement", test_data)
    
    if success:
        # Check if processing information is included
        has_processing = "processing" in response
        print_result(has_processing, "Response includes processing information")
        
        if has_processing:
            processing = response["processing"]
            
            # Check SKU lookup
            sku_success = processing.get("sku_lookup", {}).get("success", False)
            sku_found = processing.get("sku_lookup", {}).get("sku")
            print_result(sku_success, f"SKU lookup successful: {sku_found}")
            
            # Check updates
            updates = processing.get("updates", {})
            fields_updated = updates.get("fields_updated", [])
            print_result(len(fields_updated) > 0, f"Fields updated: {fields_updated}")
            
            # Check for errors
            errors = processing.get("errors", [])
            no_errors = len(errors) == 0
            print_result(no_errors, f"No processing errors: {errors if errors else 'None'}")
    
    return success, response

def test_barcode_not_found():
    """Test with a barcode that doesn't exist"""
    print_test("Barcode Not Found Test")
    
    test_data = {
        "l": 100,
        "w": 100,
        "h": 100,
        "weight": 200,
        "barcode": "9999999999999",  # Non-existent barcode
        "shape": "cube",
        "device": "qboid-scanner-01",
        "attributes": {
            "cap-tstr": "false"
        }
    }
    
    success, response = make_api_call("measurement", test_data)
    
    if success and "processing" in response:
        processing = response["processing"]
        sku_success = processing.get("sku_lookup", {}).get("success", False)
        errors = processing.get("errors", [])
        
        # Should have failed SKU lookup
        print_result(not sku_success, "SKU lookup failed as expected")
        print_result(len(errors) > 0, f"Errors reported: {errors}")
    
    return success, response

def test_empty_attributes():
    """Test with empty attributes object"""
    print_test("Empty Attributes Test")
    
    test_data = {
        "l": 75,
        "w": 75,
        "h": 75,
        "weight": 150,
        "barcode": "1234567890123",  # Known test barcode
        "shape": "cube",
        "device": "qboid-scanner-01",
        "attributes": {}  # Empty attributes
    }
    
    success, response = make_api_call("measurement", test_data)
    
    if success and "processing" in response:
        processing = response["processing"]
        attributes_updated = processing.get("updates", {}).get("attributes_updated", False)
        
        # Should not have updated attributes with empty object
        print_result(not attributes_updated, "No attributes updated with empty object")
    
    return success, response

def test_dimension_comparison():
    """Test dimension comparison with significant difference"""
    print_test("Dimension Comparison Test")
    
    # Test with dimensions that should be significantly different (>5%)
    test_data = {
        "l": 1000,  # Large difference to trigger update
        "w": 1000,
        "h": 1000,
        "weight": 2000,  # Large difference
        "barcode": "1234567890123",
        "shape": "large-cube",
        "device": "qboid-scanner-01",
        "attributes": {
            "cap-tstr": "true",
            "cello": "true"
        }
    }
    
    success, response = make_api_call("measurement", test_data)
    
    if success and "processing" in response:
        processing = response["processing"]
        dimensions_updated = processing.get("updates", {}).get("dimensions_updated", False)
        weight_updated = processing.get("updates", {}).get("weight_updated", False)
        
        print_result(dimensions_updated or weight_updated, "Dimensions or weight updated due to significant difference")
    
    return success, response

if __name__ == "__main__":
    print(f"{Colors.BLUE}================= TESTING ENHANCED MEASUREMENT PROCESSING ================={Colors.ENDC}")
    
    # Check API health
    api_healthy, _ = check_api_health()
    if not api_healthy:
        print(f"{Colors.RED}Main API is not accessible. Cannot proceed with tests.{Colors.ENDC}")
        exit(1)
    
    # Run enhanced processing tests
    results = {
        "basic_processing": test_enhanced_measurement_processing()[0],
        "barcode_not_found": test_barcode_not_found()[0],
        "empty_attributes": test_empty_attributes()[0],
        "dimension_comparison": test_dimension_comparison()[0]
    }
    
    # Print summary
    print(f"\n{Colors.BLUE}================= TEST SUMMARY ================={Colors.ENDC}")
    print(f"Tests passed: {sum(1 for success in results.values() if success)}/{len(results)}")
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        color = Colors.GREEN if passed else Colors.RED
        print(f"{color}{status}: {test_name}{Colors.ENDC}")
    
    if all(results.values()):
        print(f"{Colors.GREEN}✓ All tests passed! Enhanced measurement processing is working.{Colors.ENDC}")
    else:
        print(f"{Colors.RED}✗ Some tests failed. Check the details above.{Colors.ENDC}")
