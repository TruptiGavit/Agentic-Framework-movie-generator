from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, Type
import logging
import traceback
from datetime import datetime
from pydantic import BaseModel

class ErrorDetail(BaseModel):
    """Standardized error response model."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str
    request_id: Optional[str] = None
    path: str

class ErrorManager:
    """Centralized error management system."""
    
    def __init__(self):
        self.logger = logging.getLogger("movie_generator.errors")
        
        # Error code mappings
        self.error_codes = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            413: "REQUEST_TOO_LARGE",
            415: "UNSUPPORTED_MEDIA_TYPE",
            429: "RATE_LIMIT_EXCEEDED",
            500: "INTERNAL_ERROR",
            503: "SERVICE_UNAVAILABLE"
        }
        
        # Custom error mappings
        self.custom_errors = {
            "VALIDATION_ERROR": 400,
            "RESOURCE_NOT_FOUND": 404,
            "RESOURCE_EXISTS": 409,
            "PROCESSING_ERROR": 500,
            "AGENT_ERROR": 500,
            "CONFIG_ERROR": 500
        }
    
    async def handle_error(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle and format error response."""
        try:
            error_detail = await self._create_error_detail(request, exc)
            
            # Log error
            self._log_error(error_detail, exc)
            
            # Get status code
            status_code = self._get_status_code(exc)
            
            return JSONResponse(
                status_code=status_code,
                content=error_detail.dict()
            )
            
        except Exception as e:
            # Fallback error handling
            self.logger.error(f"Error in error handler: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    async def _create_error_detail(self, request: Request, exc: Exception) -> ErrorDetail:
        """Create standardized error detail."""
        status_code = self._get_status_code(exc)
        error_code = self._get_error_code(exc)
        
        return ErrorDetail(
            code=error_code,
            message=self._get_error_message(exc),
            details=self._get_error_details(exc),
            timestamp=datetime.now().isoformat(),
            request_id=request.state.request_id if hasattr(request.state, "request_id") else None,
            path=str(request.url.path)
        )
    
    def _get_status_code(self, exc: Exception) -> int:
        """Get HTTP status code for exception."""
        if isinstance(exc, HTTPException):
            return exc.status_code
        
        if hasattr(exc, "error_code") and exc.error_code in self.custom_errors:
            return self.custom_errors[exc.error_code]
        
        return 500
    
    def _get_error_code(self, exc: Exception) -> str:
        """Get error code for exception."""
        if hasattr(exc, "error_code"):
            return exc.error_code
        
        status_code = self._get_status_code(exc)
        return self.error_codes.get(status_code, "INTERNAL_ERROR")
    
    def _get_error_message(self, exc: Exception) -> str:
        """Get user-friendly error message."""
        if isinstance(exc, HTTPException):
            return exc.detail
        
        return str(exc)
    
    def _get_error_details(self, exc: Exception) -> Optional[Dict[str, Any]]:
        """Get additional error details."""
        details = {}
        
        if hasattr(exc, "details"):
            details.update(exc.details)
        
        if isinstance(exc, HTTPException) and exc.headers:
            details["headers"] = exc.headers
        
        return details if details else None
    
    def _log_error(self, error_detail: ErrorDetail, exc: Exception):
        """Log error with appropriate severity."""
        log_message = (
            f"Error: {error_detail.code}\n"
            f"Path: {error_detail.path}\n"
            f"Message: {error_detail.message}\n"
            f"Details: {error_detail.details}\n"
            f"Stack trace:\n{traceback.format_exc()}"
        )
        
        if error_detail.code in ["INTERNAL_ERROR", "PROCESSING_ERROR", "AGENT_ERROR"]:
            self.logger.error(log_message)
        else:
            self.logger.warning(log_message)

# Custom exceptions
class MovieGeneratorError(Exception):
    """Base exception for movie generator errors."""
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

class ValidationError(MovieGeneratorError):
    """Validation error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)

class ResourceNotFoundError(MovieGeneratorError):
    """Resource not found error."""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            f"{resource_type} not found: {resource_id}",
            "RESOURCE_NOT_FOUND",
            {"resource_type": resource_type, "resource_id": resource_id}
        )

class ProcessingError(MovieGeneratorError):
    """Processing error."""
    def __init__(self, message: str, stage: str, details: Optional[Dict[str, Any]] = None):
        error_details = {"stage": stage}
        if details:
            error_details.update(details)
        super().__init__(message, "PROCESSING_ERROR", error_details) 