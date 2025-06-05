# Qboid API Error Handling Review

## Summary
This table documents all error handling patterns across the Qboid API codebase, including HTTP status codes, error messages, and triggering circumstances.

| File | HTTP Status | Error Message | Trigger Circumstances | Error Code |
|------|-------------|---------------|----------------------|------------|
| **routers/measurements.py** |
| routers/measurements.py | 500 | str(e) | Any unhandled exception during measurement processing | - |
| **routers/barcode.py** |
| routers/barcode.py | 404 | "Barcode {barcode} not found in the system" | Barcode lookup fails - barcode doesn't exist in barcodes table | BARCODE_NOT_FOUND |
| routers/barcode.py | 400 | "Barcode {barcode} already exists in the system for SKU {sku}" | Adding new barcode when barcode already exists | DUPLICATE_BARCODE |
| routers/barcode.py | 400 | "SKU {sku} does not exist in the products table. Cannot add barcode." | Adding barcode for SKU that doesn't exist in products table | INVALID_SKU |
| routers/barcode.py | 500 | "Server error: {error_msg}" | Any unhandled exception in barcode operations | SERVER_ERROR |
| **routers/purchase_orders.py** |
| routers/purchase_orders.py | 404 | "Barcode {barcode} not found in the system" | Barcode lookup fails during PO search | BARCODE_NOT_FOUND |
| routers/purchase_orders.py | 404 | "Purchase order {po_number} not found in the system" | PO update/check when PO doesn't exist | PO_NOT_FOUND |
| routers/purchase_orders.py | 500 | "Server error: {error_msg}" | Any unhandled exception in PO operations | SERVER_ERROR |
| **routers/replenishment.py** |
| routers/replenishment.py | 404 | "Replenishment order {ro_id} not found" | RO retrieval/operations when RO doesn't exist | RO_NOT_FOUND |
| routers/replenishment.py | 404 | "Item with SKU {sku} at location {rack_location} not found in replenishment order {ro_id}" | Item picking when SKU/location combination doesn't exist in RO | ITEM_NOT_FOUND |
| routers/replenishment.py | 400 | "Replenishment order {ro_id} is already marked as Completed" | Attempting operations on completed RO | ORDER_ALREADY_COMPLETED |
| routers/replenishment.py | 400 | "Insufficient stock" | Stock check fails (currently placeholder) | INSUFFICIENT_STOCK |
| routers/replenishment.py | 400 | "Cannot cancel order with status {status}. Only orders with status 'In Process' can be cancelled." | Cancelling RO that's not in 'In Process' status | INVALID_STATUS_FOR_CANCEL |
| routers/replenishment.py | 500 | "Server error: {error_msg}" | Any unhandled exception in replenishment operations | SERVER_ERROR |
| **routers/putaway.py** |
| routers/putaway.py | 400 | "Tote {tote} already exists in the system" | Creating putaway order with duplicate tote ID | DUPLICATE_TOTE |
| routers/putaway.py | 400 | "Total quantity exceeds maximum allowed (100,000)" | Total quantity in putaway order > 100,000 | QUANTITY_EXCEEDED |
| routers/putaway.py | 400 | "Error inserting item with SKU {sku}" | Database integrity error during item insertion | ITEM_INSERT_FAILED |
| routers/putaway.py | 500 | "Database error occurred" | SQLAlchemy database errors | DATABASE_ERROR |
| routers/putaway.py | 500 | str(e) | Any other unhandled exception | GENERAL_ERROR |
| **routers/bulk_storage.py** |
| routers/bulk_storage.py | 400 | "Location {location} already has a pending order" | Creating bulk storage order at location with existing pending order | DUPLICATE_LOCATION |
| routers/bulk_storage.py | 400 | "Total quantity exceeds maximum allowed (1,000,000)" | Total quantity in bulk storage order > 1,000,000 | QUANTITY_EXCEEDED |
| routers/bulk_storage.py | 400 | "Error inserting item with SKU {sku}" | Database integrity error during item insertion | ITEM_INSERT_FAILED |
| routers/bulk_storage.py | 500 | "Database error occurred" | SQLAlchemy database errors | DATABASE_ERROR |
| routers/bulk_storage.py | 500 | str(e) | Any other unhandled exception | GENERAL_ERROR |
| **routers/art_orders.py** |
| routers/art_orders.py | 404 | "SKU {sku} does not exist in the products table" | ART operation with invalid SKU | INVALID_SKU |
| routers/art_orders.py | 400 | "Insufficient stock of SKU {sku} at location {location}" | Remove/Transfer operation with insufficient stock | INSUFFICIENT_STOCK |
| routers/art_orders.py | 500 | "Server error: {error_msg}" | Any unhandled exception in ART operations | SERVER_ERROR |
| **routers/product.py** |
| routers/product.py | 500 | "Server error: {error_msg}" | Any unhandled exception in product search | SERVER_ERROR |
| **main.py** |
| main.py | 500 | str(e) | Any unhandled exception in measurement endpoint | - |
| main.py | 503 | str(e) | Database connection failure in health check | - |
| **Model Validation Errors (422 status)** |
| models/barcode.py | 422 | "Barcode must be between 8 and 14 digits" | Invalid barcode format (not 8-14 digits) | - |
| models/barcode.py | 422 | "SKU must contain only letters, numbers, hyphens and underscores" | Invalid SKU format | - |
| models/putaway.py | 422 | "Tote must start with TOTE followed by up to 15 alphanumeric characters or hyphens" | Invalid tote format | - |
| models/putaway.py | 422 | "SKU must contain only letters, numbers, hyphens and underscores" | Invalid SKU format | - |
| models/putaway.py | 422 | "Barcode must be between 8 and 14 digits" | Invalid barcode format | - |
| models/putaway.py | 422 | "Duplicate SKUs are not allowed in a single order" | Duplicate SKUs in putaway items | - |
| models/bulk_storage.py | 422 | "Location must follow format RACK-A1-01 (RACK-<section><aisle>-<position>)" | Invalid location format | - |
| models/bulk_storage.py | 422 | "SKU must contain only letters, numbers, hyphens and underscores" | Invalid SKU format | - |
| models/bulk_storage.py | 422 | "Barcode must be between 8 and 14 digits" | Invalid barcode format | - |
| models/bulk_storage.py | 422 | "Duplicate SKUs are not allowed in a single order" | Duplicate SKUs in bulk storage items | - |
| models/art_order.py | 422 | "SKU must contain only letters, numbers, hyphens and underscores" | Invalid SKU format | - |
| models/art_order.py | 422 | "Location cannot be empty" | Empty location string | - |
| models/art_order.py | 422 | "to_location is required for Add operations" | Missing to_location for Add operation | - |
| models/art_order.py | 422 | "from_location is required for Remove operations" | Missing from_location for Remove operation | - |
| models/art_order.py | 422 | "from_location is required for Transfer operations" | Missing from_location for Transfer operation | - |
| models/art_order.py | 422 | "to_location is required for Transfer operations" | Missing to_location for Transfer operation | - |
| models/art_order.py | 422 | "from_location and to_location cannot be the same for Transfer operations" | Same source and destination locations for Transfer | - |
| models/purchase_orders.py | 422 | "Either po_number or barcode must be provided" | Missing both po_number and barcode in request | - |
| models/purchase_orders.py | 422 | "Barcode must be between 8 and 14 digits" | Invalid barcode format | - |
| models/purchase_orders.py | 422 | "PO number cannot be empty" | Empty PO number | - |
| models/replenishment.py | 422 | "Replenishment Order ID cannot be empty" | Empty RO ID | - |
| models/replenishment.py | 422 | "SKU cannot be empty" | Empty SKU | - |
| models/replenishment.py | 422 | "Rack location cannot be empty" | Empty rack location | - |
| models/replenishment.py | 422 | "Quantity picked cannot be negative" | Negative quantity picked | - |
| models/measurement.py | 422 | "Barcode must be between 8 and 14 digits" | Invalid barcode format | - |
| models/measurement.py | 422 | "Device must contain only letters, numbers, hyphens and underscores" | Invalid device format | - |
| models/measurement.py | 422 | "Required attribute {attr} is missing" | Missing required attributes (ovpk, batt, hazmat, qty) | - |
| models/measurement.py | 422 | "Attribute {attr} must be 'true' or 'false'" | Invalid boolean attribute values | - |
| models/measurement.py | 422 | "Quantity must be between 1 and 10000" | Invalid quantity value | - |
| models/measurement.py | 422 | "SKU must contain only letters, numbers, hyphens and underscores" | Invalid SKU format | - |
| models/product.py | 422 | "Search query cannot be empty" | Empty search query | - |

