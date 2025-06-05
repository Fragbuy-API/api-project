from fastapi import APIRouter, HTTPException
from sqlalchemy import text, exc
from datetime import datetime
import json
import base64
import os
import re
from pathlib import Path
import glob
import sys
import logging
import traceback

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.measurement import ProductData
from api.database import execute_with_retry
from services.measurement_processor import MeasurementProcessor

# Import standardized error handling
from error_handlers import (
    handle_database_error, handle_server_error, handle_business_logic_error,
    log_operation_start, log_operation_success, log_operation_warning,
    ErrorCodes, create_error_response
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["measurements"]
)

# Initialize the measurement processor
measurement_processor = MeasurementProcessor(execute_with_retry)

@router.post("/measurement")
async def receive_measurement(product: ProductData):
    log_operation_start("measurement processing", barcode=product.barcode, device=product.device)
    
    try:
        # Extract SKU from attributes if available
        sku = product.attributes.get('sku', 'UNKNOWN')
        
        # Get timestamp for filenames
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Define image storage directory
        base_storage_dir = os.path.join(os.path.dirname(__file__), "..", "image_storage")
        sku_storage_dir = os.path.join(base_storage_dir, sku)
        
        # Create directory if it doesn't exist
        os.makedirs(sku_storage_dir, exist_ok=True)
        
        # Process and save images
        image_path = None
        imageseg_path = None
        imagecolor_path = None
        
        # Save main image if present
        if product.image and product.image.strip():
            # Extract base64 content
            content = product.image
            if ',' in content:
                _, content = content.split(',', 1)
                
            # Define filename and path
            image_filename = f"{timestamp_str}_image.jpg"
            image_path = os.path.join(sku, image_filename)
            full_path = os.path.join(base_storage_dir, image_path)
            
            # Save image to file
            with open(full_path, "wb") as f:
                f.write(base64.b64decode(content))
        
        # Save segmentation image if present
        if product.imageseg and product.imageseg.strip():
            # Extract base64 content
            content = product.imageseg
            if ',' in content:
                _, content = content.split(',', 1)
                
            # Define filename and path
            imageseg_filename = f"{timestamp_str}_imageseg.jpg"
            imageseg_path = os.path.join(sku, imageseg_filename)
            full_path = os.path.join(base_storage_dir, imageseg_path)
            
            # Save image to file
            with open(full_path, "wb") as f:
                f.write(base64.b64decode(content))
        
        # Save color image if present
        if product.imagecolor and product.imagecolor.strip():
            # Extract base64 content
            content = product.imagecolor
            if ',' in content:
                _, content = content.split(',', 1)
                
            # Define filename and path
            imagecolor_filename = f"{timestamp_str}_imagecolor.jpg"
            imagecolor_path = os.path.join(sku, imagecolor_filename)
            full_path = os.path.join(base_storage_dir, imagecolor_path)
            
            # Save image to file
            with open(full_path, "wb") as f:
                f.write(base64.b64decode(content))
        
        # Cleanup old images (keep only 3 most recent sets)
        cleanup_old_images(sku_storage_dir)
        
        # Convert the attributes dict to JSON string
        attributes_json = json.dumps(product.attributes)
        
        # Prepare the SQL query
        query = text("""
            INSERT INTO api_received_data 
            (timestamp, sku, barcode, weight_value, weight_unit, 
             length, width, height, dimension_unit, shape, 
             device, note, attributes, image_original, imageseg, imagecolor)
            VALUES 
            (:timestamp, :sku, :barcode, :weight_value, :weight_unit,
             :length, :width, :height, :dimension_unit, :shape,
             :device, :note, :attributes, :image, :imageseg, :imagecolor)
        """)
        
        # Prepare the parameters
        params = {
            'timestamp': datetime.now(),
            'sku': sku,
            'barcode': product.barcode,
            'weight_value': product.weight,
            'weight_unit': 'g',
            'length': product.l,
            'width': product.w,
            'height': product.h,
            'dimension_unit': 'mm',
            'shape': product.shape,
            'device': product.device,
            'note': product.note,
            'attributes': attributes_json,
            'image': image_path,  # Store path instead of raw image data
            'imageseg': imageseg_path,
            'imagecolor': imagecolor_path
        }
        
        # Execute the query with retry logic
        execute_with_retry(query, params)
        logger.info(f"Successfully stored measurement data for barcode {product.barcode}")
        
        # NEW: Enhanced measurement processing
        processing_results = None
        try:
            # Prepare measurement data for processing
            measurement_data = {
                "barcode": product.barcode,
                "weight": product.weight,
                "l": product.l,
                "w": product.w,
                "h": product.h,
                "attributes": product.attributes
            }
            
            # Process the measurement data
            processing_results = measurement_processor.process_measurement(measurement_data)
            logger.info(f"Measurement processing completed for barcode {product.barcode}")
            
        except Exception as processing_error:
            # Log processing error but don't fail the entire request
            log_operation_warning("measurement processing", f"Processing failed for barcode {product.barcode}: {str(processing_error)}")
            processing_results = {
                "barcode": product.barcode,
                "sku_found": False,
                "errors": [f"Processing failed: {str(processing_error)}"],
                "updates_made": []
            }
        
        # Build response with processing information
        response = {
            "status": "success",
            "message": f"Data received and stored successfully for barcode {product.barcode}",
            "timestamp": datetime.now().isoformat(),
            "images_saved": {
                "main_image": image_path is not None,
                "segmentation": imageseg_path is not None,
                "color_image": imagecolor_path is not None
            }
        }
        
        # Add processing results if available
        if processing_results:
            response["processing"] = {
                "sku_lookup": {
                    "success": processing_results.get("sku_found", False),
                    "sku": processing_results.get("sku")
                },
                "updates": {
                    "dimensions_updated": processing_results.get("dimensions_updated", False),
                    "weight_updated": processing_results.get("weight_updated", False),
                    "attributes_updated": processing_results.get("attributes_updated", False),
                    "fields_updated": processing_results.get("updates_made", [])
                },
                "errors": processing_results.get("errors", [])
            }
        
        log_operation_success("measurement processing", f"completed for barcode {product.barcode}")
        return response
    
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error during measurement processing: {str(e)}")
        raise handle_database_error(e, "measurement data storage")
    except (ValueError, TypeError) as e:
        # Image processing or data format errors
        if "image" in str(e).lower() or "base64" in str(e).lower():
            logger.error(f"Image processing error for barcode {product.barcode}: {str(e)}")
            raise handle_business_logic_error(
                f"Image processing error: {str(e)}",
                ErrorCodes.VALIDATION_ERROR,
                400
            )
        else:
            logger.error(f"Data validation error for barcode {product.barcode}: {str(e)}")
            raise handle_business_logic_error(
                f"Data validation error: {str(e)}",
                ErrorCodes.VALIDATION_ERROR,
                400
            )
    except Exception as e:
        logger.error(f"Unexpected error during measurement processing: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                status_code=500,
                message=f"Server error during measurement processing: {str(e)}",
                error_code=ErrorCodes.SERVER_ERROR
            )
        )

