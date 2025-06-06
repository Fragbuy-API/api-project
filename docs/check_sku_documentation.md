# Check SKU Against PO API Documentation

## Overview

The Check SKU Against PO API allows you to verify if a product (identified by its barcode) is included in a specific purchase order. This document provides details on how to use the API, expected inputs and outputs, and example requests and responses.

## Endpoint

```
POST /api/v1/check_sku_against_po
```

## Authentication

Currently, the API does not require authentication. This may change in future updates.

## Request Format

The API accepts POST requests with a JSON body. The following parameters are required:

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| po_number | string | Yes      | Purchase order number (exact match) |
| barcode   | string | Yes      | Product barcode (must be 8-14 digits) |

## Response Format

The API returns responses in JSON format with the following structure:

```json
{
  "status": "success",
  "result": true,
  "po_number": "PO12345",
  "barcode": "1234567890123",
  "sku": "PRODUCT-SKU",
  "timestamp": "2025-03-14T15:23:45.123456"
}
```

The response fields are as follows:

| Field     | Type    | Description |
|-----------|---------|-------------|
| status    | string  | Status of the request ("success" or "error") |
| result    | boolean | TRUE if the SKU is in the PO, FALSE if not |
| po_number | string  | The purchase order number from the request |
| barcode   | string  | The barcode from the request |
| sku       | string  | The SKU associated with the provided barcode |
| timestamp | string  | ISO-format timestamp of when the response was generated |

## Examples

### Example 1: SKU Found in Purchase Order

**Request:**
```json
POST /api/v1/check_sku_against_po
{
  "po_number": "PO-TEST-001",
  "barcode": "1234567890123"
}
```

**Response:**
```json
{
  "status": "success",
  "result": true,
  "po_number": "PO-TEST-001",
  "barcode": "1234567890123",
  "sku": "4711M-50B",
  "timestamp": "2025-03-14T15:23:45.123456"
}
```

### Example 2: SKU Not Found in Purchase Order

**Request:**
```json
POST /api/v1/check_sku_against_po
{
  "po_number": "PO-TEST-003",
  "barcode": "1234567890123"
}
```

**Response:**
```json
{
  "status": "success",
  "result": false,
  "po_number": "PO-TEST-003",
  "barcode": "1234567890123",
  "sku": "4711M-50B",
  "timestamp": "2025-03-14T15:23:45.123456"
}
```

## Error Responses

If an error occurs, the API will return a response with an appropriate HTTP status code and an error message:

### Validation Error - Missing Required Field

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "value_error.missing",
      "loc": ["body", "po_number"],
      "msg": "Field required",
      "input": {"barcode": "1234567890123"}
    }
  ]
}
```

### Validation Error - Invalid Barcode Format

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "barcode"],
      "msg": "Value error, Barcode must be between 8 and 14 digits",
      "input": "123",
      "ctx": {
        "error": {}
      }
    }
  ]
}
```

### Barcode Not Found Error

**Status Code:** 404 Not Found

```json
{
  "detail": {
    "status": "error",
    "message": "Barcode 9999999999999 not found in the system",
    "error_code": "BARCODE_NOT_FOUND",
    "timestamp": "2025-03-14T15:23:45.123456"
  }
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
    "timestamp": "2025-03-14T15:23:45.123456"
  }
}
```

## Notes

1. The API performs an exact match on the purchase order number, unlike the find_purchase_order API which uses partial matching.
2. The API first looks up the SKU associated with the provided barcode, then checks if that SKU is included in the specified purchase order.
3. The result is a simple boolean: TRUE if the SKU is found in the PO, FALSE if not.

## Integration Examples

### cURL

```bash
curl -X POST \
  http://155.138.159.75/api/v1/check_sku_against_po \
  -H 'Content-Type: application/json' \
  -d '{
    "po_number": "PO-TEST-001",
    "barcode": "1234567890123"
}'
```

### Python

```python
import requests
import json

url = "http://155.138.159.75/api/v1/check_sku_against_po"
payload = {
    "po_number": "PO-TEST-001",
    "barcode": "1234567890123"
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
fetch('http://155.138.159.75/api/v1/check_sku_against_po', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    "po_number": "PO-TEST-001",
    "barcode": "1234567890123"
  }),
})
.then(response => response.json())
.then(data => console.log(data))
.catch((error) => console.error('Error:', error));
```

## Contact

For any issues or questions regarding the Check SKU Against PO API, please contact the Qboid API support team.
