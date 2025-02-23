from typing import Dict, Any, Optional, List
from src.core.base_agent import BaseAgent, Message
from datetime import datetime
import logging
import json
from pathlib import Path

class ScenePlanner(BaseAgent):
    """Agent responsible for breaking down plot into detailed scene descriptions."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        
        # Scene planning templates
        self.scene_templates = {
            "narrative": {
                "elements": ["setting", "characters", "action", "dialogue", "mood"],
                "transitions": ["cut", "fade", "dissolve", "match_cut"]
            },
            "educational": {
                "elements": ["concept", "visualization", "explanation", "example"],
                "transitions": ["slide", "zoom", "overlay", "split_screen"]
            },
            "promotional": {
                "elements": ["hook", "product", "benefit", "call_to_action"],
                "transitions": ["swipe", "morph", "reveal", "emphasize"]
            }
        }
        
        # Active scene plans
        self.active_scenes: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        if message.message_type == "plan_scenes":
            return await self._plan_scenes(message)
        elif message.message_type == "refine_scene":
            return await self._refine_scene(message)
        elif message.message_type == "get_scene_details":
            return await self._get_scene_details(message)
        return None
    
    async def _plan_scenes(self, message: Message) -> Message:
        """Create detailed scene plans from plot structure."""
        project_id = message.context.get("project_id")
        plot_structure = message.content.get("plot_structure", {})
        
        try:
            # Generate scene plans
            scene_plans = await self._create_scene_plans(plot_structure)
            
            # Store scene plans
            self.active_scenes[project_id] = {
                "scenes": scene_plans,
                "status": "planned",
                "timestamp": datetime.now().isoformat()
            }
            
            return Message(
                message_id=f"scenes_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="scenes_planned",
                content={"scene_plans": scene_plans},
                context={"project_id": project_id}
            )
            
        except Exception as e:
            self.logger.error(f"Scene planning failed: {str(e)}")
            raise
    
    async def _create_scene_plans(self, plot_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create detailed scene plans from plot structure."""
        video_type = plot_structure.get("type", "narrative")
        template = self.scene_templates.get(video_type, self.scene_templates["narrative"])
        
        scenes = []
        acts = plot_structure.get("acts", {})
        
        for act_name, act_data in acts.items():
            act_scenes = await self._break_down_act(
                act_name, 
                act_data, 
                template,
                plot_structure.get("narrative_elements", {})
            )
            scenes.extend(act_scenes)
        
        return scenes
    
    async def _break_down_act(self, act_name: str, act_data: Dict[str, Any],
                            template: Dict[str, List[str]], 
                            narrative_elements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break down an act into individual scenes."""
        scenes = []
        key_elements = act_data.get("key_elements", [])
        
        for element in key_elements:
            scene = {
                "scene_id": f"{act_name}_{len(scenes)}",
                "act": act_name,
                "elements": self._create_scene_elements(element, template["elements"]),
                "technical_requirements": self._determine_technical_requirements(element),
                "transitions": {
                    "in": self._select_transition(template["transitions"], "in"),
                    "out": self._select_transition(template["transitions"], "out")
                },
                "narrative_context": {
                    "setting": narrative_elements.get("setting", {}),
                    "mood": self._determine_scene_mood(element, act_name),
                    "purpose": self._determine_scene_purpose(element, act_name)
                }
            }
            scenes.append(scene)
        
        return scenes
    
    def _create_scene_elements(self, key_element: Dict[str, Any],
                             element_types: List[str]) -> Dict[str, Any]:
        """Create detailed elements for a scene."""
        elements = {}
        for element_type in element_types:
            elements[element_type] = self._generate_element_details(
                element_type,
                key_element
            )
        return elements
    
    def _generate_element_details(self, element_type: str,
                                key_element: Dict[str, Any]) -> Dict[str, Any]:
        """Generate details for a specific scene element."""
        if element_type == "setting":
            return {
                "location": key_element.get("location", ""),
                "time": key_element.get("time", ""),
                "atmosphere": key_element.get("atmosphere", "")
            }
        elif element_type == "action":
            return {
                "description": key_element.get("action_description", ""),
                "duration": key_element.get("duration", ""),
                "intensity": key_element.get("intensity", "medium")
            }
        # Add more element type handlers as needed
        return {}
    
    def _determine_technical_requirements(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Determine technical requirements for a scene."""
        return {
            "camera_movement": self._determine_camera_movement(element),
            "lighting": self._determine_lighting_requirements(element),
            "special_effects": self._identify_special_effects(element),
            "audio_requirements": self._determine_audio_needs(element)
        }
    
    async def _refine_scene(self, message: Message) -> Message:
        """Refine a specific scene based on feedback."""
        project_id = message.context.get("project_id")
        scene_id = message.content.get("scene_id")
        feedback = message.content.get("feedback", {})
        
        try:
            project_scenes = self.active_scenes.get(project_id, {}).get("scenes", [])
            scene_index = next(
                (i for i, s in enumerate(project_scenes) 
                 if s["scene_id"] == scene_id), 
                None
            )
            
            if scene_index is not None:
                refined_scene = await self._apply_scene_refinements(
                    project_scenes[scene_index],
                    feedback
                )
                project_scenes[scene_index] = refined_scene
                
                return Message(
                    message_id=f"ref_scene_{message.message_id}",
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type="scene_refined",
                    content={"refined_scene": refined_scene},
                    context={"project_id": project_id}
                )
                
        except Exception as e:
            self.logger.error(f"Scene refinement failed: {str(e)}")
            raise
    
    async def initialize(self) -> None:
        """Initialize scene planner resources."""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup scene planner resources."""
        pass 