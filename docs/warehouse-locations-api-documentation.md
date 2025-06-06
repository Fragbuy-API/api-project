# Warehouse Locations API Documentation

## Overview

The Warehouse Locations API allows you to retrieve warehouse location data from the Qboid system. This document provides details on how to use the API, expected outputs, and integration examples.

## Endpoint

```
GET /api/v1/warehouse_locations
```

## Authentication

Currently, the API does not require authentication. This may change in future updates.

## Request Format

The API accepts GET requests with optional query parameters for filtering:

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| warehouse | string | No       | Filter locations by warehouse identifier |

## Response Format

The API returns responses in JSON format with the following structure:

```json
{
  "status": "success",
  "message": "Found 8 warehouse locations",
  "count": 8,
  "locations": [
    {
      "warehouse": "DON",
      "location_code": "1HAI",
      "location_name": "HAI"
    },
    {
      "warehouse": "DON",
      "location_code": "2STORAGE",
      "location_name": "Storage"
    },
    // Additional locations...
  ],
  "timestamp": "2025-04-24T15:23:45.123456"
}
```

The response fields are as follows:

| Field      | Type    | Description |
|------------|---------|-------------|
| status     | string  | Status of the request ("success" or "error") |
| message    | string  | Description of the result |
| count      | integer | Total number of locations returned |
| locations  | array   | Array of location objects |
| timestamp  | string  | ISO-format timestamp of when the response was generated |

Each location object has the following fields:

| Field         | Type   | Description |
|---------------|--------|-------------|
| warehouse     | string | Warehouse identifier |
| location_code | string | Code for this location within the warehouse |
| location_name | string | Human-readable name for this location |

## Examples

### Example 1: Get All Warehouse Locations

**Request:**
```
GET /api/v1/warehouse_locations
```

**Response:**
```json
{
  "status": "success",
  "message": "Found 8 warehouse locations",
  "count": 8,
  "locations": [
    {
      "warehouse": "AGP23",
      "location_code": "GENERAL",
      "location_name": "General"
    },
    {
      "warehouse": "AGP23",
      "location_code": "PRESOLDRESERVE",
      "location_name": "Presold Reserve"
    },
    {
      "warehouse": "DON",
      "location_code": "1HAI",
      "location_name": "HAI"
    },
    {
      "warehouse": "DON",
      "location_code": "2STORAGE",
      "location_name": "Storage"
    },
    {
      "warehouse": "DON",
      "location_code": "3SHOWROOM",
      "location_name": "Showroom"
    },
    {
      "warehouse": "DON",
      "location_code": "4STAGING",
      "location_name": "Staging"
    },
    {
      "warehouse": "DON",
      "location_code": "5RESERVE",
      "location_name": "Reserve"
    },
    {
      "warehouse": "DUBAI",
      "location_code": "TEMP",
      "location_name": "Temporary"
    }
  ],
  "timestamp": "2025-04-24T15:23:45.123456"
}
```

### Example 2: Filter Locations by Warehouse

**Request:**
```
GET /api/v1/warehouse_locations?warehouse=DON
```

**Response:**
```json
{
  "status": "success",
  "message": "Found 5 warehouse locations",
  "count": 5,
  "locations": [
    {
      "warehouse": "DON",
      "location_code": "1HAI",
      "location_name": "HAI"
    },
    {
      "warehouse": "DON",
      "location_code": "2STORAGE",
      "location_name": "Storage"
    },
    {
      "warehouse": "DON",
      "location_code": "3SHOWROOM",
      "location_name": "Showroom"
    },
    {
      "warehouse": "DON",
      "location_code": "4STAGING",
      "location_name": "Staging"
    },
    {
      "warehouse": "DON",
      "location_code": "5RESERVE",
      "location_name": "Reserve"
    }
  ],
  "timestamp": "2025-04-24T15:23:45.123456"
}
```

### Example 3: No Results Found

**Request:**
```
GET /api/v1/warehouse_locations?warehouse=NONEXISTENT
```

**Response:**
```json
{
  "status": "success",
  "message": "No warehouse locations found",
  "count": 0,
  "locations": [],
  "timestamp": "2025-04-24T15:23:45.123456"
}
```

## Error Responses

If an error occurs, the API will return a response with an appropriate HTTP status code and an error message:

### Server Error

**Status Code:** 500 Internal Server Error

```json
{
  "detail": {
    "status": "error",
    "message": "Server error: [error message]",
    "error_code": "SERVER_ERROR",
    "timestamp": "2025-04-24T15:23:45.123456"
  }
}
```

## Integration Examples

### cURL

```bash
# Get all warehouse locations
curl -X GET "http://155.138.159.75/api/v1/warehouse_locations"

# Filter by warehouse
curl -X GET "http://155.138.159.75/api/v1/warehouse_locations?warehouse=DON"
```

### Python

```python
import requests
import json

# Get all warehouse locations
response = requests.get("http://155.138.159.75/api/v1/warehouse_locations")
data = response.json()
print(json.dumps(data, indent=2))

# Filter by warehouse
response = requests.get("http://155.138.159.75/api/v1/warehouse_locations", params={"warehouse": "DON"})
data = response.json()
print(json.dumps(data, indent=2))
```

### JavaScript

```javascript
// Get all warehouse locations
fetch('http://155.138.159.75/api/v1/warehouse_locations')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));

// Filter by warehouse
fetch('http://155.138.159.75/api/v1/warehouse_locations?warehouse=DON')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

## Health Check Endpoint

To verify that the Warehouse Locations API is up and running, you can use the health check endpoint:

```
GET /api/v1/warehouse-locations-health
```

This will return a response similar to:

```json
{
  "status": "healthy",
  "message": "Warehouse locations API endpoint is available",
  "timestamp": "2025-04-24T15:23:45.123456"
}
```

## Contact

For any issues or questions regarding the Warehouse Locations API, please contact the Qboid API support team.
