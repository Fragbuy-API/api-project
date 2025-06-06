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
    Returns matching products from the products table, including image URLs when available.
    """
    logger.info(f"Product search request received with query: {search.query}")
    
    try:
        # Build the SQL query to search both SKU and description, and join with measurement images
        query_text = """
            SELECT 
                p.sku,
                p.description,
                p.weight_value,
                p.length,
                p.width,
                p.height,
                p.dimension_unit,
                p.weight_unit,
                p.brand,
                p.created_date_utc,
                p.pictures,
                p.picture_handle_url_bottle,
                p.picture_variant_url_box,
                p.latest_qboid_image,
                p.barcode,
                p.classification,
                p.gender,
                p.type,
                p.size,
                COALESCE(latest_images.image_url, NULL) as measurement_image_url
            FROM products p
            LEFT JOIN (
                SELECT 
                    sku,
                    CONCAT('http://155.138.159.75/api/v1/product_image/', sku, '/', 
                           SUBSTRING_INDEX(image_original, '/', -1)) as image_url,
                    ROW_NUMBER() OVER (PARTITION BY sku ORDER BY timestamp DESC) as rn
                FROM api_received_data 
                WHERE image_original IS NOT NULL AND image_original != ''
            ) latest_images ON p.sku = latest_images.sku AND latest_images.rn = 1
            WHERE p.sku LIKE :search_pattern 
               OR p.description LIKE :search_pattern
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
            col_names = list(result.keys())
            
            # Convert to dictionary
            product = {}
            image_url_set = False  # Track if we've found a valid image URL
            
            for i, col in enumerate(col_names):
                value = row[i]
                
                # Process different fields differently
                if col == 'description':
                    # Map description to name in the API response
                    product['name'] = str(value) if value is not None else None
                    product['description'] = str(value) if value is not None else None
                    
                elif col == 'measurement_image_url' and value is not None and str(value).strip():
                    # Use measurement image as primary image source
                    url_value = str(value).strip()
                    product['image_url'] = url_value
                    image_url_set = True
                    logger.debug(f"Set image_url from measurement data: {url_value}")
                    
                elif col == 'latest_qboid_image' and value is not None and str(value).strip():
                    url_value = str(value).strip()
                    product[col] = url_value
                    # Use as image_url if no measurement image was found and this looks valid
                    if not image_url_set and url_value and url_value != "NA" and url_value.startswith(('http://', 'https://')):
                        product['image_url'] = url_value
                        image_url_set = True
                        logger.debug(f"Set image_url from latest_qboid_image: {url_value}")
                        
                elif col == 'picture_handle_url_bottle' and value is not None and str(value).strip():
                    url_value = str(value).strip()
                    product[col] = url_value
                    # Use as fallback image_url
                    if not image_url_set and url_value and url_value != "NA" and url_value.startswith(('http://', 'https://')):
                        product['image_url'] = url_value
                        image_url_set = True
                        logger.debug(f"Set image_url from picture_handle_url_bottle: {url_value}")
                        
                elif col == 'picture_variant_url_box' and value is not None and str(value).strip():
                    url_value = str(value).strip()
                    product[col] = url_value
                    # Use as fallback image_url
                    if not image_url_set and url_value and url_value != "NA" and url_value.startswith(('http://', 'https://')):
                        product['image_url'] = url_value
                        image_url_set = True
                        logger.debug(f"Set image_url from picture_variant_url_box: {url_value}")
                        
                elif col == 'pictures' and value is not None and str(value).strip():
                    url_value = str(value).strip()
                    product[col] = url_value
                    # Use as fallback image_url if it looks like a URL
                    if not image_url_set and url_value and url_value != "NA" and url_value.startswith(('http://', 'https://')):
                        product['image_url'] = url_value
                        image_url_set = True
                        logger.debug(f"Set image_url from pictures: {url_value}")
                        
                else:
                    # Handle different types of values
                    if value is not None:
                        if col in ['weight_value', 'length', 'width', 'height'] and isinstance(value, (int, float)):
                            product[col] = float(value)
                        elif hasattr(value, 'isoformat'):  # datetime object
                            product[col] = value.isoformat()
                        else:
                            product[col] = str(value)
                    else:
                        product[col] = None
            
            # Ensure image_url is always present (even if null) for consistency
            if 'image_url' not in product:
                product['image_url'] = None
                logger.debug(f"No valid image URL found for SKU: {product.get('sku', 'unknown')}")
            
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
        
        # Count products with image URLs for logging
        products_with_images = len([p for p in products if p.get('image_url')])
        logger.info(f"Found {len(products)} products matching the search criteria, {products_with_images} with image URLs")
        
        # Return the results
        return {
            "status": "success",
            "message": f"Found {len(products)} products matching the search criteria",
            "search_criteria": {"query": search.query, "limit": search.limit},
            "count": len(products),
            "products": products,
            "image_info": {
                "products_with_images": products_with_images,
                "products_without_images": len(products) - products_with_images,
                "image_sources_note": "Images come from measurement data or product database columns"
            },
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
