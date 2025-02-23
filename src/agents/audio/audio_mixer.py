from typing import Dict, Any, Optional, List
from src.core.base_agent import BaseAgent, Message
from datetime import datetime
import logging
import json
from pathlib import Path

class AudioMixer(BaseAgent):
    """Agent responsible for combining all audio elements into final mix."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        
        # Mixing templates
        self.mixing_templates = {
            "narrative": {
                "layers": ["dialogue", "music", "ambience", "effects"],
                "priorities": {
                    "dialogue": 1,
                    "music": 2,
                    "ambience": 3,
                    "effects": 2
                },
                "transitions": ["crossfade", "fade_in", "fade_out", "cut"]
            },
            "educational": {
                "layers": ["narration", "background_music", "effects"],
                "priorities": {
                    "narration": 1,
                    "background_music": 3,
                    "effects": 2
                },
                "transitions": ["smooth", "emphasis", "pause", "bridge"]
            },
            "promotional": {
                "layers": ["voiceover", "music", "effects"],
                "priorities": {
                    "voiceover": 1,
                    "music": 2,
                    "effects": 3
                },
                "transitions": ["impact", "build", "release", "sweep"]
            }
        }
        
        # Active mixes
        self.active_mixes: Dict[str, Dict[str, Any]] = {}
        
        # Output settings
        self.output_dir = Path("outputs/audio/final")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        if message.message_type == "mix_audio":
            return await self._mix_audio(message)
        elif message.message_type == "adjust_mix":
            return await self._adjust_mix(message)
        elif message.message_type == "get_mix":
            return await self._get_mix(message)
        return None
    
    async def _mix_audio(self, message: Message) -> Message:
        """Mix all audio elements for a scene."""
        project_id = message.context.get("project_id")
        scene_id = message.context.get("scene_id")
        audio_elements = message.content.get("audio_elements", {})
        mix_requirements = message.content.get("mix_requirements", {})
        
        try:
            # Create audio mix
            audio_mix = await self._create_audio_mix(
                audio_elements,
                mix_requirements
            )
            
            # Store mix
            if project_id not in self.active_mixes:
                self.active_mixes[project_id] = {
                    "scenes": {},
                    "timestamp": datetime.now().isoformat()
                }
            
            self.active_mixes[project_id]["scenes"][scene_id] = audio_mix
            
            # Save mix
            await self._save_audio_mix(audio_mix, project_id, scene_id)
            
            return Message(
                message_id=f"mix_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="audio_mixed",
                content={"audio_mix": audio_mix},
                context={"project_id": project_id, "scene_id": scene_id}
            )
            
        except Exception as e:
            self.logger.error(f"Audio mixing failed: {str(e)}")
            raise
    
    async def _create_audio_mix(self, audio_elements: Dict[str, Any],
                              requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create final audio mix from elements."""
        # Get appropriate template
        video_type = requirements.get("video_type", "narrative")
        template = self.mixing_templates.get(video_type, 
                                          self.mixing_templates["narrative"])
        
        # Analyze mix requirements
        mix_specs = self._analyze_mix_requirements(audio_elements, requirements)
        
        # Create mix structure
        mix_structure = {
            "metadata": {
                "duration": self._calculate_total_duration(audio_elements),
                "format": requirements.get("format", "stereo"),
                "sample_rate": requirements.get("sample_rate", 48000),
                "bit_depth": requirements.get("bit_depth", 24)
            },
            "layers": self._create_mix_layers(audio_elements, template),
            "automation": self._create_mix_automation(audio_elements, mix_specs),
            "effects": self._create_mix_effects(mix_specs)
        }
        
        # Process audio
        processed_mix = await self._process_audio_mix(mix_structure)
        
        return processed_mix
    
    def _create_mix_layers(self, audio_elements: Dict[str, Any],
                          template: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create layered mix structure."""
        layers = []
        
        for layer_name in template["layers"]:
            if layer_name in audio_elements:
                layers.append({
                    "name": layer_name,
                    "content": audio_elements[layer_name],
                    "priority": template["priorities"][layer_name],
                    "processing": self._determine_layer_processing(layer_name),
                    "routing": self._determine_layer_routing(layer_name)
                })
        
        return sorted(layers, key=lambda x: x["priority"])
    
    def _create_mix_automation(self, audio_elements: Dict[str, Any],
                             mix_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Create mix automation data."""
        automation = {
            "volume": self._create_volume_automation(audio_elements),
            "panning": self._create_panning_automation(audio_elements),
            "effects": self._create_effects_automation(mix_specs)
        }
        
        return automation
    
    async def _process_audio_mix(self, mix_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Process and render final audio mix."""
        processed_mix = {
            "metadata": mix_structure["metadata"],
            "mix_data": await self._render_mix(mix_structure),
            "layer_data": self._extract_layer_data(mix_structure),
            "automation_data": mix_structure["automation"],
            "technical_report": self._generate_mix_report(mix_structure)
        }
        
        return processed_mix
    
    async def _adjust_mix(self, message: Message) -> Message:
        """Adjust existing audio mix."""
        project_id = message.context.get("project_id")
        scene_id = message.context.get("scene_id")
        adjustments = message.content.get("adjustments", {})
        
        try:
            scene_mix = self.active_mixes.get(project_id, {}).get("scenes", {}).get(scene_id)
            if scene_mix:
                adjusted_mix = await self._apply_mix_adjustments(
                    scene_mix,
                    adjustments
                )
                
                # Update stored mix
                self.active_mixes[project_id]["scenes"][scene_id] = adjusted_mix
                
                # Save adjusted mix
                await self._save_audio_mix(adjusted_mix, project_id, scene_id)
                
                return Message(
                    message_id=f"adj_mix_{message.message_id}",
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type="mix_adjusted",
                    content={"adjusted_mix": adjusted_mix},
                    context={"project_id": project_id, "scene_id": scene_id}
                )
                
        except Exception as e:
            self.logger.error(f"Mix adjustment failed: {str(e)}")
            raise 