from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import re

class ProductDataDebug(BaseModel):
    """
    Debug version of ProductData with enhanced logging and validation
    Supports Phase 4 attributes format
    """
    timestamp: Optional[str] = None
    l: Optional[int] = Field(None, ge=1, le=10000)  # Length in mm
    w: Optional[int] = Field(None, ge=1, le=10000)  # Width in mm
    h: Optional[int] = Field(None, ge=1, le=10000)  # Height in mm
    weight: Optional[int] = Field(None, ge=1, le=100000)  # Weight in g
    barcode: str = Field(..., max_length=50)
    shape: str = Field(..., max_length=100)
    device: str = Field(..., max_length=50)
    note: Optional[str] = Field(None, max_length=1000)
    attributes: Dict[str, Any]
    photo: Optional[str] = None  # NEW: Main product image from QBoid
    image: Optional[str] = None
    imageseg: Optional[str] = None
    imagecolor: Optional[str] = None

    @validator('barcode')
    def validate_barcode(cls, v):
        if not re.match(r'^[0-9]{8,14}$', v):
            raise ValueError('Barcode must be between 8 and 14 digits')
        return v

    @validator('device')
    def validate_device(cls, v):
        if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
            raise ValueError('Device must contain only letters, numbers, hyphens and underscores')
        return v

    @validator('attributes')
    def validate_attributes(cls, v):
        """
        Validate Phase 4 attributes format:
        - cap-tstr: "true" or "false" (maps to nocap, inverted)
        - cello: "true" or "false" (maps to nocello, inverted)  
        - origin: country name string (optional)
        - origin2: additional country name string (optional)
        
        Debug version provides detailed validation logging
        """
        
        # Log all received attributes for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Validating attributes: {v}")
        
        # Check for cap-tstr (required)
        if 'cap-tstr' not in v:
            logger.error("Missing required attribute: cap-tstr")
            raise ValueError('Required attribute cap-tstr is missing')
        
        cap_tstr = v.get('cap-tstr')
        if cap_tstr not in ['true', 'false']:
            logger.error(f"Invalid cap-tstr value: {cap_tstr}")
            raise ValueError('Attribute cap-tstr must be "true" or "false"')
        logger.info(f"cap-tstr validation passed: {cap_tstr}")
        
        # Check for cello (required)
        if 'cello' not in v:
            logger.error("Missing required attribute: cello")
            raise ValueError('Required attribute cello is missing')
            
        cello = v.get('cello')
        if cello not in ['true', 'false']:
            logger.error(f"Invalid cello value: {cello}")
            raise ValueError('Attribute cello must be "true" or "false"')
        logger.info(f"cello validation passed: {cello}")
        
        # Validate origin if present (optional)
        origin = v.get('origin')
        if origin is not None:
            if not isinstance(origin, str) or len(origin.strip()) == 0:
                logger.error(f"Invalid origin value: {origin}")
                raise ValueError('Attribute origin must be a non-empty string')
            if len(origin.strip()) > 100:
                logger.error(f"Origin too long: {len(origin)} chars")
                raise ValueError('Attribute origin must be 100 characters or less')
            logger.info(f"origin validation passed: {origin}")
        else:
            logger.info("origin not provided (optional)")
        
        # Validate origin2 if present (optional)
        origin2 = v.get('origin2')
        if origin2 is not None:
            if not isinstance(origin2, str) or len(origin2.strip()) == 0:
                logger.error(f"Invalid origin2 value: {origin2}")
                raise ValueError('Attribute origin2 must be a non-empty string')
            if len(origin2.strip()) > 100:
                logger.error(f"Origin2 too long: {len(origin2)} chars")
                raise ValueError('Attribute origin2 must be 100 characters or less')
            logger.info(f"origin2 validation passed: {origin2}")
        else:
            logger.info("origin2 not provided (optional)")
        
        # Validate SKU if present (optional, used for image storage directory)
        sku = v.get('sku')
        if sku is not None:
            if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', sku):
                logger.error(f"Invalid SKU format: {sku}")
                raise ValueError('SKU must contain only letters, numbers, hyphens and underscores')
            logger.info(f"SKU validation passed: {sku}")
        else:
            logger.info("SKU not provided (will default to UNKNOWN)")
        
        logger.info("All attribute validations passed")
        return v