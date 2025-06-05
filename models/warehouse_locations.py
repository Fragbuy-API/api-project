from pydantic import BaseModel, Field, validator
from typing import Optional
import re
import logging

# Setup logging for model validation
logger = logging.getLogger(__name__)

class WarehouseLocationValidationError(ValueError):
    """Custom exception for warehouse location validation errors"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.error_code = error_code

class WarehouseLocation(BaseModel):
    """
    Model for warehouse location data.
    """
    warehouse: str = Field(..., description="Warehouse identifier")
    location_code: str = Field(..., description="Location code within the warehouse")
    location_name: str = Field(..., description="Descriptive name for the location")
    
    @validator('warehouse')
    def validate_warehouse(cls, v):
        if not v or not v.strip():
            logger.warning("Empty warehouse identifier provided")
            raise WarehouseLocationValidationError(
                'Warehouse identifier cannot be empty',
                'WAREHOUSE_EMPTY'
            )
        
        v = v.strip().upper()
        
        if len(v) > 50:
            logger.warning(f"Warehouse identifier too long: {len(v)} characters")
            raise WarehouseLocationValidationError(
                'Warehouse identifier cannot exceed 50 characters',
                'WAREHOUSE_TOO_LONG'
            )
        
        # Allow alphanumeric, hyphens, and underscores
        if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
            logger.warning(f"Invalid warehouse identifier format: {v}")
            raise WarehouseLocationValidationError(
                'Warehouse identifier must contain only letters, numbers, hyphens and underscores',
                'WAREHOUSE_INVALID_FORMAT'
            )
        
        logger.info(f"Warehouse identifier validated: {v}")
        return v
    
    @validator('location_code')
    def validate_location_code(cls, v):
        if not v or not v.strip():
            logger.warning("Empty location code provided")
            raise WarehouseLocationValidationError(
                'Location code cannot be empty',
                'LOCATION_CODE_EMPTY'
            )
        
        v = v.strip().upper()
        
        if len(v) > 30:
            logger.warning(f"Location code too long: {len(v)} characters")
            raise WarehouseLocationValidationError(
                'Location code cannot exceed 30 characters',
                'LOCATION_CODE_TOO_LONG'
            )
        
        # Allow alphanumeric, hyphens, and underscores
        if not re.match(r'^[A-Za-z0-9\-_]{1,30}$', v):
            logger.warning(f"Invalid location code format: {v}")
            raise WarehouseLocationValidationError(
                'Location code must contain only letters, numbers, hyphens and underscores',
                'LOCATION_CODE_INVALID_FORMAT'
            )
        
        logger.info(f"Location code validated: {v}")
        return v
    
    @validator('location_name')
    def validate_location_name(cls, v):
        if not v or not v.strip():
            logger.warning("Empty location name provided")
            raise WarehouseLocationValidationError(
                'Location name cannot be empty',
                'LOCATION_NAME_EMPTY'
            )
        
        v = v.strip()
        
        if len(v) > 255:
            logger.warning(f"Location name too long: {len(v)} characters")
            raise WarehouseLocationValidationError(
                'Location name cannot exceed 255 characters',
                'LOCATION_NAME_TOO_LONG'
            )
        
        # Allow more flexible characters for names but prevent dangerous ones
        if re.search(r'[<>"\\\\]', v):
            logger.warning(f"Location name contains invalid characters: {v}")
            raise WarehouseLocationValidationError(
                'Location name cannot contain < > " or \\\\ characters',
                'LOCATION_NAME_INVALID_CHARS'
            )
        
        logger.info(f"Location name validated: {v[:50]}{'...' if len(v) > 50 else ''}")
        return v
    
class WarehouseLocationFilter(BaseModel):
    """
    Model for warehouse location filtering.
    """
    warehouse: Optional[str] = Field(None, description="Filter by warehouse identifier")
    
    @validator('warehouse')
    def validate_warehouse_filter(cls, v):
        if v is not None:
            if not v.strip():
                logger.warning("Empty warehouse filter provided")
                raise WarehouseLocationValidationError(
                    'Warehouse filter cannot be empty string',
                    'WAREHOUSE_FILTER_EMPTY'
                )
            
            v = v.strip().upper()
            
            if len(v) > 50:
                logger.warning(f"Warehouse filter too long: {len(v)} characters")
                raise WarehouseLocationValidationError(
                    'Warehouse filter cannot exceed 50 characters',
                    'WAREHOUSE_FILTER_TOO_LONG'
                )
            
            # Allow alphanumeric, hyphens, and underscores
            if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
                logger.warning(f"Invalid warehouse filter format: {v}")
                raise WarehouseLocationValidationError(
                    'Warehouse filter must contain only letters, numbers, hyphens and underscores',
                    'WAREHOUSE_FILTER_INVALID_FORMAT'
                )
            
            logger.info(f"Warehouse filter validated: {v}")
        
        return v
