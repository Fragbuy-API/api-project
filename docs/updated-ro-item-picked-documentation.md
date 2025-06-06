# Replenishment Item Picked API Documentation

## Overview

The Update Item Picked API allows you to update the quantity picked for a specific item in a replenishment order, identified by ro_id, sku, and rack_location. This document provides details on how to use the API, expected inputs and outputs, and example requests and responses.

## Endpoint

```
POST /api/v1/ro_item_picked
```

## Request Format

The API accepts POST requests with a JSON body. The following parameters are supported:

| Parameter              | Type    | Required | Description |
|------------------------|---------|----------|-------------|
| ro_id                  | string  | Yes      | Replenishment order identifier |
| sku                    | string  | Yes      | Stock Keeping Unit identifier |
| rack_location          | string  | Yes      | Storage rack location for the item |
| qty_picked             | integer | Yes      | Quantity that has been picked (must be non-negative) |
| note                   | string  | No       | Optional note explaining quantity changes |
| test_insufficient_stock| boolean | No       | Test flag to simulate insufficient stock (default: false) |

### Example Requests

Basic request:
```json
{
  "ro_id": "RO-2025041104",
  "sku": "022548407455",
  "rack_location": "101-201-301",
  "qty_picked": 32
}
```

Request with note:
```json
{
  "ro_id": "RO-2025041104",
  "sku": "022548407455",
  "rack_location": "101-201-301",
  "qty_picked": 32,
  "note": "2 units damaged during picking"
}
```

Request with test flag for inventory simulation:
```json
{
  "ro_id": "RO-2025041104",
  "sku": "022548407455",
  "rack_location": "101-201-301",
  "qty_picked": 32,
  "test_insufficient_stock": true
}
```

## Response Format

### Successful Response

```json
{
  "status": "success",
  "message": "Data Added; RO In Process",
  "ro_id": "RO-2025041104",
  "sku": "022548407455",
  "rack_location": "101-201-301",
  "qty_picked": 32,
  "note": "2 units damaged during picking",
  "timestamp": "2025-04-12T10:25:45.123456"
}
```

The `note` field is only included in the response if it was provided in the request.

### Error Responses

#### Item Not Found

**Status Code:** 404 Not Found

```json
{
  "detail": {
    "status": "error",
    "message": "Item with SKU 022548407455 at location 101-201-301 not found in replenishment order RO-2025041104",
    "error_code": "ITEM_NOT_FOUND",
    "timestamp": "2025-04-12T10:30:15.123456"
  }
}
```

#### Order Already Completed

**Status Code:** 400 Bad Request

```json
{
  "detail": {
    "status": "error",
    "message": "Replenishment order RO-2025041104 is already marked as Completed",
    "error_code": "ORDER_ALREADY_COMPLETED",
    "timestamp": "2025-04-12T10:30:15.123456"
  }
}
```

#### Insufficient Stock

**Status Code:** 400 Bad Request

```json
{
  "detail": {
    "status": "error",
    "message": "Insufficient stock",
    "error_code": "INSUFFICIENT_STOCK",
    "timestamp": "2025-04-12T10:30:15.123456"
  }
}
```

This error can be triggered for testing by setting `test_insufficient_stock: true` in the request.

#### Validation Error

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "qty_picked"],
      "msg": "Value error, Quantity picked cannot be negative",
      "input": -5
    }
  ]
}
```

## Business Logic

1. The endpoint identifies items based on three parameters: ro_id, sku, and rack_location.
2. If the order status is already "Completed", the API will return an error.
3. The API includes a placeholder for checking available inventory. Currently, it always returns sufficient stock unless the test flag is set.
4. When an item is updated, the order status is changed to "In Process" if it was "Unassigned".
5. The note field allows warehouse operators to record reasons for quantity adjustments.
6. A testing flag (`test_insufficient_stock`) is available to simulate inventory shortage scenarios.

## Integration Examples

### cURL

```bash
curl -X POST "http://155.138.159.75/api/v1/ro_item_picked" \
     -H "Content-Type: application/json" \
     -d '{
       "ro_id": "RO-2025041104",
       "sku": "022548407455",
       "rack_location": "101-201-301",
       "qty_picked": 32,
       "note": "2 units damaged during picking"
     }'
```

### Python

```python
import requests

response = requests.post(
    "http://155.138.159.75/api/v1/ro_item_picked",
    json={
        "ro_id": "RO-2025041104",
        "sku": "022548407455",
        "rack_location": "101-201-301",
        "qty_picked": 32,
        "note": "2 units damaged during picking"
    }
)
data = response.json()
print(data)
```

### Testing Insufficient Stock

```python
import requests

response = requests.post(
    "http://155.138.159.75/api/v1/ro_item_picked",
    json={
        "ro_id": "RO-2025041104",
        "sku": "022548407455",
        "rack_location": "101-201-301",
        "qty_picked": 32,
        "test_insufficient_stock": true
    }
)
data = response.json()
print(data)
```

## Notes

1. The `rack_location` field must match the location stored in the replenishment order item.
2. The `note` field is optional and allows for recording reasons for quantity changes.
3. When the real inventory checking system is implemented, the `test_insufficient_stock` flag will still be available for testing purposes.
4. Changes to the order status happen automatically based on the update (Unassigned → In Process).
