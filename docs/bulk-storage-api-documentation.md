# Bulk Storage API Documentation

## Overview

The Bulk Storage API allows you to create and manage bulk storage orders in the Qboid system. A bulk storage order specifies a storage location and a list of items to be stored at that location. This document provides details on how to use the API, expected inputs and outputs, and example requests and responses.

## Endpoint

```
POST /api/v1/bulkStorage
```

## Request Format

The API accepts POST requests with a JSON body. The following parameters are required:

| Parameter             | Type    | Required | Description |
|-----------------------|---------|----------|-------------|
| location              | string  | Yes      | Storage location identifier (must follow format RACK-A1-01) |
| items                 | array   | Yes      | Array of items for storage (1-100 items) |
| test_insufficient_stock | boolean | No     | Test flag to simulate insufficient stock (default: false) |

Each item in the `items` array must have the following properties:

| Property  | Type    | Required | Description |
|-----------|---------|----------|-------------|
| sku       | string  | Yes      | Stock Keeping Unit identifier (alphanumeric, hyphens, underscores) |
| name      | string  | Yes      | Product name |
| barcode   | string  | Yes      | Product barcode (8-14 digits) |
| quantity  | integer | Yes      | Quantity (1-100,000) |

### Example Request

```json
{
  "location": "RACK-A1-01",
  "items": [
    {
      "sku": "BULK-001",
      "name": "Bulk Product 1",
      "barcode": "12345678901",
      "quantity": 100
    },
    {
      "sku": "BULK-002",
      "name": "Bulk Product 2",
      "barcode": "98765432109",
      "quantity": 50
    }
  ]
}
```

With test flag for inventory simulation:

```json
{
  "location": "RACK-A1-01",
  "items": [
    {
      "sku": "BULK-001",
      "name": "Bulk Product 1",
      "barcode": "12345678901",
      "quantity": 100
    }
  ],
  "test_insufficient_stock": true
}
```

## Response Format

### Successful Response

```json
{
  "status": "success",
  "message": "Bulk storage order created successfully for location RACK-A1-01",
  "order_id": 12345,
  "timestamp": "2025-04-22T15:45:30.123456",
  "items_processed": 2,
  "total_quantity": 150
}
```

### Error Responses

#### Duplicate Location

**Status Code:** 400 Bad Request

```json
{
  "detail": {
    "status": "error",
    "message": "Location RACK-A1-01 already has a pending order",
    "error_code": "DUPLICATE_LOCATION",
    "timestamp": "2025-04-22T15:45:30.123456"
  }
}
```

#### Quantity Exceeded

**Status Code:** 400 Bad Request

```json
{
  "detail": {
    "status": "error",
    "message": "Total quantity exceeds maximum allowed (1,000,000)",
    "error_code": "QUANTITY_EXCEEDED",
    "timestamp": "2025-04-22T15:45:30.123456"
  }
}
```

#### Insufficient Stock

**Status Code:** 400 Bad Request

```json
{
  "detail": {
    "status": "error",
    "message": "Insufficient stock to fulfill this bulk storage order",
    "error_code": "INSUFFICIENT_STOCK",
    "timestamp": "2025-04-22T15:45:30.123456"
  }
}
```

This error can be triggered for testing by setting `test_insufficient_stock: true` in the request.

#### Item Insert Failed

**Status Code:** 400 Bad Request

```json
{
  "detail": {
    "status": "error",
    "message": "Error inserting item with SKU BULK-001",
    "error_code": "ITEM_INSERT_FAILED",
    "timestamp": "2025-04-22T15:45:30.123456"
  }
}
```

#### Validation Error

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "location"],
      "msg": "Value error, Location must follow format RACK-A1-01 (RACK-<section><aisle>-<position>)",
      "input": "INVALID-LOCATION"
    }
  ]
}
```

## Business Logic

1. **Location Validation**: The location identifier must follow the format RACK-A1-01 (RACK-<section><aisle>-<position>).
2. **Duplicate Check**: The system checks if the location already has a pending order.
3. **Quantity Limits**: The system enforces limits on the quantity per item (1-100,000) and total quantity (1,000,000).
4. **Item Validation**: 
   - SKU must contain only letters, numbers, hyphens, and underscores
   - Barcode must be between 8 and 14 digits
   - No duplicate SKUs allowed in a single order
5. **Inventory Check**: The system checks if there is sufficient stock to fulfill the order (placeholder for future functionality).

## Integration Examples

### cURL

```bash
curl -X POST "http://155.138.159.75/api/v1/bulkStorage" \
     -H "Content-Type: application/json" \
     -d '{
       "location": "RACK-A1-01",
       "items": [
         {
           "sku": "BULK-001",
           "name": "Bulk Product 1",
           "barcode": "12345678901",
           "quantity": 100
         },
         {
           "sku": "BULK-002",
           "name": "Bulk Product 2",
           "barcode": "98765432109",
           "quantity": 50
         }
       ]
     }'
```

### Python

```python
import requests

response = requests.post(
    "http://155.138.159.75/api/v1/bulkStorage",
    json={
        "location": "RACK-A1-01",
        "items": [
            {
                "sku": "BULK-001",
                "name": "Bulk Product 1",
                "barcode": "12345678901",
                "quantity": 100
            },
            {
                "sku": "BULK-002",
                "name": "Bulk Product 2",
                "barcode": "98765432109",
                "quantity": 50
            }
        ]
    }
)
data = response.json()
print(data)
```

### Testing Insufficient Stock

```python
import requests

response = requests.post(
    "http://155.138.159.75/api/v1/bulkStorage",
    json={
        "location": "RACK-A1-01",
        "items": [
            {
                "sku": "BULK-001",
                "name": "Bulk Product 1",
                "barcode": "12345678901",
                "quantity": 100
            }
        ],
        "test_insufficient_stock": true
    }
)
data = response.json()
print(data)
```

## Notes

1. Maximum 100 items are allowed per bulk storage order.
2. The bulk storage API allows for larger quantities than the putaway API (100,000 per item vs 10,000).
3. When real inventory checking is implemented, the `test_insufficient_stock` flag will still be available for testing purposes.
4. All timestamps are in ISO 8601 format.
