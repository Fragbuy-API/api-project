from pydantic import BaseModel, Field
from typing import Optional

class WarehouseLocation(BaseModel):
    """
    Model for warehouse location data.
    """
    warehouse: str = Field(..., description="Warehouse identifier")
    location_code: str = Field(..., description="Location code within the warehouse")
    location_name: str = Field(..., description="Descriptive name for the location")
    
class WarehouseLocationFilter(BaseModel):
    """
    Model for warehouse location filtering.
    """
    warehouse: Optional[str] = Field(None, description="Filter by warehouse identifier")