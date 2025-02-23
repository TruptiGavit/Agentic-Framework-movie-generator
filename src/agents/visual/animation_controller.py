from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from pathlib import Path
import json
from datetime import datetime

class AnimationController(BaseVisualAgent):
    """Agent responsible for managing animation sequences and transitions."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.animation_config = {
            "output_dir": Path("outputs/animation"),
            "animation_types": {
                "character": {
                    "movement": ["walk", "run", "idle", "gesture"],
                    "expression": ["neutral", "happy", "sad", "angry"],
                    "transition": ["smooth", "quick", "delayed"]
                },
                "camera": {
                    "movement": ["pan", "tilt", "dolly", "zoom"],
                    "transition": ["cut", "fade", "dissolve"],
                    "speed": ["slow", "normal", "fast"]
                },
                "scene": {
                    "lighting": ["static", "dynamic", "transitional"],
                    "effects": ["particle", "atmospheric", "environmental"],
                    "timing": ["linear", "eased", "custom"]
                }
            },
            "keyframe_settings": {
                "interpolation": ["linear", "bezier", "step"],
                "spacing": ["uniform", "dynamic", "custom"],
                "timing": ["frames", "seconds", "percentage"]
            }
        }
        self.active_animations: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "create_animation":
            return await self._create_animation(message)
        elif message.message_type == "update_animation":
            return await self._update_animation(message)
        elif message.message_type == "get_animation_state":
            return await self._get_animation_state(message)
        return None
    
    async def _create_animation(self, message: Message) -> Message:
        """Create new animation sequence."""
        sequence_data = message.content.get("sequence_data", {})
        animation_id = message.content.get("animation_id", "")
        
        try:
            animation = await self._process_animation_creation(
                sequence_data, animation_id
            )
            
            return Message(
                message_id=f"anim_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="animation_created",
                content={"animation": animation},
                context=message.context,
                metadata={"animation_id": animation_id}
            )
        except Exception as e:
            return Message(
                message_id=f"anim_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="animation_creation_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_animation_creation(self, sequence_data: Dict[str, Any],
                                        animation_id: str) -> Dict[str, Any]:
        """Process animation sequence creation."""
        # Generate keyframes
        keyframes = self._generate_keyframes(sequence_data)
        
        # Create animation timeline
        timeline = self._create_animation_timeline(sequence_data, keyframes)
        
        # Set up transitions
        transitions = self._setup_transitions(sequence_data, timeline)
        
        # Create animation sequence
        animation = {
            "id": animation_id,
            "keyframes": keyframes,
            "timeline": timeline,
            "transitions": transitions,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "settings": self._get_animation_settings(sequence_data)
            }
        }
        
        # Store active animation
        self.active_animations[animation_id] = {
            "data": animation,
            "sequence_data": sequence_data,
            "status": "created",
            "created_at": datetime.now().isoformat()
        }
        
        return animation
    
    def _generate_keyframes(self, sequence_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate keyframes for animation sequence."""
        keyframes = []
        
        for element_type, animations in sequence_data.get("elements", {}).items():
            for anim in animations:
                keyframes.extend(self._create_element_keyframes(
                    element_type, anim
                ))
        
        # Sort keyframes by time
        keyframes.sort(key=lambda k: k.get("time", 0))
        
        return keyframes
    
    def _create_element_keyframes(self, element_type: str,
                                animation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create keyframes for a specific element."""
        keyframes = []
        
        # Get animation type settings
        anim_type_settings = self.animation_config["animation_types"].get(
            element_type, {}
        )
        
        # Create keyframes based on animation type
        if element_type == "character":
            keyframes = self._create_character_keyframes(
                animation_data, anim_type_settings
            )
        elif element_type == "camera":
            keyframes = self._create_camera_keyframes(
                animation_data, anim_type_settings
            )
        elif element_type == "scene":
            keyframes = self._create_scene_keyframes(
                animation_data, anim_type_settings
            )
        
        return keyframes
    
    def _create_animation_timeline(self, sequence_data: Dict[str, Any],
                                 keyframes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create animation timeline with proper timing and synchronization."""
        return {
            "start_time": 0,
            "end_time": sequence_data.get("duration", 0),
            "keyframe_times": [k["time"] for k in keyframes],
            "segments": self._create_timeline_segments(keyframes)
        }
    
    def _setup_transitions(self, sequence_data: Dict[str, Any],
                         timeline: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Set up transitions between keyframes."""
        transitions = []
        
        for i in range(len(timeline["keyframe_times"]) - 1):
            transitions.append({
                "from_time": timeline["keyframe_times"][i],
                "to_time": timeline["keyframe_times"][i + 1],
                "type": sequence_data.get("transition_type", "smooth"),
                "easing": sequence_data.get("easing", "linear")
            })
        
        return transitions
    
    async def initialize(self) -> None:
        """Initialize animation controller resources."""
        self.animation_config["output_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup animation controller resources."""
        self.active_animations.clear() 