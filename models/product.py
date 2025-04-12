from pydantic import BaseModel, Field, validator
from typing import Optional
import re

class ProductSearch(BaseModel):
    """
    Model for product search input. A single search term that searches both SKU and description.
    """
    query: str = Field(..., min_length=1, max_length=255, description="Search term to find in SKU or description")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of results to return")
    
    @validator('query')
    def validate_query(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Search query cannot be empty')
        return v.strip()