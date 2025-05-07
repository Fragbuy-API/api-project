#!/bin/bash

# Directory paths
LOG_DIR="/root/api/logs"
REPORT_DIR="${LOG_DIR}/reports"
WEB_DIR="/var/www/html/api-monitor"

# Make sure directories exist
mkdir -p "${LOG_DIR}"
mkdir -p "${REPORT_DIR}"
mkdir -p "${WEB_DIR}"

# Current timestamp
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
LOG_FILE="${LOG_DIR}/api_tests_${TIMESTAMP}.log"
SUMMARY_FILE="${REPORT_DIR}/summary_${TIMESTAMP}.txt"
WEB_STATUS_FILE="${WEB_DIR}/api-status.txt"

# Test scripts organized by category
declare -A TEST_GROUPS
TEST_GROUPS[Core]="/root/api/tests/test_check_sku_api.py /root/api/tests/test_unified_search.py"
TEST_GROUPS[Products]="/root/api/tests/test_product_search.py /root/api/tests/barcode_lookup_test.py"
TEST_GROUPS[Orders]="/root/api/tests/test_purchase_orders.py /root/api/tests/test_get_purchase_order.py /root/api/tests/test_update_po_status.py"
TEST_GROUPS[Warehouse]="/root/api/tests/putaway_test.py /root/api/tests/bulk_storage_test.py /root/api/tests/test_warehouse_locations.py /root/api/tests/test_art_orders.py"
TEST_GROUPS[Replenishment]="/root/api/tests/test_ro_complete.py /root/api/tests/test_ro_get_orders.py /root/api/tests/test_ro_item_picked.py /root/api/tests/test_ro_pick_cancelled.py"

# Initialize summary file
echo "API Test Summary - $(date)" > "${SUMMARY_FILE}"
echo "=================================" >> "${SUMMARY_FILE}"
echo "" >> "${SUMMARY_FILE}"

# Initialize status variables
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Initialize web status file
echo "API Test Results - Last updated: $(date)" > "${WEB_STATUS_FILE}"
echo "===============================================" >> "${WEB_STATUS_FILE}"
echo "" >> "${WEB_STATUS_FILE}"

# Run each group of tests
for GROUP in "${!TEST_GROUPS[@]}"; do
    GROUP_TESTS=0
    GROUP_PASSED=0
    GROUP_FAILED=0
    
    echo "Testing ${GROUP} APIs..." >> "${LOG_FILE}"
    echo "" >> "${LOG_FILE}"
    
    echo "## ${GROUP} APIs" >> "${SUMMARY_FILE}"
    echo "## ${GROUP} APIs" >> "${WEB_STATUS_FILE}"
    
    # Split the space-separated test scripts into an array
    IFS=' ' read -ra TEST_SCRIPTS <<< "${TEST_GROUPS[$GROUP]}"
    
    # Run each test in the group
    for TEST_SCRIPT in "${TEST_SCRIPTS[@]}"; do
        SCRIPT_NAME=$(basename "${TEST_SCRIPT}")
        
        echo "Running ${SCRIPT_NAME}..." >> "${LOG_FILE}"
        
        # Run the test and capture output
        python3 "${TEST_SCRIPT}" >> "${LOG_FILE}" 2>&1
        EXIT_CODE=$?
        
        # Increment total tests
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        GROUP_TESTS=$((GROUP_TESTS + 1))
        
        # Check result
        if [ ${EXIT_CODE} -eq 0 ]; then
            echo "✅ PASSED: ${SCRIPT_NAME}" >> "${SUMMARY_FILE}"
            echo "✅ PASSED: ${SCRIPT_NAME}" >> "${WEB_STATUS_FILE}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            GROUP_PASSED=$((GROUP_PASSED + 1))
        else
            echo "❌ FAILED: ${SCRIPT_NAME}" >> "${SUMMARY_FILE}"
            echo "❌ FAILED: ${SCRIPT_NAME}" >> "${WEB_STATUS_FILE}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            GROUP_FAILED=$((GROUP_FAILED + 1))
        fi
    done
    
    # Add group summary
    echo "" >> "${SUMMARY_FILE}"
    echo "Group Results: ${GROUP_PASSED}/${GROUP_TESTS} tests passed" >> "${SUMMARY_FILE}"
    echo "" >> "${SUMMARY_FILE}"
    
    echo "" >> "${WEB_STATUS_FILE}"
    echo "Group Results: ${GROUP_PASSED}/${GROUP_TESTS} tests passed" >> "${WEB_STATUS_FILE}"
    echo "" >> "${WEB_STATUS_FILE}"
done

# Add summary totals
echo "=================================" >> "${SUMMARY_FILE}"
echo "Overall Results:" >> "${SUMMARY_FILE}"
echo "Total Tests: ${TOTAL_TESTS}" >> "${SUMMARY_FILE}"
echo "Passed: ${PASSED_TESTS}" >> "${SUMMARY_FILE}"
echo "Failed: ${FAILED_TESTS}" >> "${SUMMARY_FILE}"

echo "===============================================" >> "${WEB_STATUS_FILE}"
echo "Overall Results:" >> "${WEB_STATUS_FILE}"
echo "Total Tests: ${TOTAL_TESTS}" >> "${WEB_STATUS_FILE}"
echo "Passed: ${PASSED_TESTS}" >> "${WEB_STATUS_FILE}"
echo "Failed: ${FAILED_TESTS}" >> "${WEB_STATUS_FILE}"

# Clean up old log files (keep last 30 days)
find "${LOG_DIR}" -name "api_tests_*.log" -type f -mtime +30 -delete
find "${REPORT_DIR}" -name "summary_*.txt" -type f -mtime +30 -delete

echo "Tests completed. Results saved to ${WEB_STATUS_FILE}"