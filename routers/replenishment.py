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
from models.replenishment import ReplenishmentOrderRequest, ReplenishmentItemPickedRequest, ReplenishmentCancelRequest, ReplenishmentCompleteRequest

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

@router.post("/ro_retrieve_order")
async def ro_retrieve_order(request: ReplenishmentOrderRequest):
    """
    Retrieve details of a specific replenishment order by ro_id.
    Returns all items in the order from the replen_order_items table.
    Also changes the order status to "In Process" if it's currently "Unassigned".
    """
    logger.info(f"ro_retrieve_order request received for order ID: {request.ro_id}")
    
    try:
        # First check if the order exists
        order_query = text("""
            SELECT ro_id, ro_date_created, ro_status, destination 
            FROM replen_orders 
            WHERE ro_id = :ro_id
        """)
        
        order_result = execute_with_retry(order_query, {'ro_id': request.ro_id})
        order_row = order_result.fetchone()
        
        if not order_row:
            logger.info(f"Replenishment order not found: {request.ro_id}")
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"Replenishment order {request.ro_id} not found",
                    "error_code": "RO_NOT_FOUND",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        current_status = order_row[2]
        
        # If the order is Unassigned, change it to In Process
        status_changed = False
        if current_status == "Unassigned":
            status_update_query = text("""
                UPDATE replen_orders
                SET ro_status = 'In Process'
                WHERE ro_id = :ro_id
            """)
            
            execute_with_retry(status_update_query, {'ro_id': request.ro_id})
            logger.info(f"Changed status for order {request.ro_id} from Unassigned to In Process")
            status_changed = True
            current_status = "In Process"  # Update for the response
        
        # Get all items in the order
        items_query = text("""
            SELECT id, sku, description, qty, qty_picked, created_at, rack_location, note
            FROM replen_order_items
            WHERE ro_id = :ro_id
            ORDER BY sku
        """)
        
        items_result = execute_with_retry(items_query, {'ro_id': request.ro_id})
        item_rows = items_result.fetchall()
        
        # Process the items
        items = []
        for row in item_rows:
            item = {
                "id": row[0],
                "sku": row[1],
                "description": row[2],
                "qty": row[3],
                "qty_picked": row[4],
                "created_at": row[5].isoformat() if row[5] else None,
                "rack_location": row[6]
            }
            
            # Only include note if it's not None/NULL
            if row[7]:
                item["note"] = row[7]
                
            items.append(item)
        
        # Create the response object
        order_info = {
            "ro_id": order_row[0],
            "ro_date_created": order_row[1].isoformat() if order_row[1] else None,
            "ro_status": current_status,  # Use updated status if changed
            "destination": order_row[3],
            "items": items,
            "item_count": len(items)
        }
        
        # Add status change info to the message if applicable
        message = f"Successfully retrieved replenishment order {request.ro_id}"
        if status_changed:
            message += ". Status changed from Unassigned to In Process"
        
        logger.info(f"Successfully retrieved order {request.ro_id} with {len(items)} items")
        return {
            "status": "success",
            "message": message,
            "order": order_info,
            "status_changed": status_changed,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in ro_retrieve_order: {error_msg}\n{error_trace}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Server error: {error_msg}",
                "error_code": "SERVER_ERROR",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.post("/ro_item_picked")
async def ro_item_picked(request: ReplenishmentItemPickedRequest):
    """
    Update the quantity picked for a specific item in a replenishment order.
    Uses ro_id, sku, and rack_location to identify the item.
    Optionally accepts a note explaining quantity changes.
    """
    logger.info(f"ro_item_picked request received: RO={request.ro_id}, SKU={request.sku}, Location={request.rack_location}, Qty={request.qty_picked}")
    
    try:
        # First check if the order and item exist with the specific rack_location
        item_query = text("""
            SELECT roi.id, roi.qty, ro.ro_status
            FROM replen_order_items roi
            JOIN replen_orders ro ON roi.ro_id = ro.ro_id
            WHERE roi.ro_id = :ro_id 
              AND roi.sku = :sku
              AND roi.rack_location = :rack_location
        """)
        
        item_result = execute_with_retry(item_query, {
            'ro_id': request.ro_id,
            'sku': request.sku,
            'rack_location': request.rack_location
        })
        
        item_row = item_result.fetchone()
        
        if not item_row:
            logger.info(f"Item not found: RO={request.ro_id}, SKU={request.sku}, Location={request.rack_location}")
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"Item with SKU {request.sku} at location {request.rack_location} not found in replenishment order {request.ro_id}",
                    "error_code": "ITEM_NOT_FOUND",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        item_id = item_row[0]
        qty_requested = item_row[1]
        ro_status = item_row[2]
        
        # Check if order is already completed
        if ro_status == 'Completed':
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": f"Replenishment order {request.ro_id} is already marked as Completed",
                    "error_code": "ORDER_ALREADY_COMPLETED",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # PLACEHOLDER: Check inventory for sufficient stock
        # In a real implementation, we would query the inventory table here
        sufficient_stock = True  # Always return TRUE for now

        # Override for testing purposes
        if request.test_insufficient_stock:
            logger.info(f"Test flag enabled - simulating insufficient stock for SKU={request.sku}")
            sufficient_stock = False

        if not sufficient_stock:
            logger.info(f"Insufficient stock for SKU={request.sku} at location {request.rack_location}")
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": "Insufficient stock",
                    "error_code": "INSUFFICIENT_STOCK",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        if not sufficient_stock:
            logger.info(f"Insufficient stock for SKU={request.sku} at location {request.rack_location}")
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": "Insufficient stock",
                    "error_code": "INSUFFICIENT_STOCK",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Update the qty_picked value and add the note if provided
        if request.note:
            update_query = text("""
                UPDATE replen_order_items
                SET qty_picked = :qty_picked, note = :note
                WHERE id = :item_id
            """)
            
            execute_with_retry(update_query, {
                'item_id': item_id,
                'qty_picked': request.qty_picked,
                'note': request.note
            })
            
            logger.info(f"Updated qty_picked for item ID={item_id} to {request.qty_picked} with note: {request.note}")
        else:
            update_query = text("""
                UPDATE replen_order_items
                SET qty_picked = :qty_picked
                WHERE id = :item_id
            """)
            
            execute_with_retry(update_query, {
                'item_id': item_id,
                'qty_picked': request.qty_picked
            })
            
            logger.info(f"Updated qty_picked for item ID={item_id} to {request.qty_picked}")
        
        # PLACEHOLDER: Add code to update SkuVault
        # This would notify SkuVault that inventory should be moved from Storage to Staging
        logger.info("PLACEHOLDER: Would notify SkuVault of inventory movement from Storage to Staging")
        
        # If status is Unassigned, change it to In Process
        if ro_status == 'Unassigned':
            status_update_query = text("""
                UPDATE replen_orders
                SET ro_status = 'In Process'
                WHERE ro_id = :ro_id
            """)
            
            execute_with_retry(status_update_query, {'ro_id': request.ro_id})
            logger.info(f"Changed status for RO={request.ro_id} from Unassigned to In Process")
        
        # Check if all items have been picked (for informational purposes only)
        completion_query = text("""
            SELECT 
                COUNT(*) as total_items,
                SUM(CASE WHEN qty_picked > 0 THEN 1 ELSE 0 END) as picked_items
            FROM 
                replen_order_items
            WHERE 
                ro_id = :ro_id
        """)
        
        completion_result = execute_with_retry(completion_query, {'ro_id': request.ro_id})
        completion_row = completion_result.fetchone()
        
        total_items = completion_row[0]
        picked_items = completion_row[1]
        
        # We always return this message
        completion_message = "Data Added; RO In Process"
        
        # Build the response
        response = {
            "status": "success",
            "message": completion_message,
            "ro_id": request.ro_id,
            "sku": request.sku,
            "rack_location": request.rack_location,
            "qty_picked": request.qty_picked,
            "timestamp": datetime.now().isoformat()
        }
        
        # Include note in response if provided
        if request.note:
            response["note"] = request.note
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in ro_item_picked: {error_msg}\n{error_trace}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Server error: {error_msg}",
                "error_code": "SERVER_ERROR",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.post("/ro_pick_cancelled")
async def ro_pick_cancelled(request: ReplenishmentCancelRequest):
    """
    Cancel picking for a replenishment order by changing its status
    from "In Process" back to "Unassigned".
    """
    logger.info(f"ro_pick_cancelled request received for order ID: {request.ro_id}")
    
    try:
        # First check if the order exists and is in the correct state
        order_query = text("""
            SELECT ro_status
            FROM replen_orders 
            WHERE ro_id = :ro_id
        """)
        
        order_result = execute_with_retry(order_query, {'ro_id': request.ro_id})
        order_row = order_result.fetchone()
        
        if not order_row:
            logger.info(f"Replenishment order not found: {request.ro_id}")
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"Replenishment order {request.ro_id} not found",
                    "error_code": "RO_NOT_FOUND",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        current_status = order_row[0]
        
        # Check if order is in the correct state to be cancelled
        if current_status != "In Process":
            logger.info(f"Cannot cancel order {request.ro_id} with status {current_status}")
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": f"Cannot cancel order with status {current_status}. Only orders with status 'In Process' can be cancelled.",
                    "error_code": "INVALID_STATUS_FOR_CANCEL",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Update the order status
        update_query = text("""
            UPDATE replen_orders
            SET ro_status = 'Unassigned'
            WHERE ro_id = :ro_id
        """)
        
        execute_with_retry(update_query, {'ro_id': request.ro_id})
        
        # Reset all qty_picked values to 0
        reset_query = text("""
            UPDATE replen_order_items
            SET qty_picked = 0
            WHERE ro_id = :ro_id
        """)
        
        execute_with_retry(reset_query, {'ro_id': request.ro_id})
        
        logger.info(f"Successfully cancelled picking for order {request.ro_id}")
        return {
            "status": "success",
            "message": f"Replenishment order {request.ro_id} has been reset to Unassigned status",
            "ro_id": request.ro_id,
            "previous_status": current_status,
            "new_status": "Unassigned",
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in ro_pick_cancelled: {error_msg}\n{error_trace}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Server error: {error_msg}",
                "error_code": "SERVER_ERROR",
                "timestamp": datetime.now().isoformat()
            }
        )


