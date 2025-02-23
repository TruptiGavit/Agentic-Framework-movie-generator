from typing import Dict, Any, Optional, List
from src.core.base_agent import BaseAgent, Message
from datetime import datetime
import logging
import json
from pathlib import Path

class MusicComposer(BaseAgent):
    """Agent responsible for generating background music and musical elements."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        
        # Music templates
        self.music_templates = {
            "narrative": {
                "genres": ["orchestral", "ambient", "cinematic", "emotional"],
                "elements": ["theme", "underscore", "stinger", "transition"],
                "moods": ["dramatic", "suspenseful", "uplifting", "melancholic"]
            },
            "educational": {
                "genres": ["light", "inspirational", "electronic", "acoustic"],
                "elements": ["background", "highlight", "transition", "endpoint"],
                "moods": ["engaging", "focused", "upbeat", "calm"]
            },
            "promotional": {
                "genres": ["corporate", "energetic", "inspiring", "modern"],
                "elements": ["intro", "build", "peak", "outro"],
                "moods": ["confident", "exciting", "professional", "dynamic"]
            }
        }
        
        # Active compositions
        self.active_compositions: Dict[str, Dict[str, Any]] = {}
        
        # Output settings
        self.output_dir = Path("outputs/audio/music")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        if message.message_type == "compose_music":
            return await self._compose_music(message)
        elif message.message_type == "adjust_music":
            return await self._adjust_music(message)
        elif message.message_type == "get_composition":
            return await self._get_composition(message)
        return None
    
    async def _compose_music(self, message: Message) -> Message:
        """Compose music for a scene or sequence."""
        project_id = message.context.get("project_id")
        scene_data = message.content.get("scene_data", {})
        requirements = message.content.get("music_requirements", {})
        
        try:
            # Generate music composition
            composition = await self._create_composition(
                scene_data,
                requirements
            )
            
            # Store composition
            if project_id not in self.active_compositions:
                self.active_compositions[project_id] = {
                    "scenes": {},
                    "timestamp": datetime.now().isoformat()
                }
            
            scene_id = scene_data.get("scene_id")
            self.active_compositions[project_id]["scenes"][scene_id] = composition
            
            # Save composition to file
            await self._save_composition(composition, project_id, scene_id)
            
            return Message(
                message_id=f"music_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="music_composed",
                content={"composition": composition},
                context={"project_id": project_id, "scene_id": scene_id}
            )
            
        except Exception as e:
            self.logger.error(f"Music composition failed: {str(e)}")
            raise
    
    async def _create_composition(self, scene_data: Dict[str, Any],
                                requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create a music composition based on scene requirements."""
        video_type = scene_data.get("type", "narrative")
        template = self.music_templates.get(video_type, 
                                         self.music_templates["narrative"])
        
        # Analyze musical needs
        musical_needs = self._analyze_musical_needs(scene_data, requirements)
        
        # Generate composition structure
        composition = {
            "metadata": {
                "scene_id": scene_data.get("scene_id"),
                "genre": self._select_genre(musical_needs, template),
                "mood": self._determine_mood(scene_data, template),
                "duration": self._calculate_duration(scene_data)
            },
            "structure": self._create_music_structure(musical_needs, template),
            "elements": self._generate_musical_elements(musical_needs, template),
            "technical_specs": self._determine_technical_specs(requirements)
        }
        
        return composition
    
    def _analyze_musical_needs(self, scene_data: Dict[str, Any],
                             requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the musical needs of a scene."""
        return {
            "primary_mood": scene_data.get("narrative_context", {}).get("mood"),
            "intensity": self._determine_intensity(scene_data),
            "key_moments": self._identify_key_moments(scene_data),
            "transitions": self._identify_musical_transitions(scene_data),
            "special_requirements": requirements.get("special_requirements", [])
        }
    
    def _create_music_structure(self, musical_needs: Dict[str, Any],
                              template: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create the structure for the music composition."""
        structure = []
        
        for element in template["elements"]:
            if self._should_include_element(element, musical_needs):
                structure.append({
                    "type": element,
                    "timing": self._determine_element_timing(element, musical_needs),
                    "characteristics": self._determine_element_characteristics(
                        element,
                        musical_needs,
                        template
                    )
                })
        
        return structure
    
    async def _adjust_music(self, message: Message) -> Message:
        """Adjust existing music based on feedback."""
        project_id = message.context.get("project_id")
        scene_id = message.context.get("scene_id")
        adjustments = message.content.get("adjustments", {})
        
        try:
            composition = self.active_compositions.get(project_id, {}).get("scenes", {}).get(scene_id)
            if composition:
                adjusted_composition = await self._apply_music_adjustments(
                    composition,
                    adjustments
                )
                
                # Update stored composition
                self.active_compositions[project_id]["scenes"][scene_id] = adjusted_composition
                
                # Save adjusted composition
                await self._save_composition(adjusted_composition, project_id, scene_id)
                
                return Message(
                    message_id=f"adj_music_{message.message_id}",
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type="music_adjusted",
                    content={"adjusted_composition": adjusted_composition},
                    context={"project_id": project_id, "scene_id": scene_id}
                )
                
        except Exception as e:
            self.logger.error(f"Music adjustment failed: {str(e)}")
            raise
    
    async def _save_composition(self, composition: Dict[str, Any],
                              project_id: str, scene_id: str):
        """Save composition to file system."""
        composition_path = self.output_dir / project_id / scene_id
        composition_path.mkdir(parents=True, exist_ok=True)
        
        # Save metadata and structure
        metadata_file = composition_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(composition, f, indent=2) 