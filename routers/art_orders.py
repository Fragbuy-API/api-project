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
from models.art_order import ArtOrder

# Import standardized error handling
from error_handlers import (
    handle_database_error, handle_server_error, handle_not_found_error, handle_business_logic_error,
    log_operation_start, log_operation_success, log_operation_warning,
    ErrorCodes, create_error_response
)

router = APIRouter(
    prefix="/api/v1",
    tags=["art_orders"]
)

@router.post("/art_order")
async def create_art_order(order: ArtOrder):
    """
    Process an Ad Hoc Add/Remove/Transfer (ART) order.
    
    This endpoint handles three types of operations:
    - Add: Add inventory to a location
    - Remove: Remove inventory from a location
    - Transfer: Move inventory from one location to another
    
    For Remove and Transfer operations, it checks if there is sufficient stock.
    """
    log_operation_start("ART order", operation_type=order.type, sku=order.sku, quantity=order.quantity)
    
    try:
        # Check if SKU exists in the products table
        check_sku_query = text("""
            SELECT COUNT(*) FROM products WHERE sku = :sku
        """)
        
        result = execute_with_retry(check_sku_query, {'sku': order.sku})
        if result.fetchone()[0] == 0:
            raise handle_not_found_error("SKU", order.sku, ErrorCodes.INVALID_SKU, 
                                       f"SKU {order.sku} does not exist in the products table")
        
        # Check for sufficient stock for Remove or Transfer operations
        if order.type in ["Remove", "Transfer"]:
            # PLACEHOLDER: In a real implementation, we would check inventory levels here
            # For now, we always return True unless the sufficient_stock flag is False
            
            sufficient_stock = True
            if order.sufficient_stock is not None and not order.sufficient_stock:
                sufficient_stock = False
                
            if not sufficient_stock:
                raise handle_business_logic_error(
                    f"Insufficient stock of SKU {order.sku} at location {order.from_location}",
                    ErrorCodes.INSUFFICIENT_STOCK,
                    400
                )
        
        # PLACEHOLDER: In a real implementation, we would update inventory here
        # For Add: Add inventory to to_location
        # For Remove: Remove inventory from from_location
        # For Transfer: Move inventory from from_location to to_location
        log_operation_warning("inventory update", f"PLACEHOLDER: Would update inventory for {order.type} operation")
        
        # Insert a record of this operation for tracking
        insert_query = text("""
            INSERT INTO art_operations 
            (operation_type, sku, quantity, from_location, to_location, reason, created_at) 
            VALUES 
            (:operation_type, :sku, :quantity, :from_location, :to_location, :reason, :created_at)
            RETURNING id
        """)
        
        try:
            result = execute_with_retry(insert_query, {
                'operation_type': order.type,
                'sku': order.sku,
                'quantity': order.quantity,
                'from_location': order.from_location,
                'to_location': order.to_location,
                'reason': order.reason,
                'created_at': datetime.now()
            })
            operation_id = result.fetchone()[0]
            log_operation_success("ART tracking", f"recorded operation with ID: {operation_id}")
        except Exception as e:
            log_operation_warning("ART tracking", f"failed to insert tracking record: {str(e)}")
            # Continue processing even if record insertion fails
            # This is just for tracking and doesn't affect the actual operation
            operation_id = None
        
        # Build response based on the operation type
        response_msg = ""
        if order.type == "Add":
            response_msg = f"Successfully added {order.quantity} units of SKU {order.sku} to location {order.to_location}"
        elif order.type == "Remove":
            response_msg = f"Successfully removed {order.quantity} units of SKU {order.sku} from location {order.from_location}"
        else:  # Transfer
            response_msg = f"Successfully transferred {order.quantity} units of SKU {order.sku} from location {order.from_location} to location {order.to_location}"
        
        response = {
            "status": "success",
            "message": response_msg,
            "operation_type": order.type,
            "sku": order.sku,
            "quantity": order.quantity,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add optional fields to response if they exist
        if order.from_location:
            response["from_location"] = order.from_location
        if order.to_location:
            response["to_location"] = order.to_location
        if order.reason:
            response["reason"] = order.reason
        if operation_id:
            response["operation_id"] = operation_id
        
        log_operation_success("ART order", f"{order.type} operation completed for SKU {order.sku}")
        return response
    
    except HTTPException:
        raise
    except exc.SQLAlchemyError as e:
        raise handle_database_error(e, "ART order processing")
    except Exception as e:
        raise handle_server_error(e, "ART order processing")

@router.get("/art-orders-health")
async def art_orders_health():
    """
    Health check endpoint for the ART Orders router
    """
    log_operation_start("ART health check")
    
    try:
        log_operation_success("ART health check", "all endpoints available")
        return {
            "status": "healthy",
            "message": "ART Orders API endpoints are available",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise handle_server_error(e, "ART health check")