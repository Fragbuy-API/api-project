from pydantic import BaseModel, Field, validator
from typing import Optional
import re
import logging

# Setup logging for model validation
logger = logging.getLogger(__name__)

class ProductValidationError(ValueError):
    """Custom exception for product validation errors"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.error_code = error_code

class ProductSearch(BaseModel):
    """
    Model for product search input. A single search term that searches both SKU and description.
    """
    query: str = Field(..., min_length=1, max_length=255, description="Search term to find in SKU or description")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of results to return")
    
    @validator('query')
    def validate_query(cls, v):
        if not v or v.strip() == "":
            logger.warning("Empty search query provided")
            raise ProductValidationError(
                'Search query cannot be empty',
                'QUERY_EMPTY'
            )
        
        v = v.strip()
        
        if len(v) > 255:
            logger.warning(f"Search query too long: {len(v)} characters")
            raise ProductValidationError(
                'Search query cannot exceed 255 characters',
                'QUERY_TOO_LONG'
            )
        
        logger.info(f"Product search query validated: {v[:50]}{'...' if len(v) > 50 else ''}")
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        if v is not None:
            if v < 1:
                logger.warning(f"Invalid limit value: {v}")
                raise ProductValidationError(
                    'Limit must be at least 1',
                    'LIMIT_TOO_SMALL'
                )
            
            if v > 100:
                logger.warning(f"Limit too large: {v}")
                raise ProductValidationError(
                    'Limit cannot exceed 100',
                    'LIMIT_TOO_LARGE'
                )
            
            logger.info(f"Product search limit validated: {v}")
        
        return v