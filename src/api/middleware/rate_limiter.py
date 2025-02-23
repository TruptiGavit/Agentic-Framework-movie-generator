from fastapi import Request, HTTPException
from typing import Dict, Tuple, Optional
import time
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict

@dataclass
class RateLimit:
    """Rate limit configuration."""
    requests: int
    window: int  # seconds
    description: str

@dataclass
class RateLimitState:
    """Rate limit state tracking."""
    count: int = 0
    window_start: float = 0.0

class RateLimiter:
    """Rate limiting middleware."""
    
    def __init__(self):
        self.logger = logging.getLogger("movie_generator.rate_limiter")
        
        # Rate limit configurations
        self.limits = {
            "default": RateLimit(100, 60, "100 requests per minute"),
            "free_tier": RateLimit(1000, 86400, "1000 requests per day"),
            "premium_tier": RateLimit(10000, 86400, "10000 requests per day"),
            "api": RateLimit(1000000, 86400, "1M requests per day")
        }
        
        # State storage
        self._state: Dict[str, Dict[str, RateLimitState]] = defaultdict(dict)
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_expired_states())
    
    async def check_rate_limit(self, request: Request) -> None:
        """Check if request exceeds rate limit."""
        try:
            # Get client identifier
            client_id = self._get_client_id(request)
            tier = await self._get_client_tier(request)
            
            # Get applicable limits
            limits = self._get_applicable_limits(tier)
            
            # Check each limit
            for limit_key, limit in limits.items():
                state = await self._check_limit(client_id, limit_key, limit)
                
                # Add rate limit headers
                self._add_rate_limit_headers(request, state, limit)
                
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Rate limit check failed: {str(e)}")
            # Allow request to proceed on error
    
    async def _check_limit(self, 
                          client_id: str, 
                          limit_key: str, 
                          limit: RateLimit) -> RateLimitState:
        """Check specific rate limit."""
        now = time.time()
        state = self._state[client_id].get(limit_key)
        
        # Initialize or reset window if needed
        if not state or (now - state.window_start) > limit.window:
            state = RateLimitState(count=0, window_start=now)
            self._state[client_id][limit_key] = state
        
        # Check limit
        if state.count >= limit.requests:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": limit.description,
                    "reset": int(state.window_start + limit.window - now)
                }
            )
        
        # Update count
        state.count += 1
        return state
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_{api_key}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip_{forwarded.split(',')[0]}"
        return f"ip_{request.client.host}"
    
    async def _get_client_tier(self, request: Request) -> str:
        """Get client tier from request."""
        # Check API key tier
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # In practice, look up API key tier in database
            return "api"
        
        # Check authenticated user tier
        user = request.state.user if hasattr(request.state, "user") else None
        if user and hasattr(user, "tier"):
            return user.tier
        
        return "free_tier"
    
    def _get_applicable_limits(self, tier: str) -> Dict[str, RateLimit]:
        """Get rate limits applicable to tier."""
        limits = {"default": self.limits["default"]}
        if tier in self.limits:
            limits[tier] = self.limits[tier]
        return limits
    
    def _add_rate_limit_headers(self, 
                               request: Request, 
                               state: RateLimitState, 
                               limit: RateLimit):
        """Add rate limit headers to response."""
        reset_time = int(state.window_start + limit.window)
        remaining = max(0, limit.requests - state.count)
        
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(limit.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time)
        }
    
    async def _cleanup_expired_states(self):
        """Periodically cleanup expired rate limit states."""
        while True:
            try:
                now = time.time()
                for client_id in list(self._state.keys()):
                    for limit_key in list(self._state[client_id].keys()):
                        state = self._state[client_id][limit_key]
                        limit = self.limits.get(limit_key, self.limits["default"])
                        if now - state.window_start > limit.window:
                            del self._state[client_id][limit_key]
                    if not self._state[client_id]:
                        del self._state[client_id]
                        
                await asyncio.sleep(60)  # Cleanup every minute
                
            except Exception as e:
                self.logger.error(f"Rate limit cleanup failed: {str(e)}")
                await asyncio.sleep(60) 