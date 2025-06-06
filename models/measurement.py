from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import re

class ProductData(BaseModel):
    request_id: Optional[str] = Field(None, max_length=50, description="Unique identifier for request deduplication")
    timestamp: Optional[str] = None
    l: Optional[int] = Field(None, ge=1, le=10000)  # Length in mm
    w: Optional[int] = Field(None, ge=1, le=10000)  # Width in mm
    h: Optional[int] = Field(None, ge=1, le=10000)  # Height in mm
    weight: Optional[int] = Field(None, ge=1, le=100000)  # Weight in g
    barcode: str = Field(..., max_length=50)
    shape: str = Field(..., max_length=100)
    device: str = Field(..., max_length=50)
    note: Optional[str] = Field(None, max_length=1000)
    attributes: Dict[str, Any]
    image: Optional[str] = None
    imageseg: Optional[str] = None
    imagecolor: Optional[str] = None

    @validator('request_id')
    def validate_request_id(cls, v):
        if v is not None and not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
            raise ValueError('Request ID must contain only letters, numbers, hyphens and underscores')
        return v

    @validator('barcode')
    def validate_barcode(cls, v):
        if not re.match(r'^[0-9]{8,14}$', v):
            raise ValueError('Barcode must be between 8 and 14 digits')
        return v

    @validator('device')
    def validate_device(cls, v):
        if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
            raise ValueError('Device must contain only letters, numbers, hyphens and underscores')
        return v

    @validator('attributes')
    def validate_attributes(cls, v):
        # Check required attributes
        required_attrs = ['ovpk', 'batt', 'hazmat', 'qty']
        for attr in required_attrs:
            if attr not in v:
                raise ValueError(f'Required attribute {attr} is missing')
        
        # Validate boolean attributes
        bool_attrs = ['ovpk', 'batt', 'hazmat']
        for attr in bool_attrs:
            if v.get(attr) not in ['true', 'false']:
                raise ValueError(f'Attribute {attr} must be "true" or "false"')
                
        # Validate quantity
        if 'qty' in v:
            try:
                qty = int(v['qty'])
                if qty < 1 or qty > 10000:
                    raise ValueError('Quantity must be between 1 and 10000')
            except ValueError:
                raise ValueError('Quantity must be a valid integer')
                
        # Validate SKU if present
        if 'sku' in v:
            if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v['sku']):
                raise ValueError('SKU must contain only letters, numbers, hyphens and underscores')
                
        return v