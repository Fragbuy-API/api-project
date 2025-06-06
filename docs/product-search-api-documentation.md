# Product Search API Documentation

## Overview

The Product Search API allows you to search for products in the Qboid system using a single query term that matches against both SKU and product description fields. The API returns detailed product information including image URLs where available.

## Endpoint

```
POST /api/v1/product_search
```

## Authentication

Currently, the API does not require authentication. This may change in future updates.

## Request Format

The API accepts POST requests with a JSON body. The following parameters are supported:

| Parameter | Type    | Required | Description |
|-----------|---------|----------|-------------|
| query     | string  | Yes      | Search term to match against SKU or description (min length: 1, max length: 255) |
| limit     | integer | No       | Maximum number of results to return (default: 10, range: 1-100) |

## Response Format

The API returns responses in JSON format with the following structure:

```json
{
  "status": "success",
  "message": "Found 5 products matching the search criteria",
  "search_criteria": {
    "query": "Kolnisch",
    "limit": 5
  },
  "count": 5,
  "products": [
    {
      "sku": "4711M-100B",
      "name": "4711 By Echt Kolnisch Wasser 100ml Splash Boxed",
      "weight_value": "0.453",
      "length": "0.00",
      "width": "0.00",
      "height": "0.00",
      "dimension_unit": "cm",
      "weight_unit": "g",
      "created_date_utc": "2016-11-08T03:50:34.0000000Z",
      "pictures": "",
      "photo_url_live": "https://storage.googleapis.com/fragbuyhd/fragbuyphotos/4711.jpg",
      "photo_url_raw": "https://storage.googleapis.com/fragbuyhd/fragbuyphotos/",
      "finalurl": "https://storage.googleapis.com/fragbuyhd/fragbuyphotos/4711.jpg",
      "image_url": "https://storage.googleapis.com/fragbuyhd/fragbuyphotos/4711.jpg",
      "barcode": null
    },
    // Additional products...
  ],
  "timestamp": "2025-05-01T00:36:04.892776"
}
```

### Response Fields

| Field           | Type    | Description |
|-----------------|---------|-------------|
| status          | string  | Status of the request ("success" or "error") |
| message         | string  | Description of the result |
| search_criteria | object  | Echo of the search parameters used |
| count           | integer | Number of products found |
| products        | array   | Array of product objects |
| timestamp       | string  | ISO-format timestamp of when the response was generated |

### Product Object Fields

Each product object in the response contains the following fields (when available in the database):

| Field           | Type    | Description |
|-----------------|---------|-------------|
| sku             | string  | Stock Keeping Unit identifier |
| name            | string  | Product name (mapped from description field) |
| weight_value    | string  | Weight value of the product |
| weight_unit     | string  | Unit of weight measurement (e.g., "g") |
| length          | string  | Length value of the product |
| width           | string  | Width value of the product |
| height          | string  | Height value of the product |
| dimension_unit  | string  | Unit of dimension measurements (e.g., "cm") |
| created_date_utc| string  | Creation date in ISO format |
| pictures        | string  | URL or reference to product pictures |
| photo_url_live  | string  | URL to the live product photo |
| photo_url_raw   | string  | URL to the raw product photo |
| finalurl        | string  | Final URL for the product image |
| image_url       | string  | URL for displaying the product image (matches finalurl) |
| barcode         | string  | Product barcode (if available) |

## Image URL Handling

The `image_url` field in product objects follows these rules:

1. **Source**: The `image_url` field always uses the value from `finalurl` directly.
   
2. **Special Values**: If `finalurl` contains "NA" or any other non-URL value, that value will be used as-is for `image_url`.
   
3. **Empty Values**: If `finalurl` is NULL in the database, `image_url` will not be included in the response.

4. **No Fallback**: The API does not fall back to other image fields (`photo_url_live`, `photo_url_raw`, or `pictures`) when `finalurl` is not available or contains "NA".

## Examples

### Example 1: Basic Search

**Request:**
```json
POST /api/v1/product_search
{
  "query": "Kolnisch",
  "limit": 5
}
```

**Response:**
See the full response format example above.

### Example 2: Search with Default Limit

**Request:**
```json
POST /api/v1/product_search
{
  "query": "4711"
}
```

**Response:**
Similar to Example 1, but with up to 10 results (default limit).

## Error Responses

If an error occurs, the API will return a response with an appropriate HTTP status code and an error message:

### Validation Error - Invalid Query

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "Search query cannot be empty",
      "type": "value_error"
    }
  ]
}
```

### Validation Error - Invalid Limit

**Status Code:** 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["body", "limit"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge",
      "ctx": {
        "limit_value": 1
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
    "timestamp": "2025-05-01T00:36:04.892776"
  }
}
```

## Health Check Endpoint

To verify that the Product Search API is up and running, you can use the health check endpoint:

```
GET /api/v1/product-health
```

This will return a response similar to:

```json
{
  "status": "healthy",
  "message": "Product search API endpoint is available",
  "timestamp": "2025-05-01T00:36:04.881052"
}
```

## Integration Examples

### cURL

```bash
curl -X POST "http://155.138.159.75/api/v1/product_search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Kolnisch",
       "limit": 5
     }'
```

### Python

```python
import requests
import json

url = "http://155.138.159.75/api/v1/product_search"
payload = {
    "query": "Kolnisch",
    "limit": 5
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
fetch('http://155.138.159.75/api/v1/product_search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    "query": "Kolnisch",
    "limit": 5
  }),
})
.then(response => response.json())
.then(data => console.log(data))
.catch((error) => console.error('Error:', error));
```

## Contact

For any issues or questions regarding the Product Search API, please contact the Qboid API support team.