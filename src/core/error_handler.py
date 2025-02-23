from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import traceback
import logging
import asyncio
from enum import Enum

from src.core.event_handler import EventHandler, Event, EventPriority

class ErrorSeverity(Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class ErrorContext:
    """Context information for an error."""
    component: str
    operation: str
    timestamp: datetime
    details: Dict[str, Any]
    traceback: str

class MovieGenerationError(Exception):
    """Base exception for movie generation errors."""
    pass

class SystemInitializationError(MovieGenerationError):
    """Raised when system initialization fails."""
    pass

class AgentError(MovieGenerationError):
    """Raised when an agent encounters an error."""
    pass

class PipelineError(MovieGenerationError):
    """Raised when a pipeline encounters an error."""
    pass

class ErrorHandler:
    """Handles system-wide error management."""
    
    def __init__(self, event_handler: EventHandler):
        self.event_handler = event_handler
        self.logger = logging.getLogger(__name__)
        
        # Error tracking
        self.active_errors: Dict[str, ErrorContext] = {}
        self.error_history: List[Dict[str, Any]] = []
        
        # Recovery strategies
        self.recovery_strategies: Dict[str, Callable] = {}
        self.retry_policies: Dict[str, Dict[str, Any]] = {
            "default": {
                "max_retries": 3,
                "delay": 1.0,
                "backoff_factor": 2.0
            }
        }
        
        # Error thresholds
        self.error_thresholds = {
            "max_concurrent": 10,
            "max_per_component": 5,
            "max_severity": ErrorSeverity.HIGH
        }
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle system errors and determine recovery action."""
        try:
            error_info = {
                "timestamp": datetime.now().isoformat(),
                "error_type": type(error).__name__,
                "message": str(error),
                "context": context
            }
            
            self.error_history.append(error_info)
            self.logger.error(f"Error occurred: {error_info}")
            
            # Determine recovery strategy
            recovery_action = await self._get_recovery_action(error, context)
            
            if recovery_action:
                self.logger.info(f"Attempting recovery: {recovery_action}")
                return recovery_action
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in error handler: {str(e)}")
            raise
    
    async def _get_recovery_action(self, error: Exception, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Determine appropriate recovery action for an error."""
        if isinstance(error, AgentError):
            return await self._handle_agent_error(error, context)
        elif isinstance(error, PipelineError):
            return await self._handle_pipeline_error(error, context)
        elif isinstance(error, SystemInitializationError):
            return await self._handle_system_error(error, context)
        return None
    
    async def register_recovery_strategy(self, error_type: str, 
                                       strategy: Callable,
                                       retry_policy: Optional[Dict[str, Any]] = None):
        """Register a recovery strategy for an error type."""
        self.recovery_strategies[error_type] = strategy
        if retry_policy:
            self.retry_policies[error_type] = retry_policy
    
    async def _attempt_recovery(self, error_id: str, error: Exception,
                              context: ErrorContext) -> bool:
        """Attempt to recover from an error."""
        error_type = error.__class__.__name__
        
        if error_type in self.recovery_strategies:
            strategy = self.recovery_strategies[error_type]
            policy = self.retry_policies.get(error_type, 
                                          self.retry_policies["default"])
            
            for attempt in range(policy["max_retries"]):
                try:
                    await strategy(error, context)
                    del self.active_errors[error_id]
                    return True
                except Exception as e:
                    delay = policy["delay"] * (policy["backoff_factor"] ** attempt)
                    await asyncio.sleep(delay)
            
        return False
    
    def _check_error_thresholds(self, context: ErrorContext) -> bool:
        """Check if error thresholds have been exceeded."""
        # Check concurrent errors
        if len(self.active_errors) >= self.error_thresholds["max_concurrent"]:
            return False
        
        # Check component errors
        component_errors = sum(
            1 for ctx in self.active_errors.values()
            if ctx.component == context.component
        )
        if component_errors >= self.error_thresholds["max_per_component"]:
            return False
        
        return True
    
    async def _handle_threshold_exceeded(self, context: ErrorContext):
        """Handle case where error thresholds are exceeded."""
        await self._emit_error_event(
            "threshold_exceeded",
            Exception("Error thresholds exceeded"),
            context,
            severity=ErrorSeverity.CRITICAL
        )
    
    async def _emit_error_event(self, error_id: str, error: Exception,
                               context: ErrorContext,
                               severity: ErrorSeverity = ErrorSeverity.HIGH):
        """Emit an error event."""
        event = Event(
            event_type="system_error",
            source="error_handler",
            data={
                "error_id": error_id,
                "error_type": error.__class__.__name__,
                "message": str(error),
                "component": context.component,
                "operation": context.operation,
                "severity": severity.name,
                "timestamp": context.timestamp.isoformat(),
                "details": context.details
            },
            priority=EventPriority.HIGH
        )
        await self.event_handler.emit_event(event)
    
    def _update_error_history(self, error_id: str, error: Exception,
                            context: ErrorContext, recovered: bool):
        """Update error history."""
        self.error_history.append({
            "error_id": error_id,
            "error_type": error.__class__.__name__,
            "message": str(error),
            "component": context.component,
            "operation": context.operation,
            "timestamp": context.timestamp.isoformat(),
            "recovered": recovered,
            "details": context.details,
            "traceback": context.traceback
        })
        
        # Limit history size
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def get_active_errors(self) -> Dict[str, ErrorContext]:
        """Get currently active errors."""
        return self.active_errors.copy()
    
    def get_error_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get error history."""
        return self.error_history[-limit:]
    
    def get_component_errors(self, component: str) -> List[Dict[str, Any]]:
        """Get errors for a specific component."""
        return [
            error for error in self.error_history
            if error["component"] == component
        ] 