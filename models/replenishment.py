from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

class ReplenishmentOrder(BaseModel):
    ro_id: str
    ro_date_created: datetime
    ro_status: str
    destination: str
    skus_in_order: int

class ReplenishmentOrderRequest(BaseModel):
    ro_id: str
    
    @validator('ro_id')
    def validate_ro_id(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Replenishment Order ID cannot be empty')
        return v

class ReplenishmentItemPickedRequest(BaseModel):
    ro_id: str
    sku: str
    qty_picked: int
    
    @validator('ro_id')
    def validate_ro_id(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Replenishment Order ID cannot be empty')
        return v
    
    @validator('sku')
    def validate_sku(cls, v):
        if not v or v.strip() == "":
            raise ValueError('SKU cannot be empty')
        return v
    
    @validator('qty_picked')
    def validate_qty_picked(cls, v):
        if v < 0:
            raise ValueError('Quantity picked cannot be negative')
        return v

class ReplenishmentCancelRequest(BaseModel):
    ro_id: str
    
    @validator('ro_id')
    def validate_ro_id(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Replenishment Order ID cannot be empty')
        return v

class ReplenishmentCompleteRequest(BaseModel):
    ro_id: str
    
    @validator('ro_id')
    def validate_ro_id(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Replenishment Order ID cannot be empty')
        return v