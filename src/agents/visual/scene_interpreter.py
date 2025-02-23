from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from pathlib import Path
import json
from datetime import datetime

class SceneInterpreter(BaseVisualAgent):
    """Agent responsible for interpreting scene descriptions into structured visual requirements."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.interpreter_config = {
            "output_dir": Path("outputs/scene_interpreter"),
            "scene_elements": {
                "characters": ["appearance", "expressions", "poses", "clothing"],
                "environment": ["location", "time", "weather", "lighting"],
                "props": ["key_objects", "background_objects", "materials"],
                "composition": ["framing", "perspective", "depth", "focus"],
                "atmosphere": ["mood", "style", "color_palette", "tone"]
            }
        }
        self.active_interpretations: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "interpret_scene":
            return await self._interpret_scene(message)
        elif message.message_type == "update_interpretation":
            return await self._update_interpretation(message)
        return None
    
    async def _interpret_scene(self, message: Message) -> Message:
        """Interpret a scene description."""
        scene_data = message.content.get("scene_data", {})
        scene_id = message.content.get("scene_id", "")
        
        try:
            interpretation = await self._process_scene_interpretation(
                scene_data, scene_id
            )
            
            return Message(
                message_id=f"interp_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="scene_interpreted",
                content={"interpretation": interpretation},
                context=message.context,
                metadata={"scene_id": scene_id}
            )
        except Exception as e:
            return Message(
                message_id=f"interp_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="interpretation_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_scene_interpretation(self, scene_data: Dict[str, Any],
                                          scene_id: str) -> Dict[str, Any]:
        """Process scene interpretation into structured format."""
        interpretation = {}
        
        # Extract scene elements
        for category, elements in self.interpreter_config["scene_elements"].items():
            interpretation[category] = self._extract_scene_elements(
                scene_data, category, elements
            )
        
        # Add scene metadata
        interpretation["metadata"] = {
            "scene_id": scene_id,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        # Store active interpretation
        self.active_interpretations[scene_id] = {
            "data": interpretation,
            "original_scene": scene_data,
            "created_at": datetime.now().isoformat()
        }
        
        return interpretation
    
    def _extract_scene_elements(self, scene_data: Dict[str, Any],
                              category: str,
                              elements: List[str]) -> Dict[str, Any]:
        """Extract specific elements from scene data."""
        extracted = {}
        category_data = scene_data.get(category, {})
        
        for element in elements:
            if element in category_data:
                extracted[element] = category_data[element]
            else:
                # Try to infer from scene description
                extracted[element] = self._infer_element(
                    scene_data.get("description", ""),
                    category,
                    element
                )
        
        return extracted
    
    def _infer_element(self, description: str,
                      category: str,
                      element: str) -> Any:
        """Infer scene element from description if not explicitly provided."""
        # Basic inference logic - should be enhanced with more sophisticated NLP
        if category == "atmosphere" and element == "mood":
            # Example mood inference from description
            mood_keywords = {
                "happy": ["joyful", "cheerful", "bright"],
                "tense": ["anxious", "nervous", "dark"],
                "calm": ["peaceful", "serene", "quiet"]
            }
            for mood, keywords in mood_keywords.items():
                if any(keyword in description.lower() for keyword in keywords):
                    return mood
        return None
    
    async def initialize(self) -> None:
        """Initialize scene interpreter resources."""
        self.interpreter_config["output_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup scene interpreter resources."""
        self.active_interpretations.clear() 