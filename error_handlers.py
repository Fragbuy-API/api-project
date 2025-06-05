"""
Standardized error handling utilities for Qboid API
"""
from fastapi import HTTPException
from datetime import datetime
import logging
import traceback

# Setup logging
logger = logging.getLogger(__name__)

# Standard error codes
class ErrorCodes:
    # General errors
    SERVER_ERROR = "SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    
    # Authentication errors (for future implementation)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"
    
    # Resource not found errors
    BARCODE_NOT_FOUND = "BARCODE_NOT_FOUND"
    SKU_NOT_FOUND = "SKU_NOT_FOUND"
    PO_NOT_FOUND = "PO_NOT_FOUND"
    RO_NOT_FOUND = "RO_NOT_FOUND"
    ITEM_NOT_FOUND = "ITEM_NOT_FOUND"
    
    # Business logic errors
    DUPLICATE_BARCODE = "DUPLICATE_BARCODE"
    DUPLICATE_TOTE = "DUPLICATE_TOTE"
    DUPLICATE_LOCATION = "DUPLICATE_LOCATION"
    INVALID_SKU = "INVALID_SKU"
    INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"
    QUANTITY_EXCEEDED = "QUANTITY_EXCEEDED"
    ORDER_ALREADY_COMPLETED = "ORDER_ALREADY_COMPLETED"
    INVALID_STATUS_FOR_CANCEL = "INVALID_STATUS_FOR_CANCEL"
    ITEM_INSERT_FAILED = "ITEM_INSERT_FAILED"

def create_error_response(
    status_code: int,
    message: str,
    error_code: str = None,
    details: dict = None
) -> dict:
    """
    Create a standardized error response structure
    
    Args:
        status_code: HTTP status code
        message: Human-readable error message
        error_code: Machine-readable error code
        details: Additional error details
    
    Returns:
        Dictionary with standardized error structure
    """
    error_response = {
        "status": "error",
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if error_code:
        error_response["error_code"] = error_code
    
    if details:
        error_response["details"] = details
    
    return error_response

def handle_database_error(e: Exception, operation: str = "database operation") -> HTTPException:
    """
    Handle database-related errors with standardized response
    
    Args:
        e: The exception that occurred
        operation: Description of the operation that failed
    
    Returns:
        HTTPException with standardized error response
    """
    error_msg = f"Database error during {operation}: {str(e)}"
    logger.error(f"{error_msg}\n{traceback.format_exc()}")
    
    return HTTPException(
        status_code=500,
        detail=create_error_response(
            status_code=500,
            message=f"Database error occurred during {operation}",
            error_code=ErrorCodes.DATABASE_ERROR
        )
    )

def handle_server_error(e: Exception, operation: str = "server operation") -> HTTPException:
    """
    Handle general server errors with standardized response
    
    Args:
        e: The exception that occurred
        operation: Description of the operation that failed
    
    Returns:
        HTTPException with standardized error response
    """
    error_msg = f"Server error during {operation}: {str(e)}"
    logger.error(f"{error_msg}\n{traceback.format_exc()}")
    
    return HTTPException(
        status_code=500,
        detail=create_error_response(
            status_code=500,
            message=f"Server error occurred during {operation}",
            error_code=ErrorCodes.SERVER_ERROR
        )
    )

def handle_not_found_error(resource_type: str, identifier: str, error_code: str) -> HTTPException:
    """
    Handle resource not found errors with standardized response
    
    Args:
        resource_type: Type of resource (e.g., "Barcode", "Purchase Order")
        identifier: The identifier that was not found
        error_code: Specific error code for this resource type
    
    Returns:
        HTTPException with standardized error response
    """
    message = f"{resource_type} {identifier} not found in the system"
    logger.warning(f"Resource not found: {message}")
    
    return HTTPException(
        status_code=404,
        detail=create_error_response(
            status_code=404,
            message=message,
            error_code=error_code
        )
    )

def handle_business_logic_error(message: str, error_code: str, status_code: int = 400) -> HTTPException:
    """
    Handle business logic errors with standardized response
    
    Args:
        message: Description of the business logic violation
        error_code: Specific error code for this violation
        status_code: HTTP status code (default: 400)
    
    Returns:
        HTTPException with standardized error response
    """
    logger.warning(f"Business logic error: {message}")
    
    return HTTPException(
        status_code=status_code,
        detail=create_error_response(
            status_code=status_code,
            message=message,
            error_code=error_code
        )
    )

def handle_authentication_error(message: str, error_code: str) -> HTTPException:
    """
    Handle authentication errors with standardized response
    
    Args:
        message: Description of the authentication failure
        error_code: Specific authentication error code
    
    Returns:
        HTTPException with standardized error response
    """
    logger.warning(f"Authentication error: {message}")
    
    return HTTPException(
        status_code=401,
        detail=create_error_response(
            status_code=401,
            message=message,
            error_code=error_code
        )
    )

def handle_authorization_error(message: str = "Access forbidden") -> HTTPException:
    """
    Handle authorization errors with standardized response
    
    Args:
        message: Description of the authorization failure
    
    Returns:
        HTTPException with standardized error response
    """
    logger.warning(f"Authorization error: {message}")
    
    return HTTPException(
        status_code=403,
        detail=create_error_response(
            status_code=403,
            message=message,
            error_code=ErrorCodes.FORBIDDEN
        )
    )

def log_operation_start(operation: str, **kwargs) -> None:
    """
    Log the start of an operation with consistent format
    
    Args:
        operation: Name of the operation starting
        **kwargs: Additional parameters to log
    """
    params_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"Starting {operation}" + (f" with params: {params_str}" if params_str else ""))

def log_operation_success(operation: str, result_summary: str = None) -> None:
    """
    Log successful completion of an operation
    
    Args:
        operation: Name of the operation that completed
        result_summary: Optional summary of the results
    """
    message = f"Successfully completed {operation}"
    if result_summary:
        message += f": {result_summary}"
    logger.info(message)

def log_operation_warning(operation: str, warning_message: str) -> None:
    """
    Log a warning during an operation
    
    Args:
        operation: Name of the operation
        warning_message: Warning message
    """
    logger.warning(f"Warning during {operation}: {warning_message}")
