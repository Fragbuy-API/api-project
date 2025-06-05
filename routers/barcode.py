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
from models.barcode import BarcodeLookup, NewBarcode

# Import standardized error handling
from error_handlers import (
    handle_database_error, handle_server_error, handle_not_found_error, handle_business_logic_error,
    log_operation_start, log_operation_success, log_operation_warning,
    ErrorCodes, create_error_response
)

router = APIRouter(
    prefix="/api/v1",
    tags=["barcode"]
)

@router.post("/barcodeLookup")
async def lookup_barcode(lookup: BarcodeLookup):
    """
    Lookup a barcode in the database and return associated SKU if found.
    """
    log_operation_start("barcode lookup", barcode=lookup.barcode)
    
    try:
        # Query the barcode in the barcodes table
        query = text("""
            SELECT sku, alternate FROM barcodes WHERE barcode = :barcode
        """)
        
        logger.info(f"Executing database query for barcode: {lookup.barcode}")
        result = execute_with_retry(query, {'barcode': lookup.barcode})
        row = result.fetchone()
        
        # Check if barcode was found
        if row is None:
            raise handle_not_found_error("Barcode", lookup.barcode, ErrorCodes.BARCODE_NOT_FOUND)
        
        # Return the SKU information with proper type handling
        sku = str(row[0]) if row[0] is not None else ""
        alternate = int(row[1]) if row[1] is not None else 0
        
        log_operation_success("barcode lookup", f"found SKU {sku} for barcode {lookup.barcode}")
        return {
            "status": "success",
            "barcode": lookup.barcode,
            "sku": sku,
            "alternate": alternate,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except exc.SQLAlchemyError as e:
        raise handle_database_error(e, "barcode lookup")
    except Exception as e:
        raise handle_server_error(e, "barcode lookup")

@router.post("/addNewBarcode")
async def add_new_barcode(new_barcode: NewBarcode):
    """
    Add a new barcode for a SKU with the correct alternate number.
    If barcode is "NA", validate SKU exists but don't store the barcode.
    If it's a new SKU, alternate = 1. Otherwise, increment from the highest existing alternate.
    """
    log_operation_start("add new barcode", sku=new_barcode.sku, barcode=new_barcode.barcode)
    
    try:
        # Handle "NA" barcode case - validate SKU exists but don't store
        if new_barcode.barcode.upper() == "NA":
            # Check if the SKU exists in the products table
            check_sku_query = text("""
                SELECT sku FROM products WHERE sku = :sku
            """)
            
            logger.info(f"Checking if SKU exists for NA barcode: {new_barcode.sku}")
            result = execute_with_retry(check_sku_query, {'sku': new_barcode.sku})
            existing_sku = result.fetchone()
            
            if existing_sku is None:
                raise handle_business_logic_error(
                    f"SKU {new_barcode.sku} does not exist in the products table. Cannot process NA barcode.",
                    ErrorCodes.INVALID_SKU,
                    400
                )
            
            logger.info(f"NA barcode received for valid SKU: {new_barcode.sku} - not stored in database")
            return {
                "status": "success",
                "message": f"NA barcode received for SKU {new_barcode.sku}. Barcode not stored - will be edited manually later.",
                "sku": new_barcode.sku,
                "barcode": new_barcode.barcode,
                "stored_in_database": False,
                "timestamp": datetime.now().isoformat()
            }
        
        # Continue with existing logic for regular barcodes
        # First check if the barcode already exists
        check_barcode_query = text("""
            SELECT sku FROM barcodes WHERE barcode = :barcode
        """)
        
        logger.info(f"Checking if barcode already exists: {new_barcode.barcode}")
        result = execute_with_retry(check_barcode_query, {'barcode': new_barcode.barcode})
        existing_barcode = result.fetchone()
        
        if existing_barcode is not None:
            existing_sku = str(existing_barcode[0]) if existing_barcode[0] is not None else ""
            raise handle_business_logic_error(
                f"Barcode {new_barcode.barcode} already exists in the system for SKU {existing_sku}",
                ErrorCodes.DUPLICATE_BARCODE,
                400
            )
            
        # Check if the SKU exists in the products table
        check_sku_query = text("""
            SELECT sku FROM products WHERE sku = :sku
        """)
        
        logger.info(f"Checking if SKU exists in products table: {new_barcode.sku}")
        result = execute_with_retry(check_sku_query, {'sku': new_barcode.sku})
        existing_sku = result.fetchone()
        
        if existing_sku is None:
            raise handle_business_logic_error(
                f"SKU {new_barcode.sku} does not exist in the products table. Cannot add barcode.",
                ErrorCodes.INVALID_SKU,
                400
            )
        
        # Find the highest alternate number for the SKU
        alternate_query = text("""
            SELECT MAX(alternate) FROM barcodes WHERE sku = :sku
        """)
        
        logger.info(f"Looking up highest alternate for SKU: {new_barcode.sku}")
        result = execute_with_retry(alternate_query, {'sku': new_barcode.sku})
        row = result.fetchone()
        
        # Explicitly convert to the right type and handle None
        highest_alternate = None
        if row is not None and row[0] is not None:
            try:
                highest_alternate = int(row[0])  # Convert to integer
                logger.info(f"Highest alternate found: {highest_alternate}")
            except (ValueError, TypeError):
                logger.warning(f"Could not convert {row[0]} to integer, using None")
                highest_alternate = None
        
        alternate_number = 1 if highest_alternate is None else highest_alternate + 1
        logger.info(f"Using alternate number: {alternate_number}")
        
        # Insert the new barcode record
        insert_query = text("""
            INSERT INTO barcodes (sku, barcode, alternate)
            VALUES (:sku, :barcode, :alternate)
        """)
        
        logger.info(f"Inserting new barcode record")
        execute_with_retry(insert_query, {
            'sku': new_barcode.sku,
            'barcode': new_barcode.barcode,
            'alternate': alternate_number
        })
        
        log_operation_success("add new barcode", f"added barcode {new_barcode.barcode} for SKU {new_barcode.sku}")
        return {
            "status": "success",
            "message": f"Barcode {new_barcode.barcode} added successfully for SKU {new_barcode.sku}",
            "sku": new_barcode.sku,
            "barcode": new_barcode.barcode,
            "alternate": alternate_number,
            "stored_in_database": True,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except exc.SQLAlchemyError as e:
        raise handle_database_error(e, "add new barcode")
    except Exception as e:
        raise handle_server_error(e, "add new barcode")

# Health check endpoint for the barcode router
@router.get("/barcode-health")
async def barcode_health():
    """
    Health check endpoint for the barcode router
    """
    log_operation_start("barcode health check")
    
    try:
        log_operation_success("barcode health check", "all endpoints available")
        return {
            "status": "healthy",
            "message": "Barcode API endpoints are available",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise handle_server_error(e, "barcode health check")