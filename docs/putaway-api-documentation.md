# Putaway Order API Documentation

## Overview

The Putaway Order API allows you to create and manage putaway orders in the Qboid system. A putaway order specifies a tote and a list of items to be moved into storage locations. This document provides details on how to use the API, expected inputs and outputs, and example requests and responses.

## Endpoint

```
POST /api/v1/putawayOrder
```

## Request Format

The API accepts POST requests with a JSON body. The following parameters are required:

| Parameter             | Type    | Required | Description |
|-----------------------|---------|----------|-------------|
| tote                  | string  | Yes      | Tote identifier (must start with "TOTE") |
| items                 | array   | Yes      | Array of items in the tote (1-50 items) |
| test_insufficient_stock | boolean | No     | Test flag to simulate insufficient stock (default: false) |

Each item in the `items` array must have the following properties:

| Property  | Type    | Required | Description |
|-----------|---------|----------|-------------|
| sku       | string  | Yes      | Stock Keeping Unit identifier (alphanumeric, hyphens, underscores) |
| name      | string  | Yes      | Product name |
| barcode   | string  | Yes      | Product barcode (8-14 digits) |
| quantity  | integer | Yes      | Quantity (1-10,000) |

### Example Request

```json
{
  "tote": "TOTE123ABC",
  "items": [
    {
      "sku": "SKU-001",
      "name": "Test Product 1",
      "barcode": "12345678901",
      "quantity": 5
    },
    {
      "sku": "SKU-002",
      "name": "Test Product 2",
      "barcode": "98765432109",
      "quantity": 3
    }
  ]
}
```

With test flag for inventory simulation:

```json
{
  "tote": "TOTE123ABC",
  "items": [
    {
      "sku": "SKU-001",
      "name": "Test Product 1",
      "barcode": "12345678901",
      "quantity": 5
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
  "message": "Putaway order created successfully for tote TOTE123ABC",
  "order_id": 12345,
  "timestamp": "2025-04-22T15:30:45.123456",
  "items_processed": 2,
  "total_quantity": 8
}
```

### Error Responses

#### Duplicate Tote

**Status Code:** 400 Bad Request

```json
{
  "detail": {
    "status": "error",
    "message": "Tote TOTE123ABC already exists in the system",
    "error_code": "DUPLICATE_TOTE",
    "timestamp": "2025-04-22T15:30:45.123456"
  }
}
```

#### Quantity Exceeded

**Status Code:** 400 Bad Request

```json
{
  "detail": {
    "status": "error",
    "message": "Total quantity exceeds maximum allowed (100,000)",
    "error_code": "QUANTITY_EXCEEDED",
    "timestamp": "2025-04-22T15:30:45.123456"
  }
}
```

#### Insufficient Stock

**Status Code:** 400 Bad Request

```json
{
  "detail": {
    "status": "error",
    "message": "Insufficient stock to fulfill this putaway order",
    "error_code": "INSUFFICIENT_STOCK",
    "timestamp": "2025-04-22T15:30:45.123456"
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
    "message": "Error inserting item with SKU SKU-001",
    "error_code": "ITEM_INSERT_FAILED",
    "timestamp": "2025-04-22T15:30:45.123456"
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
      "loc": ["body", "tote"],
      "msg": "Value error, Tote must start with TOTE followed by up to 15 alphanumeric characters or hyphens",
      "input": "INVALID_TOTE_FORMAT"
    }
  ]
}
```

## Business Logic

1. **Tote Validation**: The tote identifier must start with "TOTE" followed by up to 15 alphanumeric characters or hyphens.
2. **Duplicate Check**: The system checks if the tote already exists in the database.
3. **Quantity Limits**: The system enforces limits on the quantity per item (1-10,000) and total quantity.
4. **Item Validation**: 
   - SKU must contain only letters, numbers, hyphens, and underscores
   - Barcode must be between 8 and 14 digits
   - No duplicate SKUs allowed in a single order
5. **Inventory Check**: The system checks if there is sufficient stock to fulfill the order (placeholder for future functionality).

## Integration Examples

### cURL

```bash
curl -X POST "http://155.138.159.75/api/v1/putawayOrder" \
     -H "Content-Type: application/json" \
     -d '{
       "tote": "TOTE123ABC",
       "items": [
         {
           "sku": "SKU-001",
           "name": "Test Product 1",
           "barcode": "12345678901",
           "quantity": 5
         },
         {
           "sku": "SKU-002",
           "name": "Test Product 2",
           "barcode": "98765432109",
           "quantity": 3
         }
       ]
     }'
```

### Python

```python
import requests

response = requests.post(
    "http://155.138.159.75/api/v1/putawayOrder",
    json={
        "tote": "TOTE123ABC",
        "items": [
            {
                "sku": "SKU-001",
                "name": "Test Product 1",
                "barcode": "12345678901",
                "quantity": 5
            },
            {
                "sku": "SKU-002",
                "name": "Test Product 2",
                "barcode": "98765432109",
                "quantity": 3
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
    "http://155.138.159.75/api/v1/putawayOrder",
    json={
        "tote": "TOTE123ABC",
        "items": [
            {
                "sku": "SKU-001",
                "name": "Test Product 1",
                "barcode": "12345678901",
                "quantity": 5
            }
        ],
        "test_insufficient_stock": True
    }
)
data = response.json()
print(data)
```

## Notes

1. Maximum 50 items are allowed per putaway order.
2. The API performs extensive validation on input data to ensure data integrity.
3. When real inventory checking is implemented, the `test_insufficient_stock` flag will still be available for testing purposes.
4. All timestamps are in ISO 8601 format.
