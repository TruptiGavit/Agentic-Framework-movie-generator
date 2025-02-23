from typing import Dict, Any, Optional, List
from src.core.base_agent import BaseAgent, Message
from datetime import datetime
import logging
import json
from pathlib import Path

class CharacterDeveloper(BaseAgent):
    """Agent responsible for creating and managing character profiles and development."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        
        # Character templates
        self.character_templates = {
            "narrative": {
                "attributes": [
                    "personality", "background", "goals", "conflicts",
                    "relationships", "arc"
                ],
                "development_stages": [
                    "introduction", "growth", "challenge", "transformation"
                ]
            },
            "educational": {
                "attributes": [
                    "expertise", "teaching_style", "credibility",
                    "communication_style"
                ],
                "development_stages": [
                    "establish_authority", "demonstrate_knowledge",
                    "engage_audience", "reinforce_learning"
                ]
            },
            "promotional": {
                "attributes": [
                    "role", "authenticity", "relatability", "persuasiveness"
                ],
                "development_stages": [
                    "build_trust", "present_problem", "offer_solution",
                    "call_to_action"
                ]
            }
        }
        
        # Active character profiles
        self.active_characters: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        if message.message_type == "create_characters":
            return await self._create_characters(message)
        elif message.message_type == "develop_character":
            return await self._develop_character(message)
        elif message.message_type == "get_character_profile":
            return await self._get_character_profile(message)
        return None
    
    async def _create_characters(self, message: Message) -> Message:
        """Create character profiles based on plot and scene requirements."""
        project_id = message.context.get("project_id")
        plot_structure = message.content.get("plot_structure", {})
        scene_plans = message.content.get("scene_plans", [])
        
        try:
            # Generate character profiles
            character_profiles = await self._generate_character_profiles(
                plot_structure,
                scene_plans
            )
            
            # Store character profiles
            self.active_characters[project_id] = {
                "characters": character_profiles,
                "status": "created",
                "timestamp": datetime.now().isoformat()
            }
            
            return Message(
                message_id=f"chars_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="characters_created",
                content={"character_profiles": character_profiles},
                context={"project_id": project_id}
            )
            
        except Exception as e:
            self.logger.error(f"Character creation failed: {str(e)}")
            raise
    
    async def _generate_character_profiles(self, plot_structure: Dict[str, Any],
                                        scene_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate detailed character profiles."""
        video_type = plot_structure.get("type", "narrative")
        template = self.character_templates.get(video_type, 
                                             self.character_templates["narrative"])
        
        characters = {}
        # Identify required characters from plot and scenes
        required_characters = self._identify_required_characters(plot_structure, scene_plans)
        
        for char_name, char_requirements in required_characters.items():
            characters[char_name] = {
                "profile": self._create_character_profile(char_name, char_requirements, template),
                "development": self._plan_character_development(char_requirements, template),
                "scenes": self._map_character_scenes(char_name, scene_plans)
            }
        
        return characters
    
    def _create_character_profile(self, name: str, requirements: Dict[str, Any],
                                template: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed profile for a character."""
        profile = {
            "name": name,
            "role": requirements.get("role", "supporting"),
            "attributes": {}
        }
        
        # Generate attributes based on template
        for attr in template["attributes"]:
            profile["attributes"][attr] = self._generate_attribute(
                attr,
                requirements,
                template
            )
        
        return profile
    
    def _plan_character_development(self, requirements: Dict[str, Any],
                                  template: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan character development through stages."""
        development = []
        for stage in template["development_stages"]:
            development.append({
                "stage": stage,
                "description": self._generate_stage_description(stage, requirements),
                "objectives": self._generate_stage_objectives(stage, requirements),
                "character_changes": self._determine_character_changes(stage, requirements)
            })
        return development
    
    def _map_character_scenes(self, character_name: str,
                            scene_plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map character appearances and development in scenes."""
        character_scenes = []
        for scene in scene_plans:
            if self._character_in_scene(character_name, scene):
                character_scenes.append({
                    "scene_id": scene["scene_id"],
                    "role": self._determine_scene_role(character_name, scene),
                    "actions": self._extract_character_actions(character_name, scene),
                    "development_points": self._identify_development_points(
                        character_name,
                        scene
                    )
                })
        return character_scenes
    
    async def _develop_character(self, message: Message) -> Message:
        """Develop a character's profile and arc."""
        project_id = message.context.get("project_id")
        character_name = message.content.get("character_name")
        development_data = message.content.get("development_data", {})
        
        try:
            project_characters = self.active_characters.get(project_id, {}).get("characters", {})
            if character_name in project_characters:
                updated_character = await self._apply_character_development(
                    project_characters[character_name],
                    development_data
                )
                project_characters[character_name] = updated_character
                
                return Message(
                    message_id=f"dev_{message.message_id}",
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type="character_developed",
                    content={"updated_character": updated_character},
                    context={"project_id": project_id}
                )
                
        except Exception as e:
            self.logger.error(f"Character development failed: {str(e)}")
            raise
    
    async def _apply_character_development(self, character: Dict[str, Any],
                                        development_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply development changes to a character."""
        # Update character attributes
        for attr, value in development_data.get("attribute_changes", {}).items():
            if attr in character["profile"]["attributes"]:
                character["profile"]["attributes"][attr] = self._merge_attribute_changes(
                    character["profile"]["attributes"][attr],
                    value
                )
        
        # Update development stages
        for stage in character["development"]:
            if stage["stage"] in development_data.get("stage_updates", {}):
                stage.update(development_data["stage_updates"][stage["stage"]])
        
        return character
    
    async def initialize(self) -> None:
        """Initialize character developer resources."""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup character developer resources."""
        pass 