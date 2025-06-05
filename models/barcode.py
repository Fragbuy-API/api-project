from pydantic import BaseModel, Field, validator
from typing import Optional
import re
import logging

# Setup logging for model validation
logger = logging.getLogger(__name__)

class BarcodeValidationError(ValueError):
    """Custom exception for barcode validation errors"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.error_code = error_code

class BarcodeLookup(BaseModel):
    barcode: str = Field(..., max_length=50, description="Barcode to lookup (8-14 digits or 'NA')")
    
    @validator('barcode')
    def validate_barcode(cls, v):
        if not v or not v.strip():
            logger.warning("Empty barcode provided for lookup")
            raise BarcodeValidationError(
                'Barcode cannot be empty', 
                'BARCODE_EMPTY'
            )
        
        # Remove any whitespace
        v = v.strip()
        
        # Allow "NA" as a special case for unavailable barcodes
        if v.upper() == "NA":
            return v.upper()
        
        # Otherwise, validate as normal 8-14 digit barcode
        if not re.match(r'^[0-9]{8,14}$', v):
            logger.warning(f"Invalid barcode format provided: {v}")
            raise BarcodeValidationError(
                'Barcode must be between 8 and 14 digits or "NA" for not available', 
                'BARCODE_INVALID_FORMAT'
            )
        
        return v

class NewBarcode(BaseModel):
    sku: str = Field(..., max_length=50, description="Stock Keeping Unit identifier")
    barcode: str = Field(..., max_length=50, description="Barcode to associate with SKU (8-14 digits or 'NA')")
    
    @validator('sku')
    def validate_sku(cls, v):
        if not v or not v.strip():
            logger.warning("Empty SKU provided for new barcode")
            raise BarcodeValidationError(
                'SKU cannot be empty', 
                'SKU_EMPTY'
            )
        
        # Remove any whitespace and convert to uppercase
        v = v.strip().upper()
        
        if len(v) > 50:
            logger.warning(f"SKU too long: {len(v)} characters")
            raise BarcodeValidationError(
                'SKU cannot exceed 50 characters', 
                'SKU_TOO_LONG'
            )
        
        if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
            logger.warning(f"Invalid SKU format provided: {v}")
            raise BarcodeValidationError(
                'SKU must contain only letters, numbers, hyphens and underscores', 
                'SKU_INVALID_FORMAT'
            )
        
        return v
    
    @validator('barcode')
    def validate_barcode(cls, v):
        if not v or not v.strip():
            logger.warning("Empty barcode provided for new barcode creation")
            raise BarcodeValidationError(
                'Barcode cannot be empty', 
                'BARCODE_EMPTY'
            )
        
        # Remove any whitespace
        v = v.strip()
        
        # Allow "NA" as a special case for unavailable barcodes
        if v.upper() == "NA":
            return v.upper()
        
        # Otherwise, validate as normal 8-14 digit barcode
        if not re.match(r'^[0-9]{8,14}$', v):
            logger.warning(f"Invalid barcode format provided: {v}")
            raise BarcodeValidationError(
                'Barcode must be between 8 and 14 digits or "NA" for not available', 
                'BARCODE_INVALID_FORMAT'
            )
        
        return v