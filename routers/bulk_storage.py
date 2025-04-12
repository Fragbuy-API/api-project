from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from datetime import datetime
import json
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models.bulk_storage import BulkStorageOrder
from api.database import execute_with_retry

router = APIRouter(
    prefix="/api/v1",
    tags=["bulk_storage"]
)

@router.post("/bulkStorage")
async def create_bulk_storage(order: BulkStorageOrder):
    try:
        # Check if location already has a pending order
        check_query = text("""
            SELECT COUNT(*) FROM bulk_storage_orders WHERE location = :location
        """)
        result = execute_with_retry(check_query, {'location': order.location})
        if result.fetchone()[0] > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": f"Location {order.location} already has a pending order",
                    "error_code": "DUPLICATE_LOCATION",
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Calculate total quantity for validation
        total_quantity = sum(item.quantity for item in order.items)
        if total_quantity > 1000000:  # Higher limit for bulk storage
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": "Total quantity exceeds maximum allowed (1,000,000)",
                    "error_code": "QUANTITY_EXCEEDED",
                    "timestamp": datetime.now().isoformat()
                }
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
                execute_with_retry(
                    text("DELETE FROM bulk_storage_orders WHERE id = :id"),
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
            "message": f"Bulk storage order created successfully for location {order.location}",
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