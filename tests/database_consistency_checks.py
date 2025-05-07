#!/usr/bin/python3

import pymysql
import json
import os
import csv
from datetime import datetime
from decimal import Decimal

# Database connection parameters
DB_CONFIG = {
    "host": "155.138.159.75",
    "user": "Qboid",
    "password": "JY8xM2ch5#Q[",
    "db": "products",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

# Path to save results
RESULTS_DIR = "/var/www/html/api-monitor/db-checks"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Schema information from CSV file
SCHEMA_FILE = "/root/api/columns_202505060911.csv"

# JSON serializer for objects not serializable by default JSON code
def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)  # Convert Decimal to float for JSON serialization
    raise TypeError(f"Type {type(obj)} not serializable")

def load_schema_info():
    """Load schema information from the CSV file"""
    tables = {}
    primary_keys = {}
    
    with open(SCHEMA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            table_name = row['table_name']
            column_name = row['column_name']
            column_key = row['column_key']
            
            # Initialize table entry if not exists
            if table_name not in tables:
                tables[table_name] = []
            
            # Add column to table
            tables[table_name].append({
                'name': column_name,
                'type': row['data_type'],
                'is_key': column_key == 'PRI'
            })
            
            # Record primary key
            if column_key == 'PRI':
                primary_keys[table_name] = column_name
    
    return tables, primary_keys

def convert_to_serializable(value):
    """Convert value to a JSON-serializable type"""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value

def run_query(connection, query, description):
    """Run a query and return results with metadata"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Convert all results to serializable format
            serializable_results = []
            for row in results:
                serializable_row = {}
                for key, value in row.items():
                    serializable_row[key] = convert_to_serializable(value)
                serializable_results.append(serializable_row)
            
            return {
                "description": description,
                "query": query,
                "results": serializable_results,
                "count": len(results),
                "status": "warning" if len(results) > 0 else "healthy"
            }
    except Exception as e:
        return {
            "description": description,
            "query": query,
            "error": str(e),
            "status": "error"
        }

def run_consistency_checks():
    """Run all consistency checks and return results"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        
        # Load schema information
        tables, primary_keys = load_schema_info()
        print(f"Loaded schema for {len(tables)} tables")
        
        # Define checks based on schema
        checks = []
        
        # Check for duplicate primary keys in major tables
        for table_name, pk_column in primary_keys.items():
            checks.append({
                "query": f"""
                    SELECT {pk_column}, COUNT(*) as count 
                    FROM {table_name} 
                    GROUP BY {pk_column} 
                    HAVING COUNT(*) > 1
                    LIMIT 100
                """,
                "description": f"Duplicate primary keys ({pk_column}) in {table_name} table"
            })
        
        # Check for orphaned foreign keys in related tables
        # products -> barcodes
        if 'products' in tables and 'barcodes' in tables:
            checks.append({
                "query": """
                    SELECT b.* 
                    FROM barcodes b
                    LEFT JOIN products p ON b.sku = p.sku
                    WHERE p.sku IS NULL AND b.sku IS NOT NULL
                    LIMIT 100
                """,
                "description": "Barcodes referencing non-existent products"
            })
        
        # putaway_orders -> putaway_items
        if 'putaway_orders' in tables and 'putaway_items' in tables:
            checks.append({
                "query": """
                    SELECT pi.* 
                    FROM putaway_items pi
                    LEFT JOIN putaway_orders po ON pi.order_id = po.id
                    WHERE po.id IS NULL AND pi.order_id IS NOT NULL
                    LIMIT 100
                """,
                "description": "Putaway items referencing non-existent orders"
            })
        
        # bulk_storage_orders -> bulk_storage_items
        if 'bulk_storage_orders' in tables and 'bulk_storage_items' in tables:
            checks.append({
                "query": """
                    SELECT bsi.* 
                    FROM bulk_storage_items bsi
                    LEFT JOIN bulk_storage_orders bso ON bsi.order_id = bso.id
                    WHERE bso.id IS NULL AND bsi.order_id IS NOT NULL
                    LIMIT 100
                """,
                "description": "Bulk storage items referencing non-existent orders"
            })
        
        # purchase_orders -> po_lines
        if 'purchase_orders' in tables and 'po_lines' in tables:
            checks.append({
                "query": """
                    SELECT pol.* 
                    FROM po_lines pol
                    LEFT JOIN purchase_orders po ON pol.po_number = po.po_number
                    WHERE po.po_number IS NULL AND pol.po_number IS NOT NULL
                    LIMIT 100
                """,
                "description": "PO lines referencing non-existent purchase orders"
            })
        
        # replen_orders -> replen_order_items
        if 'replen_orders' in tables and 'replen_order_items' in tables:
            checks.append({
                "query": """
                    SELECT roi.* 
                    FROM replen_order_items roi
                    LEFT JOIN replen_orders ro ON roi.ro_id = ro.ro_id
                    WHERE ro.ro_id IS NULL AND roi.ro_id IS NOT NULL
                    LIMIT 100
                """,
                "description": "Replenishment order items referencing non-existent orders"
            })
        
        # Check for products referenced in various tables that don't exist
        for table, column in [
            ('putaway_items', 'sku'),
            ('bulk_storage_items', 'sku'),
            ('po_lines', 'sku'),
            ('replen_order_items', 'sku'),
            ('art_operations', 'sku')
        ]:
            if table in tables:
                for col in tables[table]:
                    if col['name'] == column:
                        checks.append({
                            "query": f"""
                                SELECT t.* 
                                FROM {table} t
                                LEFT JOIN products p ON t.{column} = p.sku
                                WHERE p.sku IS NULL AND t.{column} IS NOT NULL
                                LIMIT 100
                            """,
                            "description": f"Invalid SKUs in {table} table"
                        })
                        break
        
        # Check for null values in important columns
        important_non_null_columns = [
            ('products', 'sku'),
            ('barcodes', 'barcode'),
            ('purchase_orders', 'po_number'),
            ('putaway_orders', 'tote'),
            ('bulk_storage_orders', 'location')
        ]
        
        for table, column in important_non_null_columns:
            if table in tables:
                for col in tables[table]:
                    if col['name'] == column:
                        checks.append({
                            "query": f"""
                                SELECT * FROM {table}
                                WHERE {column} IS NULL OR {column} = ''
                                LIMIT 100
                            """,
                            "description": f"Null or empty values in {table}.{column}"
                        })
                        break
                        
        # Check for uniqueness of barcode values
        if 'barcodes' in tables:
            checks.append({
                "query": """
                    SELECT barcode, COUNT(*) as count 
                    FROM barcodes 
                    GROUP BY barcode 
                    HAVING COUNT(*) > 1
                    LIMIT 100
                """,
                "description": "Duplicate barcodes"
            })
        
        # Run all checks
        results = []
        for check in checks:
            print(f"Running check: {check['description']}")
            result = run_query(connection, check["query"], check["description"])
            results.append(result)
            print(f"  Status: {result['status']}, Count: {result.get('count', 'error')}")
        
        # Calculate overall status
        has_errors = any(result["status"] == "error" for result in results)
        warnings = sum(1 for result in results if result["status"] == "warning")
        
        if has_errors:
            overall_status = "error"
        elif warnings > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        # Prepare final report
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "total_checks": len(checks),
            "warnings": warnings,
            "has_errors": has_errors,
            "checks": results
        }
        
        # Save report to file
        filename = f"{RESULTS_DIR}/latest.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=json_serial)
        
        # Also save a timestamped version for history
        timestamp_filename = f"{RESULTS_DIR}/report_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        with open(timestamp_filename, 'w') as f:
            json.dump(report, f, indent=2, default=json_serial)
        
        # Print summary to stdout (for cron logs)
        print(f"Database checks completed: {len(checks)} checks, {warnings} warnings, {has_errors} errors")
        if warnings > 0 or has_errors:
            print(f"Issues found in these checks:")
            for result in results:
                if result["status"] in ["warning", "error"]:
                    status_msg = "WARNING" if result["status"] == "warning" else "ERROR"
                    issue_count = result.get("count", "error")
                    print(f"- {result['description']}: {status_msg} - {issue_count} issues found")
        
        connection.close()
        return True
    
    except Exception as e:
        error_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "error",
            "error": str(e)
        }
        
        # Save error report
        with open(f"{RESULTS_DIR}/latest.json", 'w') as f:
            json.dump(error_report, f, indent=2)
        
        print(f"Error running database checks: {str(e)}")
        return False

if __name__ == "__main__":
    run_consistency_checks()