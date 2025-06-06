# Ad Hoc Add/Remove/Transfer (ART) Orders API Documentation

## Overview

The Ad Hoc Add/Remove/Transfer (ART) Orders API allows you to perform manual inventory adjustments in the Qboid system. This document provides details on how to use the API, expected inputs and outputs, error handling, and integration examples.

## Endpoint

```
POST /api/v1/art_order
```

## Authentication

Currently, the API does not require authentication. This may change in future updates.

## Request Format

The API accepts POST requests with a JSON body. The following parameters are supported:

| Parameter       | Type    | Required              | Description |
|-----------------|---------|----------------------|-------------|
| type            | string  | Yes                  | Operation type: "Add", "Remove", or "Transfer" |
| sku             | string  | Yes                  | Stock Keeping Unit identifier |
| quantity        | integer | Yes                  | Quantity to add, remove, or transfer (1-1,000,000) |
| from_location   | string  | For Remove/Transfer  | Source location (format: RACK-A1-01) |
| to_location     | string  | For Add/Transfer     | Destination location (format: RACK-A1-01) |
| reason          | string  | No                   | Optional reason for the operation |
| sufficient_stock| boolean | No                   | For testing: simulate insufficient stock |

**Notes on location requirements:**
- For "Add" operations, `to_location` is required
- For "Remove" operations, `from_location` is required
- For "Transfer" operations, both `from_location` and `to_location` are required and must be different

## Response Format

The API returns responses in JSON format with the following structure:

```json
{
  "status": "success",
  "message": "Successfully added 50 units of SKU 4711M-50B to location RACK-A1-01",
  "operation_type": "Add",
  "sku": "4711M-50B",
  "quantity": 50,
  "to_location": "RACK-A1-01",
  "reason": "Restocking",
  "operation_id": 12345,
  "timestamp": "2025-04-15T14:30:25.123456"
}
```

The response fields are as follows:

| Field           | Type    | Description |
|-----------------|---------|-------------|
| status          | string  | Status of the request ("success" or "error") |
| message         | string  | Description of the result |
| operation_type  | string  | Type of operation performed |
| sku             | string  | Stock Keeping Unit identifier |
| quantity        | integer | Quantity processed |
| from_location   | string  | Source location (only for Remove/Transfer) |
| to_location     | string  | Destination location (only for Add/Transfer) |
| reason          | string  | Reason for the operation (if provided) |
| operation_id    | integer | Unique identifier for the operation in the system |
| timestamp       | string  | ISO-format timestamp of when the response was generated |

## Examples

### Example 1: Add Inventory

**Request:**
```json
POST /api/v1/art_order
{
  "type": "Add",
  "sku": "4711M-50B",
  "quantity": 50,
  "to_location": "RACK-A1-01",
  "reason": "Restocking"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully added 50 units of SKU 4711M-50B to location RACK-A1-01",
  "operation_type": "Add",
  "sku": "4711M-50B",
  "quantity": 50,
  "to_location": "RACK-A1-01",
  "reason": "Restocking",
  "operation_id": 12345,
  "timestamp": "2025-04-15T14:30:25.123456"
}
```

### Example 2: Remove Inventory

**Request:**
```json
POST /api/v1/art_order
{
  "type": "Remove",
  "sku": "4711M-50B",
  "quantity": 20,
  "from_location": "RACK-A1-01",
  "reason": "Damaged goods"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully removed 20 units of SKU 4711M-50B from location RACK-A1-01",
  "operation_type": "Remove",
  "sku": "4711M-50B",
  "quantity": 20,
  "from_location": "RACK-A1-01",
  "reason": "Damaged goods",
  "operation_id": 12346,
  "timestamp": "2025-04-15T14:35:12.654321"
}
```

### Example 3: Transfer Inventory

