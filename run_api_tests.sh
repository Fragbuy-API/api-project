#!/bin/bash

# API Test Automation Script (Web Status Version)
# This script runs specified API test scripts and displays results on a status page

# =============== CONFIGURATION ===============
# Test scripts to run (add or remove scripts as needed)
TEST_SCRIPTS=(
  "/root/api/tests/test_check_sku_api.py"
  "/root/api/tests/test_purchase_orders.py"
  "/root/api/tests/test_update_po_status.py"
)

# Log and status page directories
LOG_DIR="/root/api/logs"
REPORT_DIR="${LOG_DIR}/reports"
WEB_DIR="/var/www/html/api-monitor"  # Updated path for the web monitor
STATUS_FILE="${WEB_DIR}/api-status.txt"
HTML_STATUS_FILE="${WEB_DIR}/index.html"

# Python virtual environment path (if applicable)
VENV_PATH="/root/api/venv"

# Maximum log retention (in days)
LOG_RETENTION_DAYS=30

# =============== FUNCTIONS ===============

# Initialize log directories
initialize() {
  # Create log directories if they don't exist
  mkdir -p "${LOG_DIR}"
  mkdir -p "${REPORT_DIR}"
  mkdir -p "${WEB_DIR}"  # Ensure web directory exists
  
  # Create timestamp for this run
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  LOG_FILE="${LOG_DIR}/api_tests_${TIMESTAMP}.log"
  SUMMARY_FILE="${REPORT_DIR}/summary_${TIMESTAMP}.txt"
  
  # Start with clean summary file
  echo "Qboid API Test Summary - $(date)" > "${SUMMARY_FILE}"
  echo "============================================" >> "${SUMMARY_FILE}"
  echo "" >> "${SUMMARY_FILE}"
}

# Activate Python virtual environment if it exists
activate_venv() {
  if [ -d "${VENV_PATH}" ]; then
    source "${VENV_PATH}/bin/activate"
    echo "Activated Python virtual environment at ${VENV_PATH}" >> "${LOG_FILE}"
  else
    echo "Warning: Virtual environment not found at ${VENV_PATH}" >> "${LOG_FILE}"
  fi
}

# Run a test script and return success/failure
run_test() {
  local test_script=$1
  local script_name=$(basename "${test_script}")
  local test_log="${LOG_DIR}/${script_name%.py}_${TIMESTAMP}.log"
  
  echo "Running test: ${script_name}..."
  echo "Running test: ${script_name}..." >> "${LOG_FILE}"
  
  # Execute the test script
  python3 "${test_script}" > "${test_log}" 2>&1
  local exit_code=$?
  
  # Check for failure indicators
  if grep -q "Some tests failed" "${test_log}" || [ $exit_code -ne 0 ]; then
    local failure_count=$(grep -c "✗ FAIL" "${test_log}" || echo "Unknown")
    echo "❌ FAILED: ${script_name} - ${failure_count} failures detected" >> "${SUMMARY_FILE}"
    
    # Extract failure details and add to summary
    echo "   Failure details:" >> "${SUMMARY_FILE}"
    grep -B 1 -A 3 "✗ FAIL" "${test_log}" | sed 's/^/   /' >> "${SUMMARY_FILE}"
    echo "" >> "${SUMMARY_FILE}"
    
    return 1
  else
    local pass_count=$(grep -c "✓ PASS" "${test_log}" || echo "Unknown")
    echo "✅ PASSED: ${script_name} - ${pass_count} tests passed" >> "${SUMMARY_FILE}"
    return 0
  fi
}

# Clean up old log files
cleanup_logs() {
  if [ -d "${LOG_DIR}" ]; then
    echo "Cleaning up logs older than ${LOG_RETENTION_DAYS} days..." >> "${LOG_FILE}"
    find "${LOG_DIR}" -name "*.log" -type f -mtime +${LOG_RETENTION_DAYS} -delete
    find "${REPORT_DIR}" -name "*.txt" -type f -mtime +${LOG_RETENTION_DAYS} -delete
  fi
}

