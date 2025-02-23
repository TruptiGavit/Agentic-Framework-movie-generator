from typing import Optional, Dict, Any
from src.core.base_agent import BaseAgent, Message

class BaseVisualAgent(BaseAgent):
    """Base class for all visual generation agents."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.visual_settings: Dict[str, Any] = {}
        self.style_guide: Dict[str, Any] = {}
    
    async def update_style_guide(self, style_guide: Dict[str, Any]) -> None:
        """Update the style guide for visual consistency."""
        self.style_guide.update(style_guide)
        await self._apply_style_settings()
    
    async def _apply_style_settings(self) -> None:
        """Apply style settings to visual generation."""
        pass 