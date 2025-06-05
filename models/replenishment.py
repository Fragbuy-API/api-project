from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import logging
import re

# Setup logging for model validation
logger = logging.getLogger(__name__)

class ReplenishmentValidationError(ValueError):
    """Custom exception for replenishment validation errors"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.error_code = error_code

class ReplenishmentOrder(BaseModel):
    """Response model for replenishment order data"""
    ro_id: str
    ro_date_created: datetime
    ro_status: str
    destination: str
    skus_in_order: int

class ReplenishmentOrderRequest(BaseModel):
    ro_id: str = Field(..., max_length=50, description="Replenishment order identifier")
    
    @validator('ro_id')
    def validate_ro_id(cls, v):
        if not v or not v.strip():
            logger.warning("Empty replenishment order ID provided")
            raise ReplenishmentValidationError(
                'Replenishment Order ID cannot be empty', 
                'RO_ID_EMPTY'
            )
        
        v = v.strip()
        
        if len(v) > 50:
            logger.warning(f"Replenishment order ID too long: {len(v)} characters")
            raise ReplenishmentValidationError(
                'Replenishment Order ID cannot exceed 50 characters', 
                'RO_ID_TOO_LONG'
            )
        
        return v

class ReplenishmentItemPickedRequest(BaseModel):
    ro_id: str = Field(..., max_length=50, description="Replenishment order identifier")
    sku: str = Field(..., max_length=50, description="Stock Keeping Unit identifier")
    rack_location: str = Field(..., max_length=30, description="Rack location identifier")
    qty_picked: int = Field(..., ge=0, description="Quantity picked (0 or greater)")
    note: Optional[str] = Field(None, max_length=500, description="Optional note about the picking operation")
    test_insufficient_stock: Optional[bool] = Field(False, description="Test flag to simulate insufficient stock")
    
    @validator('ro_id')
    def validate_ro_id(cls, v):
        if not v or not v.strip():
            logger.warning("Empty replenishment order ID provided for item picking")
            raise ReplenishmentValidationError(
                'Replenishment Order ID cannot be empty', 
                'RO_ID_EMPTY'
            )
        
        v = v.strip()
        
        if len(v) > 50:
            logger.warning(f"Replenishment order ID too long: {len(v)} characters")
            raise ReplenishmentValidationError(
                'Replenishment Order ID cannot exceed 50 characters', 
                'RO_ID_TOO_LONG'
            )
        
        return v
    
    @validator('sku')
    def validate_sku(cls, v):
        if not v or not v.strip():
            logger.warning("Empty SKU provided for item picking")
            raise ReplenishmentValidationError(
                'SKU cannot be empty', 
                'SKU_EMPTY'
            )
        
        v = v.strip().upper()
        
        if len(v) > 50:
            logger.warning(f"SKU too long: {len(v)} characters")
            raise ReplenishmentValidationError(
                'SKU cannot exceed 50 characters', 
                'SKU_TOO_LONG'
            )
        
        if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
            logger.warning(f"Invalid SKU format provided: {v}")
            raise ReplenishmentValidationError(
                'SKU must contain only letters, numbers, hyphens and underscores', 
                'SKU_INVALID_FORMAT'
            )
        
        return v
    
    @validator('rack_location')
    def validate_rack_location(cls, v):
        if not v or not v.strip():
            logger.warning("Empty rack location provided for item picking")
            raise ReplenishmentValidationError(
                'Rack location cannot be empty', 
                'RACK_LOCATION_EMPTY'
            )
        
        v = v.strip().upper()
        
        if len(v) > 30:
            logger.warning(f"Rack location too long: {len(v)} characters")
            raise ReplenishmentValidationError(
                'Rack location cannot exceed 30 characters', 
                'RACK_LOCATION_TOO_LONG'
            )
        
        return v
    
    @validator('qty_picked')
    def validate_qty_picked(cls, v):
        if v < 0:
            logger.warning(f"Negative quantity picked provided: {v}")
            raise ReplenishmentValidationError(
                'Quantity picked cannot be negative', 
                'QTY_PICKED_NEGATIVE'
            )
        
        if v > 1000000:  # Reasonable upper limit
            logger.warning(f"Quantity picked too high: {v}")
            raise ReplenishmentValidationError(
                'Quantity picked cannot exceed 1,000,000', 
                'QTY_PICKED_TOO_HIGH'
            )
        
        return v
    
    @validator('note')
    def validate_note(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None  # Convert empty string to None
            
            if len(v) > 500:
                logger.warning(f"Note too long: {len(v)} characters")
                raise ReplenishmentValidationError(
                    'Note cannot exceed 500 characters', 
                    'NOTE_TOO_LONG'
                )
        
        return v

class ReplenishmentCancelRequest(BaseModel):
    ro_id: str = Field(..., max_length=50, description="Replenishment order identifier to cancel")
    
    @validator('ro_id')
    def validate_ro_id(cls, v):
        if not v or not v.strip():
            logger.warning("Empty replenishment order ID provided for cancellation")
            raise ReplenishmentValidationError(
                'Replenishment Order ID cannot be empty', 
                'RO_ID_EMPTY'
            )
        
        v = v.strip()
        
        if len(v) > 50:
            logger.warning(f"Replenishment order ID too long: {len(v)} characters")
            raise ReplenishmentValidationError(
                'Replenishment Order ID cannot exceed 50 characters', 
                'RO_ID_TOO_LONG'
            )
        
        return v

class ReplenishmentCompleteRequest(BaseModel):
    ro_id: str = Field(..., max_length=50, description="Replenishment order identifier to complete")
    
    @validator('ro_id')
    def validate_ro_id(cls, v):
        if not v or not v.strip():
            logger.warning("Empty replenishment order ID provided for completion")
            raise ReplenishmentValidationError(
                'Replenishment Order ID cannot be empty', 
                'RO_ID_EMPTY'
            )
        
        v = v.strip()
        
        if len(v) > 50:
            logger.warning(f"Replenishment order ID too long: {len(v)} characters")
            raise ReplenishmentValidationError(
                'Replenishment Order ID cannot exceed 50 characters', 
                'RO_ID_TOO_LONG'
            )
        
        return v