# Update the web status page
update_web_status() {
  local total_tests=$1
  local failed_tests=$2
  
  # Create a copy of the summary with added HTML metadata
  cp "${SUMMARY_FILE}" "${STATUS_FILE}"
  
  # Add timestamp and link to the status file
  echo "" >> "${STATUS_FILE}"
  echo "Last update: $(date)" >> "${STATUS_FILE}"
  echo "Log directory: ${LOG_DIR}" >> "${STATUS_FILE}"
  
  # Create or update the HTML status page if it doesn't exist
  cat > "${HTML_STATUS_FILE}" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="300"> <!-- Refresh every 5 minutes -->
    <title>Qboid API Status</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        pre {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            white-space: pre-wrap;
            font-family: SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }
        .status-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .refresh-time {
            font-size: 0.9rem;
            color: #6c757d;
        }
        .success { color: #28a745; }
        .failure { color: #dc3545; }
        .status-indicator {
            font-size: 1.2rem;
            font-weight: bold;
            padding: 6px 12px;
            border-radius: 4px;
        }
        .status-success {
            background-color: #d4edda;
            color: #155724;
        }
        .status-failure {
            background-color: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="status-header">
        <h1>Qboid API Status</h1>
        <span class="refresh-time">Auto-refreshes every 5 minutes</span>
    </div>
    
    <div id="status-indicator">
        <!-- Will be filled dynamically -->
    </div>
    
    <h2>Latest Test Results</h2>
    <pre id="status">Loading test results...</pre>

    <script>
        function updatePage() {
            fetch('api-status.txt?' + new Date().getTime())
                .then(response => response.text())
                .then(data => {
                    document.getElementById('status').textContent = data;
                    
                    // Update status indicator
                    const statusIndicator = document.getElementById('status-indicator');
                    if (data.includes('❌ FAILED')) {
                        statusIndicator.innerHTML = '<span class="status-indicator status-failure">⚠️ Some Tests Are Failing</span>';
                    } else {
                        statusIndicator.innerHTML = '<span class="status-indicator status-success">✅ All Tests Passing</span>';
                    }
                })
                .catch(err => {
                    document.getElementById('status').textContent = 'Error loading status: ' + err;
                });
        }
        
        // Initial update
        updatePage();
        
        // Refresh every 5 minutes (300000 ms)
        setInterval(updatePage, 300000);
    </script>
</body>
</html>
EOF
  
  echo "Updated web status page at ${HTML_STATUS_FILE}" >> "${LOG_FILE}"
  
  # Set proper permissions
  chmod 644 "${STATUS_FILE}" "${HTML_STATUS_FILE}"
}

# =============== MAIN SCRIPT ===============

# Initialize logging
initialize

echo "API test run started at $(date)" >> "${LOG_FILE}"

# Activate virtual environment if needed
activate_venv

# Initialize counters
TOTAL_TESTS=0
FAILED_TESTS=0

# Run each test script
for test_script in "${TEST_SCRIPTS[@]}"; do
  if [ -f "${test_script}" ]; then
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Run the test
    if ! run_test "${test_script}"; then
      FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
  else
    echo "Error: Test script not found: ${test_script}" >> "${LOG_FILE}"
    echo "❓ MISSING: $(basename ${test_script}) - File not found" >> "${SUMMARY_FILE}"
  fi
done

# Add summary statistics
echo "" >> "${SUMMARY_FILE}"
echo "============================================" >> "${SUMMARY_FILE}"
echo "SUMMARY: ${FAILED_TESTS} of ${TOTAL_TESTS} test scripts failed" >> "${SUMMARY_FILE}"
echo "Test run completed at $(date)" >> "${SUMMARY_FILE}"

# Log completion
echo "API test run completed at $(date)" >> "${LOG_FILE}"
echo "Results: ${FAILED_TESTS} of ${TOTAL_TESTS} test scripts failed" >> "${LOG_FILE}"

# Update the web status page
update_web_status "${TOTAL_TESTS}" "${FAILED_TESTS}"

# Clean up old logs
cleanup_logs

# Exit with number of failed tests as status code
exit ${FAILED_TESTS}