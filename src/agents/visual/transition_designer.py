from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import cv2
from pathlib import Path
import json
from datetime import datetime

class TransitionDesigner(BaseVisualAgent):
    """Agent responsible for designing and implementing scene transitions."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.transition_config = {
            "output_dir": Path("outputs/transitions"),
            "cache_dir": Path("cache/transitions"),
            "transition_types": {
                "fade": {
                    "duration_range": (0.5, 3.0),
                    "ease_types": ["linear", "ease-in", "ease-out", "ease-in-out"]
                },
                "dissolve": {
                    "blend_modes": ["normal", "overlay", "screen", "multiply"],
                    "smoothness": 0.8
                },
                "wipe": {
                    "directions": ["left", "right", "up", "down", "radial"],
                    "edge_softness": 0.2
                },
                "morph": {
                    "control_points": 16,
                    "smoothness": 0.7,
                    "match_colors": True
                },
                "zoom": {
                    "scale_range": (0.5, 2.0),
                    "blur_strength": 0.3
                }
            }
        }
        self.active_transitions: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "design_transition":
            return await self._design_transition(message)
        elif message.message_type == "apply_transition":
            return await self._apply_transition(message)
        elif message.message_type == "get_transition_frames":
            return await self._get_transition_frames(message)
        return None
    
    async def _design_transition(self, message: Message) -> Message:
        """Design a transition between scenes."""
        scene_data = message.content.get("scene_data", {})
        transition_type = message.content.get("transition_type", "fade")
        transition_id = message.content.get("transition_id", "")
        
        try:
            transition_plan = await self._create_transition_plan(
                scene_data, transition_type, transition_id
            )
            
            return Message(
                message_id=f"trans_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="transition_designed",
                content={"transition_plan": transition_plan},
                context=message.context,
                metadata={"transition_id": transition_id}
            )
        except Exception as e:
            return Message(
                message_id=f"trans_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="transition_design_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _create_transition_plan(self, scene_data: Dict[str, Any],
                                    transition_type: str,
                                    transition_id: str) -> Dict[str, Any]:
        """Create a detailed transition plan."""
        # Extract scene information
        scene_from = scene_data.get("from_scene", {})
        scene_to = scene_data.get("to_scene", {})
        duration = scene_data.get("duration", 1.0)
        
        # Analyze scenes for optimal transition
        analysis = self._analyze_scenes(scene_from, scene_to)
        
        # Generate transition parameters
        params = self._generate_transition_parameters(
            transition_type, analysis, duration
        )
        
        # Create keyframes
        keyframes = self._generate_transition_keyframes(params, duration)
        
        transition_plan = {
            "type": transition_type,
            "parameters": params,
            "keyframes": keyframes,
            "duration": duration,
            "metadata": self._create_transition_metadata(scene_data, transition_type)
        }
        
        # Store active transition
        self.active_transitions[transition_id] = transition_plan
        
        return transition_plan
    
    def _analyze_scenes(self, scene_from: Dict[str, Any],
                       scene_to: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze scenes for transition compatibility."""
        return {
            "color_similarity": self._calculate_color_similarity(scene_from, scene_to),
            "motion_vectors": self._calculate_motion_vectors(scene_from, scene_to),
            "composition_change": self._analyze_composition_change(scene_from, scene_to),
            "focal_points": self._identify_focal_points(scene_from, scene_to)
        }
    
    def _generate_transition_parameters(self, transition_type: str,
                                     analysis: Dict[str, Any],
                                     duration: float) -> Dict[str, Any]:
        """Generate transition parameters based on scene analysis."""
        config = self.transition_config["transition_types"][transition_type]
        
        if transition_type == "fade":
            return self._generate_fade_parameters(config, analysis, duration)
        elif transition_type == "dissolve":
            return self._generate_dissolve_parameters(config, analysis, duration)
        elif transition_type == "wipe":
            return self._generate_wipe_parameters(config, analysis, duration)
        elif transition_type == "morph":
            return self._generate_morph_parameters(config, analysis, duration)
        elif transition_type == "zoom":
            return self._generate_zoom_parameters(config, analysis, duration)
        
        raise ValueError(f"Unsupported transition type: {transition_type}")
    
    def _generate_transition_keyframes(self, params: Dict[str, Any],
                                     duration: float) -> List[Dict[str, Any]]:
        """Generate keyframes for the transition."""
        keyframes = []
        frame_count = int(duration * 30)  # Assuming 30 fps
        
        for i in range(frame_count):
            progress = i / (frame_count - 1)
            keyframes.append({
                "time": progress * duration,
                "progress": progress,
                "parameters": self._interpolate_parameters(params, progress)
            })
        
        return keyframes
    
    def _interpolate_parameters(self, params: Dict[str, Any],
                              progress: float) -> Dict[str, Any]:
        """Interpolate parameters for a specific keyframe."""
        interpolated = {}
        for key, value in params.items():
            if isinstance(value, (int, float)):
                interpolated[key] = self._ease_value(value, progress)
            elif isinstance(value, (list, tuple)) and len(value) == 2:
                start, end = value
                interpolated[key] = self._ease_value(start + (end - start) * progress, progress)
            else:
                interpolated[key] = value
        return interpolated
    
    def _ease_value(self, value: float, progress: float,
                    ease_type: str = "ease-in-out") -> float:
        """Apply easing function to a value."""
        if ease_type == "linear":
            return value
        elif ease_type == "ease-in":
            return value * (progress ** 2)
        elif ease_type == "ease-out":
            return value * (1 - (1 - progress) ** 2)
        elif ease_type == "ease-in-out":
            if progress < 0.5:
                return value * (2 * progress ** 2)
            else:
                return value * (1 - (-2 * progress + 2) ** 2 / 2)
        return value
    
    def _create_transition_metadata(self, scene_data: Dict[str, Any],
                                  transition_type: str) -> Dict[str, Any]:
        """Create metadata for transition."""
        return {
            "timestamp": datetime.now().isoformat(),
            "scene_from_id": scene_data.get("from_scene", {}).get("id"),
            "scene_to_id": scene_data.get("to_scene", {}).get("id"),
            "transition_type": transition_type,
            "config": self.transition_config["transition_types"][transition_type]
        }
    
    async def initialize(self) -> None:
        """Initialize transition designer resources."""
        self.transition_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.transition_config["cache_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup transition designer resources."""
        self.active_transitions.clear() 