from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging
from enum import Enum

class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Event:
    """Represents a system event."""
    event_type: str
    source: str
    data: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = datetime.now()

class EventHandler:
    """Handles system-wide events and coordinates responses."""
    
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.is_running = False
        self.event_queue = asyncio.Queue()
        self.logger = logging.getLogger(__name__)
        
        # Event filtering and routing
        self.event_filters: Dict[str, Callable] = {}
        self.priority_queues: Dict[EventPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in EventPriority
        }
    
    async def start(self):
        """Start the event handler."""
        self.is_running = True
        await self._process_events()
    
    async def stop(self):
        """Stop the event handler."""
        self.is_running = False
        # Clear all queues
        self.event_queue = asyncio.Queue()
        for queue in self.priority_queues.values():
            while not queue.empty():
                await queue.get()
    
    def register_handler(self, event_type: str, handler: Callable,
                        filter_func: Optional[Callable] = None):
        """Register an event handler with optional filter."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        
        if filter_func:
            self.event_filters[event_type] = filter_func
    
    async def emit_event(self, event: Event):
        """Emit an event into the system."""
        # Add to history
        self.event_history.append(event)
        
        # Route to appropriate priority queue
        await self.priority_queues[event.priority].put(event)
        
        # Also add to main queue for processing
        await self.event_queue.put(event)
        
        self.logger.debug(f"Event emitted: {event.event_type} from {event.source}")
    
    async def _process_events(self):
        """Process events from queues."""
        while self.is_running:
            try:
                # Process priority queues first
                for priority in reversed(EventPriority):
                    while not self.priority_queues[priority].empty():
                        event = await self.priority_queues[priority].get()
                        await self._handle_event(event)
                
                # Process main queue
                if not self.event_queue.empty():
                    event = await self.event_queue.get()
                    await self._handle_event(event)
                
                await asyncio.sleep(0.1)  # Prevent CPU overload
                
            except Exception as e:
                self.logger.error(f"Error processing events: {str(e)}")
    
    async def _handle_event(self, event: Event):
        """Handle a single event."""
        if event.event_type in self.handlers:
            # Apply filter if exists
            filter_func = self.event_filters.get(event.event_type)
            if filter_func and not filter_func(event):
                return
            
            # Execute handlers
            for handler in self.handlers[event.event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    self.logger.error(
                        f"Error in event handler for {event.event_type}: {str(e)}"
                    )
    
    def get_recent_events(self, limit: int = 100) -> List[Event]:
        """Get recent events from history."""
        return self.event_history[-limit:]
    
    def get_events_by_type(self, event_type: str) -> List[Event]:
        """Get events of a specific type."""
        return [e for e in self.event_history if e.event_type == event_type]
    
    def clear_history(self):
        """Clear event history."""
        self.event_history.clear()
    
    async def wait_for_event(self, event_type: str, 
                           timeout: Optional[float] = None) -> Optional[Event]:
        """Wait for a specific event to occur."""
        async def event_waiter():
            while self.is_running:
                if not self.event_queue.empty():
                    event = await self.event_queue.get()
                    if event.event_type == event_type:
                        return event
                await asyncio.sleep(0.1)
        
        try:
            return await asyncio.wait_for(event_waiter(), timeout)
        except asyncio.TimeoutError:
            return None
    
    def add_middleware(self, middleware: Callable):
        """Add middleware for event processing."""
        async def middleware_wrapper(event: Event):
            modified_event = await middleware(event)
            if modified_event:
                await self._handle_event(modified_event)
        
        self.register_handler("*", middleware_wrapper) 