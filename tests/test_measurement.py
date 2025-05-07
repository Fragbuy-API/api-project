import requests
import json
from datetime import datetime

# API endpoint
API_URL = "http://155.138.159.75:8000/api/v1/measurement"

# Test data matching the structure in body.json
test_data = {
    "timestamp": datetime.now().isoformat(),
    "l": 187,
    "w": 102,
    "h": 58,
    "weight": 560,
    "barcode": "860003782507",
    "shape": "Cuboidal",
    "device": "FH0402211700010",
    "note": "Test measurement",
    "attributes": {
        "ovpk": "false",
        "batt": "true",
        "hazmat": "false",
        "qty": "5",
        "sku": "TEST-SKU-001"  # Added SKU for testing
    },
    "image": "test_image_data"
}

# Send POST request
try:
    response = requests.post(API_URL, json=test_data)
    
    # Print the response
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    
except Exception as e:
    print(f"Error: {str(e)}")

# Also test the health endpoint
try:
    health_response = requests.get("http://155.138.159.75:8000/api/v1/health")
    print("\nHealth Check:")
    print(f"Status Code: {health_response.status_code}")
    print("Response:")
    print(json.dumps(health_response.json(), indent=2))
    
except Exception as e:
    print(f"Health Check Error: {str(e)}")