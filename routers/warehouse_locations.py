from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text, exc
from datetime import datetime
import logging
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database connection
from database import execute_with_retry

# Import standardized error handling
from error_handlers import (
    handle_database_error, handle_server_error, handle_not_found_error, handle_business_logic_error,
    log_operation_start, log_operation_success, log_operation_warning,
    ErrorCodes, create_error_response
)

router = APIRouter(
    prefix="/api/v1",
    tags=["warehouse_locations"]
)

@router.get("/warehouse_locations")
async def get_warehouse_locations(warehouse: str = Query(None, description="Filter by warehouse identifier")):
    """
    Get all warehouse locations, with optional filtering by warehouse.
    Returns location data in JSON format.
    """
    log_operation_start("warehouse locations", warehouse_filter=warehouse)
    
    try:
        # Build query based on filter
        if warehouse:
            query = text("""
                SELECT warehouse, location_code, location_name
                FROM warehouse_locations
                WHERE warehouse = :warehouse
                ORDER BY warehouse, location_code
            """)
            params = {'warehouse': warehouse}
            logger.debug(f"Filtering by warehouse: {warehouse}")
        else:
            query = text("""
                SELECT warehouse, location_code, location_name
                FROM warehouse_locations
                ORDER BY warehouse, location_code
            """)
            params = {}
            logger.debug("No filter applied, returning all locations")
        
        # Execute the query
        result = execute_with_retry(query, params)
        
        # Process the results
        locations = []
        for row in result:
            location = {
                "warehouse": row[0],
                "location_code": row[1],
                "location_name": row[2]
            }
            locations.append(location)
        
        # Check if any locations were found
        if not locations:
            log_operation_success("warehouse locations", "no locations found matching criteria")
            
            return {
                "status": "success",
                "message": "No warehouse locations found",
                "count": 0,
                "locations": [],
                "timestamp": datetime.now().isoformat()
            }
        
        log_operation_success("warehouse locations", f"found {len(locations)} locations")
        
        # Return the results
        return {
            "status": "success",
            "message": f"Found {len(locations)} warehouse locations",
            "count": len(locations),
            "locations": locations,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except exc.SQLAlchemyError as e:
        raise handle_database_error(e, "warehouse locations retrieval")
    except Exception as e:
        raise handle_server_error(e, "warehouse locations retrieval")

# Health check endpoint
@router.get("/warehouse-locations-health")
async def warehouse_locations_health():
    """
    Health check endpoint for the warehouse locations API
    """
    log_operation_start("warehouse locations health check")
    
    try:
        log_operation_success("warehouse locations health check", "endpoint available")
        return {
            "status": "healthy",
            "message": "Warehouse locations API endpoint is available",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise handle_server_error(e, "warehouse locations health check")