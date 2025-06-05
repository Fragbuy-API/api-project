from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import re
import logging

# Setup logging for model validation
logger = logging.getLogger(__name__)

class MeasurementValidationError(ValueError):
    """Custom exception for measurement validation errors"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message)
        self.error_code = error_code

class ProductDataDebug(BaseModel):
    """
    Debug version of ProductData with enhanced logging and validation
    Supports Phase 4 attributes format
    """
    timestamp: Optional[str] = Field(None, description="Timestamp of measurement (optional)")
    l: Optional[int] = Field(None, ge=1, le=10000, description="Length in mm (1-10,000)")
    w: Optional[int] = Field(None, ge=1, le=10000, description="Width in mm (1-10,000)")
    h: Optional[int] = Field(None, ge=1, le=10000, description="Height in mm (1-10,000)")
    weight: Optional[int] = Field(None, ge=1, le=100000, description="Weight in g (1-100,000)")
    barcode: str = Field(..., max_length=50, description="Product barcode (8-14 digits)")
    shape: str = Field(..., max_length=100, description="Product shape description")
    device: str = Field(..., max_length=50, description="Measurement device identifier")
    note: Optional[str] = Field(None, max_length=1000, description="Optional measurement notes")
    attributes: Dict[str, Any] = Field(..., description="Product attributes (cap-tstr, cello, origin, etc.)")
    photo: Optional[str] = Field(None, description="Main product image from QBoid (optional)")
    image: Optional[str] = Field(None, description="Base64 encoded product image (optional)")
    imageseg: Optional[str] = Field(None, description="Base64 encoded segmentation image (optional)")
    imagecolor: Optional[str] = Field(None, description="Base64 encoded color image (optional)")

    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None  # Convert empty string to None
            # Could add ISO format validation here if needed
        return v

    @validator('barcode')
    def validate_barcode(cls, v):
        if not v or not v.strip():
            logger.warning("Empty barcode provided for measurement")
            raise MeasurementValidationError(
                'Barcode cannot be empty', 
                'BARCODE_EMPTY'
            )
        
        v = v.strip()
        
        # Allow "NA" as a special case for unavailable barcodes
        if v.upper() == "NA":
            return v.upper()
        
        if not re.match(r'^[0-9]{8,14}$', v):
            logger.warning(f"Invalid barcode format provided: {v}")
            raise MeasurementValidationError(
                'Barcode must be between 8 and 14 digits or "NA" for not available', 
                'BARCODE_INVALID_FORMAT'
            )
        
        return v

    @validator('shape')
    def validate_shape(cls, v):
        if not v or not v.strip():
            logger.warning("Empty shape provided for measurement")
            raise MeasurementValidationError(
                'Shape description cannot be empty', 
                'SHAPE_EMPTY'
            )
        
        v = v.strip()
        
        if len(v) > 100:
            logger.warning(f"Shape description too long: {len(v)} characters")
            raise MeasurementValidationError(
                'Shape description cannot exceed 100 characters', 
                'SHAPE_TOO_LONG'
            )
        
        return v

    @validator('device')
    def validate_device(cls, v):
        if not v or not v.strip():
            logger.warning("Empty device identifier provided")
            raise MeasurementValidationError(
                'Device identifier cannot be empty', 
                'DEVICE_EMPTY'
            )
        
        v = v.strip()
        
        if len(v) > 50:
            logger.warning(f"Device identifier too long: {len(v)} characters")
            raise MeasurementValidationError(
                'Device identifier cannot exceed 50 characters', 
                'DEVICE_TOO_LONG'
            )
        
        if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', v):
            logger.warning(f"Invalid device format provided: {v}")
            raise MeasurementValidationError(
                'Device must contain only letters, numbers, hyphens and underscores', 
                'DEVICE_INVALID_FORMAT'
            )
        
        return v

    @validator('note')
    def validate_note(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None  # Convert empty string to None
            
            if len(v) > 1000:
                logger.warning(f"Note too long: {len(v)} characters")
                raise MeasurementValidationError(
                    'Note cannot exceed 1000 characters', 
                    'NOTE_TOO_LONG'
                )
        
        return v

    @validator('l', 'w', 'h')
    def validate_dimensions(cls, v, field):
        if v is not None:
            if v <= 0:
                logger.warning(f"Invalid {field.name} dimension: {v}")
                raise MeasurementValidationError(
                    f'{field.name.upper()} dimension must be greater than 0', 
                    f'{field.name.upper()}_INVALID'
                )
            
            if v > 10000:
                logger.warning(f"{field.name.upper()} dimension too large: {v}")
                raise MeasurementValidationError(
                    f'{field.name.upper()} dimension cannot exceed 10,000 mm', 
                    f'{field.name.upper()}_TOO_LARGE'
                )
        
        return v

    @validator('weight')
    def validate_weight(cls, v):
        if v is not None:
            if v <= 0:
                logger.warning(f"Invalid weight: {v}")
                raise MeasurementValidationError(
                    'Weight must be greater than 0', 
                    'WEIGHT_INVALID'
                )
            
            if v > 100000:
                logger.warning(f"Weight too large: {v}")
                raise MeasurementValidationError(
                    'Weight cannot exceed 100,000 grams', 
                    'WEIGHT_TOO_LARGE'
                )
        
        return v

    @validator('attributes')
    def validate_attributes(cls, v):
        """
        Validate Phase 4 attributes format:
        - cap-tstr: "true" or "false" (maps to nocap, inverted)
        - cello: "true" or "false" (maps to nocello, inverted)  
        - origin: country name string (optional)
        - origin2: additional country name string (optional)
        
        Enhanced version with standardized error handling
        """
        
        # Log all received attributes for debugging
        logger.info(f"Validating attributes: {v}")
        
        if not isinstance(v, dict):
            logger.error(f"Attributes must be a dictionary, got {type(v)}")
            raise MeasurementValidationError(
                'Attributes must be a dictionary', 
                'ATTRIBUTES_INVALID_TYPE'
            )
        
        # Check for cap-tstr (required)
        if 'cap-tstr' not in v:
            logger.error("Missing required attribute: cap-tstr")
            raise MeasurementValidationError(
                'Required attribute cap-tstr is missing', 
                'CAP_TSTR_MISSING'
            )
        
        cap_tstr = v.get('cap-tstr')
        if cap_tstr not in ['true', 'false']:
            logger.error(f"Invalid cap-tstr value: {cap_tstr}")
            raise MeasurementValidationError(
                'Attribute cap-tstr must be "true" or "false"', 
                'CAP_TSTR_INVALID'
            )
        logger.info(f"cap-tstr validation passed: {cap_tstr}")
        
        # Check for cello (required)
        if 'cello' not in v:
            logger.error("Missing required attribute: cello")
            raise MeasurementValidationError(
                'Required attribute cello is missing', 
                'CELLO_MISSING'
            )
            
        cello = v.get('cello')
        if cello not in ['true', 'false']:
            logger.error(f"Invalid cello value: {cello}")
            raise MeasurementValidationError(
                'Attribute cello must be "true" or "false"', 
                'CELLO_INVALID'
            )
        logger.info(f"cello validation passed: {cello}")
        
        # Validate origin if present (optional)
        origin = v.get('origin')
        if origin is not None:
            if not isinstance(origin, str) or len(origin.strip()) == 0:
                logger.error(f"Invalid origin value: {origin}")
                raise MeasurementValidationError(
                    'Attribute origin must be a non-empty string', 
                    'ORIGIN_INVALID'
                )
            if len(origin.strip()) > 100:
                logger.error(f"Origin too long: {len(origin)} chars")
                raise MeasurementValidationError(
                    'Attribute origin must be 100 characters or less', 
                    'ORIGIN_TOO_LONG'
                )
            logger.info(f"origin validation passed: {origin}")
        else:
            logger.info("origin not provided (optional)")
        
        # Validate origin2 if present (optional)
        origin2 = v.get('origin2')
        if origin2 is not None:
            if not isinstance(origin2, str) or len(origin2.strip()) == 0:
                logger.error(f"Invalid origin2 value: {origin2}")
                raise MeasurementValidationError(
                    'Attribute origin2 must be a non-empty string', 
                    'ORIGIN2_INVALID'
                )
            if len(origin2.strip()) > 100:
                logger.error(f"Origin2 too long: {len(origin2)} chars")
                raise MeasurementValidationError(
                    'Attribute origin2 must be 100 characters or less', 
                    'ORIGIN2_TOO_LONG'
                )
            logger.info(f"origin2 validation passed: {origin2}")
        else:
            logger.info("origin2 not provided (optional)")
        
        # Validate SKU if present (optional, used for image storage directory)
        sku = v.get('sku')
        if sku is not None:
            if not isinstance(sku, str) or len(sku.strip()) == 0:
                logger.error(f"Invalid SKU value: {sku}")
                raise MeasurementValidationError(
                    'SKU must be a non-empty string', 
                    'SKU_INVALID'
                )
            
            sku_cleaned = sku.strip().upper()
            if not re.match(r'^[A-Za-z0-9\-_]{1,50}$', sku_cleaned):
                logger.error(f"Invalid SKU format: {sku}")
                raise MeasurementValidationError(
                    'SKU must contain only letters, numbers, hyphens and underscores', 
                    'SKU_INVALID_FORMAT'
                )
            logger.info(f"SKU validation passed: {sku}")
        else:
            logger.info("SKU not provided (will default to UNKNOWN)")
        
        logger.info("All attribute validations passed")
        return v

# Legacy alias for backward compatibility
ProductData = ProductDataDebug