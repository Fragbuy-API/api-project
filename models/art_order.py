from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, Literal
import re

class ArtOrder(BaseModel):
    """
    Model for Ad Hoc Add/Remove/Transfer (ART) operations.
    Handles validation for all three operation types.
    """
    type: Literal["Add", "Remove", "Transfer"] = Field(..., description="Type of operation")
    sku: str = Field(..., max_length=50, description="Stock Keeping Unit")
    quantity: int = Field(..., gt=0, le=1000000, description="Quantity to add, remove, or transfer")
    from_location: Optional[str] = Field(None, max_length=30, description="Source location")
    to_location: Optional[str] = Field(None, max_length=30, description="Destination location")
    reason: Optional[str] = Field(None, max_length=255, description="Reason for the operation")
    sufficient_stock: Optional[bool] = Field(None, description="Flag to simulate insufficient stock (for testing)")
    
    # Alias qty to quantity for backward compatibility
    class Config:
        allow_population_by_field_name = True
        @staticmethod
        def schema_extra(schema, model):
            # Add "qty" as an alias for "quantity" in the schema
            props = schema.get("properties", {})
            if "quantity" in props:
                props["qty"] = props["quantity"]
    
    @validator('sku')
    def validate_sku(cls, v):
        if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
            raise ValueError('SKU must contain only letters, numbers, hyphens and underscores')
        return v.upper()  # Standardize SKUs to uppercase
    
    # Accept any non-empty location string
    @validator('from_location', 'to_location')
    def validate_location(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError('Location cannot be empty')
        return v.upper() if v else v  # Standardize locations to uppercase if not None
    
    @root_validator(pre=True, skip_on_failure=True)
    def validate_locations_for_type(cls, values):
        order_type = values.get('type')
        from_location = values.get('from_location')
        to_location = values.get('to_location')
        
        # Check if qty is provided instead of quantity
        if 'qty' in values and 'quantity' not in values:
            values['quantity'] = values['qty']
        
        if order_type == "Add" and to_location is None:
            raise ValueError('to_location is required for Add operations')
        
        if order_type == "Remove" and from_location is None:
            raise ValueError('from_location is required for Remove operations')
        
        if order_type == "Transfer":
            if from_location is None:
                raise ValueError('from_location is required for Transfer operations')
            if to_location is None:
                raise ValueError('to_location is required for Transfer operations')
            if from_location == to_location:
                raise ValueError('from_location and to_location cannot be the same for Transfer operations')
        
        return values