## Error Handling Patterns Observed

### Consistent Patterns ✅
- **HTTP Status Codes**: Generally consistent (400 for business logic, 404 for not found, 422 for validation, 500 for server errors)
- **Error Structure**: Most endpoints return structured error objects with status, message, error_code, and timestamp
- **Database Validation**: Comprehensive SKU and barcode format validation across models
- **Business Logic Validation**: Good validation for domain-specific rules (tote formats, location formats, etc.)

### Inconsistencies ⚠️
- **Error Codes**: Some endpoints don't include error_code field (measurements.py, main.py)
- **Message Format**: Some use generic str(e) while others have specific messages
- **Exception Handling**: Not all endpoints have comprehensive try/catch blocks
- **Logging**: Inconsistent logging across different routers

### Missing Error Handling 🔴
- **Rate Limiting**: No API rate limiting error handling
- **Authentication**: No authentication error handling (not yet implemented)
- **Input Sanitization**: Limited SQL injection protection beyond parameterized queries
- **File Upload**: No file size/type validation errors for image uploads
- **Concurrent Operations**: No handling for concurrent modification scenarios

## Recommendations

1. **Standardize Error Response Format**: Ensure all endpoints return the same error structure
2. **Add Missing Error Codes**: Include error_code field in all error responses
3. **Improve Logging**: Add consistent logging across all routers
4. **Add Input Validation**: Enhanced validation for edge cases and security
5. **Database Transaction Handling**: Better rollback handling for complex operations
6. **Add Authentication Errors**: Prepare error handling for upcoming authentication system