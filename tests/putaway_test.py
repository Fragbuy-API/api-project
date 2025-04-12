import requests
import json
from datetime import datetime

# API endpoint
API_URL = "http://155.138.159.75/api/v1/putawayOrder"

# Test data
test_data = {
    "tote": "TOTE123",
    "items": [
        {
            "sku": "SKU001",
            "name": "Test Product 1",
            "barcode": "123456789",
            "quantity": 5
        },
        {
            "sku": "SKU002",
            "name": "Test Product 2",
            "barcode": "987654321",
            "quantity": 3
        }
    ]
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
    health_response = requests.get("http://155.138.159.75/api/v1/health")
    print("\nHealth Check:")
    print(f"Status Code: {health_response.status_code}")
    print("Response:")
    print(json.dumps(health_response.json(), indent=2))
    
except Exception as e:
    print(f"Health Check Error: {str(e)}")