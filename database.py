from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection with pooling and reconnection settings
DATABASE_URL = "mysql+pymysql://Qboid:JY8xM2ch5#Q[@155.138.159.75/products"
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True  # Enable automatic reconnection
)

def execute_with_retry(query, params, max_retries=3):
    """Execute a database query with retry logic"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Executing query (attempt {attempt+1}/{max_retries})")
            with engine.connect() as connection:
                result = connection.execute(query, params)
                connection.commit()
                logger.info("Query executed successfully")
                return result
        except Exception as e:
            logger.error(f"Database error on attempt {attempt+1}: {str(e)}")
            if attempt == max_retries - 1:  # Last attempt
                logger.error("Maximum retry attempts reached, raising exception")
                raise  # Re-raise the last error
            time.sleep(1 * (attempt + 1))  # Exponential backoff
            logger.info(f"Retrying in {1 * (attempt + 1)} seconds")

def log_api_request(endpoint: str, method: str, status_code: int, 
                   response_time_ms: int, request_id: Optional[str] = None,
                   error_message: Optional[str] = None, ip_address: Optional[str] = None,
                   user_agent: Optional[str] = None) -> None:
    """Log an API request to the api_request_log table"""
    try:
        query = text("""
            INSERT INTO api_request_log 
            (request_id, endpoint, method, status_code, response_time_ms, 
             error_message, timestamp, ip_address, user_agent)
            VALUES 
            (:request_id, :endpoint, :method, :status_code, :response_time_ms, 
             :error_message, :timestamp, :ip_address, :user_agent)
        """)
        
        params = {
            'request_id': request_id,
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time_ms': response_time_ms,
            'error_message': error_message,
            'timestamp': datetime.now(),
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        execute_with_retry(query, params)
        logger.debug(f"Logged API request: {method} {endpoint} -> {status_code}")
        
    except Exception as e:
        # Don't let logging errors break the main request
        logger.error(f"Failed to log API request: {str(e)}")

def check_request_idempotency(request_id: str) -> Optional[int]:
    """Check if a request ID has already been processed. Returns record ID if found."""
    try:
        query = text("""
            SELECT id FROM api_received_data 
            WHERE request_id = :request_id
            LIMIT 1
        """)
        
        result = execute_with_retry(query, {'request_id': request_id})
        row = result.fetchone()
        
        if row:
            logger.info(f"Found duplicate request_id: {request_id}")
            return row[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Error checking request idempotency: {str(e)}")
        # On error, assume it's not a duplicate to allow processing
        return None

def get_api_error_rates(hours: int = 1) -> Dict[str, Any]:
    """Get API error rates for the specified number of hours"""
    try:
        query = text("""
            SELECT 
                COUNT(*) as total_requests,
                SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count,
                SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) as server_error_count,
                SUM(CASE WHEN status_code >= 400 AND status_code < 500 THEN 1 ELSE 0 END) as client_error_count,
                AVG(response_time_ms) as avg_response_time,
                MAX(response_time_ms) as max_response_time
            FROM api_request_log 
            WHERE timestamp >= NOW() - INTERVAL :hours HOUR
        """)
        
        result = execute_with_retry(query, {'hours': hours})
        row = result.fetchone()
        
        if row and row[0] > 0:  # If we have data
            total_requests = row[0]
            error_count = row[1] or 0
            server_error_count = row[2] or 0
            client_error_count = row[3] or 0
            avg_response_time = float(row[4]) if row[4] else 0.0
            max_response_time = row[5] or 0
            
            return {
                "total_requests": total_requests,
                "error_count": error_count,
                "server_error_count": server_error_count,
                "client_error_count": client_error_count,
                "error_rate_percent": round((error_count / total_requests) * 100, 2),
                "avg_response_time_ms": round(avg_response_time, 2),
                "max_response_time_ms": max_response_time
            }
        else:
            return {
                "total_requests": 0,
                "error_count": 0,
                "server_error_count": 0,
                "client_error_count": 0,
                "error_rate_percent": 0.0,
                "avg_response_time_ms": 0.0,
                "max_response_time_ms": 0
            }
            
    except Exception as e:
        logger.error(f"Error getting API error rates: {str(e)}")
        return {
            "error": f"Failed to get error rates: {str(e)}"
        }

def get_endpoint_performance_stats() -> Dict[str, Any]:
    """Get performance statistics by endpoint for the last 24 hours"""
    try:
        query = text("""
            SELECT 
                endpoint,
                COUNT(*) as request_count,
                AVG(response_time_ms) as avg_response_time,
                MAX(response_time_ms) as max_response_time,
                SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count
            FROM api_request_log 
            WHERE timestamp >= NOW() - INTERVAL 24 HOUR
            GROUP BY endpoint
            ORDER BY request_count DESC
        """)
        
        result = execute_with_retry(query, {})
        rows = result.fetchall()
        
        endpoint_stats = []
        for row in rows:
            endpoint = row[0]
            request_count = row[1]
            avg_response_time = float(row[2]) if row[2] else 0.0
            max_response_time = row[3] or 0
            error_count = row[4] or 0
            
            endpoint_stats.append({
                "endpoint": endpoint,
                "request_count": request_count,
                "avg_response_time_ms": round(avg_response_time, 2),
                "max_response_time_ms": max_response_time,
                "error_count": error_count,
                "error_rate_percent": round((error_count / request_count) * 100, 2) if request_count > 0 else 0.0
            })
        
        return {"endpoints": endpoint_stats}
        
    except Exception as e:
        logger.error(f"Error getting endpoint performance stats: {str(e)}")
        return {"error": f"Failed to get endpoint stats: {str(e)}"}

def get_recent_errors(limit: int = 10) -> Dict[str, Any]:
    """Get recent error details"""
    try:
        query = text("""
            SELECT 
                timestamp,
                endpoint,
                method,
                status_code,
                error_message,
                request_id,
                response_time_ms
            FROM api_request_log 
            WHERE status_code >= 400
            ORDER BY timestamp DESC
            LIMIT :limit
        """)
        
        result = execute_with_retry(query, {'limit': limit})
        rows = result.fetchall()
        
        recent_errors = []
        for row in rows:
            recent_errors.append({
                "timestamp": row[0].isoformat() if row[0] else None,
                "endpoint": row[1],
                "method": row[2],
                "status_code": row[3],
                "error_message": row[4],
                "request_id": row[5],
                "response_time_ms": row[6]
            })
        
        return {"recent_errors": recent_errors}
        
    except Exception as e:
        logger.error(f"Error getting recent errors: {str(e)}")
        return {"error": f"Failed to get recent errors: {str(e)}"}

def cleanup_old_logs(days_to_keep: int = 30) -> int:
    """Clean up old log entries. Returns number of deleted records."""
    try:
        query = text("""
            DELETE FROM api_request_log 
            WHERE timestamp < NOW() - INTERVAL :days DAY
        """)
        
        result = execute_with_retry(query, {'days': days_to_keep})
        deleted_count = result.rowcount
        
        logger.info(f"Cleaned up {deleted_count} old log entries (older than {days_to_keep} days)")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up old logs: {str(e)}")
        return 0