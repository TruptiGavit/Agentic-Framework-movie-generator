from typing import Dict, Any, Optional, List
from src.core.base_agent import BaseAgent, Message
from datetime import datetime
import logging
import json
from pathlib import Path

class DialogueGenerator(BaseAgent):
    """Agent responsible for generating contextually appropriate dialogue."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        
        # Dialogue templates
        self.dialogue_templates = {
            "narrative": {
                "styles": ["natural", "dramatic", "comedic", "tense"],
                "elements": ["conversation", "monologue", "argument", "revelation"],
                "transitions": ["pause", "interruption", "response", "silence"]
            },
            "educational": {
                "styles": ["instructive", "engaging", "explanatory", "interactive"],
                "elements": ["introduction", "explanation", "example", "summary"],
                "transitions": ["question", "clarification", "emphasis", "review"]
            },
            "promotional": {
                "styles": ["persuasive", "conversational", "testimonial", "enthusiastic"],
                "elements": ["hook", "pitch", "evidence", "call_to_action"],
                "transitions": ["build-up", "emphasis", "connection", "closure"]
            }
        }
        
        # Active dialogue sets
        self.active_dialogues: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        if message.message_type == "generate_dialogue":
            return await self._generate_dialogue(message)
        elif message.message_type == "refine_dialogue":
            return await self._refine_dialogue(message)
        elif message.message_type == "get_scene_dialogue":
            return await self._get_scene_dialogue(message)
        return None
    
    async def _generate_dialogue(self, message: Message) -> Message:
        """Generate dialogue for a scene based on characters and context."""
        project_id = message.context.get("project_id")
        scene_data = message.content.get("scene_data", {})
        characters = message.content.get("characters", {})
        
        try:
            # Generate dialogue for the scene
            dialogue_set = await self._create_dialogue_set(
                scene_data,
                characters
            )
            
            # Store dialogue
            if project_id not in self.active_dialogues:
                self.active_dialogues[project_id] = {
                    "scenes": {},
                    "timestamp": datetime.now().isoformat()
                }
            
            scene_id = scene_data.get("scene_id")
            self.active_dialogues[project_id]["scenes"][scene_id] = dialogue_set
            
            return Message(
                message_id=f"dial_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="dialogue_generated",
                content={"dialogue": dialogue_set},
                context={"project_id": project_id, "scene_id": scene_id}
            )
            
        except Exception as e:
            self.logger.error(f"Dialogue generation failed: {str(e)}")
            raise
    
    async def _create_dialogue_set(self, scene_data: Dict[str, Any],
                                 characters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a complete dialogue set for a scene."""
        video_type = scene_data.get("type", "narrative")
        template = self.dialogue_templates.get(video_type, 
                                            self.dialogue_templates["narrative"])
        
        # Analyze scene requirements
        scene_requirements = self._analyze_scene_requirements(scene_data)
        
        # Generate dialogue structure
        dialogue_structure = self._create_dialogue_structure(
            scene_requirements,
            template
        )
        
        # Generate actual dialogue
        dialogue_set = {
            "metadata": {
                "scene_id": scene_data.get("scene_id"),
                "style": self._determine_dialogue_style(scene_data, template),
                "tone": scene_data.get("narrative_context", {}).get("mood", "neutral")
            },
            "structure": dialogue_structure,
            "exchanges": self._generate_dialogue_exchanges(
                dialogue_structure,
                characters,
                scene_requirements
            )
        }
        
        return dialogue_set
    
    def _create_dialogue_structure(self, scene_requirements: Dict[str, Any],
                                 template: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create the structure for scene dialogue."""
        structure = []
        
        # Break down scene into dialogue segments
        for element in scene_requirements.get("elements", []):
            structure.append({
                "type": self._determine_dialogue_type(element, template),
                "participants": self._identify_participants(element),
                "objectives": self._determine_dialogue_objectives(element),
                "transitions": self._plan_transitions(element, template)
            })
        
        return structure
    
    def _generate_dialogue_exchanges(self, structure: List[Dict[str, Any]],
                                   characters: Dict[str, Any],
                                   requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actual dialogue exchanges."""
        exchanges = []
        
        for segment in structure:
            segment_exchanges = self._create_segment_dialogue(
                segment,
                characters,
                requirements
            )
            exchanges.extend(segment_exchanges)
        
        return exchanges
    
    def _create_segment_dialogue(self, segment: Dict[str, Any],
                               characters: Dict[str, Any],
                               requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create dialogue for a specific segment."""
        exchanges = []
        
        # Generate dialogue based on segment type and participants
        for participant in segment["participants"]:
            character_profile = characters.get(participant, {})
            dialogue_line = self._generate_character_dialogue(
                character_profile,
                segment,
                requirements
            )
            
            exchanges.append({
                "speaker": participant,
                "line": dialogue_line,
                "delivery": self._determine_delivery_style(
                    character_profile,
                    segment
                ),
                "actions": self._generate_accompanying_actions(
                    character_profile,
                    segment
                )
            })
        
        return exchanges
    
    async def _refine_dialogue(self, message: Message) -> Message:
        """Refine existing dialogue based on feedback."""
        project_id = message.context.get("project_id")
        scene_id = message.context.get("scene_id")
        feedback = message.content.get("feedback", {})
        
        try:
            scene_dialogue = self.active_dialogues.get(project_id, {}).get("scenes", {}).get(scene_id)
            if scene_dialogue:
                refined_dialogue = await self._apply_dialogue_refinements(
                    scene_dialogue,
                    feedback
                )
                
                self.active_dialogues[project_id]["scenes"][scene_id] = refined_dialogue
                
                return Message(
                    message_id=f"ref_dial_{message.message_id}",
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type="dialogue_refined",
                    content={"refined_dialogue": refined_dialogue},
                    context={"project_id": project_id, "scene_id": scene_id}
                )
                
        except Exception as e:
            self.logger.error(f"Dialogue refinement failed: {str(e)}")
            raise
    
    async def initialize(self) -> None:
        """Initialize dialogue generator resources."""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup dialogue generator resources."""
        pass 