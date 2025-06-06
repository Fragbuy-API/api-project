# Enhanced Purchase Orders Search API Documentation

## Overview

The Enhanced Purchase Orders Search API allows you to search for purchase orders in the Qboid system by either:
- Text search (matching against both purchase order number and supplier name)
- Product barcode(s)

This document provides details on how to use the API, expected inputs and outputs, and example requests and responses.

## Endpoint

```
POST /api/v1/find_purchase_order
```

## Authentication

Currently, the API does not require authentication. This may change in future updates.

## Request Format

The API accepts POST requests with a JSON body. The following parameters are supported:

| Parameter | Type                | Required | Description |
|-----------|---------------------|----------|-------------|
| po_number | string              | No*      | Text to search in both purchase order number and supplier name (partial match) |
| barcode   | string or string[]  | No*      | Product barcode (must be 8-14 digits) or an array of barcodes |

\* At least one of `po_number` or `barcode` must be provided.

## Response Format

The API returns responses in JSON format with the following structure:

```json
{
  "status": "success",
  "message": "Description of the result",
  "results": [
    {
      "po_number": "SVPO2000300015",
      "status": "NoneReceived",
      "supplier_name": "Al Hussein",
      "created_date": "2025-01-28T17:12:07.5146577Z",
      "order_date": "2025-01-28T05:00:00.0000000Z",
      "arrival_due_date": "2025-02-03T05:00:00.0000000Z",
      "ship_to_warehouse": "AGP23"
    },
    // Additional purchase orders...
  ],
  "count": 1,
  "timestamp": "2025-03-26T16:30:45.123456"
}
```

The `results` array will contain purchase order objects with the following fields:

| Field              | Type   | Description |
|--------------------|--------|-------------|
| po_number          | string | Purchase order number |
| status             | string | Current status of the order |
| supplier_name      | string | Name of the supplier |
| created_date       | string | Date when the PO was created |
| order_date         | string | Date when the order was placed |
| arrival_due_date   | string | Expected arrival date |
| ship_to_warehouse  | string | Destination warehouse |

## Examples

### Example 1: Search by PO Number Text

**Request:**
```json
POST /api/v1/find_purchase_order
{
  "po_number": "SVPO2000300"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Found 12 matching purchase orders",
  "results": [
    {
      "po_number": "SVPO2000300015",
      "status": "NoneReceived",
      "supplier_name": "Al Hussein",
      "created_date": "2025-01-28T17:12:07.5146577Z",
      "order_date": "2025-01-28T05:00:00.0000000Z",
      "arrival_due_date": "2025-02-03T05:00:00.0000000Z",
      "ship_to_warehouse": "AGP23"
    },
    {
      "po_number": "SVPO2000300044",
      "status": "Pending",
      "supplier_name": "Fragrance World",
      "created_date": "2025-02-01T10:25:33.1258793Z",
      "order_date": "2025-02-01T05:00:00.0000000Z",
      "arrival_due_date": "2025-02-15T05:00:00.0000000Z",
      "ship_to_warehouse": "AGP23"
    },
    // Additional purchase orders...
  ],
  "count": 12,
  "timestamp": "2025-03-26T16:30:45.123456"
}
```

### Example 2: Search by Supplier Name

**Request:**
```json
POST /api/v1/find_purchase_order
{
  "po_number": "Hussein"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Found 3 matching purchase orders",
  "results": [
    {
      "po_number": "SVPO2000300015",
      "status": "NoneReceived",
      "supplier_name": "Al Hussein",
      "created_date": "2025-01-28T17:12:07.5146577Z",
      "order_date": "2025-01-28T05:00:00.0000000Z",
      "arrival_due_date": "2025-02-03T05:00:00.0000000Z",
      "ship_to_warehouse": "AGP23"
    },
    {
      "po_number": "SVPO2000300098",
      "status": "In Progress",
      "supplier_name": "Al Hussein",
      "created_date": "2025-02-12T09:18:45.7893214Z",
      "order_date": "2025-02-12T05:00:00.0000000Z",
      "arrival_due_date": "2025-02-26T05:00:00.0000000Z",
      "ship_to_warehouse": "AGP23"
    },
    {
      "po_number": "SVPO2000300157",
      "status": "Pending",
      "supplier_name": "Al Hussein",
      "created_date": "2025-02-28T14:53:21.4572368Z",
      "order_date": "2025-02-28T05:00:00.0000000Z",
      "arrival_due_date": "2025-03-14T05:00:00.0000000Z",
      "ship_to_warehouse": "AGP23"
    }
  ],
  "count": 3,
  "timestamp": "2025-03-26T16:30:45.123456"
}
```

