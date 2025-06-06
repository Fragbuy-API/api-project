from fastapi import FastAPI, HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import create_engine, text, exc
from sqlalchemy.pool import QueuePool
import json
from datetime import datetime
import time
import logging
import traceback
import uuid

# Import routers
from routers import measurements, putaway, bulk_storage, barcode, product, purchase_orders, replenishment, art_orders, warehouse_locations, proship, monitoring
from routers.filesystem import router as fs_router
from routers.measurements_debug import router as debug_router

# Import models
from models.measurement import ProductData

# Import database functions
from database import log_api_request, get_api_error_rates, get_endpoint_performance_stats, get_recent_errors

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

# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")
        
        # Add request ID to headers for downstream use
        request.state.request_id = request_id
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log the request
            try:
                log_api_request(
                    endpoint=str(request.url.path),
                    method=request.method,
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    request_id=request_id,
                    error_message=None,
                    ip_address=client_ip,
                    user_agent=user_agent
                )
            except Exception as e:
                logger.error(f"Failed to log request: {str(e)}")
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log the error request
            try:
                log_api_request(
                    endpoint=str(request.url.path),
                    method=request.method,
                    status_code=500,
                    response_time_ms=response_time_ms,
                    request_id=request_id,
                    error_message=str(e),
                    ip_address=client_ip,
                    user_agent=user_agent
                )
            except Exception as log_error:
                logger.error(f"Failed to log error request: {str(log_error)}")
            
            # Re-raise the exception
            raise e

# FastAPI application setup
app = FastAPI(
    title="Qboid API Project",
    description="Warehouse management and e-commerce integration system",
    version="1.0.0",
    openapi_url="/openapi.json",
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

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

@app.get("/api/v1/health")
async def health_check():
    """Comprehensive health check endpoint with detailed error handling and monitoring data"""
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
        
        # Get monitoring data
        error_rates = get_api_error_rates(hours=1)
        endpoint_stats = get_endpoint_performance_stats()
        recent_errors = get_recent_errors(limit=5)
        
        # Determine overall health status
        overall_status = "healthy"
        health_issues = []
        
        # Check error rates
        if isinstance(error_rates, dict) and 'error_rate_percent' in error_rates:
            if error_rates['error_rate_percent'] > 10:  # More than 10% errors
                overall_status = "degraded"
                health_issues.append(f"High error rate: {error_rates['error_rate_percent']}%")
            elif error_rates['error_rate_percent'] > 5:  # More than 5% errors
                if overall_status == "healthy":
                    overall_status = "warning"
                health_issues.append(f"Elevated error rate: {error_rates['error_rate_percent']}%")
        
        # Check average response time
        if isinstance(error_rates, dict) and 'avg_response_time_ms' in error_rates:
            if error_rates['avg_response_time_ms'] > 2000:  # More than 2 seconds
                overall_status = "degraded"
                health_issues.append(f"Slow response time: {error_rates['avg_response_time_ms']}ms")
            elif error_rates['avg_response_time_ms'] > 1000:  # More than 1 second
                if overall_status == "healthy":
                    overall_status = "warning"
                health_issues.append(f"Elevated response time: {error_rates['avg_response_time_ms']}ms")
        
        log_operation_success("health check", f"API and database are {overall_status}")
        
        response = {
            "status": overall_status,
            "message": "API is running and database is connected",
            "database": "connected",
            "timestamp": datetime.now().isoformat(),
            "monitoring": {
                "error_rates_1h": error_rates,
                "endpoint_performance_24h": endpoint_stats,
                "recent_errors": recent_errors
            }
        }
        
        if health_issues:
            response["health_issues"] = health_issues
        
        return response
        
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
    app.include_router(monitoring.router)  # Monitoring and metrics endpoints
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
