from pydantic import BaseModel, Field, validator
from typing import List

class ParentOrderItem(BaseModel):
    orderId: str = Field(..., description="The order ID to update")
    parentOrderId: str = Field(..., description="The parent order ID to set")
    
    @validator('orderId', 'parentOrderId')
    def validate_order_id(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Order ID cannot be empty')
        return v

class ParentOrderUpdateRequest(BaseModel):
    items: List[ParentOrderItem] = Field(..., min_items=1, description="The list of orders to update with parent order IDs")

class OrderCancelledRequest(BaseModel):
    orderId: str = Field(..., description="The order ID to check cancellation status")
    
    @validator('orderId')
    def validate_order_id(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Order ID cannot be empty')
        return v