from typing import Optional, Dict, Any
from src.core.base_agent import BaseAgent, Message

class BaseAudioAgent(BaseAgent):
    """Base class for all audio generation agents."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.audio_context: Dict[str, Any] = {}
        self.audio_settings: Dict[str, Any] = {}
    
    async def update_audio_settings(self, settings: Dict[str, Any]) -> None:
        """Update the audio generation settings."""
        self.audio_settings.update(settings) 