from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import asyncio
from datetime import datetime
import logging

@dataclass
class MessageRoute:
    """Defines a message routing path."""
    source: str
    destination: str
    message_type: str
    handler: Callable

class MessageBus:
    """Central message bus for inter-agent communication."""
    
    def __init__(self):
        self.routes: Dict[str, List[MessageRoute]] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.message_queue = asyncio.Queue()
        self.is_running = False
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the message bus."""
        self.is_running = True
        await self._process_messages()
    
    async def stop(self):
        """Stop the message bus."""
        self.is_running = False
        # Clear any remaining messages
        while not self.message_queue.empty():
            await self.message_queue.get()
    
    def register_route(self, route: MessageRoute):
        """Register a new message route."""
        if route.message_type not in self.routes:
            self.routes[route.message_type] = []
        self.routes[route.message_type].append(route)
    
    def subscribe(self, message_type: str, handler: Callable):
        """Subscribe to a message type."""
        if message_type not in self.subscribers:
            self.subscribers[message_type] = []
        self.subscribers[message_type].append(handler)
    
    async def publish(self, message: Any):
        """Publish a message to the bus."""
        await self.message_queue.put(message)
    
    async def _process_messages(self):
        """Process messages from the queue."""
        while self.is_running:
            try:
                message = await self.message_queue.get()
                await self._route_message(message)
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
    
    async def _route_message(self, message: Any):
        """Route a message to its handlers."""
        message_type = message.message_type
        
        # Handle registered routes
        if message_type in self.routes:
            for route in self.routes[message_type]:
                if (route.source == message.sender and 
                    route.destination == message.receiver):
                    try:
                        await route.handler(message)
                    except Exception as e:
                        self.logger.error(f"Error in route handler: {str(e)}")
        
        # Handle subscribers
        if message_type in self.subscribers:
            for handler in self.subscribers[message_type]:
                try:
                    await handler(message)
                except Exception as e:
                    self.logger.error(f"Error in subscriber handler: {str(e)}") 