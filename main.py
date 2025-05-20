from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text, exc
from sqlalchemy.pool import QueuePool
from typing import Optional, Dict
import json
from datetime import datetime
import time

# Import routers
from routers import measurements, putaway, bulk_storage, barcode, product, purchase_orders, replenishment, art_orders, warehouse_locations, proship
from routers.filesystem import router as fs_router

app = FastAPI(
    title="Fragbuy API Project",
    version="1.0.0",
    openapi_url="/openapi.json",
)

# Database connection with pooling and reconnection settings
DATABASE_URL = "mysql+pymysql://Qboid:JY8xM2ch5#Q[@155.138.159.75/products"
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True  # Enable automatic reconnection
)

# Data model for the incoming JSON
class ProductData(BaseModel):
    timestamp: Optional[str] = None
    l: Optional[int] = None
    w: Optional[int] = None
    h: Optional[int] = None
    weight: Optional[int] = None
    barcode: str
    shape: str
    device: str
    note: Optional[str] = None
    attributes: Dict
    image: Optional[str] = None
    imageseg: Optional[str] = None
    imagecolor: Optional[str] = None

app = FastAPI()

def execute_with_retry(query, params, max_retries=3):
    """Execute a database query with retry logic"""
    for attempt in range(max_retries):
        try:
            with engine.connect() as connection:
                result = connection.execute(query, params)
                connection.commit()
                return result
        except exc.OperationalError as e:
            if attempt == max_retries - 1:  # Last attempt
                raise  # Re-raise the last error
            time.sleep(1 * (attempt + 1))  # Exponential backoff
            continue

@app.post("/api/v1/measurement")
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
        
        # Extract SKU from barcode or attributes if available
        sku = product.attributes.get('sku', 'UNKNOWN')
        
        # Prepare the parameters
        params = {
            'timestamp': datetime.now(),
            'sku': sku,
            'barcode': product.barcode,
            'weight_value': product.weight,
            'weight_unit': 'g',  # Default to grams as per the sample data
            'length': product.l,
            'width': product.w,
            'height': product.h,
            'dimension_unit': 'mm',  # Default to millimeters as per the sample data
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

@app.get("/api/v1/health")
async def health_check():
    try:
        # Test database connection with retry logic
        execute_with_retry(text("SELECT 1"), {})
        
        return {
            "status": "healthy",
            "message": "API is running and database is connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# Include routers
app.include_router(measurements.router)
app.include_router(putaway.router)
app.include_router(bulk_storage.router)
app.include_router(barcode.router)  
app.include_router(product.router)  
app.include_router(purchase_orders.router)
app.include_router(replenishment.router)
app.include_router(art_orders.router)  
app.include_router(warehouse_locations.router)
app.include_router(proship.router)
app.include_router(fs_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)