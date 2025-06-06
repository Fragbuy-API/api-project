from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging
import traceback

# Import database functions
from database import get_api_error_rates, get_endpoint_performance_stats, get_recent_errors, cleanup_old_logs

# Import standardized error handling
from error_handlers import (
    handle_server_error, log_operation_start, log_operation_success,
    ErrorCodes, create_error_response
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["monitoring"]
)

@router.get("/monitoring/detailed-health")
async def detailed_health_check():
    """
    Detailed health check with comprehensive monitoring data
    """
    log_operation_start("detailed health check")
    
    try:
        # Get error rates for different time periods
        error_rates_1h = get_api_error_rates(hours=1)
        error_rates_6h = get_api_error_rates(hours=6)
        error_rates_24h = get_api_error_rates(hours=24)
        
        # Get endpoint performance statistics
        endpoint_stats = get_endpoint_performance_stats()
        
        # Get recent errors
        recent_errors = get_recent_errors(limit=20)
        
        # Determine system health status
        overall_status = "healthy"
        health_issues = []
        warnings = []
        
        # Analyze 1-hour error rates
        if isinstance(error_rates_1h, dict) and 'error_rate_percent' in error_rates_1h:
            if error_rates_1h['error_rate_percent'] > 15:
                overall_status = "critical"
                health_issues.append(f"Critical error rate (1h): {error_rates_1h['error_rate_percent']}%")
            elif error_rates_1h['error_rate_percent'] > 10:
                if overall_status in ["healthy", "warning"]:
                    overall_status = "degraded"
                health_issues.append(f"High error rate (1h): {error_rates_1h['error_rate_percent']}%")
            elif error_rates_1h['error_rate_percent'] > 5:
                if overall_status == "healthy":
                    overall_status = "warning"
                warnings.append(f"Elevated error rate (1h): {error_rates_1h['error_rate_percent']}%")
        
        # Analyze response times
        if isinstance(error_rates_1h, dict) and 'avg_response_time_ms' in error_rates_1h:
            if error_rates_1h['avg_response_time_ms'] > 5000:
                overall_status = "critical"
                health_issues.append(f"Critical response time (1h): {error_rates_1h['avg_response_time_ms']}ms")
            elif error_rates_1h['avg_response_time_ms'] > 2000:
                if overall_status in ["healthy", "warning"]:
                    overall_status = "degraded"
                health_issues.append(f"Slow response time (1h): {error_rates_1h['avg_response_time_ms']}ms")
            elif error_rates_1h['avg_response_time_ms'] > 1000:
                if overall_status == "healthy":
                    overall_status = "warning"
                warnings.append(f"Elevated response time (1h): {error_rates_1h['avg_response_time_ms']}ms")
        
        # Check for server errors
        if isinstance(error_rates_1h, dict) and 'server_error_count' in error_rates_1h:
            if error_rates_1h['server_error_count'] > 10:
                overall_status = "critical"
                health_issues.append(f"High server error count (1h): {error_rates_1h['server_error_count']}")
            elif error_rates_1h['server_error_count'] > 5:
                if overall_status in ["healthy", "warning"]:
                    overall_status = "degraded"
                health_issues.append(f"Elevated server error count (1h): {error_rates_1h['server_error_count']}")
        
        log_operation_success("detailed health check", f"system status is {overall_status}")
        
        response = {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "system_health": {
                "overall_status": overall_status,
                "health_issues": health_issues,
                "warnings": warnings
            },
            "metrics": {
                "error_rates": {
                    "last_1_hour": error_rates_1h,
                    "last_6_hours": error_rates_6h,
                    "last_24_hours": error_rates_24h
                },
                "endpoint_performance": endpoint_stats,
                "recent_errors": recent_errors
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in detailed health check: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                status_code=500,
                message=f"Failed to perform detailed health check: {str(e)}",
                error_code=ErrorCodes.SERVER_ERROR
            )
        )

