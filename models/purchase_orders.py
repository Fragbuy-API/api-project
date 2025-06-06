from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, Literal, List, Union
import re
import logging

# Setup logging for model validation
logger = logging.getLogger(__name__)

class PurchaseOrderValidationError(ValueError):
    """Custom exception for purchase order validation errors"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.error_code = error_code

class FindPurchaseOrderRequest(BaseModel):
    po_number: Optional[str] = Field(None, max_length=50, description="Purchase order number (partial match allowed)")
    barcode: Optional[Union[str, List[str]]] = Field(None, description="Single barcode or list of barcodes (8-14 digits each)")
    
    @validator('po_number')
    def validate_po_number(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None  # Convert empty string to None
            
            if len(v) > 50:
                logger.warning(f"PO number too long: {len(v)} characters")
                raise PurchaseOrderValidationError(
                    'PO number cannot exceed 50 characters', 
                    'PO_NUMBER_TOO_LONG'
                )
        
        return v
    
    @validator('barcode')
    def validate_barcode(cls, v):
        if v is None:
            return v
        
        # If it's a single barcode
        if isinstance(v, str):
            v = v.strip()
            if len(v) == 0:
                logger.warning("Empty barcode string provided")
                raise PurchaseOrderValidationError(
                    'Barcode cannot be empty', 
                    'BARCODE_EMPTY'
                )
            
            # Allow "NA" as a special case for unavailable barcodes
            if v.upper() == "NA":
                return v.upper()
            
            if not re.match(r'^[0-9]{8,14}$', v):
                logger.warning(f"Invalid barcode format provided: {v}")
                raise PurchaseOrderValidationError(
                    'Barcode must be between 8 and 14 digits or "NA" for not available', 
                    'BARCODE_INVALID_FORMAT'
                )
            return v
        
        # If it's a list of barcodes
        if isinstance(v, list):
            if len(v) == 0:
                logger.warning("Empty barcode list provided")
                raise PurchaseOrderValidationError(
                    'Barcode list cannot be empty', 
                    'BARCODE_LIST_EMPTY'
                )
            
            if len(v) > 50:  # Reasonable limit for list size
                logger.warning(f"Too many barcodes in list: {len(v)}")
                raise PurchaseOrderValidationError(
                    'Cannot process more than 50 barcodes in a single request', 
                    'BARCODE_LIST_TOO_LONG'
                )
                
            for i, barcode in enumerate(v):
                if not isinstance(barcode, str):
                    logger.warning(f"Non-string barcode in list at position {i}")
                    raise PurchaseOrderValidationError(
                        'Barcode list must contain only strings', 
                        'BARCODE_LIST_INVALID_TYPE'
                    )
                
                barcode = barcode.strip()
                if len(barcode) == 0:
                    logger.warning(f"Empty barcode in list at position {i}")
                    raise PurchaseOrderValidationError(
                        'Barcode list cannot contain empty strings', 
                        'BARCODE_LIST_EMPTY_ITEM'
                    )
                
                # Allow "NA" as a special case
                if barcode.upper() == "NA":
                    v[i] = barcode.upper()
                    continue
                
                if not re.match(r'^[0-9]{8,14}$', barcode):
                    logger.warning(f"Invalid barcode format in list: {barcode}")
                    raise PurchaseOrderValidationError(
                        f'Barcode {barcode} must be between 8 and 14 digits or "NA" for not available', 
                        'BARCODE_LIST_INVALID_FORMAT'
                    )
                v[i] = barcode
            
            return v
        
        logger.warning(f"Invalid barcode type: {type(v)}")
        raise PurchaseOrderValidationError(
            'Barcode must be a string or a list of strings', 
            'BARCODE_INVALID_TYPE'
        )
    
    @root_validator(pre=True)
    def validate_at_least_one_field(cls, values):
        po_number = values.get('po_number')
        barcode = values.get('barcode')
        
        # Handle empty strings as None
        if po_number is not None and isinstance(po_number, str) and po_number.strip() == "":
            po_number = None
            values['po_number'] = None
        
        if barcode is not None:
            if isinstance(barcode, str) and barcode.strip() == "":
                barcode = None
                values['barcode'] = None
            elif isinstance(barcode, list) and len(barcode) == 0:
                barcode = None
                values['barcode'] = None
        
        if po_number is None and barcode is None:
            logger.warning("Neither po_number nor barcode provided")
            raise PurchaseOrderValidationError(
                'Either po_number or barcode must be provided', 
                'MISSING_SEARCH_CRITERIA'
            )
            
        return values

class CheckSkuAgainstPoRequest(BaseModel):
    po_number: str = Field(..., max_length=50, description="Purchase order number (exact match required)")
    barcode: str = Field(..., max_length=27, description="Product barcode (8-14 digits)")
    
    @validator('po_number')
    def validate_po_number(cls, v):
        if not v or not v.strip():
            logger.warning("Empty PO number provided")
            raise PurchaseOrderValidationError(
                'PO number cannot be empty', 
                'PO_NUMBER_EMPTY'
            )
        
        v = v.strip()
        
        if len(v) > 50:
            logger.warning(f"PO number too long: {len(v)} characters")
            raise PurchaseOrderValidationError(
                'PO number cannot exceed 50 characters', 
                'PO_NUMBER_TOO_LONG'
            )
        
        return v
    
    @validator('barcode')
    def validate_barcode(cls, v):
        if not v or not v.strip():
            logger.warning("Empty barcode provided for SKU check")
            raise PurchaseOrderValidationError(
                'Barcode cannot be empty', 
                'BARCODE_EMPTY'
            )
        
        v = v.strip()
        
        # Allow "NA" as a special case for unavailable barcodes
        if v.upper() == "NA":
            return v.upper()
        
        if not re.match(r'^[0-9]{8,14}$', v):
            logger.warning(f"Invalid barcode format provided: {v}")
            raise PurchaseOrderValidationError(
                'Barcode must be between 8 and 14 digits or "NA" for not available', 
                'BARCODE_INVALID_FORMAT'
            )
        
        return v

class UpdatePoStatusRequest(BaseModel):
    po_number: str = Field(..., max_length=50, description="Purchase order number (exact match required)")
    status: Literal["NoneReceived", "PartiallyReceived", "Completed", "Cancelled"] = Field(..., description="New status for the purchase order")
    
    @validator('po_number')
    def validate_po_number(cls, v):
        if not v or not v.strip():
            logger.warning("Empty PO number provided for status update")
            raise PurchaseOrderValidationError(
                'PO number cannot be empty', 
                'PO_NUMBER_EMPTY'
            )
        
        v = v.strip()
        
        if len(v) > 50:
            logger.warning(f"PO number too long: {len(v)} characters")
            raise PurchaseOrderValidationError(
                'PO number cannot exceed 50 characters', 
                'PO_NUMBER_TOO_LONG'
            )
        
        return v

class GetPurchaseOrderRequest(BaseModel):
    po_number: str = Field(..., max_length=50, description="Purchase order number to retrieve (exact match required)")
    
    @validator('po_number')
    def validate_po_number(cls, v):
        if not v or not v.strip():
            logger.warning("Empty PO number provided for retrieval")
            raise PurchaseOrderValidationError(
                'PO number cannot be empty', 
                'PO_NUMBER_EMPTY'
            )
        
        v = v.strip()
        
        if len(v) > 50:
            logger.warning(f"PO number too long: {len(v)} characters")
            raise PurchaseOrderValidationError(
                'PO number cannot exceed 50 characters', 
                'PO_NUMBER_TOO_LONG'
            )
        
        return v