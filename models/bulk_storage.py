from pydantic import BaseModel, Field, validator
from typing import List, Optional
import re
import logging

# Setup logging for model validation
logger = logging.getLogger(__name__)

class BulkStorageValidationError(ValueError):
    """Custom exception for bulk storage validation errors"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.error_code = error_code

class BulkStorageItem(BaseModel):
    sku: str = Field(..., max_length=50, description="Stock Keeping Unit identifier")
    name: str = Field(..., max_length=255, description="Product name")
    barcode: str = Field(..., max_length=50, description="Product barcode (8-14 digits)")
    quantity: int = Field(..., gt=0, le=100000, description="Quantity for bulk storage (1-100,000)")

    @validator('sku')
    def validate_sku(cls, v):
        if not v or not v.strip():
            logger.warning("Empty SKU provided for bulk storage item")
            raise BulkStorageValidationError(
                'SKU cannot be empty', 
                'SKU_EMPTY'
            )
        
        # Remove any whitespace and convert to uppercase
        v = v.strip().upper()
        
        if len(v) > 50:
            logger.warning(f"SKU too long: {len(v)} characters")
            raise BulkStorageValidationError(
                'SKU cannot exceed 50 characters', 
                'SKU_TOO_LONG'
            )
        
        if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
            logger.warning(f"Invalid SKU format provided: {v}")
            raise BulkStorageValidationError(
                'SKU must contain only letters, numbers, hyphens and underscores', 
                'SKU_INVALID_FORMAT'
            )
        
        return v

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            logger.warning("Empty product name provided for bulk storage item")
            raise BulkStorageValidationError(
                'Product name cannot be empty', 
                'NAME_EMPTY'
            )
        
        v = v.strip()
        
        if len(v) > 255:
            logger.warning(f"Product name too long: {len(v)} characters")
            raise BulkStorageValidationError(
                'Product name cannot exceed 255 characters', 
                'NAME_TOO_LONG'
            )
        
        return v

    @validator('barcode')
    def validate_barcode(cls, v):
        if not v or not v.strip():
            logger.warning("Empty barcode provided for bulk storage item")
            raise BulkStorageValidationError(
                'Barcode cannot be empty', 
                'BARCODE_EMPTY'
            )
        
        # Remove any whitespace
        v = v.strip()
        
        # Allow "NA" as a special case for unavailable barcodes
        if v.upper() == "NA":
            return v.upper()
        
        if not re.match(r'^[0-9]{8,14}$', v):
            logger.warning(f"Invalid barcode format provided: {v}")
            raise BulkStorageValidationError(
                'Barcode must be between 8 and 14 digits or "NA" for not available', 
                'BARCODE_INVALID_FORMAT'
            )
        
        return v

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            logger.warning(f"Invalid quantity provided: {v}")
            raise BulkStorageValidationError(
                'Quantity must be greater than 0', 
                'QUANTITY_INVALID'
            )
        
        if v > 100000:
            logger.warning(f"Quantity too high: {v}")
            raise BulkStorageValidationError(
                'Quantity cannot exceed 100,000 units per item', 
                'QUANTITY_TOO_HIGH'
            )
        
        return v

class BulkStorageOrder(BaseModel):
    location: str = Field(..., max_length=30, description="Storage location identifier")
    items: List[BulkStorageItem] = Field(..., min_items=1, max_items=100, description="List of items for bulk storage (1-100 items)")
    test_insufficient_stock: Optional[bool] = Field(False, description="Test flag to simulate insufficient stock")

    @validator('location')
    def validate_location(cls, v):
        if not v or not v.strip():
            logger.warning("Empty location provided for bulk storage order")
            raise BulkStorageValidationError(
                'Storage location cannot be empty', 
                'LOCATION_EMPTY'
            )
        
        # Remove any whitespace and convert to uppercase
        v = v.strip().upper()
        
        if len(v) > 30:
            logger.warning(f"Location identifier too long: {len(v)} characters")
            raise BulkStorageValidationError(
                'Location identifier cannot exceed 30 characters', 
                'LOCATION_TOO_LONG'
            )
        
        # Note: Location format validation is currently commented out in original code
        # Keeping it flexible for now, but could be uncommented if strict format needed:
        # if not re.match(r'^RACK-[A-Z][0-9]-[0-9]{2}$', v):
        #     logger.warning(f"Invalid location format provided: {v}")
        #     raise BulkStorageValidationError(
        #         'Location must follow format RACK-A1-01 (RACK-<section><aisle>-<position>)', 
        #         'LOCATION_INVALID_FORMAT'
        #     )
        
        return v

    @validator('items')
    def validate_items(cls, v):
        if not v or len(v) == 0:
            logger.warning("Empty items list provided for bulk storage order")
            raise BulkStorageValidationError(
                'At least one item is required for bulk storage order', 
                'ITEMS_EMPTY'
            )
        
        if len(v) > 100:
            logger.warning(f"Too many items in bulk storage order: {len(v)}")
            raise BulkStorageValidationError(
                'Cannot exceed 100 items in a single bulk storage order', 
                'ITEMS_TOO_MANY'
            )
        
        return v

    @validator('items')
    def validate_unique_skus(cls, v):
        skus = [item.sku for item in v]
        if len(skus) != len(set(skus)):
            duplicate_skus = [sku for sku in set(skus) if skus.count(sku) > 1]
            logger.warning(f"Duplicate SKUs found in bulk storage order: {duplicate_skus}")
            raise BulkStorageValidationError(
                f'Duplicate SKUs are not allowed in a single order: {", ".join(duplicate_skus)}', 
                'DUPLICATE_SKUS'
            )
        
        return v

    @validator('items')
    def validate_total_quantity(cls, v):
        total_quantity = sum(item.quantity for item in v)
        if total_quantity > 1000000:
            logger.warning(f"Total quantity too high: {total_quantity}")
            raise BulkStorageValidationError(
                f'Total quantity ({total_quantity}) exceeds maximum allowed (1,000,000) for bulk storage order', 
                'TOTAL_QUANTITY_TOO_HIGH'
            )
        
        return v