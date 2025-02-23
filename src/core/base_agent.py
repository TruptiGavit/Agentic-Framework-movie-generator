from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel

class Message(BaseModel):
    message_id: str
    sender: str
    receiver: str
    message_type: str
    content: Dict[str, Any]
    context: Dict[str, Any]
    metadata: Dict[str, Any]

class BaseAgent(ABC):
    """Base class for all agents in the framework."""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.state: Dict[str, Any] = {}
    
    @abstractmethod
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming message and return optional response."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize agent state and resources."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup agent resources."""
        pass 