from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, Literal
import re
import logging

# Setup logging for model validation
logger = logging.getLogger(__name__)

class ArtOrderValidationError(ValueError):
    """Custom exception for ART order validation errors"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.error_code = error_code

class ArtOrder(BaseModel):
    """
    Model for Ad Hoc Add/Remove/Transfer (ART) operations.
    Handles validation for all three operation types.
    """
    type: Literal["Add", "Remove", "Transfer"] = Field(..., description="Type of operation (Add, Remove, or Transfer)")
    sku: str = Field(..., max_length=50, description="Stock Keeping Unit identifier")
    quantity: int = Field(..., gt=0, le=1000000, description="Quantity to add, remove, or transfer (1-1,000,000)")
    from_location: Optional[str] = Field(None, max_length=30, description="Source location (required for Remove and Transfer)")
    to_location: Optional[str] = Field(None, max_length=30, description="Destination location (required for Add and Transfer)")
    reason: Optional[str] = Field(None, max_length=255, description="Reason for the operation (optional)")
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
        if not v or not v.strip():
            logger.warning("Empty SKU provided for ART order")
            raise ArtOrderValidationError(
                'SKU cannot be empty', 
                'SKU_EMPTY'
            )
        
        # Remove any whitespace and convert to uppercase
        v = v.strip().upper()
        
        if len(v) > 50:
            logger.warning(f"SKU too long: {len(v)} characters")
            raise ArtOrderValidationError(
                'SKU cannot exceed 50 characters', 
                'SKU_TOO_LONG'
            )
        
        if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
            logger.warning(f"Invalid SKU format provided: {v}")
            raise ArtOrderValidationError(
                'SKU must contain only letters, numbers, hyphens and underscores', 
                'SKU_INVALID_FORMAT'
            )
        
        return v
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            logger.warning(f"Invalid quantity provided: {v}")
            raise ArtOrderValidationError(
                'Quantity must be greater than 0', 
                'QUANTITY_INVALID'
            )
        
        if v > 1000000:
            logger.warning(f"Quantity too high: {v}")
            raise ArtOrderValidationError(
                'Quantity cannot exceed 1,000,000 units', 
                'QUANTITY_TOO_HIGH'
            )
        
        return v
    
    @validator('reason')
    def validate_reason(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None  # Convert empty string to None
            if len(v) > 255:
                logger.warning(f"Reason too long: {len(v)} characters")
                raise ArtOrderValidationError(
                    'Reason cannot exceed 255 characters', 
                    'REASON_TOO_LONG'
                )
        return v
    
    # Accept any non-empty location string
    @validator('from_location', 'to_location')
    def validate_location(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                logger.warning("Empty location string provided")
                raise ArtOrderValidationError(
                    'Location cannot be empty', 
                    'LOCATION_EMPTY'
                )
            if len(v) > 30:
                logger.warning(f"Location too long: {len(v)} characters")
                raise ArtOrderValidationError(
                    'Location cannot exceed 30 characters', 
                    'LOCATION_TOO_LONG'
                )
            return v.upper()  # Standardize locations to uppercase
        return v
    
    @root_validator(pre=True, skip_on_failure=True)
    def validate_locations_for_type(cls, values):
        order_type = values.get('type')
        from_location = values.get('from_location')
        to_location = values.get('to_location')
        
        # Check if qty is provided instead of quantity (backward compatibility)
        if 'qty' in values and 'quantity' not in values:
            logger.info("Converting 'qty' field to 'quantity' for backward compatibility")
            values['quantity'] = values['qty']
        
        # Validate required locations based on operation type
        if order_type == "Add":
            if to_location is None or (isinstance(to_location, str) and to_location.strip() == ""):
                logger.warning("Missing to_location for Add operation")
                raise ArtOrderValidationError(
                    'to_location is required for Add operations', 
                    'TO_LOCATION_REQUIRED'
                )
        
        elif order_type == "Remove":
            if from_location is None or (isinstance(from_location, str) and from_location.strip() == ""):
                logger.warning("Missing from_location for Remove operation")
                raise ArtOrderValidationError(
                    'from_location is required for Remove operations', 
                    'FROM_LOCATION_REQUIRED'
                )
        
        elif order_type == "Transfer":
            if from_location is None or (isinstance(from_location, str) and from_location.strip() == ""):
                logger.warning("Missing from_location for Transfer operation")
                raise ArtOrderValidationError(
                    'from_location is required for Transfer operations', 
                    'FROM_LOCATION_REQUIRED'
                )
            if to_location is None or (isinstance(to_location, str) and to_location.strip() == ""):
                logger.warning("Missing to_location for Transfer operation")
                raise ArtOrderValidationError(
                    'to_location is required for Transfer operations', 
                    'TO_LOCATION_REQUIRED'
                )
            if from_location and to_location and from_location.strip().upper() == to_location.strip().upper():
                logger.warning(f"Same location used for Transfer: {from_location}")
                raise ArtOrderValidationError(
                    'from_location and to_location cannot be the same for Transfer operations', 
                    'LOCATIONS_SAME_FOR_TRANSFER'
                )
        
        return values