@router.post("/ro_complete")
async def ro_complete(request: ReplenishmentCompleteRequest):
    """
    Mark a replenishment order as Completed after user confirmation.
    Called after all items have been picked and the user confirms completion.
    """
    logger.info(f"ro_complete request received for order ID: {request.ro_id}")
    
    try:
        # First check if the order exists 
        order_query = text("""
            SELECT ro_status
            FROM replen_orders 
            WHERE ro_id = :ro_id
        """)
        
        order_result = execute_with_retry(order_query, {'ro_id': request.ro_id})
        order_row = order_result.fetchone()
        
        if not order_row:
            logger.info(f"Replenishment order not found: {request.ro_id}")
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"Replenishment order {request.ro_id} not found",
                    "error_code": "RO_NOT_FOUND",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        current_status = order_row[0]
        
        # Check if order is already completed
        if current_status == "Completed":
            logger.info(f"Order {request.ro_id} is already completed")
            return {
                "status": "success",
                "message": f"Replenishment order {request.ro_id} is already marked as Completed",
                "ro_id": request.ro_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Check if all items have been picked
        completion_query = text("""
            SELECT 
                COUNT(*) as total_items,
                SUM(CASE WHEN qty_picked > 0 THEN 1 ELSE 0 END) as picked_items
            FROM 
                replen_order_items
            WHERE 
                ro_id = :ro_id
        """)
        
        completion_result = execute_with_retry(completion_query, {'ro_id': request.ro_id})
        completion_row = completion_result.fetchone()
        
        total_items = completion_row[0]
        picked_items = completion_row[1]
        
        # If not all items have been picked, return a warning
        if total_items > picked_items:
            logger.warning(f"Not all items have been picked for order {request.ro_id}")
            return {
                "status": "warning",
                "message": f"Not all items have been picked for order {request.ro_id}. {picked_items} of {total_items} items have been picked.",
                "ro_id": request.ro_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Update the order status to Completed
        update_query = text("""
            UPDATE replen_orders
            SET ro_status = 'Completed'
            WHERE ro_id = :ro_id
        """)
        
        execute_with_retry(update_query, {'ro_id': request.ro_id})
        
        logger.info(f"Successfully marked order {request.ro_id} as Completed")
        return {
            "status": "success",
            "message": f"Replenishment order {request.ro_id} has been marked as Completed",
            "ro_id": request.ro_id,
            "previous_status": current_status,
            "new_status": "Completed",
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in ro_complete: {error_msg}\n{error_trace}")
        
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