def cleanup_old_images(sku_dir):
    """
    Keep only the 3 most recent sets of images for each SKU.
    A 'set' consists of images with the same timestamp prefix.
    """
    try:
        logger.debug(f"Starting image cleanup for directory: {sku_dir}")
        # Get all unique timestamps from filenames
        timestamps = set()
        for file in os.listdir(sku_dir):
            match = re.match(r'(\d{8}_\d{6})_', file)
            if match:
                timestamps.add(match.group(1))
        
        # If we have more than 3 timestamps, delete the oldest ones
        if len(timestamps) > 3:
            # Sort timestamps (newest first)
            sorted_timestamps = sorted(timestamps, reverse=True)
            
            # Get timestamps to delete (all except the 3 newest)
            timestamps_to_delete = sorted_timestamps[3:]
            
            # Delete files with these timestamps
            for ts in timestamps_to_delete:
                for file in glob.glob(os.path.join(sku_dir, f"{ts}_*")):
                    os.remove(file)
                    logger.info(f"Deleted old image: {file}")
            
            logger.info(f"Image cleanup completed: removed {len(timestamps_to_delete)} old timestamp sets")
    
    except Exception as e:
        logger.error(f"Error during image cleanup: {str(e)}")
        # Log the error but don't let it disrupt the main process

@router.get("/product_image/{sku}/{image_filename}")
async def get_product_image(sku: str, image_filename: str):
    """
    Retrieve a product image by SKU and filename.
    """
    log_operation_start("image retrieval", sku=sku, filename=image_filename)
    
    try:
        # Validate the filename to prevent directory traversal attacks
        if '..' in image_filename or '/' in image_filename:
            logger.warning(f"Invalid filename attempted: {image_filename}")
            raise handle_business_logic_error(
                "Invalid filename - path traversal not allowed",
                ErrorCodes.VALIDATION_ERROR,
                400
            )
            
        # Build the full path
        base_storage_dir = os.path.join(os.path.dirname(__file__), "..", "image_storage")
        file_path = os.path.join(base_storage_dir, sku, image_filename)
        
        # Check if file exists
        if not os.path.isfile(file_path):
            logger.info(f"Image not found: {file_path}")
            raise HTTPException(
                status_code=404,
                detail=create_error_response(
                    status_code=404,
                    message=f"Image {image_filename} not found for SKU {sku}",
                    error_code="IMAGE_NOT_FOUND"
                )
            )
            
        # Determine content type
        content_type = "image/jpeg"  # Assume JPEG by default
        if image_filename.lower().endswith(".png"):
            content_type = "image/png"
            
        log_operation_success("image retrieval", f"serving {image_filename} for SKU {sku}")
            
        # Return the image file
        from fastapi.responses import FileResponse
        return FileResponse(file_path, media_type=content_type)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving image {image_filename} for SKU {sku}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                status_code=500,
                message=f"Server error retrieving image: {str(e)}",
                error_code=ErrorCodes.SERVER_ERROR
            )
        )
