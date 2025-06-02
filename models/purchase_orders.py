from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, Literal, List, Union
import re

class FindPurchaseOrderRequest(BaseModel):
    po_number: Optional[str] = Field(None, max_length=50)
    barcode: Optional[Union[str, List[str]]] = Field(None)
    
    @validator('barcode')
    def validate_barcode(cls, v):
        if v is None:
            return v
            
        # If it's a single barcode
        if isinstance(v, str):
            if not re.match(r'^[0-9]{8,14}$', v):
                raise ValueError('Barcode must be between 8 and 14 digits')
            return v
        
        # If it's a list of barcodes
        if isinstance(v, list):
            if len(v) == 0:
                raise ValueError('Barcode list cannot be empty')
                
            for barcode in v:
                if not isinstance(barcode, str):
                    raise ValueError('Barcode list must contain only strings')
                if not re.match(r'^[0-9]{8,14}$', barcode):
                    raise ValueError(f'Barcode {barcode} must be between 8 and 14 digits')
            
            return v
            
        raise ValueError('Barcode must be a string or a list of strings')
    
    # Using root_validator instead of field validator to simplify
    @root_validator(pre=True)
    def validate_at_least_one_field(cls, values):
        po_number = values.get('po_number')
        barcode = values.get('barcode')
        
        if po_number is None and barcode is None:
            raise ValueError('Either po_number or barcode must be provided')
            
        return values
        
class CheckSkuAgainstPoRequest(BaseModel):
    po_number: str = Field(..., max_length=50)
    barcode: str = Field(..., max_length=27)
    
    @validator('po_number')
    def validate_po_number(cls, v):
        if not v or v.strip() == "":
            raise ValueError('PO number cannot be empty')
        return v
    
    @validator('barcode')
    def validate_barcode(cls, v):
        if not re.match(r'^[0-9]{8,14}$', v):
            raise ValueError('Barcode must be between 8 and 14 digits')
        return v

class UpdatePoStatusRequest(BaseModel):
    po_number: str = Field(..., max_length=50)
    status: Literal["Complete", "Incomplete", "Unassigned"] = Field(...)
    
    @validator('po_number')
    def validate_po_number(cls, v):
        if not v or v.strip() == "":
            raise ValueError('PO number cannot be empty')
        return v
    
class GetPurchaseOrderRequest(BaseModel):
    po_number: str = Field(..., max_length=50)
    
    @validator('po_number')
    def validate_po_number(cls, v):
        if not v or v.strip() == "":
            raise ValueError('PO number cannot be empty')
        return v