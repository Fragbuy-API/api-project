# Replenishment Orders API Documentation

## Overview

The Replenishment Orders API allows you to manage warehouse replenishment workflows in the Qboid system. This document provides comprehensive details on all available endpoints, including request formats, response structures, error handling, and integration examples.

## Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Data Models](#data-models)
3. [Error Handling](#error-handling)
4. [API Endpoints Details](#api-endpoints-details)
   - [Get Replenishment Orders](#1-get-replenishment-orders)
   - [Retrieve Replenishment Order](#2-retrieve-replenishment-order)
   - [Update Item Picked](#3-update-item-picked)
   - [Cancel Picking Process](#4-cancel-picking-process)
   - [Complete Replenishment Order](#5-complete-replenishment-order)
5. [Integration Examples](#integration-examples)

## API Endpoints

| Method | Endpoint                   | Description                                     |
|--------|----------------------------|-------------------------------------------------|
| GET    | `/api/v1/ro_get_orders`    | Get all active replenishment orders             |
| POST   | `/api/v1/ro_retrieve_order`| Get details of a specific replenishment order   |
| POST   | `/api/v1/ro_item_picked`   | Update quantity picked for an item              |
| POST   | `/api/v1/ro_pick_cancelled`| Cancel picking process and reset order status   |
| POST   | `/api/v1/ro_complete`      | Mark a replenishment order as completed         |
| GET    | `/api/v1/replenishment-health` | API health check endpoint                   |

## Data Models

### Replenishment Order Status Values

| Status       | Description                                        |
|--------------|----------------------------------------------------|
| `Unassigned` | Initial status when order is created               |
| `In Process` | Order is being picked                              |
| `Completed`  | All items have been picked and order is complete   |

### Database Tables

The API utilizes three main tables in the database:

1. **replen_orders** - Main orders table
   - `ro_id` - Unique identifier for replenishment orders
   - `ro_date_created` - Order creation timestamp
   - `ro_status` - Current status (Unassigned, In Process, Completed)
   - `destination` - Staging or Bulk Order Workstation

2. **replen_order_items** - Items within orders
   - `id` - Unique identifier for items
   - `ro_id` - Reference to parent order
   - `sku` - Stock Keeping Unit
   - `description` - Product description
   - `qty` - Total quantity to pick
   - `qty_picked` - Quantity that has been picked
   - `created_at` - Creation timestamp

3. **storage_locations** - SKU locations in the warehouse
   - `rack_location` - Location identifier (format: XXX-XXX-XXX)
   - `sku` - Stock Keeping Unit

## Error Handling

The API uses standard HTTP status codes to indicate success or failure:

| Status Code | Description                                         |
|-------------|-----------------------------------------------------|
| 200         | Success                                             |
| 400         | Bad Request (invalid input or business rule violation) |
| 404         | Resource Not Found                                  |
| 422         | Validation Error (invalid data format)              |
| 500         | Server Error                                        |

Error responses follow this structure:

```json
{
  "detail": {
    "status": "error",
    "message": "Detailed error description",
    "error_code": "ERROR_CODE",
    "timestamp": "2025-04-12T10:30:15.123456"
  }
}
```

Validation errors (422) have a slightly different format showing field-specific errors:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "field_name"],
      "msg": "Error message",
      "input": "invalid_value"
    }
  ]
}
```

## API Endpoints Details

### 1. Get Replenishment Orders

Retrieves all active replenishment orders (status not "Completed").

#### Endpoint

```
GET /api/v1/ro_get_orders
```

#### Request Format

This endpoint doesn't require any request parameters.

#### Response Format

```json
{
  "status": "success",
  "message": "Found 3 active replenishment orders",
  "orders": [
    {
      "ro_id": "RO-2025041104",
      "ro_date_created": "2025-04-11T23:07:44",
      "ro_status": "Unassigned",
      "destination": "Bulk Order Workstation",
      "skus_in_order": 6
    },
    {
      "ro_id": "RO-2025041103",
      "ro_date_created": "2025-04-10T23:07:44",
      "ro_status": "In Process",
      "destination": "Staging",
      "skus_in_order": 7
    }
  ],
  "count": 2,
  "timestamp": "2025-04-12T10:15:30.123456"
}
```

#### Response Fields

| Field           | Type    | Description |
|-----------------|---------|-------------|
| ro_id           | string  | Replenishment order identifier |
| ro_date_created | string  | ISO-format timestamp of when the order was created |
| ro_status       | string  | Current status of the order (Unassigned, In Process) |
| destination     | string  | Destination for picked items (Staging or Bulk Order Workstation) |
| skus_in_order   | integer | Number of different SKUs in this replenishment order |

### 2. Retrieve Replenishment Order

Retrieves detailed information about a specific replenishment order, including all items.
If the order's status is "Unassigned", it will be changed to "In Process".

#### Endpoint

```
POST /api/v1/ro_retrieve_order
```

#### Request Format

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| ro_id     | string | Yes      | Replenishment order identifier |

Example request:
```json
{
  "ro_id": "RO-2025041104"
}
```

#### Response Format

```json
{
  "status": "success",
  "message": "Successfully retrieved replenishment order RO-2025041104. Status changed from Unassigned to In Process",
  "order": {
    "ro_id": "RO-2025041104",
    "ro_date_created": "2025-04-11T23:07:44",
    "ro_status": "In Process",
    "destination": "Bulk Order Workstation",
    "items": [
      {
        "id": 4,
        "sku": "022548407455",
        "description": "Decant - Tory Burch W 7.5ml Unboxed Spray",
        "qty": 65,
        "qty_picked": 32,
        "created_at": "2025-04-11T23:08:59",
        "rack_location": "101-201-301"
      },
      {
        "id": 5,
        "sku": "085715564009",
        "description": "Oscar De La Renta Bella Blanca edp W 100ml Spray Boxed",
        "qty": 28,
        "qty_picked": 0,
        "created_at": "2025-04-11T23:08:59",
        "rack_location": "101-201-302"
      }
    ],
    "item_count": 2
  },
  "status_changed": true,
  "timestamp": "2025-04-12T10:20:30.123456"
}
```

#### Response Fields

Order object:

| Field           | Type    | Description |
|-----------------|---------|-------------|
| ro_id           | string  | Replenishment order identifier |
| ro_date_created | string  | ISO-format timestamp of when the order was created |
| ro_status       | string  | Current status of the order |
| destination     | string  | Destination for picked items |
| items           | array   | Array of items in this replenishment order |
| item_count      | integer | Total number of items in the order |

Item objects:

| Field         | Type    | Description |
|---------------|---------|-------------|
| id            | integer | Unique identifier for this item record |
| sku           | string  | Stock Keeping Unit identifier |
| description   | string  | Product description |
| qty           | integer | Quantity requested |
| qty_picked    | integer | Quantity that has been picked |
| created_at    | string  | ISO-format timestamp of when the item was added |
| rack_location | string  | Storage location for this SKU |

### 3. Update Item Picked

Updates the quantity picked for a specific item in a replenishment order, identified by ro_id, sku, and rack_location.

#### Endpoint

```
POST /api/v1/ro_item_picked
```

#### Request Format

| Parameter     | Type    | Required | Description |
|---------------|---------|----------|-------------|
| ro_id         | string  | Yes      | Replenishment order identifier |
| sku           | string  | Yes      | Stock Keeping Unit identifier |
| rack_location | string  | Yes      | Storage rack location for the item |
| qty_picked    | integer | Yes      | Quantity that has been picked (must be non-negative) |
| note          | string  | No       | Optional note explaining quantity changes |

Example request:
```json
{
  "ro_id": "RO-2025041104",
  "sku": "022548407455",
  "rack_location": "101-201-301",
  "qty_picked": 32,
  "note": "2 units damaged during picking"
}
```

#### Response Format

If the order is still in process:

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

If all items have been picked and the order is now complete:

```json
{
  "status": "success",
  "message": "Data Added; RO Complete",
  "ro_id": "RO-2025041104",
  "sku": "022548407455",
  "rack_location": "101-201-301",
  "qty_picked": 65,
  "note": "Last items picked from top shelf",
  "timestamp": "2025-04-12T10:25:45.123456"
}
```

The `message` field indicates whether the order is still in process or if it has been completed.

#### Business Logic

1. If the order status is already "Completed", the API will return an error.
2. If the requested SKU doesn't exist in the specified order, the API will return an error.
3. When an item is updated, the order status is changed to "In Process" if it was "Unassigned".
4. If all items in the order have been picked (qty_picked > 0), the order status is automatically changed to "Completed".
5. Future versions will check inventory levels to ensure sufficient stock is available.
6. Future versions will integrate with SkuVault to update inventory locations.

### 4. Cancel Picking Process

Cancels the picking process for a replenishment order, changing its status from "In Process" back to "Unassigned" and resetting all qty_picked values to 0.

#### Endpoint

```
POST /api/v1/ro_pick_cancelled
```

#### Request Format

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| ro_id     | string | Yes      | Replenishment order identifier |

Example request:
```json
{
  "ro_id": "RO-2025041103"
}
```

#### Response Format

```json
{
  "status": "success",
  "message": "Replenishment order RO-2025041103 has been reset to Unassigned status",
  "ro_id": "RO-2025041103",
  "previous_status": "In Process",
  "new_status": "Unassigned",
  "timestamp": "2025-04-12T11:15:30.123456"
}
```

#### Business Logic

1. Only orders with status "In Process" can be cancelled.
2. When an order is cancelled, all qty_picked values are reset to 0.
3. The order status is changed from "In Process" to "Unassigned".

### 5. Complete Replenishment Order

Explicitly marks a replenishment order as completed after user confirmation.

#### Endpoint

```
POST /api/v1/ro_complete
```

#### Request Format

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| ro_id     | string | Yes      | Replenishment order identifier |

Example request:
```json
{
  "ro_id": "RO-2025041104"
}
```

#### Response Format

If the order is successfully completed:

```json
{
  "status": "success",
  "message": "Replenishment order RO-2025041104 has been marked as Completed",
  "ro_id": "RO-2025041104",
  "previous_status": "In Process",
  "new_status": "Completed",
  "timestamp": "2025-04-12T11:25:45.123456"
}
```

If the order is already completed:

```json
{
  "status": "success",
  "message": "Replenishment order RO-2025041104 is already marked as Completed",
  "ro_id": "RO-2025041104",
  "timestamp": "2025-04-12T11:25:45.123456"
}
```

If not all items have been picked:

```json
{
  "status": "warning",
  "message": "Not all items have been picked for order RO-2025041104. 3 of 6 items have been picked.",
  "ro_id": "RO-2025041104",
  "timestamp": "2025-04-12T11:25:45.123456"
}
```

#### Business Logic

1. The endpoint checks if all items have been picked. If not, it returns a warning but doesn't change the status.
2. If the order is already completed, it returns a success message without making changes.
3. Otherwise, it changes the order status to "Completed".

## Integration Examples

### cURL Examples

#### Get Replenishment Orders
```bash
curl -X GET "http://155.138.159.75/api/v1/ro_get_orders"
```

#### Retrieve Specific Order
```bash
curl -X POST "http://155.138.159.75/api/v1/ro_retrieve_order" \
     -H "Content-Type: application/json" \
     -d '{"ro_id": "RO-2025041104"}'
```

#### Update Item Picked
```bash
curl -X POST "http://155.138.159.75/api/v1/ro_item_picked" \
     -H "Content-Type: application/json" \
     -d '{
       "ro_id": "RO-2025041104",
       "sku": "022548407455",
       "qty_picked": 32
     }'
```

#### Cancel Picking Process
```bash
curl -X POST "http://155.138.159.75/api/v1/ro_pick_cancelled" \
     -H "Content-Type: application/json" \
     -d '{"ro_id": "RO-2025041103"}'
```

#### Complete Order
```bash
curl -X POST "http://155.138.159.75/api/v1/ro_complete" \
     -H "Content-Type: application/json" \
     -d '{"ro_id": "RO-2025041104"}'
```

### Python Examples

```python
import requests
import json

base_url = "http://155.138.159.75/api/v1"

# Get active replenishment orders
def get_orders():
    response = requests.get(f"{base_url}/ro_get_orders")
    return response.json()

# Retrieve specific replenishment order
def get_order_details(ro_id):
    response = requests.post(
        f"{base_url}/ro_retrieve_order",
        json={"ro_id": ro_id}
    )
    return response.json()

# Update item picked
def update_item_picked(ro_id, sku, qty_picked):
    response = requests.post(
        f"{base_url}/ro_item_picked",
        json={
            "ro_id": ro_id,
            "sku": sku,
            "qty_picked": qty_picked
        }
    )
    return response.json()

# Cancel picking process
def cancel_picking(ro_id):
    response = requests.post(
        f"{base_url}/ro_pick_cancelled",
        json={"ro_id": ro_id}
    )
    return response.json()

# Complete order
def complete_order(ro_id):
    response = requests.post(
        f"{base_url}/ro_complete",
        json={"ro_id": ro_id}
    )
    return response.json()

# Example usage
orders = get_orders()
print(f"Found {orders['count']} active orders")

if orders['count'] > 0:
    # Get details of the first order
    first_order_id = orders['orders'][0]['ro_id']
    order_details = get_order_details(first_order_id)
    
    # Update an item in the order
    if order_details['order']['items']:
        first_item = order_details['order']['items'][0]
        update_result = update_item_picked(
            first_order_id,
            first_item['sku'],
            first_item['qty']  # Pick all
        )
        print(f"Update result: {update_result['message']}")
```

### JavaScript Examples

```javascript
const baseUrl = 'http://155.138.159.75/api/v1';

// Get active replenishment orders
async function getOrders() {
  const response = await fetch(`${baseUrl}/ro_get_orders`);
  return await response.json();
}

// Retrieve specific replenishment order
async function getOrderDetails(roId) {
  const response = await fetch(`${baseUrl}/ro_retrieve_order`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ro_id: roId })
  });
  return await response.json();
}

