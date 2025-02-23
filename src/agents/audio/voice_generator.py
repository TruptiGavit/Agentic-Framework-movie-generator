from typing import Dict, Any, Optional, List
from src.core.base_agent import BaseAgent, Message
from datetime import datetime
import logging
import json
from pathlib import Path

class VoiceGenerator(BaseAgent):
    """Agent responsible for dialogue-to-speech conversion and voice casting."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        
        # Voice templates
        self.voice_templates = {
            "character_types": {
                "protagonist": {
                    "qualities": ["clear", "engaging", "distinctive"],
                    "ranges": ["natural", "emotive", "dynamic"]
                },
                "supporting": {
                    "qualities": ["balanced", "complementary", "consistent"],
                    "ranges": ["flexible", "adaptable", "controlled"]
                },
                "narrator": {
                    "qualities": ["authoritative", "warm", "professional"],
                    "ranges": ["measured", "articulate", "resonant"]
                }
            },
            "voice_styles": {
                "dramatic": ["intense", "expressive", "powerful"],
                "conversational": ["natural", "relaxed", "authentic"],
                "professional": ["clear", "confident", "polished"]
            },
            "emotional_ranges": {
                "neutral": ["balanced", "controlled", "steady"],
                "emotional": ["expressive", "dynamic", "varied"],
                "intense": ["powerful", "dramatic", "impactful"]
            }
        }
        
        # Active voice profiles
        self.active_voices: Dict[str, Dict[str, Any]] = {}
        
        # Output settings
        self.output_dir = Path("outputs/audio/voice")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        if message.message_type == "generate_voice":
            return await self._generate_voice(message)
        elif message.message_type == "cast_voices":
            return await self._cast_voices(message)
        elif message.message_type == "adjust_voice":
            return await self._adjust_voice(message)
        return None
    
    async def _generate_voice(self, message: Message) -> Message:
        """Generate voice audio for dialogue."""
        project_id = message.context.get("project_id")
        scene_id = message.context.get("scene_id")
        dialogue_data = message.content.get("dialogue", {})
        voice_profiles = message.content.get("voice_profiles", {})
        
        try:
            # Generate voice audio
            voice_audio = await self._create_voice_audio(
                dialogue_data,
                voice_profiles
            )
            
            # Store voice audio
            if project_id not in self.active_voices:
                self.active_voices[project_id] = {
                    "scenes": {},
                    "timestamp": datetime.now().isoformat()
                }
            
            self.active_voices[project_id]["scenes"][scene_id] = voice_audio
            
            # Save voice audio
            await self._save_voice_audio(voice_audio, project_id, scene_id)
            
            return Message(
                message_id=f"voice_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="voice_generated",
                content={"voice_audio": voice_audio},
                context={"project_id": project_id, "scene_id": scene_id}
            )
            
        except Exception as e:
            self.logger.error(f"Voice generation failed: {str(e)}")
            raise
    
    async def _cast_voices(self, message: Message) -> Message:
        """Cast appropriate voices for characters."""
        project_id = message.context.get("project_id")
        characters = message.content.get("characters", {})
        requirements = message.content.get("voice_requirements", {})
        
        try:
            # Generate voice casting
            voice_casting = await self._create_voice_casting(
                characters,
                requirements
            )
            
            # Store voice casting
            if project_id not in self.active_voices:
                self.active_voices[project_id] = {
                    "casting": voice_casting,
                    "timestamp": datetime.now().isoformat()
                }
            
            return Message(
                message_id=f"cast_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="voices_cast",
                content={"voice_casting": voice_casting},
                context={"project_id": project_id}
            )
            
        except Exception as e:
            self.logger.error(f"Voice casting failed: {str(e)}")
            raise
    
    async def _create_voice_casting(self, characters: Dict[str, Any],
                                  requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create voice casting for characters."""
        casting = {}
        
        for char_name, char_data in characters.items():
            # Determine character type and requirements
            char_type = self._determine_character_type(char_data)
            voice_requirements = self._analyze_voice_requirements(
                char_data,
                requirements
            )
            
            # Select voice profile
            casting[char_name] = {
                "voice_profile": self._select_voice_profile(char_type, voice_requirements),
                "voice_style": self._determine_voice_style(char_data),
                "emotional_range": self._determine_emotional_range(char_data),
                "technical_specs": self._determine_voice_specs(requirements)
            }
        
        return casting
    
    async def _create_voice_audio(self, dialogue_data: Dict[str, Any],
                                voice_profiles: Dict[str, Any]) -> Dict[str, Any]:
        """Create voice audio for dialogue."""
        voice_audio = {
            "metadata": {
                "duration": self._calculate_dialogue_duration(dialogue_data),
                "technical_specs": voice_profiles.get("technical_specs", {})
            },
            "segments": []
        }
        
        for dialogue in dialogue_data.get("exchanges", []):
            segment = await self._generate_voice_segment(
                dialogue,
                voice_profiles.get(dialogue["speaker"], {})
            )
            voice_audio["segments"].append(segment)
        
        return voice_audio
    
    async def _generate_voice_segment(self, dialogue: Dict[str, Any],
                                    voice_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a single voice segment."""
        return {
            "speaker": dialogue["speaker"],
            "text": dialogue["line"],
            "audio_data": await self._synthesize_voice(
                dialogue["line"],
                voice_profile,
                dialogue.get("delivery", {})
            ),
            "timing": dialogue.get("timing", {}),
            "metadata": {
                "emotion": dialogue.get("emotion", "neutral"),
                "intensity": dialogue.get("intensity", "medium")
            }
        }
    
    async def _adjust_voice(self, message: Message) -> Message:
        """Adjust voice audio based on feedback."""
        project_id = message.context.get("project_id")
        scene_id = message.context.get("scene_id")
        adjustments = message.content.get("adjustments", {})
        
        try:
            voice_audio = self.active_voices.get(project_id, {}).get("scenes", {}).get(scene_id)
            if voice_audio:
                adjusted_audio = await self._apply_voice_adjustments(
                    voice_audio,
                    adjustments
                )
                
                # Update stored audio
                self.active_voices[project_id]["scenes"][scene_id] = adjusted_audio
                
                # Save adjusted audio
                await self._save_voice_audio(adjusted_audio, project_id, scene_id)
                
                return Message(
                    message_id=f"adj_voice_{message.message_id}",
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type="voice_adjusted",
                    content={"adjusted_audio": adjusted_audio},
                    context={"project_id": project_id, "scene_id": scene_id}
                )
                
        except Exception as e:
            self.logger.error(f"Voice adjustment failed: {str(e)}")
            raise 