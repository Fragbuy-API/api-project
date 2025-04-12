from pydantic import BaseModel, validator  # Added validator here
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