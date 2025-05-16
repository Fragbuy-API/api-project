import pymysql
import time
from decimal import Decimal, InvalidOperation

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'your_database'
}

class PriceCalculationTester:
    def __init__(self):
        self.connection = pymysql.connect(**DB_CONFIG)
        self.cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        self.tests_run = 0
        self.tests_passed = 0
        
    def setup(self):
        """Set up test environment"""
        # Drop and recreate test tables
        self.execute_query("DROP TABLE IF EXISTS test_global_constants")
        self.execute_query("DROP TABLE IF EXISTS test_prices")
        self.execute_query("CREATE TABLE test_global_constants LIKE global_constants")
        self.execute_query("CREATE TABLE test_prices LIKE prices")
        
        # Insert test constants
        self.execute_query("""
            INSERT INTO test_global_constants (constant_name, constant_value) VALUES
            ('GLOBALFX', 1.3500),
            ('FLEXDELTA', 2.50),
            ('RETDELTA', 5.00),
            ('BESTBUYDELTA', 7.50),
            ('EBAYDELTA', 3.75)
        """)
        
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        try:
            self.cursor.execute(query, params or ())
            self.connection.commit()
            
            if query.strip().upper().startswith("SELECT"):
                return self.cursor.fetchall()
            return None
        except Exception as e:
            print(f"SQL Error: {e}")
            print(f"Query: {query}")
            if params:
                print(f"Params: {params}")
            self.connection.rollback()
            raise
    
    def safe_decimal(self, value, default=None):
        """Safely convert a value to Decimal"""
        if value is None:
            return default
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            print(f"Warning: Could not convert '{value}' to Decimal")
            return default
    
    def run_test(self, test_name, actual, expected, precision=2):
        """Run a test and report results"""
        self.tests_run += 1
        
        if actual is None and expected is None:
            passed = True
        elif actual is None or expected is None:
            passed = False
        elif isinstance(actual, Decimal) and isinstance(expected, Decimal):
            passed = abs(actual - expected) < Decimal('0.01')
        else:
            passed = actual == expected
            
        if passed:
            self.tests_passed += 1
            result = "PASSED"
        else:
            result = "FAILED"
            
        print(f"Test {self.tests_run}: {test_name} - {result}")
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")
        print()
        
        return passed
    
    def test_initial_insert(self):
        """Test 1: Insert basic product and check calculations"""
        # First check table structure to adapt our test
        table_info = self.execute_query("DESCRIBE test_prices")
        columns = [row['Field'] for row in table_info]
        
        # Display column names for debugging
        print("Available columns in test_prices table:")
        print(", ".join(columns))
        
        # Insert test record with correct column name
        self.execute_query(
            "INSERT INTO test_prices (sku, fragbuy_cad) VALUES (%s, %s)",
            ("TEST001", 100.00)
        )
        
        # Get the inserted record
        result = self.execute_query(
            "SELECT * FROM test_prices WHERE sku = %s",
            ["TEST001"]
        )
        
        if not result:
            print("ERROR: Could not retrieve test record")
            return
            
        result = result[0]
        
        # Display all column values for debugging
        print("Retrieved record values:")
        for column, value in result.items():
            print(f"{column}: {value}")
        
        # Test fragbuy_usd calculation
        self.run_test(
            "fragbuy_usd Calculation",
            self.safe_decimal(result.get('fragbuy_usd')),
            Decimal('74.07'),  # 100.00 / 1.35
        )
        
        # Test fragflex_cad calculation
        self.run_test(
            "fragflex_cad Calculation",
            self.safe_decimal(result.get('fragflex_cad')),
            Decimal('102.50'),  # 100.00 + 2.50
        )
        
    def test_fragbuy_update(self):
        """Test 2: Update fragbuy_cad and check cascading updates"""
        self.execute_query(
            "UPDATE test_prices SET fragbuy_cad = %s WHERE sku = %s",
            (120.00, "TEST001")
        )
        
        # Get the updated record
        result = self.execute_query(
            "SELECT * FROM test_prices WHERE sku = %s",
            ["TEST001"]
        )
        
        if not result:
            print("ERROR: Could not retrieve updated test record")
            return
            
        result = result[0]
        
        # Test updated ret_cad calculation
        self.run_test(
            "ret_cad After Update",
            self.safe_decimal(result.get('ret_cad')),
            Decimal('125.00'),  # 120.00 + 5.00
        )
        
    def test_globalfx_update(self):
        """Test 3: Update GLOBALFX and check all USD values update"""
        self.execute_query(
            "UPDATE test_global_constants SET constant_value = %s WHERE constant_name = %s",
            (1.25, "GLOBALFX")
        )
        
        # Wait briefly for trigger to complete
        time.sleep(0.5)
        
        # Get the updated record
        result = self.execute_query(
            "SELECT * FROM test_prices WHERE sku = %s",
            ["TEST001"]
        )
        
        if not result:
            print("ERROR: Could not retrieve updated test record")
            return
            
        result = result[0]
        
        # Test updated fragbuy_usd calculation
        self.run_test(
            "fragbuy_usd After GLOBALFX Change",
            self.safe_decimal(result.get('fragbuy_usd')),
            Decimal('96.00'),  # 120.00 / 1.25
        )
        
    def test_flexdelta_update(self):
        """Test 4: Update FLEXDELTA and check calculations"""
        self.execute_query(
            "UPDATE test_global_constants SET constant_value = %s WHERE constant_name = %s",
            (3.50, "FLEXDELTA")
        )
        
        # Wait briefly for trigger to complete
        time.sleep(0.5)
        
        # Get the updated record
        result = self.execute_query(
            "SELECT * FROM test_prices WHERE sku = %s",
            ["TEST001"]
        )
        
        if not result:
            print("ERROR: Could not retrieve updated test record")
            return
            
        result = result[0]
        
        # Test updated fragflex_cad calculation
        self.run_test(
            "fragflex_cad After FLEXDELTA Change",
            self.safe_decimal(result.get('fragflex_cad')),
            Decimal('123.50'),  # 120.00 + 3.50
        )
        
    def test_msrp_enforcement(self):
        """Test 5: Test msrp_cad minimum enforcement"""
        # Set msrp_cad to a value below fragbuy_cad
        self.execute_query(
            "UPDATE test_prices SET msrp_cad = %s WHERE sku = %s",
            (110.00, "TEST001")
        )
        
        # Get the updated record
        result = self.execute_query(
            "SELECT * FROM test_prices WHERE sku = %s",
            ["TEST001"]
        )
        
        if not result:
            print("ERROR: Could not retrieve updated test record")
            return
            
        result = result[0]
        
        # Test msrp_cad enforcement (should equal fragbuy_cad)
        self.run_test(
            "msrp_cad Minimum Enforcement",
            self.safe_decimal(result.get('msrp_cad')),
            Decimal('120.00'),  # Should be equal to fragbuy_cad
        )
        
    def cleanup(self):
        """Clean up test environment"""
        try:
            self.execute_query("DROP TABLE IF EXISTS test_global_constants")
            self.execute_query("DROP TABLE IF EXISTS test_prices")
        finally:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
        
    def run_all_tests(self):
        """Run all tests"""
        try:
            self.setup()
            
            self.test_initial_insert()
            self.test_fragbuy_update()
            self.test_globalfx_update()
            self.test_flexdelta_update()
            self.test_msrp_enforcement()
            
            print("\n=== Test Summary ===")
            print(f"Total Tests: {self.tests_run}")
            print(f"Tests Passed: {self.tests_passed}")
            if self.tests_run > 0:
                print(f"Success Rate: {(self.tests_passed / self.tests_run) * 100:.2f}%")
            else:
                print("Success Rate: N/A (no tests run)")
            
        except Exception as e:
            print(f"Test execution error: {e}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    tester = PriceCalculationTester()
    tester.run_all_tests()