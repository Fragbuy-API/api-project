from fastapi import APIRouter, HTTPException
from sqlalchemy import text, exc
from datetime import datetime
import logging
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database connection
from database import execute_with_retry
from models.proship import ParentOrderUpdateRequest, OrderCancelledRequest

# Import standardized error handling
from error_handlers import (
    handle_database_error, handle_server_error, handle_not_found_error, handle_business_logic_error,
    log_operation_start, log_operation_success, log_operation_warning,
    ErrorCodes, create_error_response
)

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
    log_operation_start("parent order update", order_count=len(request.items))
    
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
                    log_operation_warning("parent order update", f"order not found: {item.orderId}")
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
                
                logger.debug(f"Successfully updated parentOrderId for order {item.orderId}")
                updated_count += 1
                
            except Exception as e:
                log_operation_warning("parent order update", f"failed to update order {item.orderId}: {str(e)}")
                failed_count += 1
                failed_orders.append({
                    "orderId": item.orderId,
                    "reason": str(e)
                })
        
        # Prepare the response
        response_status = "success" if failed_count == 0 else "partial_success"
        log_operation_success("parent order update", f"completed: {updated_count} updated, {failed_count} failed")
        
        return {
            "status": response_status,
            "message": f"Updated {updated_count} orders, {failed_count} failed",
            "updatedCount": updated_count,
            "failedCount": failed_count,
            "failedOrders": failed_orders,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except exc.SQLAlchemyError as e:
        raise handle_database_error(e, "parent order update")
    except Exception as e:
        raise handle_server_error(e, "parent order update")

@router.post("/order_cancelled")
async def check_order_cancelled(request: OrderCancelledRequest):
    """
    Check if an order is cancelled.
    
    This endpoint accepts an orderId and returns a boolean value indicating
    whether the order status is "cancelled".
    """
    log_operation_start("order cancelled check", order_id=request.orderId)
    
    try:
        # Query the order status from the database
        query = text("""
            SELECT orderStatus FROM orders WHERE orderId = :orderId
        """)
        
        result = execute_with_retry(query, {'orderId': request.orderId})
        row = result.fetchone()
        
        # Check if order exists
        if row is None:
            raise handle_not_found_error("Order", request.orderId, ErrorCodes.ORDER_NOT_FOUND)
        
        # Check if order status is "cancelled"
        order_status = row[0]
        is_cancelled = order_status.lower() == "cancelled"
        
        log_operation_success("order cancelled check", f"order {request.orderId} status: {order_status}, cancelled: {is_cancelled}")
        
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
    except exc.SQLAlchemyError as e:
        raise handle_database_error(e, "order cancelled check")
    except Exception as e:
        raise handle_server_error(e, "order cancelled check")

@router.get("/proship-health")
async def proship_health():
    """
    Health check endpoint for the ProShip integration
    """
    log_operation_start("ProShip health check")
    
    try:
        log_operation_success("ProShip health check", "all endpoints available")
        return {
            "status": "healthy",
            "message": "ProShip integration API endpoints are available",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise handle_server_error(e, "ProShip health check")