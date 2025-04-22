from pydantic import BaseModel, Field, validator
from typing import List, Optional
import re

class PutawayItem(BaseModel):
    sku: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    barcode: str = Field(..., max_length=50)
    quantity: int = Field(..., gt=0, le=10000)  # Greater than 0, less than or equal to 10000

    @validator('sku')
    def validate_sku(cls, v):
        if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
            raise ValueError('SKU must contain only letters, numbers, hyphens and underscores')
        return v

    @validator('barcode')
    def validate_barcode(cls, v):
        if not re.match(r'^[0-9]{8,14}$', v):
            raise ValueError('Barcode must be between 8 and 14 digits')
        return v

class PutawayOrder(BaseModel):
    tote: str = Field(..., max_length=20)
    items: List[PutawayItem] = Field(..., min_items=1, max_items=50)
    test_insufficient_stock: Optional[bool] = Field(False, description="Test flag to simulate insufficient stock")

    @validator('tote')
    def validate_tote(cls, v):
        if not re.match(r'^TOTE[A-Z0-9\-]{1,15}$', v):
            raise ValueError('Tote must start with TOTE followed by up to 15 alphanumeric characters or hyphens')
        return v.upper()

    @validator('items')
    def validate_unique_skus(cls, v):
        skus = [item.sku for item in v]
        if len(skus) != len(set(skus)):
            raise ValueError('Duplicate SKUs are not allowed in a single order')
        return v