# Purchase Orders API Documentation

## Overview

The Purchase Orders API allows you to search for purchase orders in the Qboid system by either a purchase order number or product barcode(s). This document provides details on how to use the API, expected inputs and outputs, and example requests and responses.

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
| po_number | string              | No*      | Purchase order number (can be partial) |
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
      "po_number": "PO12345",
      "status": "Pending",
      "supplier_name": "Supplier XYZ",
      "created_date": "2025-03-01",
      "order_date": "2025-03-02",
      "arrival_due_date": "2025-03-15",
      "ship_to_warehouse": "Warehouse A"
    },
    // Additional purchase orders...
  ],
  "count": 2,
  "timestamp": "2025-03-14T15:23:45.123456"
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

### Example 1: Search by Purchase Order Number

**Request:**
```json
POST /api/v1/find_purchase_order
{
  "po_number": "PO2025"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Found 2 matching purchase orders",
  "results": [
    {
      "po_number": "PO2025-001",
      "status": "In Transit",
      "supplier_name": "Acme Inc.",
      "created_date": "2025-03-01",
      "order_date": "2025-03-02",
      "arrival_due_date": "2025-03-20",
      "ship_to_warehouse": "Central Warehouse"
    },
    {
      "po_number": "PO2025-002",
      "status": "Pending",
      "supplier_name": "Global Suppliers",
      "created_date": "2025-03-05",
      "order_date": "2025-03-06",
      "arrival_due_date": "2025-03-25",
      "ship_to_warehouse": "East Warehouse"
    }
  ],
  "count": 2,
  "timestamp": "2025-03-14T15:23:45.123456"
}
```

### Example 2: Search by Single Barcode

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
      "po_number": "PO2025-003",
      "status": "Processing",
      "supplier_name": "Best Products Ltd.",
      "created_date": "2025-03-10",
      "order_date": "2025-03-11",
      "arrival_due_date": "2025-03-30",
      "ship_to_warehouse": "West Warehouse"
    }
  ],
  "count": 1,
  "timestamp": "2025-03-14T15:23:45.123456"
}
```

### Example 3: Search by Multiple Barcodes

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
      "po_number": "PO2025-003",
      "status": "Processing",
      "supplier_name": "Best Products Ltd.",
      "created_date": "2025-03-10",
      "order_date": "2025-03-11",
      "arrival_due_date": "2025-03-30",
      "ship_to_warehouse": "West Warehouse"
    }
  ],
  "count": 1,
  "timestamp": "2025-03-14T15:23:45.123456"
}
```

### Example 4: No Results Found

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
  "timestamp": "2025-03-14T15:23:45.123456"
}
```