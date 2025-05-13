from pydantic import BaseModel, Field, validator
from typing import List,Optional
import re

class BulkStorageItem(BaseModel):
    sku: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    barcode: str = Field(..., max_length=50)
    quantity: int = Field(..., gt=0, le=100000)  # Greater than 0, less than or equal to 100000

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

class BulkStorageOrder(BaseModel):
    location: str = Field(..., max_length=30)
    items: List[BulkStorageItem] = Field(..., min_items=1, max_items=100)  # Allow more items for bulk storage
    # Add to BulkStorageOrder class
    test_insufficient_stock: Optional[bool] = Field(False, description="Test flag to simulate insufficient stock")

    #@validator('location')
    #def validate_location(cls, v):
    #    if not re.match(r'^RACK-[A-Z][0-9]-[0-9]{2}$', v):
    #        raise ValueError('Location must follow format RACK-A1-01 (RACK-<section><aisle>-<position>)')
    #    return v.upper()

    @validator('items')
    def validate_unique_skus(cls, v):
        skus = [item.sku for item in v]
        if len(skus) != len(set(skus)):
            raise ValueError('Duplicate SKUs are not allowed in a single order')
        return v