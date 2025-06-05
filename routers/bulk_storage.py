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

from models.bulk_storage import BulkStorageOrder
from api.database import execute_with_retry

# Import standardized error handling
from error_handlers import (
    handle_database_error, handle_business_logic_error, handle_server_error,
    log_operation_start, log_operation_success, log_operation_warning,
    ErrorCodes, create_error_response
)

# Rest of the file remains the same

router = APIRouter(
    prefix="/api/v1",
    tags=["bulk_storage"]
)

@router.post("/bulkStorage")
async def create_bulk_storage(order: BulkStorageOrder):
    log_operation_start("bulk storage order creation", location=order.location, items_count=len(order.items))
    
    try:
        # Check if location already has a pending order
        check_query = text("""
            SELECT COUNT(*) FROM bulk_storage_orders WHERE location = :location
        """)
        result = execute_with_retry(check_query, {'location': order.location})
        if result.fetchone()[0] > 0:
            logger.warning(f"Attempt to create bulk storage order at location with pending order: {order.location}")
            raise handle_business_logic_error(
                f"Location {order.location} already has a pending order",
                ErrorCodes.DUPLICATE_LOCATION,
                400
            )

        # Calculate total quantity for validation
        total_quantity = sum(item.quantity for item in order.items)
        if total_quantity > 1000000:  # Higher limit for bulk storage
            logger.warning(f"Bulk storage order total quantity {total_quantity} exceeds maximum (1,000,000)")
            raise handle_business_logic_error(
                "Total quantity exceeds maximum allowed (1,000,000)",
                ErrorCodes.QUANTITY_EXCEEDED,
                400
            )

        # Add inventory check placeholder here, before inserting records
        # PLACEHOLDER: Check inventory for sufficient stock
        # In a real implementation, we would query the inventory table here
        sufficient_stock = True  # Default to TRUE
        
        # Override for testing purposes
        if order.test_insufficient_stock:
            logger.info(f"Test flag enabled - simulating insufficient stock for bulk storage order")
            sufficient_stock = False
            
        if not sufficient_stock:
            logger.warning(f"Insufficient stock for bulk storage order at location {order.location}")
            raise handle_business_logic_error(
                "Insufficient stock to fulfill this bulk storage order",
                ErrorCodes.INSUFFICIENT_STOCK,
                400
            )
        
        # Insert the main order record
        order_query = text("""
            INSERT INTO bulk_storage_orders 
            (location, timestamp) 
            VALUES 
            (:location, :timestamp)
            RETURNING id
        """)
        
        result = execute_with_retry(order_query, {
            'location': order.location,
            'timestamp': datetime.now()
        })
        
        order_id = result.fetchone()[0]
        
        # Insert items
        item_query = text("""
            INSERT INTO bulk_storage_items 
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
                        text("DELETE FROM bulk_storage_orders WHERE id = :id"),
                        {'id': order_id}
                    )
                    logger.info(f"Rolled back bulk storage order {order_id} due to item insertion failure")
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback bulk storage order {order_id}: {str(rollback_error)}")
                
                raise handle_business_logic_error(
                    f"Error inserting item with SKU {item.sku}",
                    ErrorCodes.ITEM_INSERT_FAILED,
                    400
                )
        
        log_operation_success("bulk storage order creation", f"created order {order_id} for location {order.location} with {len(order.items)} items")
        
        return {
            "status": "success",
            "message": f"Bulk storage order created successfully for location {order.location}",
            "order_id": order_id,
            "timestamp": datetime.now().isoformat(),
            "items_processed": len(order.items),
            "total_quantity": total_quantity
        }
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise handle_database_error(e, "bulk storage order creation")
    except Exception as e:
        logger.error(f"Unexpected error during bulk storage order creation: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                status_code=500,
                message=f"Server error during bulk storage order creation: {str(e)}",
                error_code=ErrorCodes.SERVER_ERROR
            )
        )