from src.core.base_agent import BaseAgent, Message
from typing import Optional, Dict, Any

class BaseStoryAgent(BaseAgent):
    """Base class for all story development agents."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.story_context: Dict[str, Any] = {}
    
    async def update_story_context(self, context: Dict[str, Any]) -> None:
        """Update the story context with new information."""
        self.story_context.update(context) 