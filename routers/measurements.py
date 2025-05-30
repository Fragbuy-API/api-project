from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from datetime import datetime
import json
import base64
import os
import re
from pathlib import Path
import glob
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.measurement import ProductData
from api.database import execute_with_retry

router = APIRouter(
    prefix="/api/v1",
    tags=["measurements"]
)

@router.post("/measurement")
async def receive_measurement(product: ProductData):
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
        
        return {
            "status": "success",
            "message": f"Data received and stored successfully for barcode {product.barcode}",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
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
                    print(f"Deleted old image: {file}")
    
    except Exception as e:
        print(f"Error during image cleanup: {str(e)}")
        # Log the error but don't let it disrupt the main process

@router.get("/product_image/{sku}/{image_filename}")
async def get_product_image(sku: str, image_filename: str):
    """
    Retrieve a product image by SKU and filename.
    """
    try:
        # Validate the filename to prevent directory traversal attacks
        if '..' in image_filename or '/' in image_filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
            
        # Build the full path
        base_storage_dir = os.path.join(os.path.dirname(__file__), "..", "image_storage")
        file_path = os.path.join(base_storage_dir, sku, image_filename)
        
        # Check if file exists
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="Image not found")
            
        # Determine content type
        content_type = "image/jpeg"  # Assume JPEG by default
        if image_filename.lower().endswith(".png"):
            content_type = "image/png"
            
        # Return the image file
        from fastapi.responses import FileResponse
        return FileResponse(file_path, media_type=content_type)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))