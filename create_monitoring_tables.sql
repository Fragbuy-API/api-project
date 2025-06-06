-- Create API request logging table for monitoring and metrics
-- This table stores detailed information about all API requests for analysis

CREATE TABLE IF NOT EXISTS api_request_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    request_id VARCHAR(50) NULL,
    endpoint VARCHAR(100) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INT NOT NULL,
    response_time_ms INT NOT NULL,
    error_message TEXT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    
    -- Indexes for better query performance
    INDEX idx_timestamp (timestamp),
    INDEX idx_endpoint (endpoint),
    INDEX idx_status_code (status_code),
    INDEX idx_request_id (request_id),
    INDEX idx_endpoint_timestamp (endpoint, timestamp),
    INDEX idx_status_timestamp (status_code, timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add request_id column to existing api_received_data table if it doesn't exist
-- This allows for idempotency checking in measurement processing

ALTER TABLE api_received_data 
ADD COLUMN IF NOT EXISTS request_id VARCHAR(50) NULL AFTER id,
ADD INDEX IF NOT EXISTS idx_request_id (request_id);

-- Create a comment for documentation
ALTER TABLE api_request_log COMMENT = 'Stores API request logs for monitoring, metrics, and performance analysis';
ALTER TABLE api_received_data COMMENT = 'Stores received measurement data with optional request_id for idempotency';

-- Show table structures for verification
DESCRIBE api_request_log;
DESCRIBE api_received_data;
