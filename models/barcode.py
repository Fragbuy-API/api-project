from pydantic import BaseModel, Field, validator
from typing import Optional
import re

class BarcodeLookup(BaseModel):
    barcode: str = Field(..., max_length=50)
    
    @validator('barcode')
    def validate_barcode(cls, v):
        # Allow "NA" as a special case for unavailable barcodes
        if v.upper() == "NA":
            return v.upper()
        
        # Otherwise, validate as normal 8-14 digit barcode
        if not re.match(r'^[0-9]{8,14}$', v):
            raise ValueError('Barcode must be between 8 and 14 digits or "NA" for not available')
        return v

class NewBarcode(BaseModel):
    sku: str = Field(..., max_length=50)
    barcode: str = Field(..., max_length=50)
    
    @validator('sku')
    def validate_sku(cls, v):
        if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
            raise ValueError('SKU must contain only letters, numbers, hyphens and underscores')
        return v.upper()  # Standardize SKUs to uppercase
    
    @validator('barcode')
    def validate_barcode(cls, v):
        # Allow "NA" as a special case for unavailable barcodes
        if v.upper() == "NA":
            return v.upper()
        
        # Otherwise, validate as normal 8-14 digit barcode
        if not re.match(r'^[0-9]{8,14}$', v):
            raise ValueError('Barcode must be between 8 and 14 digits or "NA" for not available')
        return v