// Update item picked
async function updateItemPicked(roId, sku, qtyPicked) {
  const response = await fetch(`${baseUrl}/ro_item_picked`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ro_id: roId,
      sku: sku,
      qty_picked: qtyPicked
    })
  });
  return await response.json();
}

// Cancel picking process
async function cancelPicking(roId) {
  const response = await fetch(`${baseUrl}/ro_pick_cancelled`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ro_id: roId })
  });
  return await response.json();
}

// Complete order
async function completeOrder(roId) {
  const response = await fetch(`${baseUrl}/ro_complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ro_id: roId })
  });
  return await response.json();
}

// Example usage
async function example() {
  try {
    const orders = await getOrders();
    console.log(`Found ${orders.count} active orders`);
    
    if (orders.count > 0) {
      // Get details of the first order
      const firstOrderId = orders.orders[0].ro_id;
      const orderDetails = await getOrderDetails(firstOrderId);
      
      // Update an item in the order
      if (orderDetails.order.items.length > 0) {
        const firstItem = orderDetails.order.items[0];
        const updateResult = await updateItemPicked(
          firstOrderId,
          firstItem.sku,
          firstItem.qty  // Pick all
        );
        console.log(`Update result: ${updateResult.message}`);
      }
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

example();
```

## Health Check Endpoint

To verify that the Replenishment API is up and running, you can use the health check endpoint:

```
GET /api/v1/replenishment-health
```

This will return a response similar to:

```json
{
  "status": "healthy",
  "message": "Replenishment API endpoints are available",
  "timestamp": "2025-04-12T10:40:25.123456"
}
```

## Contact

For any issues or questions regarding the Replenishment API, please contact the Qboid API support team.
