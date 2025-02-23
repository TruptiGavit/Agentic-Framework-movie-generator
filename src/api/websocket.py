from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set, Any
import logging
import json
import asyncio
from datetime import datetime

class WebSocketManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        self.logger = logging.getLogger("movie_generator.websocket")
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "projects": set(),
            "system": set()
        }
    
    async def connect(self, websocket: WebSocket, channel: str):
        """Connect websocket to channel."""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
    
    def disconnect(self, websocket: WebSocket, channel: str):
        """Disconnect websocket from channel."""
        self.active_connections[channel].remove(websocket)
    
    async def broadcast(self, channel: str, message: Dict[str, Any]):
        """Broadcast message to all connections in channel."""
        if channel not in self.active_connections:
            return
            
        message_data = {
            "timestamp": datetime.now().isoformat(),
            "channel": channel,
            "data": message
        }
        
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message_data)
            except Exception as e:
                self.logger.error(f"Failed to send message: {str(e)}")
                await self.disconnect(connection, channel)

websocket_manager = WebSocketManager()

# Add these endpoints to main.py: 