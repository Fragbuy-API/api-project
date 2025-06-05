from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from datetime import datetime
import json
import logging
import traceback
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from models.putaway import PutawayOrder
from api.database import execute_with_retry

# Import standardized error handling
from error_handlers import (
    handle_database_error, handle_business_logic_error, handle_server_error,
    log_operation_start, log_operation_success, log_operation_warning,
    ErrorCodes, create_error_response
)

router = APIRouter(
    prefix="/api/v1",
    tags=["putaway"]
)

@router.post("/putawayOrder")
async def create_putaway_order(order: PutawayOrder):
    log_operation_start("putaway order creation", tote=order.tote, items_count=len(order.items))
    
    try:
        # Check if tote already exists
        check_query = text("""
            SELECT COUNT(*) FROM putaway_orders WHERE tote = :tote
        """)
        result = execute_with_retry(check_query, {'tote': order.tote})
        if result.fetchone()[0] > 0:
            logger.warning(f"Attempt to create putaway order with duplicate tote: {order.tote}")
            raise handle_business_logic_error(
                f"Tote {order.tote} already exists in the system",
                ErrorCodes.DUPLICATE_TOTE,
                400
            )

        # Calculate total quantity for validation
        total_quantity = sum(item.quantity for item in order.items)
        if total_quantity > 100000:  # Example business rule
            logger.warning(f"Putaway order total quantity {total_quantity} exceeds maximum (100,000)")
            raise handle_business_logic_error(
                "Total quantity exceeds maximum allowed (100,000)",
                ErrorCodes.QUANTITY_EXCEEDED,
                400
            )

        # Add inventory check placeholder here, before inserting records
        # PLACEHOLDER: Check inventory for sufficient stock
        # In a real implementation, we would query the inventory table here
        sufficient_stock = True  # Default to TRUE
        
        # Override for testing purposes
        if order.test_insufficient_stock:
            logger.info(f"Test flag enabled - simulating insufficient stock for putaway order")
            sufficient_stock = False
            
        if not sufficient_stock:
            logger.warning(f"Insufficient stock for putaway order with tote {order.tote}")
            raise handle_business_logic_error(
                "Insufficient stock to fulfill this putaway order",
                ErrorCodes.INSUFFICIENT_STOCK,
                400
            )
        
        # Insert the main order record
        order_query = text("""
            INSERT INTO putaway_orders 
            (tote, timestamp) 
            VALUES 
            (:tote, :timestamp)
            RETURNING id
        """)
        
        result = execute_with_retry(order_query, {
            'tote': order.tote,
            'timestamp': datetime.now()
        })
        
        order_id = result.fetchone()[0]
        
        # Insert items
        item_query = text("""
            INSERT INTO putaway_items 
            (order_id, sku, name, barcode, quantity) 
            VALUES 
            (:order_id, :sku, :name, :barcode, :quantity)
        """)
        
        for item in order.items:
            try:
                execute_with_retry(item_query, {
                    'order_id': order_id,
                    'sku': item.sku,
                    'name': item.name,
                    'barcode': item.barcode,
                    'quantity': item.quantity
                })
            except IntegrityError as e:
                # Rollback the entire order if any item fails
                logger.error(f"Integrity error inserting item with SKU {item.sku}: {str(e)}")
                try:
                    execute_with_retry(
                        text("DELETE FROM putaway_orders WHERE id = :id"),
                        {'id': order_id}
                    )
                    logger.info(f"Rolled back putaway order {order_id} due to item insertion failure")
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback putaway order {order_id}: {str(rollback_error)}")
                
                raise handle_business_logic_error(
                    f"Error inserting item with SKU {item.sku}",
                    ErrorCodes.ITEM_INSERT_FAILED,
                    400
                )
        
        log_operation_success("putaway order creation", f"created order {order_id} for tote {order.tote} with {len(order.items)} items")
        
        return {
            "status": "success",
            "message": f"Putaway order created successfully for tote {order.tote}",
            "order_id": order_id,
            "timestamp": datetime.now().isoformat(),
            "items_processed": len(order.items),
            "total_quantity": total_quantity
        }
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise handle_database_error(e, "putaway order creation")
    except Exception as e:
        logger.error(f"Unexpected error during putaway order creation: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                status_code=500,
                message=f"Server error during putaway order creation: {str(e)}",
                error_code=ErrorCodes.SERVER_ERROR
            )
        )