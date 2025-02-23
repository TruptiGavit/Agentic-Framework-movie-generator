from fastapi import Request, HTTPException
from typing import Dict, Any, Optional
import logging
import json
from pydantic import ValidationError

class RequestValidator:
    """Request validation middleware."""
    
    def __init__(self):
        self.logger = logging.getLogger("movie_generator.validator")
        
        # Request size limits
        self.size_limits = {
            "body": 10 * 1024 * 1024,  # 10MB
            "file": 100 * 1024 * 1024  # 100MB
        }
        
        # Content type restrictions
        self.allowed_content_types = {
            "/projects/": ["application/json"],
            "/upload/": ["multipart/form-data"],
            "/export/": ["application/json"]
        }
    
    async def validate_request(self, request: Request) -> None:
        """Validate incoming request."""
        try:
            # Validate content type
            await self._validate_content_type(request)
            
            # Validate request size
            await self._validate_request_size(request)
            
            # Validate request body
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._validate_request_body(request)
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Request validation failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request: {str(e)}"
            )
    
    async def _validate_content_type(self, request: Request):
        """Validate request content type."""
        content_type = request.headers.get("content-type", "").lower()
        
        # Check path-specific content types
        for path, allowed_types in self.allowed_content_types.items():
            if request.url.path.startswith(path):
                if not any(allowed.lower() in content_type for allowed in allowed_types):
                    raise HTTPException(
                        status_code=415,
                        detail=f"Unsupported media type. Allowed types: {allowed_types}"
                    )
    
    async def _validate_request_size(self, request: Request):
        """Validate request size."""
        content_length = request.headers.get("content-length")
        if content_length:
            size = int(content_length)
            limit = self.size_limits["file"] if "upload" in request.url.path else self.size_limits["body"]
            
            if size > limit:
                raise HTTPException(
                    status_code=413,
                    detail=f"Request too large. Maximum size: {limit/1024/1024}MB"
                )
    
    async def _validate_request_body(self, request: Request):
        """Validate request body structure."""
        try:
            body = await request.json()
            # Additional validation logic here
            
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON in request body"
            ) 