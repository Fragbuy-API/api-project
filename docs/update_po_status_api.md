# Update PO Status API Documentation

## Overview

The Update PO Status API allows you to change the status of a purchase order to one of four valid states. This document provides details on how to use the API, expected inputs and outputs, and example requests and responses.

## Endpoint

```
POST /api/v1/update_po_status
```

## Authentication

Currently, the API does not require authentication. This may change in future updates.

## Request Format

The API accepts POST requests with a JSON body. The following parameters are required:

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| po_number | string | Yes      | Purchase order number (exact match, max 50 characters) |
| status    | string | Yes      | New status of the purchase order (see valid values below) |

### Valid Status Values

The API accepts exactly four status values:

| Status Value        | Description |
|--------------------|-------------|
| `"NoneReceived"`   | No items have been received yet |
| `"PartiallyReceived"` | Some but not all items have been received |
| `"Completed"`      | All items have been received and order is complete |
| `"Cancelled"`      | Order has been cancelled and will not be received |

## Response Format

The API returns responses in JSON format with the following structure:

```json
{
  "status": "success",
  "message": "Purchase order PO12345 status updated to Completed",
  "po_number": "PO12345",
  "new_status": "Completed",
  "timestamp": "2025-06-06T15:23:45.123456",
  "partner_api_notification": {
    "success": true,
    "timestamp": "2025-06-06T15:23:45.123456"
  }
}
```

The response fields are as follows:

| Field                    | Type    | Description |
|--------------------------|---------|-------------|
| status                   | string  | Status of the request ("success" or "error") |
| message                  | string  | Description of the result |
| po_number                | string  | The purchase order number from the request |
| new_status               | string  | The updated status value |
| timestamp                | string  | ISO-format timestamp of when the response was generated |
| partner_api_notification | object  | (Only included when status is "Completed") Information about the notification sent to the partner API |

## Examples

### Example 1: Set Purchase Order Status to Completed

**Request:**
```json
POST /api/v1/update_po_status
{
  "po_number": "PO-TEST-001",
  "status": "Completed"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Purchase order PO-TEST-001 status updated to Completed",
  "po_number": "PO-TEST-001",
  "new_status": "Completed",
  "timestamp": "2025-06-06T15:23:45.123456",
  "partner_api_notification": {
    "success": true,
    "timestamp": "2025-06-06T15:23:45.123456"
  }
}
```

### Example 2: Set Purchase Order Status to PartiallyReceived

**Request:**
```json
POST /api/v1/update_po_status
{
  "po_number": "PO-TEST-002",
  "status": "PartiallyReceived"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Purchase order PO-TEST-002 status updated to PartiallyReceived",
  "po_number": "PO-TEST-002",
  "new_status": "PartiallyReceived",
  "timestamp": "2025-06-06T15:23:45.123456"
}
```

### Example 3: Set Purchase Order Status to Cancelled

**Request:**
```json
POST /api/v1/update_po_status
{
  "po_number": "PO-TEST-003",
  "status": "Cancelled"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Purchase order PO-TEST-003 status updated to Cancelled",
  "po_number": "PO-TEST-003",
  "new_status": "Cancelled",
  "timestamp": "2025-06-06T15:23:45.123456"
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
    "message": "Purchase order NONEXISTENT-PO not found in the system",
    "error_code": "PO_NOT_FOUND",
    "timestamp": "2025-06-06T15:23:45.123456"
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
      "loc": ["body", "status"],
      "msg": "Field required",
      "input": {"po_number": "PO-TEST-001"}
    }
  ]
}
```

### Validation Error - Invalid Status Value

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "status"],
      "msg": "Input should be 'NoneReceived', 'PartiallyReceived', 'Completed' or 'Cancelled'",
      "input": "invalid-status",
      "ctx": {
        "expected": "'NoneReceived', 'PartiallyReceived', 'Completed' or 'Cancelled'"
      }
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
      "msg": "PO number cannot be empty",
      "input": ""
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
    "timestamp": "2025-06-06T15:23:45.123456"
  }
}
```

## Business Logic Notes

1. **Exact Match**: The API performs an exact match on the purchase order number.
2. **Partner API Notification**: When status is set to "Completed", a notification is automatically sent to the partner API (currently a placeholder implementation).
3. **Status Validation**: Only the four specified status values are accepted. The validation is enforced at the Pydantic model level.
4. **Search Exclusion**: Purchase orders with "Completed" or "Cancelled" status are excluded from search results in other API endpoints.
5. **No Automatic Transitions**: Status changes are entirely user-controlled through this endpoint - the system does not automatically change statuses based on business logic.

## Integration Examples

### cURL

```bash
curl -X POST \
  http://155.138.159.75/api/v1/update_po_status \
  -H 'Content-Type: application/json' \
  -d '{
    "po_number": "PO-TEST-001",
    "status": "Completed"
}'
```

### Python

```python
import requests
import json

url = "http://155.138.159.75/api/v1/update_po_status"
payload = {
    "po_number": "PO-TEST-001",
    "status": "Completed"
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
fetch('http://155.138.159.75/api/v1/update_po_status', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    "po_number": "PO-TEST-001",
    "status": "Completed"
  }),
})
.then(response => response.json())
.then(data => console.log(data))
.catch((error) => console.error('Error:', error));
```

## Workflow Integration

### Typical Status Flow

A common workflow might follow this pattern:

1. **NoneReceived** → Initial state when PO is created but no items received
2. **PartiallyReceived** → When some but not all items are received  
3. **Completed** → When all items are received and PO is finalized
4. **Cancelled** → When PO is cancelled and will not be received

However, the API allows flexible status updates and does not enforce any particular workflow sequence.

## Testing

The API includes comprehensive test coverage in `tests/test_update_po_status.py` with the following test scenarios:

- ✅ Valid status updates for all four status values
- ✅ Non-existent purchase order handling
- ✅ Missing required field validation
- ✅ Invalid status value validation
- ✅ Partner API notification verification (for "Completed" status)

## Contact

For any issues or questions regarding the Update PO Status API, please contact the Qboid API support team.

---

**Last Updated:** June 6, 2025  
**API Version:** v1  
**Document Version:** 3.0 (Updated to match SkuVault status values)
