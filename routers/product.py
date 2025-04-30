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
from models.product import ProductSearch

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
    logger.info(f"Product search request received with query: {search.query}")
    
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
            has_finalurl = False  # Track if we've found a valid finalurl
            
            for i, col in enumerate(col_names):
                # Process different fields differently
                if col == 'description':
                    # Map description to name in the API response
                    product['name'] = str(row[i]) if row[i] is not None else None
                # Check for finalurl specifically
                elif col == 'finalurl' and row[i] is not None and str(row[i]).strip():
                    url_value = str(row[i])
                    product[col] = url_value
                    # Only use as image_url if it's not "NA" 
                    if url_value != "NA":
                        product['image_url'] = url_value
                        has_finalurl = True
                    else:
                        # Store NA value but don't use as image_url
                        product[col] = url_value
                # Store other image fields
                elif col in ['photo_url_live', 'photo_url_raw', 'pictures'] and row[i] is not None and str(row[i]).strip():
                    url_value = str(row[i])
                    product[col] = url_value
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
            
            # If no valid finalurl, try to use one of the other image fields
            if not has_finalurl:
                for img_field in ['photo_url_live', 'photo_url_raw', 'pictures']:
                    if img_field in product and product[img_field] and product[img_field] != "NA":
                        product['image_url'] = product[img_field]
                        break
            
            # If no valid image URL was found, don't include image_url field
            # This avoids having "NA" as the image_url value
            
            products.append(product)
        
        # Check if any products were found
        if not products:
            logger.info(f"No products found matching query: {search.query}")
            
            return {
                "status": "success",
                "message": f"No products found matching the search criteria",
                "search_criteria": {"query": search.query, "limit": search.limit},
                "count": 0,
                "products": [],
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"Found {len(products)} products matching the search criteria")
        
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
    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in product search: {error_msg}\n{error_trace}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Server error: {error_msg}",
                "error_code": "SERVER_ERROR",
                "timestamp": datetime.now().isoformat()
            }
        )

# Health check endpoint
@router.get("/product-health")
async def product_health():
    """
    Health check endpoint for the product search API
    """
    try:
        return {
            "status": "healthy",
            "message": "Product search API endpoint is available",
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