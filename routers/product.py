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
from models.product import ProductSearch

# Import standardized error handling
from error_handlers import (
    handle_database_error, handle_server_error, handle_business_logic_error,
    log_operation_start, log_operation_success, log_operation_warning,
    ErrorCodes, create_error_response
)

router = APIRouter(
    prefix="/api/v1",
    tags=["product"]
)

@router.post("/product_search")
async def search_product(search: ProductSearch):
    """
    Search products using a single query term that searches both SKU and description columns.
    Returns matching products from the products table, using only columns that exist.
    """
    log_operation_start("product search", query=search.query, limit=search.limit)
    
    try:
        # First, get the actual columns in the products table
        describe_query = text("DESCRIBE products")
        result = execute_with_retry(describe_query, {})
        
        # Extract column names from the result
        columns = [row[0] for row in result]
        logger.info(f"Available columns in products table: {columns}")
        
        # Build the SELECT part of our query using only columns that exist
        required_columns = ["sku", "description"]  # These must exist
        optional_columns = ["weight_value", "length", "width", "height", 
                           "dimension_unit", "weight_unit", "category", "created_date_utc",
                           "pictures", "photo_url_live", "photo_url_raw", "finalurl", "barcode"]
        
        select_columns = []
        for col in required_columns:
            if col in columns:
                select_columns.append(col)
            else:
                logger.warning(f"Required column '{col}' not found in products table!")
                
        for col in optional_columns:
            if col in columns:
                select_columns.append(col)
        
        # Create the SELECT clause
        select_clause = ", ".join(select_columns)
        logger.info(f"Using columns: {select_clause}")
        
        # Build the SQL query to search both SKU and description
        query_text = f"""
            SELECT {select_clause}
            FROM products 
            WHERE sku LIKE :search_pattern 
               OR description LIKE :search_pattern
            LIMIT :limit
        """
        params = {
            'search_pattern': f'%{search.query}%', 
            'limit': search.limit
        }
        logger.info(f"Searching for pattern: %{search.query}% in both SKU and description")
        
        # Execute the query
        query = text(query_text)
        result = execute_with_retry(query, params)
        
        # Process the results
        products = []
        for row in result:
            # Get column names from result
            col_names = result.keys()
            
            # Convert to dictionary
            product = {}
            
            for i, col in enumerate(col_names):
                # Process different fields differently
                if col == 'description':
                    # Map description to name in the API response
                    product['name'] = str(row[i]) if row[i] is not None else None
                # Handle finalurl specifically for image_url
                elif col == 'finalurl':
                    if row[i] is not None:
                        url_value = str(row[i])
                        product[col] = url_value
                        # Always use finalurl as image_url even if it's "NA"
                        product['image_url'] = url_value
                    else:
                        product[col] = None
                # Store other fields normally
                else:
                    # Handle different types of values
                    if row[i] is not None:
                        if col in ['weight_value', 'length', 'width', 'height'] and isinstance(row[i], (int, float)):
                            product[col] = float(row[i])
                        elif hasattr(row[i], 'isoformat'):  # datetime object
                            product[col] = row[i].isoformat()
                        else:
                            product[col] = str(row[i])
                    else:
                        product[col] = None
            
            products.append(product)
        
        # Check if any products were found
        if not products:
            log_operation_success("product search", f"no products found for query: {search.query}")
            
            return {
                "status": "success",
                "message": f"No products found matching the search criteria",
                "search_criteria": {"query": search.query, "limit": search.limit},
                "count": 0,
                "products": [],
                "timestamp": datetime.now().isoformat()
            }
        
        log_operation_success("product search", f"found {len(products)} products matching the search criteria")
        
        # Return the results
        return {
            "status": "success",
            "message": f"Found {len(products)} products matching the search criteria",
            "search_criteria": {"query": search.query, "limit": search.limit},
            "count": len(products),
            "products": products,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except exc.SQLAlchemyError as e:
        raise handle_database_error(e, "product search")
    except Exception as e:
        raise handle_server_error(e, "product search")

# Health check endpoint
@router.get("/product-health")
async def product_health():
    """
    Health check endpoint for the product search API
    """
    log_operation_start("product health check")
    
    try:
        log_operation_success("product health check", "all endpoints available")
        return {
            "status": "healthy",
            "message": "Product search API endpoint is available",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise handle_server_error(e, "product health check")