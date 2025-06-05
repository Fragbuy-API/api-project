from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text, exc
from sqlalchemy.pool import QueuePool
import json
from datetime import datetime
import time
import logging
import traceback

# Import routers
from routers import measurements, putaway, bulk_storage, barcode, product, purchase_orders, replenishment, art_orders, warehouse_locations, proship
from routers.filesystem import router as fs_router
from routers.measurements_debug import router as debug_router

# Import models
from models.measurement import ProductData

# Import standardized error handling
from error_handlers import (
    handle_database_error, handle_server_error, log_operation_start, 
    log_operation_success, ErrorCodes, create_error_response
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI application setup
app = FastAPI(
    title="Qboid API Project",
    description="Warehouse management and e-commerce integration system",
    version="1.0.0",
    openapi_url="/openapi.json",
)

# Database connection with pooling and reconnection settings
DATABASE_URL = "mysql+pymysql://Qboid:JY8xM2ch5#Q[@155.138.159.75/products"
try:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,  # Recycle connections after 30 minutes
        pool_pre_ping=True  # Enable automatic reconnection
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

def execute_with_retry(query, params, max_retries=3):
    """Execute a database query with retry logic and enhanced error handling"""
    operation_id = f"query_{int(datetime.now().timestamp() * 1000)}"
    
    for attempt in range(max_retries):
        try:
            logger.info(f"[{operation_id}] Executing database query (attempt {attempt+1}/{max_retries})")
            
            with engine.connect() as connection:
                result = connection.execute(query, params)
                connection.commit()
                
                logger.info(f"[{operation_id}] Database query executed successfully")
                return result
                
        except exc.OperationalError as e:
            error_msg = str(e)
            logger.error(f"[{operation_id}] Database operational error on attempt {attempt+1}: {error_msg}")
            
            if attempt == max_retries - 1:  # Last attempt
                logger.error(f"[{operation_id}] Maximum retry attempts reached, raising exception")
                raise handle_database_error(e, "database query execution")
                
            sleep_time = 1 * (attempt + 1)  # Exponential backoff
            logger.info(f"[{operation_id}] Retrying in {sleep_time} seconds")
            time.sleep(sleep_time)
            continue
            
        except exc.SQLAlchemyError as e:
            logger.error(f"[{operation_id}] Database error on attempt {attempt+1}: {str(e)}")
            raise handle_database_error(e, "database query execution")
            
        except Exception as e:
            logger.error(f"[{operation_id}] Unexpected error during database query: {str(e)}")
            logger.error(f"[{operation_id}] Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=create_error_response(
                    status_code=500,
                    message=f"Unexpected error during database operation: {str(e)}",
                    error_code=ErrorCodes.SERVER_ERROR
                )
            )

@app.post("/api/v1/measurement")
async def receive_measurement(product: ProductData):
    """Receive and store product measurement data with comprehensive error handling"""
    log_operation_start("measurement data processing", barcode=product.barcode, device=product.device)
    
    try:
        # Convert the attributes dict to JSON string
        attributes_json = json.dumps(product.attributes)
        logger.info(f"Processing measurement for barcode: {product.barcode}, device: {product.device}")
        
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
        logger.info(f"Extracted SKU: {sku} for barcode: {product.barcode}")
        
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
        
        log_operation_success("measurement data processing", f"stored data for barcode {product.barcode}")
        
        return {
            "status": "success",
            "message": f"Data received and stored successfully for barcode {product.barcode}",
            "barcode": product.barcode,
            "sku": sku,
            "device": product.device,
            "timestamp": datetime.now().isoformat()
        }
    
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error during measurement processing: {str(e)}")
        raise handle_database_error(e, "measurement data insertion")
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON encoding error for attributes: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=create_error_response(
                status_code=400,
                message="Invalid attributes data - could not encode to JSON",
                error_code=ErrorCodes.VALIDATION_ERROR
            )
        )
        
    except ValueError as e:
        logger.error(f"Validation error during measurement processing: {str(e)}")
        # Check if it's a custom validation error with error_code
        error_code = getattr(e, 'error_code', ErrorCodes.VALIDATION_ERROR)
        raise HTTPException(
            status_code=422,
            detail=create_error_response(
                status_code=422,
                message=str(e),
                error_code=error_code
            )
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during measurement processing: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                status_code=500,
                message=f"Server error during measurement processing: {str(e)}",
                error_code=ErrorCodes.SERVER_ERROR
            )
        )

@app.get("/api/v1/health")
async def health_check():
    """Comprehensive health check endpoint with detailed error handling"""
    log_operation_start("health check")
    
    try:
        # Test database connection with retry logic
        logger.info("Testing database connection for health check")
        test_result = execute_with_retry(text("SELECT 1 as test_value"), {})
        
        # Verify we got the expected result
        row = test_result.fetchone()
        if row is None or row[0] != 1:
            logger.error("Health check failed - unexpected database response")
            raise HTTPException(
                status_code=503,
                detail=create_error_response(
                    status_code=503,
                    message="Database health check failed - unexpected response",
                    error_code=ErrorCodes.DATABASE_ERROR
                )
            )
        
        log_operation_success("health check", "API and database are healthy")
        
        return {
            "status": "healthy",
            "message": "API is running and database is connected",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
        
    except exc.SQLAlchemyError as e:
        logger.error(f"Health check failed - database error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=create_error_response(
                status_code=503,
                message="Database connection failed during health check",
                error_code=ErrorCodes.DATABASE_ERROR
            )
        )
        
    except HTTPException:
        # Re-raise HTTPExceptions (like those from execute_with_retry)
        raise
        
    except Exception as e:
        logger.error(f"Health check failed - unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=503,
            detail=create_error_response(
                status_code=503,
                message=f"Health check failed due to server error: {str(e)}",
                error_code=ErrorCodes.SERVER_ERROR
            )
        )

# Include routers with error handling
try:
    logger.info("Including API routers...")
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
    app.include_router(debug_router)  # Debug endpoint for measurement analysis
    logger.info("All API routers included successfully")
except Exception as e:
    logger.error(f"Failed to include API routers: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise

if __name__ == "__main__":
    try:
        import uvicorn
        logger.info("Starting Qboid API server...")
        logger.info("Server configuration: host=0.0.0.0, port=8000")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError as e:
        logger.error(f"Failed to import uvicorn: {str(e)}")
        print("Error: uvicorn is required to run the server. Install it with: pip install uvicorn")
        exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        exit(1)