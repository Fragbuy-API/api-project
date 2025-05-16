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
from models.proship import ParentOrderUpdateRequest, OrderCancelledRequest

router = APIRouter(
    prefix="/api/v1",
    tags=["proship"]
)

@router.post("/update_parent_orders")
async def update_parent_orders(request: ParentOrderUpdateRequest):
    """
    Update parent order IDs for the specified order IDs.
    
    This endpoint accepts a list of orderId and parentOrderId pairs and updates
    the database to set the parentOrderId for each specified order.
    """
    logger.info(f"Parent order update request received for {len(request.items)} orders")
    
    try:
        # Initialize counters for response
        updated_count = 0
        failed_count = 0
        failed_orders = []
        
        # Process each order in the request
        for item in request.items:
            try:
                # First check if the order exists
                check_query = text("""
                    SELECT COUNT(*) FROM orders WHERE orderId = :orderId
                """)
                
                result = execute_with_retry(check_query, {'orderId': item.orderId})
                if result.fetchone()[0] == 0:
                    logger.warning(f"Order not found: {item.orderId}")
                    failed_count += 1
                    failed_orders.append({
                        "orderId": item.orderId,
                        "reason": "Order not found"
                    })
                    continue
                
                # Update the parentOrderId for this order
                update_query = text("""
                    UPDATE orders 
                    SET parentOrderId = :parentOrderId 
                    WHERE orderId = :orderId
                """)
                
                execute_with_retry(update_query, {
                    'orderId': item.orderId,
                    'parentOrderId': item.parentOrderId
                })
                
                logger.info(f"Successfully updated parentOrderId for order {item.orderId}")
                updated_count += 1
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error updating order {item.orderId}: {error_msg}")
                failed_count += 1
                failed_orders.append({
                    "orderId": item.orderId,
                    "reason": error_msg
                })
        
        # Prepare the response
        return {
            "status": "success" if failed_count == 0 else "partial_success",
            "message": f"Updated {updated_count} orders, {failed_count} failed",
            "updatedCount": updated_count,
            "failedCount": failed_count,
            "failedOrders": failed_orders,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in update_parent_orders: {error_msg}\n{error_trace}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Server error: {error_msg}",
                "error_code": "SERVER_ERROR",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.post("/order_cancelled")
async def check_order_cancelled(request: OrderCancelledRequest):
    """
    Check if an order is cancelled.
    
    This endpoint accepts an orderId and returns a boolean value indicating
    whether the order status is "cancelled".
    """
    logger.info(f"Order cancelled check request received for order ID: {request.orderId}")
    
    try:
        # Query the order status from the database
        query = text("""
            SELECT orderStatus FROM orders WHERE orderId = :orderId
        """)
        
        result = execute_with_retry(query, {'orderId': request.orderId})
        row = result.fetchone()
        
        # Check if order exists
        if row is None:
            logger.warning(f"Order not found: {request.orderId}")
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"Order {request.orderId} not found",
                    "error_code": "ORDER_NOT_FOUND",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Check if order status is "cancelled"
        order_status = row[0]
        is_cancelled = order_status.lower() == "cancelled"
        
        logger.info(f"Order {request.orderId} has status '{order_status}', is_cancelled={is_cancelled}")
        
        # Return the result
        return {
            "status": "success",
            "orderId": request.orderId,
            "isCancelled": is_cancelled,
            "orderStatus": order_status,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in check_order_cancelled: {error_msg}\n{error_trace}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Server error: {error_msg}",
                "error_code": "SERVER_ERROR",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/proship-health")
async def proship_health():
    """
    Health check endpoint for the ProShip integration
    """
    try:
        return {
            "status": "healthy",
            "message": "ProShip integration API endpoints are available",
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