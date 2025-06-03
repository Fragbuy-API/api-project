from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import re

class ProductDataDebug(BaseModel):
    """
    Flexible version of ProductData for debugging - relaxed validation
    """
    timestamp: Optional[str] = None
    l: Optional[int] = Field(None, ge=0, le=10000)  # Allow 0 and None
    w: Optional[int] = Field(None, ge=0, le=10000)  # Allow 0 and None
    h: Optional[int] = Field(None, ge=0, le=10000)  # Allow 0 and None
    weight: Optional[int] = Field(None, ge=0, le=100000)  # Allow 0 and None
    barcode: str = Field(..., max_length=50)
    shape: Optional[str] = Field(None, max_length=100)  # Make optional
    device: Optional[str] = Field(None, max_length=50)  # Make optional
    note: Optional[str] = Field(None, max_length=1000)
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict)  # Make optional with default
    image: Optional[str] = None
    imageseg: Optional[str] = None
    imagecolor: Optional[str] = None

    @validator('barcode')
    def validate_barcode(cls, v):
        # More flexible barcode validation
        if not v or len(v.strip()) == 0:
            return "unknown"  # Allow empty/missing barcodes
        
        # Allow "na" or similar
        if v.lower() in ['na', 'n/a', 'none', 'unknown']:
            return v
            
        # Standard barcode validation
        if re.match(r'^[0-9]{8,14}$', v):
            return v
        
        # If it doesn't match, just return as-is for debugging
        return v

    @validator('device')
    def validate_device(cls, v):
        if not v:
            return "unknown"
        # More flexible device validation
        return str(v)

    @validator('attributes')
    def validate_attributes(cls, v):
        # Very relaxed validation - accept any attributes structure
        if v is None:
            return {}
        
        if not isinstance(v, dict):
            return {}
            
        # No required attributes for debugging
        return v

    @validator('shape')
    def validate_shape(cls, v):
        if not v:
            return "unknown"
        return str(v)
