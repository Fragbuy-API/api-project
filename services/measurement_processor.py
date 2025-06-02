import logging
import json
from typing import Dict, Any, Optional, Tuple
from sqlalchemy import text
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

class MeasurementProcessor:
    """
    Service class to handle processing of measurement data including:
    - Barcode to SKU lookup
    - Dimension and weight comparison
    - Attributes parsing and product updates
    """
    
    def __init__(self, database_executor):
        self.execute_with_retry = database_executor
    
    def process_measurement(self, measurement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing function for measurement data
        
        Args:
            measurement_data: Dict containing barcode, dimensions, weight, attributes, etc.
            
        Returns:
            Dict with processing results and any updates made
        """
        try:
            processing_results = {
                "barcode": measurement_data.get("barcode"),
                "sku_found": False,
                "sku": None,
                "dimensions_updated": False,
                "weight_updated": False,
                "attributes_updated": False,
                "errors": [],
                "updates_made": []
            }
            
            # Phase 2: Barcode to SKU Lookup
            sku = self._lookup_sku_from_barcode(measurement_data.get("barcode"))
            if not sku:
                processing_results["errors"].append("Barcode not found in database")
                return processing_results
            
            processing_results["sku_found"] = True
            processing_results["sku"] = sku
            
            # Get current product data
            current_product = self._get_current_product_data(sku)
            if not current_product:
                processing_results["errors"].append(f"SKU {sku} not found in products table")
                return processing_results
            
            # Phase 3: Dimension & Weight Comparison
            dimension_updates = self._compare_and_get_dimension_updates(
                measurement_data, current_product
            )
            
            # Phase 4: Parse New attributes_json Format
            attribute_updates = self._parse_attributes_and_get_updates(
                measurement_data.get("attributes", {})
            )
            
            # Phase 5: Update Products Table
            all_updates = {**dimension_updates, **attribute_updates}
            
            if all_updates:
                success = self._update_products_table(sku, all_updates)
                if success:
                    processing_results["updates_made"] = list(all_updates.keys())
                    if dimension_updates:
                        processing_results["dimensions_updated"] = True
                        processing_results["weight_updated"] = "weight_value" in dimension_updates
                    if attribute_updates:
                        processing_results["attributes_updated"] = True
                else:
                    processing_results["errors"].append("Failed to update products table")
            
            return processing_results
            
        except Exception as e:
            logger.error(f"Error processing measurement: {str(e)}")
            return {
                "barcode": measurement_data.get("barcode"),
                "sku_found": False,
                "errors": [f"Processing error: {str(e)}"],
                "updates_made": []
            }
    
    def _lookup_sku_from_barcode(self, barcode: str) -> Optional[str]:
        """Look up SKU from barcode using barcodes table"""
        try:
            query = text("SELECT sku FROM barcodes WHERE barcode = :barcode LIMIT 1")
            result = self.execute_with_retry(query, {"barcode": barcode})
            row = result.fetchone()
            
            if row and row[0]:
                logger.info(f"Found SKU {row[0]} for barcode {barcode}")
                return str(row[0])
            
            logger.warning(f"No SKU found for barcode {barcode}")
            return None
            
        except Exception as e:
            logger.error(f"Error looking up SKU for barcode {barcode}: {str(e)}")
            return None
    
    def _get_current_product_data(self, sku: str) -> Optional[Dict]:
        """Get current product data from products table"""
        try:
            query = text("""
                SELECT sku, weight_value, weight_unit, length, width, height, 
                       dimension_unit, nocap, nocello, origin
                FROM products 
                WHERE sku = :sku
            """)
            result = self.execute_with_retry(query, {"sku": sku})
            row = result.fetchone()
            
            if row:
                return {
                    "sku": row[0],
                    "weight_value": float(row[1]) if row[1] is not None else None,
                    "weight_unit": row[2],
                    "length": float(row[3]) if row[3] is not None else None,
                    "width": float(row[4]) if row[4] is not None else None,
                    "height": float(row[5]) if row[5] is not None else None,
                    "dimension_unit": row[6],
                    "nocap": int(row[7]) if row[7] is not None else None,
                    "nocello": int(row[8]) if row[8] is not None else None,
                    "origin": row[9]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting product data for SKU {sku}: {str(e)}")
            return None
    
    def _compare_and_get_dimension_updates(self, measurement_data: Dict, current_product: Dict) -> Dict:
        """Compare dimensions and weight, return updates if >5% difference"""
        updates = {}
        
        try:
            # Check weight
            measured_weight = measurement_data.get("weight")
            if measured_weight and current_product.get("weight_value"):
                current_weight = current_product["weight_value"]
                if self._is_significant_difference(measured_weight, current_weight):
                    updates["weight_value"] = measured_weight
                    # Assume weight is in grams from measurement device
                    updates["weight_unit"] = "g"
                    logger.info(f"Weight update: {current_weight} -> {measured_weight}")
            
            # Check dimensions
            dimension_mappings = [
                ("l", "length"),
                ("w", "width"), 
                ("h", "height")
            ]
            
            for measurement_key, db_key in dimension_mappings:
                measured_value = measurement_data.get(measurement_key)
                if measured_value and current_product.get(db_key):
                    current_value = current_product[db_key]
                    if self._is_significant_difference(measured_value, current_value):
                        updates[db_key] = measured_value
                        logger.info(f"{db_key} update: {current_value} -> {measured_value}")
            
            # Set dimension unit if any dimension was updated
            if any(key in updates for key in ["length", "width", "height"]):
                updates["dimension_unit"] = "mm"
            
            return updates
            
        except Exception as e:
            logger.error(f"Error comparing dimensions: {str(e)}")
            return {}
    
    def _is_significant_difference(self, new_value: float, current_value: float) -> bool:
        """Check if difference is greater than 5%"""
        if current_value == 0:
            return new_value != 0
        
        percentage_diff = abs((new_value - current_value) / current_value) * 100
        return percentage_diff > 5.0
    
    def _parse_attributes_and_get_updates(self, attributes: Dict) -> Dict:
        """Parse new attributes format and return product table updates"""
        updates = {}
        
        try:
            # Handle cap-tstr -> nocap (inverted)
            cap_tstr = attributes.get("cap-tstr")
            if cap_tstr is not None:
                if cap_tstr.lower() == "true":
                    updates["nocap"] = 0  # cap-tstr true means nocap false
                elif cap_tstr.lower() == "false":
                    updates["nocap"] = 1  # cap-tstr false means nocap true
                logger.info(f"cap-tstr '{cap_tstr}' -> nocap {updates.get('nocap')}")
            
            # Handle cello -> nocello (inverted)
            cello = attributes.get("cello")
            if cello is not None:
                if cello.lower() == "true":
                    updates["nocello"] = 0  # cello true means nocello false
                elif cello.lower() == "false":
                    updates["nocello"] = 1  # cello false means nocello true
                logger.info(f"cello '{cello}' -> nocello {updates.get('nocello')}")
            
            # Handle origin and origin2 -> origin field
            origin1 = attributes.get("origin", "").strip()
            origin2 = attributes.get("origin2", "").strip()
            
            origin_codes = []
            
            if origin1:
                code1 = self._lookup_country_code(origin1)
                if code1:
                    origin_codes.append(code1)
            
            if origin2:
                code2 = self._lookup_country_code(origin2)
                if code2:
                    origin_codes.append(code2)
            
            if origin_codes:
                updates["origin"] = ", ".join(origin_codes)
                logger.info(f"Origin update: {origin1}/{origin2} -> {updates['origin']}")
            
            return updates
            
        except Exception as e:
            logger.error(f"Error parsing attributes: {str(e)}")
            return {}
    
    def _lookup_country_code(self, country_name: str) -> Optional[str]:
        """Look up country code from country name"""
        try:
            # Clean country name
            clean_name = country_name.strip().lower()
            
            query = text("""
                SELECT country_code 
                FROM countries 
                WHERE LOWER(country_name) LIKE :pattern
                LIMIT 1
            """)
            
            result = self.execute_with_retry(query, {"pattern": f"%{clean_name}%"})
            row = result.fetchone()
            
            if row:
                logger.info(f"Found country code {row[0]} for '{country_name}'")
                return row[0]
            
            logger.warning(f"No country code found for '{country_name}'")
            return None
            
        except Exception as e:
            logger.error(f"Error looking up country code for '{country_name}': {str(e)}")
            return None
    
    def _update_products_table(self, sku: str, updates: Dict) -> bool:
        """Update products table with the provided updates"""
        try:
            if not updates:
                return True
            
            # Build dynamic UPDATE query
            set_clauses = []
            params = {"sku": sku}
            
            for field, value in updates.items():
                set_clauses.append(f"{field} = :{field}")
                params[field] = value
            
            query_text = f"""
                UPDATE products 
                SET {', '.join(set_clauses)}
                WHERE sku = :sku
            """
            
            query = text(query_text)
            result = self.execute_with_retry(query, params)
            
            logger.info(f"Updated products table for SKU {sku} with {len(updates)} fields")
            return True
            
        except Exception as e:
            logger.error(f"Error updating products table for SKU {sku}: {str(e)}")
            return False
