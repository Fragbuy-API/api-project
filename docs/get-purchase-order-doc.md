# Get Purchase Order API Documentation

## Overview

The Get Purchase Order API allows you to retrieve detailed information about a specific purchase order including all line items. This document provides details on how to use the API, expected inputs and outputs, and example requests and responses.

## Endpoint

```
POST /api/v1/get_purchase_order
```

## Authentication

Currently, the API does not require authentication. This may change in future updates.

## Request Format

The API accepts POST requests with a JSON body. The following parameter is required:

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| po_number | string | Yes      | Purchase order number (exact match) |

## Response Format

The API returns responses in JSON format with the following structure:

```json
{
  "status": "success",
  "message": "Found 8 items in purchase order SVPO2000300015",
  "purchase_order": {
    "po_number": "SVPO2000300015",
    "status": "NoneReceived",
    "supplier_name": "Al Hussein",
    "created_date": "2025-01-28T17:12:07.5146577Z",
    "order_date": "2025-01-28T05:00:00.0000000Z",
    "arrival_due_date": "2025-02-03T05:00:00.0000000Z",
    "ship_to_warehouse": "AGP23"
  },
  "items": [
    {
      "sku": "FWAETHEREXM-100B",
      "quantity": 96,
      "description": "Fragrance World Aether Extrait de Parfum M 100ml Boxed"
    },
    {
      "sku": "LATAFAM-100B",
      "quantity": 96,
      "description": "Lattafa Fakhar M Edp 100ml Boxed"
    },
    {
      "sku": "FWAFTEFFEXTM-100B",
      "quantity": 48,
      "description": "Fragrance World After Effect Extrait De Parfum M 80ml Boxed"
    },
    {
      "sku": "LATSOEDPW-100B",
      "quantity": 48,
      "description": "Lattafa Sondos EDP W 100ml Boxed"
    },
    {
      "sku": "FWWINTM-100B",
      "quantity": 96,
      "description": "Fragrance World  Whiskey Intense M 100ml Boxed"
    },
    {
      "sku": "RASITSESM-100B",
      "quantity": 120,
      "description": "Rasasi It's Essential M 100ml Boxed"
    },
    {
      "sku": "LATAFAW-100B",
      "quantity": 96,
      "description": "Lattafa Fakhar EDP W 100ml Boxed"
    },
    {
      "sku": "FRGWAPBSM-80B",
      "quantity": 48,
      "description": "Fragrance World Artisan Perfume Brown Sugar EDP M 100ml Boxed"
    }
  ],
  "total_quantity": 648,
  "timestamp": "2025-03-26T15:58:33.022515"
}
```

The response fields are as follows:

| Field            | Type    | Description |
|------------------|---------|-------------|
| status           | string  | Status of the request ("success" or "error") |
| message          | string  | Description of the result |
| purchase_order   | object  | Basic information about the purchase order (if available) |
| items            | array   | Array of line items in the purchase order |
| total_quantity   | integer | Sum of quantities of all items in the purchase order |
| timestamp        | string  | ISO-format timestamp of when the response was generated |

Each item in the `items` array contains:

| Field       | Type    | Description |
|-------------|---------|-------------|
| sku         | string  | Product SKU |
| quantity    | integer | Quantity ordered |
| description | string  | Product description from the products table |

## Examples

### Example 1: Get Details for an Existing Purchase Order

**Request:**
```json
POST /api/v1/get_purchase_order
{
  "po_number": "SVPO2000300015"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Found 4 items in purchase order SVPO2000300138",
  "purchase_order": {
    "po_number": "SVPO2000300138",
    "status": "In Progress",
    "supplier_name": "Afnan Perfumes",
    "created_date": "2023-11-15",
    "order_date": "2023-11-16",
    "arrival_due_date": "2023-12-15",
    "ship_to_warehouse": "Main Warehouse"
  },
  "items": [
    {
      "sku": "AFTURBLUEEDPM-90B",
      "quantity": 528,
      "description": "Afnan Turathi Blue Eau De Parfum Men 90ml Boxed"
    },
    {
      "sku": "AFNSUPTPSRW-90B",
      "quantity": 192,
      "description": "Afnan Supremacy Not Only Intense Pour Homme EDP 90ml Boxed"
    },
    {
      "sku": "AFN9PMRBLM-100B",
      "quantity": 528,
      "description": "Afnan 9PM Ruby EDP Men 100ml Boxed"
    },
    {
      "sku": "AFNRAREGLDW-100B",
      "quantity": 96,
      "description": "Afnan Rare Gold Women EDP 100ml Boxed"
    }
  ],
  "total_quantity": 1344,
  "timestamp": "2025-03-26T15:23:45.123456"
}
```

### Example 2: Purchase Order Not Found

**Request:**
```json
POST /api/v1/get_purchase_order
{
  "po_number": "NONEXISTENT-PO-123456789"
}
```

**Response:**
```json
{
  "detail": {
    "status": "error",
    "message": "Purchase order NONEXISTENT-PO-123456789 not found in the system",
    "error_code": "PO_NOT_FOUND",
    "timestamp": "2025-03-26T15:23:45.123456"
  }
}
```

## Error Responses

If an error occurs, the API will return a response with an appropriate HTTP status code and an error message:

### Purchase Order Not Found

**Status Code:** 404 Not Found

```json
{
  "detail": {
    "status": "error",
    "message": "Purchase order NONEXISTENT-PO-123456789 not found in the system",
    "error_code": "PO_NOT_FOUND",
    "timestamp": "2025-03-26T15:23:45.123456"
  }
}
```

### Validation Error - Missing Required Field

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "po_number"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

### Validation Error - Empty PO Number

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "po_number"],
      "msg": "Value error, PO number cannot be empty",
      "input": "",
      "ctx": {
        "error": {}
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
    "timestamp": "2025-03-26T15:23:45.123456"
  }
}
```

## Notes

1. The API performs an exact match on the purchase order number.
2. If basic purchase order information is available in the purchase_orders table, it will be included in the response. Otherwise, only the line items will be returned.
3. The total_quantity field represents the sum of all quantities across all line items in the purchase order.
4. The API first checks if the PO exists in the po_lines table before attempting to retrieve any data.

## Integration Examples

### cURL

```bash
curl -X POST \
  http://155.138.159.75/api/v1/get_purchase_order \
  -H 'Content-Type: application/json' \
  -d '{
    "po_number": "SVPO2000300015"
}'
```

### Python

```python
import requests
import json

url = "http://155.138.159.75/api/v1/get_purchase_order"
payload = {
    "po_number": "SVPO2000300015"
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
fetch('http://155.138.159.75/api/v1/get_purchase_order', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    "po_number": "SVPO2000300015"
  }),
})
.then(response => response.json())
.then(data => console.log(data))
.catch((error) => console.error('Error:', error));
```

## Contact

For any issues or questions regarding the Get Purchase Order API, please contact the Qboid API support team.
