from fastapi import APIRouter, HTTPException
from sqlalchemy import text, exc
from datetime import datetime
import logging
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database connection
from api.database import execute_with_retry
from models.purchase_orders import FindPurchaseOrderRequest, CheckSkuAgainstPoRequest, UpdatePoStatusRequest, GetPurchaseOrderRequest

# Import standardized error handling
from error_handlers import (
    handle_database_error, handle_server_error, handle_not_found_error, handle_business_logic_error,
    log_operation_start, log_operation_success, log_operation_warning,
    ErrorCodes, create_error_response
)

router = APIRouter(
    prefix="/api/v1",
    tags=["purchase_orders"]
)

@router.post("/find_purchase_order")
async def find_purchase_order(request: FindPurchaseOrderRequest):
    """
    Find purchase orders based on either text search (po_number or supplier_name) or barcode(s).
    
    If text is provided in po_number field, returns POs where either:
    - The po_number contains the provided text
    - The supplier_name contains the provided text
    
    If a single barcode is provided, looks up associated SKU and returns POs containing that SKU.
    If multiple barcodes are provided, returns only POs containing ALL the SKUs associated with those barcodes.
    Only returns POs with status not "Completed" or "Cancelled".
    """
    log_operation_start("find purchase order", po_number=request.po_number, barcode=request.barcode)
    
    try:
        if request.po_number is not None:
            # Search by PO number or supplier name
            logger.info(f"Searching for POs with number or supplier containing: {request.po_number}")
            
            # Query for both po_number and supplier_name
            query = text("""
                SELECT po_number, status, supplier_name, created_date, 
                       order_date, arrival_due_date, ship_to_warehouse
                FROM purchase_orders 
                WHERE po_number LIKE :search_pattern
                   OR supplier_name LIKE :search_pattern
                AND (status IS NULL OR status NOT IN ('Completed', 'Cancelled'))
                LIMIT 50
            """)
            
            result = execute_with_retry(query, {'search_pattern': f'%{request.po_number}%'})
            
        else:
            # Search by barcode(s) - implementation remains the same
            if isinstance(request.barcode, str):
                # Single barcode handling
                logger.info(f"Looking up SKU for single barcode: {request.barcode}")
                
                # First get the SKU associated with the barcode
                barcode_query = text("""
                    SELECT sku FROM barcodes WHERE barcode = :barcode
                """)
                
                barcode_result = execute_with_retry(barcode_query, {'barcode': request.barcode})
                sku_row = barcode_result.fetchone()
                
                if sku_row is None:
                    raise handle_not_found_error("Barcode", request.barcode, ErrorCodes.BARCODE_NOT_FOUND)
                
                sku = str(sku_row[0]) if sku_row[0] is not None else ""
                logger.info(f"Found SKU for barcode {request.barcode}: {sku}")
                
                # Now find purchase orders containing this SKU
                query = text("""
                    SELECT po.po_number, po.status, po.supplier_name, po.created_date, 
                           po.order_date, po.arrival_due_date, po.ship_to_warehouse
                    FROM purchase_orders po
                    JOIN po_lines pol ON po.po_number = pol.po_number
                    WHERE pol.sku = :sku
                    AND (po.status IS NULL OR po.status NOT IN ('Completed', 'Cancelled'))
                    GROUP BY po.po_number
                    LIMIT 50
                """)
                
                result = execute_with_retry(query, {'sku': sku})
                
            else:
                # Multiple barcodes handling
                logger.info(f"Looking up SKUs for {len(request.barcode)} barcodes")
                
                # Get SKUs for all barcodes
                skus = []
                for barcode in request.barcode:
                    barcode_query = text("""
                        SELECT sku FROM barcodes WHERE barcode = :barcode
                    """)
                    
                    barcode_result = execute_with_retry(barcode_query, {'barcode': barcode})
                    sku_row = barcode_result.fetchone()
                    
                    if sku_row is None:
                        raise handle_not_found_error("Barcode", barcode, ErrorCodes.BARCODE_NOT_FOUND)
                    
                    sku = str(sku_row[0]) if sku_row[0] is not None else ""
                    skus.append(sku)
                    logger.info(f"Found SKU for barcode {barcode}: {sku}")
                
                # Find purchase orders containing ALL of these SKUs
                # We'll do this by finding POs that have a count of matching SKUs equal to the number of SKUs we're looking for
                placeholders = ', '.join([f':sku{i}' for i in range(len(skus))])
                params = {f'sku{i}': sku for i, sku in enumerate(skus)}
                
                query = text(f"""
                    SELECT po.po_number, po.status, po.supplier_name, po.created_date, 
                           po.order_date, po.arrival_due_date, po.ship_to_warehouse
                    FROM purchase_orders po
                    WHERE (po.status IS NULL OR po.status NOT IN ('Completed', 'Cancelled'))
                    AND (
                        SELECT COUNT(DISTINCT pol.sku)
                        FROM po_lines pol
                        WHERE pol.po_number = po.po_number
                        AND pol.sku IN ({placeholders})
                    ) = :sku_count
                    LIMIT 50
                """)
                
                params['sku_count'] = len(skus)
                result = execute_with_retry(query, params)
        
        # Process the results
        rows = result.fetchall()
        if not rows:
            log_operation_success("find purchase order", "no matching purchase orders found")
            return {
                "status": "success",
                "message": "No matching purchase orders found",
                "results": [],
                "count": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Format the results with error handling for each field
        purchase_orders = []
        for row in rows:
            try:
                po = {
                    "po_number": str(row[0]) if row[0] is not None else "",
                    "status": str(row[1]) if row[1] is not None else "",
                    "supplier_name": str(row[2]) if row[2] is not None else "",
                    "created_date": str(row[3]) if row[3] is not None else "",
                    "order_date": str(row[4]) if row[4] is not None else "",
                    "arrival_due_date": str(row[5]) if row[5] is not None else "",
                    "ship_to_warehouse": str(row[6]) if row[6] is not None else ""
                }
                purchase_orders.append(po)
            except Exception as e:
                logger.error(f"Error processing row: {e}")
                # Continue with next row rather than failing completely
                continue
        
        log_operation_success("find purchase order", f"found {len(purchase_orders)} matching purchase orders")
        return {
            "status": "success",
            "message": f"Found {len(purchase_orders)} matching purchase orders",
            "results": purchase_orders,
            "count": len(purchase_orders),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except exc.SQLAlchemyError as e:
        raise handle_database_error(e, "find purchase order")
    except Exception as e:
        raise handle_server_error(e, "find purchase order")
    
@router.post("/check_sku_against_po")
async def check_sku_against_po(request: CheckSkuAgainstPoRequest):
    """
    Check if the SKU associated with the provided barcode is included in the specified purchase order.
    
    Returns TRUE if the SKU is in the PO, FALSE if not.
    """
    log_operation_start("check SKU against PO", po_number=request.po_number, barcode=request.barcode)
    
    try:
        # First get the SKU associated with the barcode
        barcode_query = text("""
            SELECT sku FROM barcodes WHERE barcode = :barcode
        """)
        
        barcode_result = execute_with_retry(barcode_query, {'barcode': request.barcode})
        sku_row = barcode_result.fetchone()
        
        if sku_row is None:
            raise handle_not_found_error("Barcode", request.barcode, ErrorCodes.BARCODE_NOT_FOUND)
        
        sku = str(sku_row[0]) if sku_row[0] is not None else ""
        logger.info(f"Found SKU for barcode {request.barcode}: {sku}")
        
        # Now check if this SKU is in the specified purchase order
        check_query = text("""
            SELECT COUNT(*) FROM po_lines
            WHERE po_number = :po_number AND sku = :sku
        """)
        
        check_result = execute_with_retry(check_query, {
            'po_number': request.po_number,
            'sku': sku
        })
        
        count_row = check_result.fetchone()
        count = int(count_row[0]) if count_row is not None and count_row[0] is not None else 0
        
        result = count > 0
        log_operation_success("check SKU against PO", f"SKU {sku} {'found' if result else 'not found'} in PO {request.po_number}")
        
        return {
            "status": "success",
            "result": result,
            "po_number": request.po_number,
            "barcode": request.barcode,
            "sku": sku,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except exc.SQLAlchemyError as e:
        raise handle_database_error(e, "check SKU against PO")
    except Exception as e:
        raise handle_server_error(e, "check SKU against PO")

@router.post("/update_po_status")
async def update_po_status(request: UpdatePoStatusRequest):
    """
    Update the status of a purchase order to either Complete or Incomplete.
    
    If the status is set to Complete, a notification will be sent to the partner API.
    """
    log_operation_start("update PO status", po_number=request.po_number, status=request.status)
    
    try:
        # First check if the PO exists
        check_query = text("""
            SELECT COUNT(*) FROM purchase_orders WHERE po_number = :po_number
        """)
        
        check_result = execute_with_retry(check_query, {'po_number': request.po_number})
        count_row = check_result.fetchone()
        count = int(count_row[0]) if count_row is not None and count_row[0] is not None else 0
        
        if count == 0:
            raise handle_not_found_error("Purchase order", request.po_number, ErrorCodes.PO_NOT_FOUND)
        
        # Update the status in our database
        update_query = text("""
            UPDATE purchase_orders 
            SET status = :status 
            WHERE po_number = :po_number
        """)
        
        # Use the status directly without mapping
        new_status = request.status
        
        execute_with_retry(update_query, {
            'po_number': request.po_number,
            'status': new_status
        })
        
        logger.info(f"Updated status for PO {request.po_number} to {new_status}")
        
        # If the status is Completed, notify the partner API
        partner_api_notification = None
        if request.status == "Completed":
            try:
                # Placeholder for partner API integration
                # This will be replaced with actual API call in the future
                logger.info(f"Sending notification to partner API for PO {request.po_number}")
                
                # Simulate a successful notification
                partner_api_notification = {
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"Partner API notification sent successfully for PO {request.po_number}")
            except Exception as e:
                logger.error(f"Error sending notification to partner API: {str(e)}")
                partner_api_notification = {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        log_operation_success("update PO status", f"updated PO {request.po_number} to {new_status}")
        
        # Return success response
        response = {
            "status": "success",
            "message": f"Purchase order {request.po_number} status updated to {new_status}",
            "po_number": request.po_number,
            "new_status": new_status,
            "timestamp": datetime.now().isoformat()
        }
        
        # Include partner API notification if applicable
        if partner_api_notification:
            response["partner_api_notification"] = partner_api_notification
            
        return response
        
    except HTTPException:
        raise
    except exc.SQLAlchemyError as e:
        raise handle_database_error(e, "update PO status")
    except Exception as e:
        raise handle_server_error(e, "update PO status")
    
@router.post("/get_purchase_order")
async def get_purchase_order(request: GetPurchaseOrderRequest):
    """
    Get detailed information about a purchase order including all line items.
    
    Returns information about all items in the purchase order including SKU, 
    quantity, and product description from the products table.
    """
    log_operation_start("get purchase order details", po_number=request.po_number)
    
    try:
        # First check if the PO exists in the po_lines table
        check_query = text("""
            SELECT COUNT(*) FROM po_lines WHERE po_number = :po_number
        """)
        
        check_result = execute_with_retry(check_query, {'po_number': request.po_number})
        count_row = check_result.fetchone()
        count = int(count_row[0]) if count_row is not None and count_row[0] is not None else 0
        
        if count == 0:
            raise handle_not_found_error("Purchase order", request.po_number, ErrorCodes.PO_NOT_FOUND)
        
        # Get the line items with product descriptions
        query = text("""
            SELECT 
                pl.sku, 
                pl.quantity, 
                p.description
            FROM 
                po_lines pl
            LEFT JOIN 
                products p ON pl.sku = p.sku
            WHERE 
                pl.po_number = :po_number
        """)
        
        result = execute_with_retry(query, {'po_number': request.po_number})
        rows = result.fetchall()
        
        # Format the results
        line_items = []
        total_quantity = 0
        
        for row in rows:
            sku = str(row[0]) if row[0] is not None else ""
            quantity = int(row[1]) if row[1] is not None else 0
            description = str(row[2]) if row[2] is not None else ""
            
            line_items.append({
                "sku": sku,
                "quantity": quantity,
                "description": description
            })
            
            total_quantity += quantity
        
        logger.info(f"Found {len(line_items)} items for PO {request.po_number}")
        
        # Get basic PO information from purchase_orders table if available
        po_info = {}
        try:
            po_query = text("""
                SELECT 
                    po_number, status, supplier_name, created_date, 
                    order_date, arrival_due_date, ship_to_warehouse
                FROM 
                    purchase_orders 
                WHERE 
                    po_number = :po_number
                LIMIT 1
            """)
            
            po_result = execute_with_retry(po_query, {'po_number': request.po_number})
            po_row = po_result.fetchone()
            
            if po_row is not None:
                po_info = {
                    "po_number": str(po_row[0]) if po_row[0] is not None else "",
                    "status": str(po_row[1]) if po_row[1] is not None else "",
                    "supplier_name": str(po_row[2]) if po_row[2] is not None else "",
                    "created_date": str(po_row[3]) if po_row[3] is not None else "",
                    "order_date": str(po_row[4]) if po_row[4] is not None else "",
                    "arrival_due_date": str(po_row[5]) if po_row[5] is not None else "",
                    "ship_to_warehouse": str(po_row[6]) if po_row[6] is not None else ""
                }
        except Exception as e:
            # Log the error but don't fail the request
            logger.warning(f"Failed to get PO details from purchase_orders table: {str(e)}")
            # Leave po_info as an empty dict
        
        log_operation_success("get purchase order details", f"retrieved {len(line_items)} items for PO {request.po_number}")
        
        response = {
            "status": "success",
            "message": f"Found {len(line_items)} items in purchase order {request.po_number}",
            "purchase_order": po_info,
            "items": line_items,
            "total_quantity": total_quantity,
            "timestamp": datetime.now().isoformat()
        }
        
        return response
        
    except HTTPException:
        raise
    except exc.SQLAlchemyError as e:
        raise handle_database_error(e, "get purchase order details")
    except Exception as e:
        raise handle_server_error(e, "get purchase order details")

# Health check endpoint for the purchase order router
@router.get("/purchase-orders-health")
async def purchase_order_health():
    """
    Health check endpoint for the purchase order router
    """
    try:
        return {
            "status": "healthy",
            "message": "Purchase Order API endpoints are available",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                status_code=500,
                message=f"Health check failed: {str(e)}",
                error_code=ErrorCodes.SERVER_ERROR
            )
        )