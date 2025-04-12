from fastapi import APIRouter, HTTPException
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
    tags=["replenishment"]
)

@router.get("/ro_get_orders")
async def ro_get_orders():
    """
    Get all replenishment orders that don't have status 'Completed'.
    Returns additional information including the number of SKUs in each order.
    """
    logger.info("ro_get_orders request received")
    
    try:
        # Query to get orders and count of SKUs
        query = text("""
            SELECT 
                ro.ro_id,
                ro.ro_date_created,
                ro.ro_status,
                ro.destination,
                COUNT(roi.sku) as skus_in_order
            FROM 
                replen_orders ro
            LEFT JOIN 
                replen_order_items roi ON ro.ro_id = roi.ro_id
            WHERE 
                ro.ro_status != 'Completed'
            GROUP BY 
                ro.ro_id, ro.ro_date_created, ro.ro_status, ro.destination
            ORDER BY 
                ro.ro_date_created DESC
        """)
        
        result = execute_with_retry(query, {})
        rows = result.fetchall()
        
        if not rows:
            logger.info("No active replenishment orders found")
            return {
                "status": "success",
                "message": "No active replenishment orders found",
                "orders": [],
                "count": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Process results
        orders = []
        for row in rows:
            order = {
                "ro_id": row[0],
                "ro_date_created": row[1].isoformat() if row[1] else None,
                "ro_status": row[2],
                "destination": row[3],
                "skus_in_order": row[4]
            }
            orders.append(order)
        
        logger.info(f"Found {len(orders)} active replenishment orders")
        return {
            "status": "success",
            "message": f"Found {len(orders)} active replenishment orders",
            "orders": orders,
            "count": len(orders),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in ro_get_orders: {error_msg}\n{error_trace}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Server error: {error_msg}",
                "error_code": "SERVER_ERROR",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/replenishment-health")
async def replenishment_health():
    """
    Health check endpoint for the replenishment router
    """
    try:
        return {
            "status": "healthy",
            "message": "Replenishment API endpoints are available",
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