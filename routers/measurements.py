from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from datetime import datetime
import json
import sys
import os

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
        
        # Extract SKU from attributes if available
        sku = product.attributes.get('sku', 'UNKNOWN')
        
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
            'image': product.image,
            'imageseg': product.imageseg,
            'imagecolor': product.imagecolor
        }
        
        # Execute the query with retry logic
        execute_with_retry(query, params)
        
        return {
            "status": "success",
            "message": f"Data received and stored successfully for barcode {product.barcode}",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )