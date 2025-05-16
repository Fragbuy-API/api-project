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

router = APIRouter(
    prefix="/api/v1",
    tags=["putaway"]
)

@router.post("/putawayOrder")
async def create_putaway_order(order: PutawayOrder):
    try:
        # Check if tote already exists
        check_query = text("""
            SELECT COUNT(*) FROM putaway_orders WHERE tote = :tote
        """)
        result = execute_with_retry(check_query, {'tote': order.tote})
        #if result.fetchone()[0] > 0:
        #    raise HTTPException(
        #        status_code=400,
        #        detail={
        #            "status": "error",
        #            "message": f"Tote {order.tote} already exists in the system",
        #            "error_code": "DUPLICATE_TOTE",
        #            "timestamp": datetime.now().isoformat()
        #        }
        #    )

        # Calculate total quantity for validation
        total_quantity = sum(item.quantity for item in order.items)
        if total_quantity > 100000:  # Example business rule
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": "Total quantity exceeds maximum allowed (100,000)",
                    "error_code": "QUANTITY_EXCEEDED",
                    "timestamp": datetime.now().isoformat()
                }
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
            logger.info(f"Insufficient stock for putaway order with tote {order.tote}")
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": "Insufficient stock to fulfill this putaway order",
                    "error_code": "INSUFFICIENT_STOCK",
                    "timestamp": datetime.now().isoformat()
                }
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
                execute_with_retry(
                    text("DELETE FROM putaway_orders WHERE id = :id"),
                    {'id': order_id}
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "error",
                        "message": f"Error inserting item with SKU {item.sku}",
                        "error_code": "ITEM_INSERT_FAILED",
                        "timestamp": datetime.now().isoformat()
                    }
                )
        
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
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Database error occurred",
                "error_code": "DATABASE_ERROR",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e),
                "error_code": "GENERAL_ERROR",
                "timestamp": datetime.now().isoformat()
            }
        )