### Example 3: Search by Single Barcode

**Request:**
```json
POST /api/v1/find_purchase_order
{
  "barcode": "1234567890123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Found 1 matching purchase orders",
  "results": [
    {
      "po_number": "SVPO2000300044",
      "status": "Pending",
      "supplier_name": "Fragrance World",
      "created_date": "2025-02-01T10:25:33.1258793Z",
      "order_date": "2025-02-01T05:00:00.0000000Z",
      "arrival_due_date": "2025-02-15T05:00:00.0000000Z",
      "ship_to_warehouse": "AGP23"
    }
  ],
  "count": 1,
  "timestamp": "2025-03-26T16:30:45.123456"
}
```

### Example 4: Search by Multiple Barcodes

**Request:**
```json
POST /api/v1/find_purchase_order
{
  "barcode": ["1234567890123", "9876543210987"]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Found 1 matching purchase orders",
  "results": [
    {
      "po_number": "SVPO2000300044",
      "status": "Pending",
      "supplier_name": "Fragrance World",
      "created_date": "2025-02-01T10:25:33.1258793Z",
      "order_date": "2025-02-01T05:00:00.0000000Z",
      "arrival_due_date": "2025-02-15T05:00:00.0000000Z", 
      "ship_to_warehouse": "AGP23"
    }
  ],
  "count": 1,
  "timestamp": "2025-03-26T16:30:45.123456"
}
```

### Example 5: No Results Found

**Request:**
```json
POST /api/v1/find_purchase_order
{
  "po_number": "NONEXISTENT"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "No matching purchase orders found",
  "results": [],
  "count": 0,
  "timestamp": "2025-03-26T16:30:45.123456"
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
      "loc": ["body"],
      "msg": "Value error, Either po_number or barcode must be provided",
      "input": {},
      "ctx": {
        "error": {}
      }
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
    "timestamp": "2025-03-26T16:30:45.123456"
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
    "timestamp": "2025-03-26T16:30:45.123456"
  }
}
```

## Notes

1. When searching with text (using the `po_number` parameter), the API will look for matches in both:
   - The purchase order number field
   - The supplier name field
   
2. Text search uses a "contains" approach, so partial matches will be returned (e.g., searching for "hussein" will match supplier "Al Hussein").

3. When searching by barcode, the API first looks up the SKU associated with that barcode, then finds purchase orders containing that SKU.

4. When searching by multiple barcodes, the API only returns purchase orders that contain ALL the SKUs associated with those barcodes.

5. Only purchase orders with status that is not "Completed" or "Cancelled" are returned.

## Integration Examples

### cURL

```bash
curl -X POST \
  http://155.138.159.75/api/v1/find_purchase_order \
  -H 'Content-Type: application/json' \
  -d '{
    "po_number": "Hussein"
}'
```

### Python

```python
import requests
import json

url = "http://155.138.159.75/api/v1/find_purchase_order"
payload = {
    "po_number": "SVPO2000300"
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
fetch('http://155.138.159.75/api/v1/find_purchase_order', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    "po_number": "Hussein"
  }),
})
.then(response => response.json())
.then(data => console.log(data))
.catch((error) => console.error('Error:', error));
```

## Contact

For any issues or questions regarding the Enhanced Purchase Orders Search API, please contact the Qboid API support team.