**Request:**
```json
POST /api/v1/art_order
{
  "type": "Transfer",
  "sku": "4711M-50B",
  "quantity": 30,
  "from_location": "RACK-A1-01",
  "to_location": "RACK-B2-02",
  "reason": "Reorganizing inventory"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully transferred 30 units of SKU 4711M-50B from location RACK-A1-01 to location RACK-B2-02",
  "operation_type": "Transfer",
  "sku": "4711M-50B",
  "quantity": 30,
  "from_location": "RACK-A1-01",
  "to_location": "RACK-B2-02",
  "reason": "Reorganizing inventory",
  "operation_id": 12347,
  "timestamp": "2025-04-15T14:40:18.987654"
}
```

## Error Responses

If an error occurs, the API will return a response with an appropriate HTTP status code and an error message:

### Invalid SKU Error

**Status Code:** 404 Not Found

```json
{
  "detail": {
    "status": "error",
    "message": "SKU NONEXISTENT-SKU does not exist in the products table",
    "error_code": "INVALID_SKU",
    "timestamp": "2025-04-15T14:45:30.123456"
  }
}
```

### Insufficient Stock Error

**Status Code:** 400 Bad Request

```json
{
  "detail": {
    "status": "error",
    "message": "Insufficient stock of SKU 4711M-50B at location RACK-A1-01",
    "error_code": "INSUFFICIENT_STOCK",
    "timestamp": "2025-04-15T14:50:25.654321"
  }
}
```

### Validation Error - Missing Required Location

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body"],
      "msg": "Value error, to_location is required for Add operations",
      "input": {
        "type": "Add",
        "sku": "4711M-50B",
        "quantity": 50
      }
    }
  ]
}
```

### Validation Error - Invalid Location Format

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "to_location"],
      "msg": "Value error, Location must follow format RACK-A1-01 (RACK-<section><aisle>-<position>)",
      "input": {
        "type": "Add",
        "sku": "4711M-50B",
        "quantity": 50,
        "to_location": "INVALID-LOCATION"
      }
    }
  ]
}
```

### Server Error

**Status Code:** 500 Internal Server Error

```json
{
  "detail": {
    "status": "error",
    "message": "Server error: [error message]",
    "error_code": "SERVER_ERROR",
    "timestamp": "2025-04-15T14:55:40.987654"
  }
}
```

## Business Logic

1. **SKU Validation**: All SKUs are validated against the products table in the database. Invalid SKUs result in a 404 error.
2. **Stock Checking**: For Remove and Transfer operations, the system checks if there's sufficient stock at the source location before proceeding.
3. **Location Format**: All locations must follow the format RACK-A1-01, representing the rack, section, aisle, and position.
4. **Operation Tracking**: All operations are tracked in the art_operations table for audit purposes.

## Integration Examples

### cURL

```bash
curl -X POST "http://155.138.159.75/api/v1/art_order" \
     -H "Content-Type: application/json" \
     -d '{
       "type": "Add",
       "sku": "4711M-50B",
       "quantity": 50,
       "to_location": "RACK-A1-01",
       "reason": "Restocking"
     }'
```

### Python

```python
import requests
import json

url = "http://155.138.159.75/api/v1/art_order"
payload = {
    "type": "Add",
    "sku": "4711M-50B",
    "quantity": 50,
    "to_location": "RACK-A1-01",
    "reason": "Restocking"
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()

print(json.dumps(data, indent=2))
```

### JavaScript

```javascript
fetch('http://155.138.159.75/api/v1/art_order', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    "type": "Add",
    "sku": "4711M-50B",
    "quantity": 50,
    "to_location": "RACK-A1-01",
    "reason": "Restocking"
  }),
})
.then(response => response.json())
.then(data => console.log(data))
.catch((error) => console.error('Error:', error));
```

## Health Check Endpoint

To verify that the ART Orders API is up and running, you can use the health check endpoint:

```
GET /api/v1/art-orders-health
```

This will return a response similar to:

```json
{
  "status": "healthy",
  "message": "ART Orders API endpoints are available",
  "timestamp": "2025-04-15T15:00:00.123456"
}
```

## Future Enhancements

1. Integration with SkuVault or other inventory management systems
2. Bulk operation support for processing multiple SKUs in a single request
3. Inventory level checking against a live inventory database
4. Support for additional operation types (e.g., Count, Adjust)

## Contact

For any issues or questions regarding the ART Orders API, please contact the Qboid API support team.
