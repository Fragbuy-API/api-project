from pydantic import BaseModel, Field, validator
from typing import List, Optional
import re
import logging

# Setup logging for model validation
logger = logging.getLogger(__name__)

class PutawayValidationError(ValueError):
    """Custom exception for putaway validation errors"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.error_code = error_code

class PutawayItem(BaseModel):
    sku: str = Field(..., max_length=50, description="Stock Keeping Unit identifier")
    name: Optional[str] = Field(None, max_length=255, description="Product name (optional)")
    barcode: Optional[str] = Field(None, max_length=50, description="Product barcode (8-14 digits, optional)")
    quantity: int = Field(..., gt=0, le=10000, description="Quantity to putaway (1-10,000)")

    @validator('sku')
    def validate_sku(cls, v):
        if not v or not v.strip():
            logger.warning("Empty SKU provided for putaway item")
            raise PutawayValidationError(
                'SKU cannot be empty', 
                'SKU_EMPTY'
            )
        
        # Remove any whitespace and convert to uppercase
        v = v.strip().upper()
        
        if len(v) > 50:
            logger.warning(f"SKU too long: {len(v)} characters")
            raise PutawayValidationError(
                'SKU cannot exceed 50 characters', 
                'SKU_TOO_LONG'
            )
        
        if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
            logger.warning(f"Invalid SKU format provided: {v}")
            raise PutawayValidationError(
                'SKU must contain only letters, numbers, hyphens and underscores', 
                'SKU_INVALID_FORMAT'
            )
        
        return v

    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None  # Convert empty string to None
            if len(v) > 255:
                logger.warning(f"Product name too long: {len(v)} characters")
                raise PutawayValidationError(
                    'Product name cannot exceed 255 characters', 
                    'NAME_TOO_LONG'
                )
        return v

    @validator('barcode')
    def validate_barcode(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None  # Convert empty string to None
            
            # Allow "NA" as a special case for unavailable barcodes
            if v.upper() == "NA":
                return v.upper()
            
            if not re.match(r'^[0-9]{8,14}$', v):
                logger.warning(f"Invalid barcode format provided: {v}")
                raise PutawayValidationError(
                    'Barcode must be between 8 and 14 digits or "NA" for not available', 
                    'BARCODE_INVALID_FORMAT'
                )
        
        return v

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            logger.warning(f"Invalid quantity provided: {v}")
            raise PutawayValidationError(
                'Quantity must be greater than 0', 
                'QUANTITY_INVALID'
            )
        
        if v > 10000:
            logger.warning(f"Quantity too high: {v}")
            raise PutawayValidationError(
                'Quantity cannot exceed 10,000 units per item', 
                'QUANTITY_TOO_HIGH'
            )
        
        return v

class PutawayOrder(BaseModel):
    tote: str = Field(..., max_length=20, description="Tote identifier (must start with 'TOTE')")
    items: List[PutawayItem] = Field(..., min_items=1, max_items=50, description="List of items to putaway (1-50 items)")
    test_insufficient_stock: Optional[bool] = Field(False, description="Test flag to simulate insufficient stock")

    @validator('tote')
    def validate_tote(cls, v):
        if not v or not v.strip():
            logger.warning("Empty tote identifier provided")
            raise PutawayValidationError(
                'Tote identifier cannot be empty', 
                'TOTE_EMPTY'
            )
        
        # Remove any whitespace and convert to uppercase
        v = v.strip().upper()
        
        if len(v) > 20:
            logger.warning(f"Tote identifier too long: {len(v)} characters")
            raise PutawayValidationError(
                'Tote identifier cannot exceed 20 characters', 
                'TOTE_TOO_LONG'
            )
        
        if not re.match(r'^TOTE[A-Z0-9\-]{1,15}$', v):
            logger.warning(f"Invalid tote format provided: {v}")
            raise PutawayValidationError(
                'Tote must start with TOTE followed by up to 15 alphanumeric characters or hyphens', 
                'TOTE_INVALID_FORMAT'
            )
        
        return v

    @validator('items')
    def validate_items(cls, v):
        if not v or len(v) == 0:
            logger.warning("Empty items list provided for putaway order")
            raise PutawayValidationError(
                'At least one item is required for putaway order', 
                'ITEMS_EMPTY'
            )
        
        if len(v) > 50:
            logger.warning(f"Too many items in putaway order: {len(v)}")
            raise PutawayValidationError(
                'Cannot exceed 50 items in a single putaway order', 
                'ITEMS_TOO_MANY'
            )
        
        return v

    @validator('items')
    def validate_unique_skus(cls, v):
        skus = [item.sku for item in v]
        if len(skus) != len(set(skus)):
            duplicate_skus = [sku for sku in set(skus) if skus.count(sku) > 1]
            logger.warning(f"Duplicate SKUs found in putaway order: {duplicate_skus}")
            raise PutawayValidationError(
                f'Duplicate SKUs are not allowed in a single order: {", ".join(duplicate_skus)}', 
                'DUPLICATE_SKUS'
            )
        
        return v

    @validator('items')
    def validate_total_quantity(cls, v):
        total_quantity = sum(item.quantity for item in v)
        if total_quantity > 100000:
            logger.warning(f"Total quantity too high: {total_quantity}")
            raise PutawayValidationError(
                f'Total quantity ({total_quantity}) exceeds maximum allowed (100,000) for putaway order', 
                'TOTAL_QUANTITY_TOO_HIGH'
            )
        
        return v