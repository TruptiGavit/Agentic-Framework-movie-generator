from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
import numpy as np
from pathlib import Path
import json
from datetime import datetime

class CameraDesigner(BaseVisualAgent):
    """Agent responsible for designing camera movements and shot composition."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.camera_config = {
            "output_dir": Path("outputs/camera"),
            "shot_types": {
                "wide": {
                    "fov": 90,
                    "distance": "far",
                    "movement": ["pan", "tilt"]
                },
                "medium": {
                    "fov": 60,
                    "distance": "medium",
                    "movement": ["dolly", "track"]
                },
                "close": {
                    "fov": 35,
                    "distance": "near",
                    "movement": ["focus", "zoom"]
                }
            },
            "movement_presets": {
                "pan": {"axis": "horizontal", "speed": "smooth"},
                "tilt": {"axis": "vertical", "speed": "smooth"},
                "dolly": {"axis": "forward", "speed": "medium"},
                "track": {"axis": "lateral", "speed": "medium"},
                "crane": {"axis": "vertical", "speed": "slow"},
                "zoom": {"type": "optical", "speed": "variable"}
            }
        }
        self.active_shots: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "design_shot":
            return await self._design_shot(message)
        elif message.message_type == "update_camera":
            return await self._update_camera(message)
        elif message.message_type == "get_shot_design":
            return await self._get_shot_design(message)
        return None
    
    async def _design_shot(self, message: Message) -> Message:
        """Design camera shot based on scene requirements."""
        shot_data = message.content.get("shot_data", {})
        shot_id = message.content.get("shot_id", "")
        
        try:
            shot_design = await self._process_shot_design(
                shot_data, shot_id
            )
            
            return Message(
                message_id=f"shot_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="shot_designed",
                content={"shot_design": shot_design},
                context=message.context,
                metadata={"shot_id": shot_id}
            )
        except Exception as e:
            return Message(
                message_id=f"shot_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="shot_design_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_shot_design(self, shot_data: Dict[str, Any],
                                 shot_id: str) -> Dict[str, Any]:
        """Process shot design creation."""
        # Determine shot type
        shot_type = self._determine_shot_type(shot_data)
        
        # Calculate camera parameters
        camera_params = self._calculate_camera_parameters(shot_data, shot_type)
        
        # Plan camera movement
        movement_plan = self._plan_camera_movement(shot_data, camera_params)
        
        # Create shot design
        shot_design = {
            "shot_id": shot_id,
            "type": shot_type,
            "camera": camera_params,
            "movement": movement_plan,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        
        # Store active shot
        self.active_shots[shot_id] = {
            "design": shot_design,
            "shot_data": shot_data,
            "status": "created",
            "created_at": datetime.now().isoformat()
        }
        
        return shot_design
    
    def _determine_shot_type(self, shot_data: Dict[str, Any]) -> str:
        """Determine appropriate shot type based on scene requirements."""
        subject_distance = shot_data.get("subject_distance", "medium")
        composition = shot_data.get("composition", {})
        
        if composition.get("emphasis") == "environment":
            return "wide"
        elif composition.get("emphasis") == "detail":
            return "close"
        return "medium"
    
    def _calculate_camera_parameters(self, shot_data: Dict[str, Any],
                                  shot_type: str) -> Dict[str, Any]:
        """Calculate camera parameters for the shot."""
        shot_config = self.camera_config["shot_types"][shot_type]
        
        return {
            "position": self._calculate_camera_position(shot_data, shot_config),
            "rotation": self._calculate_camera_rotation(shot_data),
            "fov": shot_config["fov"],
            "focus_distance": self._calculate_focus_distance(shot_data, shot_config)
        }
    
    def _plan_camera_movement(self, shot_data: Dict[str, Any],
                            camera_params: Dict[str, Any]) -> Dict[str, Any]:
        """Plan camera movement for the shot."""
        movement_type = shot_data.get("movement_type", "static")
        
        if movement_type == "static":
            return {"type": "static"}
        
        preset = self.camera_config["movement_presets"].get(movement_type, {})
        return {
            "type": movement_type,
            "start": camera_params["position"],
            "end": self._calculate_end_position(shot_data, camera_params),
            "duration": shot_data.get("duration", 5.0),
            "settings": preset
        }
    
    async def initialize(self) -> None:
        """Initialize camera designer resources."""
        self.camera_config["output_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup camera designer resources."""
        self.active_shots.clear() 