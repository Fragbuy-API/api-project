from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from datetime import datetime
import logging
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database connection
from database import execute_with_retry

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
    logger.info(f"Warehouse locations request received. Filter warehouse: {warehouse}")
    
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
            logger.info(f"Filtering by warehouse: {warehouse}")
        else:
            query = text("""
                SELECT warehouse, location_code, location_name
                FROM warehouse_locations
                ORDER BY warehouse, location_code
            """)
            params = {}
            logger.info("No filter applied, returning all locations")
        
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
            logger.info("No warehouse locations found")
            
            return {
                "status": "success",
                "message": "No warehouse locations found",
                "count": 0,
                "locations": [],
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"Found {len(locations)} warehouse locations")
        
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
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error retrieving warehouse locations: {error_msg}\n{error_trace}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Server error: {error_msg}",
                "error_code": "SERVER_ERROR",
                "timestamp": datetime.now().isoformat()
            }
        )

# Health check endpoint
@router.get("/warehouse-locations-health")
async def warehouse_locations_health():
    """
    Health check endpoint for the warehouse locations API
    """
    try:
        return {
            "status": "healthy",
            "message": "Warehouse locations API endpoint is available",
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