@router.get("/monitoring/metrics")
async def get_api_metrics():
    """
    Get comprehensive API metrics and performance data
    """
    log_operation_start("API metrics retrieval")
    
    try:
        # Get metrics for different time periods
        metrics_1h = get_api_error_rates(hours=1)
        metrics_6h = get_api_error_rates(hours=6)
        metrics_24h = get_api_error_rates(hours=24)
        
        # Get endpoint-specific performance
        endpoint_performance = get_endpoint_performance_stats()
        
        log_operation_success("API metrics retrieval", "metrics collected successfully")
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "overview": {
                    "last_1_hour": metrics_1h,
                    "last_6_hours": metrics_6h,
                    "last_24_hours": metrics_24h
                },
                "endpoints": endpoint_performance
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving API metrics: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                status_code=500,
                message=f"Failed to retrieve API metrics: {str(e)}",
                error_code=ErrorCodes.SERVER_ERROR
            )
        )

@router.get("/monitoring/errors")
async def get_error_details(limit: int = 50):
    """
    Get detailed error information
    """
    log_operation_start("error details retrieval", limit=limit)
    
    try:
        # Validate limit
        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=400,
                detail=create_error_response(
                    status_code=400,
                    message="Limit must be between 1 and 1000",
                    error_code=ErrorCodes.VALIDATION_ERROR
                )
            )
        
        # Get recent errors
        error_data = get_recent_errors(limit=limit)
        
        log_operation_success("error details retrieval", f"retrieved {len(error_data.get('recent_errors', []))} error records")
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "error_details": error_data,
            "summary": {
                "total_errors_returned": len(error_data.get('recent_errors', [])),
                "limit_applied": limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving error details: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                status_code=500,
                message=f"Failed to retrieve error details: {str(e)}",
                error_code=ErrorCodes.SERVER_ERROR
            )
        )

@router.post("/monitoring/cleanup-logs")
async def cleanup_api_logs(days_to_keep: int = 30):
    """
    Clean up old API request logs
    """
    log_operation_start("log cleanup", days_to_keep=days_to_keep)
    
    try:
        # Validate days_to_keep
        if days_to_keep < 1 or days_to_keep > 365:
            raise HTTPException(
                status_code=400,
                detail=create_error_response(
                    status_code=400,
                    message="Days to keep must be between 1 and 365",
                    error_code=ErrorCodes.VALIDATION_ERROR
                )
            )
        
        # Perform cleanup
        deleted_count = cleanup_old_logs(days_to_keep)
        
        log_operation_success("log cleanup", f"deleted {deleted_count} old log entries")
        
        return {
            "status": "success",
            "message": f"Log cleanup completed successfully",
            "deleted_records": deleted_count,
            "retention_days": days_to_keep,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during log cleanup: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                status_code=500,
                message=f"Failed to cleanup logs: {str(e)}",
                error_code=ErrorCodes.SERVER_ERROR
            )
        )

@router.get("/monitoring/system-status")
async def get_system_status():
    """
    Get simplified system status for dashboard display
    """
    log_operation_start("system status check")
    
    try:
        # Get recent metrics
        recent_metrics = get_api_error_rates(hours=1)
        
        # Determine status
        if isinstance(recent_metrics, dict) and 'error_rate_percent' in recent_metrics:
            error_rate = recent_metrics['error_rate_percent']
            avg_response_time = recent_metrics.get('avg_response_time_ms', 0)
            
            if error_rate > 10 or avg_response_time > 2000:
                status = "critical"
                status_message = "System experiencing issues"
            elif error_rate > 5 or avg_response_time > 1000:
                status = "warning"
                status_message = "System performance degraded"
            else:
                status = "healthy"
                status_message = "All systems operational"
        else:
            status = "healthy"
            status_message = "All systems operational"
        
        log_operation_success("system status check", f"status is {status}")
        
        return {
            "status": status,
            "message": status_message,
            "timestamp": datetime.now().isoformat(),
            "metrics_summary": {
                "error_rate_percent": recent_metrics.get('error_rate_percent', 0) if isinstance(recent_metrics, dict) else 0,
                "avg_response_time_ms": recent_metrics.get('avg_response_time_ms', 0) if isinstance(recent_metrics, dict) else 0,
                "total_requests_1h": recent_metrics.get('total_requests', 0) if isinstance(recent_metrics, dict) else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response(
                status_code=500,
                message=f"Failed to get system status: {str(e)}",
                error_code=ErrorCodes.SERVER_ERROR
            )
        )
