# ProShip Integration API Documentation

## Overview

The ProShip Integration API provides integration points between the Qboid system and ProShip's shipping software. This document provides details on how to use the API, expected inputs and outputs, and integration examples.

## Endpoints

### Update Parent Orders

```
POST /api/v1/update_parent_orders
```

This endpoint updates parent order relationships in the Qboid system. It accepts a list of order ID and parent order ID pairs, and updates the database to set the parent order ID for each specified order.

#### Request Format

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| items     | array  | Yes      | Array of order items to update |

Each item in the `items` array must have the following structure:

| Parameter     | Type   | Required | Description |
|---------------|--------|----------|-------------|
| orderId       | string | Yes      | The order ID to update |
| parentOrderId | string | Yes      | The parent order ID to set |

Example request:
```json
{
  "items": [
    {
      "orderId": "1288592238",
      "parentOrderId": "1288590000"
    },
    {
      "orderId": "1288592239",
      "parentOrderId": "1288590000"
    }
  ]
}
```

#### Response Format

The API returns a JSON response with the following structure:

```json
{
  "status": "success",
  "message": "Updated 2 orders, 0 failed",
  "updatedCount": 2,
  "failedCount": 0,
  "failedOrders": [],
  "timestamp": "2025-05-15T14:30:25.123456"
}
```

The response fields are as follows:

| Field        | Type    | Description |
|--------------|---------|-------------|
| status       | string  | Status of the request ("success", "partial_success", or "error") |
| message      | string  | Summary message about the operation |
| updatedCount | integer | Number of orders successfully updated |
| failedCount  | integer | Number of orders that failed to update |
| failedOrders | array   | Details about any orders that failed to update |
| timestamp    | string  | ISO-format timestamp of when the response was generated |

If any orders fail to update, the `failedOrders` array will contain objects with the following structure:

```json
{
  "orderId": "1288592240",
  "reason": "Order not found"
}
```

#### Error Responses

If an error occurs, the API will return a response with an appropriate HTTP status code and an error message:

##### Validation Error - Empty Items Array

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "items"],
      "msg": "ensure this value has at least 1 items",
      "input": []
    }
  ]
}
```

##### Validation Error - Missing Required Field

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "value_error.missing",
      "loc": ["body", "items", 0, "parentOrderId"],
      "msg": "field required",
      "input": {"orderId": "1288592238"}
    }
  ]
}
```

##### Server Error

**Status Code:** 500 Internal Server Error

```json
{
  "detail": {
    "status": "error",
    "message": "Server error: [error message]",
    "error_code": "SERVER_ERROR",
    "timestamp": "2025-05-15T14:55:40.987654"
  }
}
```

### Check Order Cancelled

```
POST /api/v1/order_cancelled
```

This endpoint checks if an order is cancelled in the Qboid system. It accepts an order ID and returns a boolean value indicating whether the order status is "cancelled".

#### Request Format

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| orderId   | string | Yes      | The order ID to check |

Example request:
```json
{
  "orderId": "1288592238"
}
```

#### Response Format

The API returns a JSON response with the following structure:

```json
{
  "status": "success",
  "orderId": "1288592238",
  "isCancelled": false,
  "orderStatus": "shipped",
  "timestamp": "2025-05-15T14:35:12.654321"
}
```

The response fields are as follows:

| Field       | Type    | Description |
|-------------|---------|-------------|
| status      | string  | Status of the request ("success" or "error") |
| orderId     | string  | The order ID that was checked |
| isCancelled | boolean | TRUE if the order status is "cancelled", FALSE otherwise |
| orderStatus | string  | The current status of the order |
| timestamp   | string  | ISO-format timestamp of when the response was generated |

#### Error Responses

If an error occurs, the API will return a response with an appropriate HTTP status code and an error message:

##### Order Not Found

**Status Code:** 404 Not Found

```json
{
  "detail": {
    "status": "error",
    "message": "Order NONEXISTENT-ORDER not found",
    "error_code": "ORDER_NOT_FOUND",
    "timestamp": "2025-05-15T14:40:18.987654"
  }
}
```

##### Validation Error - Empty Order ID

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "orderId"],
      "msg": "Value error, Order ID cannot be empty",
      "input": ""
    }
  ]
}
```

##### Server Error

**Status Code:** 500 Internal Server Error

```json
{
  "detail": {
    "status": "error",
    "message": "Server error: [error message]",
    "error_code": "SERVER_ERROR",
    "timestamp": "2025-05-15T14:55:40.987654"
  }
}
```

### Health Check

```
GET /api/v1/proship-health
```

This endpoint verifies that the ProShip Integration API is available and functioning correctly.

#### Response Format

```json
{
  "status": "healthy",
  "message": "ProShip integration API endpoints are available",
  "timestamp": "2025-05-15T15:00:00.123456"
}
```

## Integration Examples

### Update Parent Orders

#### cURL

```bash
curl -X POST "http://155.138.159.75/api/v1/update_parent_orders" \
     -H "Content-Type: application/json" \
     -d '{
       "items": [
         {
           "orderId": "1288592238",
           "parentOrderId": "1288590000"
         },
         {
           "orderId": "1288592239",
           "parentOrderId": "1288590000"
         }
       ]
     }'
```

#### Python

```python
import requests
import json

url = "http://155.138.159.75/api/v1/update_parent_orders"
payload = {
  "items": [
    {
      "orderId": "1288592238",
      "parentOrderId": "1288590000"
    },
    {
      "orderId": "1288592239",
      "parentOrderId": "1288590000"
    }
  ]
}
headers = {
  "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()

print(json.dumps(data, indent=2))
```

#### JavaScript

```javascript
fetch('http://155.138.159.75/api/v1/update_parent_orders', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    "items": [
      {
        "orderId": "1288592238",
        "parentOrderId": "1288590000"
      },
      {
        "orderId": "1288592239",
        "parentOrderId": "1288590000"
      }
    ]
  }),
})
.then(response => response.json())
.then(data => console.log(data))
.catch((error) => console.error('Error:', error));
```

### Check Order Cancelled

#### cURL

```bash
curl -X POST "http://155.138.159.75/api/v1/order_cancelled" \
     -H "Content-Type: application/json" \
     -d '{
       "orderId": "1288592238"
     }'
```

#### Python

```python
import requests
import json

url = "http://155.138.159.75/api/v1/order_cancelled"
payload = {
  "orderId": "1288592238"
}
headers = {
  "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()

print(json.dumps(data, indent=2))
```

#### JavaScript

```javascript
fetch('http://155.138.159.75/api/v1/order_cancelled', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    "orderId": "1288592238"
  }),
})
.then(response => response.json())
.then(data => console.log(data))
.catch((error) => console.error('Error:', error));
```

## Notes

1. The API performs an exact match on the order IDs.
2. If an order ID does not exist in the database, it will be reported as a failed update but will not cause the entire operation to fail.
3. The `order_cancelled` endpoint returns a simple boolean response indicating whether the order status is "cancelled".

## Contact

For any issues or questions regarding the ProShip Integration API, please contact the Qboid API support team.
