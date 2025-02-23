from typing import Optional, Dict, Any
from src.core.base_agent import BaseAgent, Message
import bpy

class Base3DAgent(BaseAgent):
    """Base class for all 3D production agents."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.scene_context: Dict[str, Any] = {}
        self.render_settings: Dict[str, Any] = {}
    
    async def update_render_settings(self, settings: Dict[str, Any]) -> None:
        """Update the render settings."""
        self.render_settings.update(settings)
        self._apply_render_settings()
    
    def _apply_render_settings(self) -> None:
        """Apply render settings to Blender scene."""
        render = bpy.context.scene.render
        render.engine = self.render_settings.get("engine", "CYCLES")
        render.use_motion_blur = self.render_settings.get("motion_blur", False)
        render.resolution_x = self.render_settings.get("resolution_x", 1920)
        render.resolution_y = self.render_settings.get("resolution_y", 1080) 