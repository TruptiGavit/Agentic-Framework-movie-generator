from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
import numpy as np
import cv2
from pathlib import Path
import json
from datetime import datetime

class SpecialEffectsCoordinator(BaseVisualAgent):
    """Agent responsible for coordinating and applying special effects."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.sfx_config = {
            "output_dir": Path("outputs/sfx"),
            "cache_dir": Path("cache/sfx"),
            "effect_types": {
                "explosion": {
                    "particle_count": 1000,
                    "duration": 2.0,
                    "scale": 1.0,
                    "intensity": 0.8
                },
                "magic": {
                    "particle_types": ["sparkle", "glow", "trail"],
                    "color_palette": ["#FFD700", "#FF69B4", "#00FFFF"],
                    "intensity": 0.7
                },
                "weather": {
                    "types": ["rain", "snow", "fog", "lightning"],
                    "density": 0.5,
                    "wind_speed": 1.0
                },
                "energy": {
                    "types": ["beam", "shield", "wave"],
                    "color": "#00FF00",
                    "intensity": 0.6
                }
            }
        }
        self.active_effects: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "create_effect":
            return await self._create_effect(message)
        elif message.message_type == "apply_effect":
            return await self._apply_effect(message)
        elif message.message_type == "composite_effects":
            return await self._composite_effects(message)
        return None
    
    async def _create_effect(self, message: Message) -> Message:
        """Create a new special effect."""
        effect_type = message.content.get("effect_type", "")
        effect_params = message.content.get("parameters", {})
        effect_id = message.content.get("effect_id", "")
        
        try:
            effect_result = await self._generate_effect(
                effect_type, effect_params, effect_id
            )
            
            return Message(
                message_id=f"sfx_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="effect_created",
                content={"effect_result": effect_result},
                context=message.context,
                metadata={"effect_id": effect_id}
            )
        except Exception as e:
            return Message(
                message_id=f"sfx_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="effect_creation_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _generate_effect(self, effect_type: str,
                             params: Dict[str, Any],
                             effect_id: str) -> Dict[str, Any]:
        """Generate special effect elements."""
        if effect_type == "explosion":
            effect_data = await self._generate_explosion_effect(params)
        elif effect_type == "magic":
            effect_data = await self._generate_magic_effect(params)
        elif effect_type == "weather":
            effect_data = await self._generate_weather_effect(params)
        elif effect_type == "energy":
            effect_data = await self._generate_energy_effect(params)
        else:
            raise ValueError(f"Unknown effect type: {effect_type}")
        
        # Store active effect
        self.active_effects[effect_id] = {
            "type": effect_type,
            "parameters": params,
            "data": effect_data,
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "effect_id": effect_id,
            "type": effect_type,
            "data": effect_data,
            "metadata": self._create_effect_metadata(effect_type, params)
        }
    
    async def _generate_explosion_effect(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate explosion effect elements."""
        particle_count = params.get("particle_count", 
                                  self.sfx_config["effect_types"]["explosion"]["particle_count"])
        scale = params.get("scale", 
                          self.sfx_config["effect_types"]["explosion"]["scale"])
        
        # Generate particle system
        particles = self._generate_particle_system(particle_count, scale)
        
        # Generate shockwave
        shockwave = self._generate_shockwave(scale)
        
        # Generate debris
        debris = self._generate_debris(scale)
        
        return {
            "particles": particles,
            "shockwave": shockwave,
            "debris": debris,
            "duration": params.get("duration", 2.0)
        }
    
    async def _generate_magic_effect(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate magic effect elements."""
        effect_type = params.get("magic_type", "sparkle")
        color_palette = params.get("colors", 
                                 self.sfx_config["effect_types"]["magic"]["color_palette"])
        
        # Generate base elements
        elements = self._generate_magic_elements(effect_type, color_palette)
        
        # Generate particles
        particles = self._generate_magic_particles(effect_type, color_palette)
        
        return {
            "elements": elements,
            "particles": particles,
            "color_palette": color_palette,
            "duration": params.get("duration", 1.5)
        }
    
    async def _apply_effect(self, message: Message) -> Message:
        """Apply special effect to content."""
        content = message.content.get("content", {})
        effect_id = message.content.get("effect_id", "")
        
        try:
            if effect_id not in self.active_effects:
                raise ValueError(f"Effect not found: {effect_id}")
            
            effect = self.active_effects[effect_id]
            result = await self._apply_effect_to_content(content, effect)
            
            return Message(
                message_id=f"apply_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="effect_applied",
                content={"result": result},
                context=message.context,
                metadata={"effect_id": effect_id}
            )
        except Exception as e:
            return Message(
                message_id=f"apply_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="effect_application_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _apply_effect_to_content(self, content: Dict[str, Any],
                                     effect: Dict[str, Any]) -> Dict[str, Any]:
        """Apply effect to content."""
        if "image" in content:
            result = await self._apply_to_image(content["image"], effect)
        elif "sequence" in content:
            result = await self._apply_to_sequence(content["sequence"], effect)
        else:
            raise ValueError("No valid content provided")
        
        return {
            "type": effect["type"],
            "result": result,
            "parameters": effect["parameters"]
        }
    
    def _create_effect_metadata(self, effect_type: str,
                              params: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for special effect."""
        return {
            "timestamp": datetime.now().isoformat(),
            "effect_type": effect_type,
            "parameters": params,
            "config": self.sfx_config["effect_types"][effect_type]
        }
    
    async def initialize(self) -> None:
        """Initialize special effects resources."""
        self.sfx_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.sfx_config["cache_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup special effects resources."""
        self.active_effects.clear() 