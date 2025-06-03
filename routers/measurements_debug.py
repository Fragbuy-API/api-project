from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text
from datetime import datetime
import json
import base64
import os
import re
from pathlib import Path
import glob
import sys
import logging

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.measurement_debug import ProductDataDebug
from database import execute_with_retry
from services.measurement_processor import MeasurementProcessor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["measurements_debug"]
)

# Initialize the measurement processor
measurement_processor = MeasurementProcessor(execute_with_retry)

@router.post("/measurement_debug")
async def receive_measurement_debug(request: Request, product: ProductDataDebug):
    """
    Debug version of measurement endpoint that logs all incoming data
    """
    try:
        # LOG: Get raw JSON body
        body = await request.body()
        logger.info(f"=== RAW JSON RECEIVED ===")
        logger.info(f"Content-Type: {request.headers.get('content-type', 'Unknown')}")
        logger.info(f"Content-Length: {len(body)}")
        
        # Try to parse and log formatted JSON
        try:
            raw_json = json.loads(body.decode('utf-8'))
            logger.info(f"Parsed JSON structure:")
            
            # Log each field separately for clarity
            for key, value in raw_json.items():
                if key in ['image', 'imageseg', 'imagecolor']:
                    if isinstance(value, str):
                        if value.startswith('data:'):
                            logger.info(f"{key}: [BASE64 DATA - {len(value)} chars]")
                        elif value.startswith('/'):
                            logger.info(f"{key}: [FILE PATH] {value}")
                        else:
                            logger.info(f"{key}: [STRING] {value[:100]}...")
                    else:
                        logger.info(f"{key}: {value}")
                else:
                    logger.info(f"{key}: {value}")
                    
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.info(f"Raw body: {body.decode('utf-8')[:1000]}...")
        
        # LOG: Parsed ProductData object
        logger.info(f"=== PARSED PRODUCT DATA ===")
        logger.info(f"Barcode: {product.barcode}")
        logger.info(f"Dimensions: L={product.l}, W={product.w}, H={product.h}")
        logger.info(f"Weight: {product.weight}")
        logger.info(f"Device: {product.device}")
        logger.info(f"Attributes: {product.attributes}")
        
        # LOG: Image data analysis
        logger.info(f"=== IMAGE DATA ANALYSIS ===")
        
        def analyze_image_field(field_name, field_value):
            if not field_value:
                logger.info(f"{field_name}: [EMPTY]")
                return None, "empty"
            
            if field_value.startswith('data:'):
                logger.info(f"{field_name}: [BASE64 DATA] {len(field_value)} chars")
                return field_value, "base64"
            elif field_value.startswith('/'):
                logger.info(f"{field_name}: [FILE PATH] {field_value}")
                return field_value, "file_path"
            else:
                logger.info(f"{field_name}: [UNKNOWN FORMAT] {field_value[:50]}...")
                return field_value, "unknown"
        
        image_data, image_type = analyze_image_field("image", product.image)
        imageseg_data, imageseg_type = analyze_image_field("imageseg", product.imageseg)
        imagecolor_data, imagecolor_type = analyze_image_field("imagecolor", product.imagecolor)
        
        # Extract SKU from attributes if available
        sku = product.attributes.get('sku', 'UNKNOWN')
        logger.info(f"Extracted SKU: {sku}")
        
        # Get timestamp for filenames
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Define image storage directory
        base_storage_dir = os.path.join(os.path.dirname(__file__), "..", "image_storage")
        sku_storage_dir = os.path.join(base_storage_dir, sku)
        
        # Create directory if it doesn't exist
        os.makedirs(sku_storage_dir, exist_ok=True)
        logger.info(f"Image storage directory: {sku_storage_dir}")
        
        # Process and save images based on type
        image_path = None
        imageseg_path = None
        imagecolor_path = None
        
        def process_image(field_name, data, data_type, suffix):
            if not data:
                return None
                
            try:
                if data_type == "base64":
                    # Handle base64 data
                    content = data
                    if ',' in content:
                        _, content = content.split(',', 1)
                    
                    filename = f"{timestamp_str}_{suffix}.jpg"
                    file_path = os.path.join(sku, filename)
                    full_path = os.path.join(base_storage_dir, file_path)
                    
                    with open(full_path, "wb") as f:
                        f.write(base64.b64decode(content))
                    
                    logger.info(f"Saved {field_name} as {full_path}")
                    return file_path
                    
                elif data_type == "file_path":
                    # For file paths, we'll just store the path reference
                    # In a real scenario, you might want to download/copy the file
                    logger.info(f"Storing file path reference for {field_name}: {data}")
                    return data
                    
                else:
                    logger.warning(f"Unknown data type for {field_name}: {data_type}")
                    return data
                    
            except Exception as e:
                logger.error(f"Error processing {field_name}: {e}")
                return None
        
        # Process each image
        image_path = process_image("image", image_data, image_type, "image")
        imageseg_path = process_image("imageseg", imageseg_data, imageseg_type, "imageseg")
        imagecolor_path = process_image("imagecolor", imagecolor_data, imagecolor_type, "imagecolor")
        
        # Only cleanup if we actually saved files (not file paths)
        if any(t == "base64" for t in [image_type, imageseg_type, imagecolor_type]):
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
            'image': image_path,
            'imageseg': imageseg_path,
            'imagecolor': imagecolor_path
        }
        
        logger.info(f"=== DATABASE PARAMETERS ===")
        for key, value in params.items():
            if key in ['image', 'imageseg', 'imagecolor']:
                logger.info(f"{key}: {value}")
            else:
                logger.info(f"{key}: {value}")
        
        # Execute the query with retry logic
        execute_with_retry(query, params)
        
        # Enhanced measurement processing
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
            
            logger.info(f"=== PROCESSING MEASUREMENT DATA ===")
            # Process the measurement data
            processing_results = measurement_processor.process_measurement(measurement_data)
            logger.info(f"Processing results: {processing_results}")
            
        except Exception as processing_error:
            logger.error(f"Measurement processing error: {str(processing_error)}")
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
            "debug_info": {
                "image_types": {
                    "image": image_type,
                    "imageseg": imageseg_type,
                    "imagecolor": imagecolor_type
                },
                "sku_extracted": sku,
                "storage_directory": sku_storage_dir
            },
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
        
        logger.info(f"=== FINAL RESPONSE ===")
        logger.info(f"Response: {json.dumps(response, indent=2)}")
        
        return response
    
    except Exception as e:
        logger.error(f"=== ERROR OCCURRED ===")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        
        # Enhanced error handling
        if "image" in str(e).lower() or "base64" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": f"Image processing error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

def cleanup_old_images(sku_dir):
    """
    Keep only the 3 most recent sets of images for each SKU.
    A 'set' consists of images with the same timestamp prefix.
    """
    try:
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
    
    except Exception as e:
        logger.error(f"Error during image cleanup: {str(e)}")
