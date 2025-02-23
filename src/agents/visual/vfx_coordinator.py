from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
from pathlib import Path
import torch
import cv2
import asyncio
from datetime import datetime

class VFXCoordinator(BaseVisualAgent):
    """Agent responsible for coordinating and applying visual effects."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.vfx_config = {
            "output_dir": Path("outputs/vfx"),
            "cache_dir": Path("cache/vfx"),
            "effect_types": {
                "particle": {"max_particles": 1000, "lifetime": 2.0},
                "glow": {"radius": 10, "intensity": 0.5},
                "blur": {"radius": 5, "type": "gaussian"},
                "color_grade": {"intensity": 0.7},
                "distortion": {"amount": 0.3},
            }
        }
        self.active_effects: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "apply_effects":
            return await self._apply_effects(message)
        elif message.message_type == "create_effect":
            return await self._create_effect(message)
        elif message.message_type == "modify_effect":
            return await self._modify_effect(message)
        return None
    
    async def _apply_effects(self, message: Message) -> Message:
        """Apply visual effects to images or sequences."""
        content = message.content.get("content", {})
        effects = message.content.get("effects", [])
        sequence_id = message.content.get("sequence_id", "")
        
        try:
            vfx_result = await self._process_effects(content, effects, sequence_id)
            
            return Message(
                message_id=f"vfx_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="effects_applied",
                content={"vfx_result": vfx_result},
                context=message.context,
                metadata={"sequence_id": sequence_id}
            )
        except Exception as e:
            return Message(
                message_id=f"vfx_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="effects_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_effects(self, content: Dict[str, Any],
                             effects: List[Dict[str, Any]],
                             sequence_id: str) -> Dict[str, Any]:
        """Process and apply visual effects."""
        # Load content
        if "image" in content:
            result = await self._apply_effects_to_image(content["image"], effects)
        elif "sequence" in content:
            result = await self._apply_effects_to_sequence(content["sequence"], effects)
        else:
            raise ValueError("No valid content provided")
        
        # Save result
        output_path = await self._save_result(result, sequence_id)
        
        return {
            "status": "success",
            "output_path": str(output_path),
            "applied_effects": effects,
            "metadata": self._create_vfx_metadata(effects)
        }
    
    async def _apply_effects_to_image(self, image: Image.Image,
                                    effects: List[Dict[str, Any]]) -> Image.Image:
        """Apply effects to a single image."""
        result = image.copy()
        
        for effect in effects:
            effect_type = effect["type"]
            params = effect["parameters"]
            
            if effect_type == "particle":
                result = await self._apply_particle_effect(result, params)
            elif effect_type == "glow":
                result = self._apply_glow_effect(result, params)
            elif effect_type == "blur":
                result = self._apply_blur_effect(result, params)
            elif effect_type == "color_grade":
                result = self._apply_color_grading(result, params)
            elif effect_type == "distortion":
                result = self._apply_distortion(result, params)
        
        return result
    
    async def _apply_particle_effect(self, image: Image.Image,
                                   params: Dict[str, Any]) -> Image.Image:
        """Apply particle system effect."""
        # Create particle layer
        particle_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
        
        # Generate particles
        particles = self._generate_particles(params)
        
        # Render particles
        for particle in particles:
            self._render_particle(particle_layer, particle)
        
        # Composite layers
        return Image.alpha_composite(image.convert('RGBA'), particle_layer)
    
    def _apply_glow_effect(self, image: Image.Image,
                          params: Dict[str, Any]) -> Image.Image:
        """Apply glow effect."""
        radius = params.get("radius", self.vfx_config["effect_types"]["glow"]["radius"])
        intensity = params.get("intensity", self.vfx_config["effect_types"]["glow"]["intensity"])
        
        # Create glow layer
        glow = image.filter(ImageFilter.GaussianBlur(radius))
        enhancer = ImageEnhance.Brightness(glow)
        glow = enhancer.enhance(1 + intensity)
        
        # Blend with original
        return Image.blend(image, glow, intensity)
    
    def _apply_blur_effect(self, image: Image.Image,
                          params: Dict[str, Any]) -> Image.Image:
        """Apply blur effect."""
        radius = params.get("radius", self.vfx_config["effect_types"]["blur"]["radius"])
        blur_type = params.get("type", self.vfx_config["effect_types"]["blur"]["type"])
        
        if blur_type == "gaussian":
            return image.filter(ImageFilter.GaussianBlur(radius))
        elif blur_type == "motion":
            return self._apply_motion_blur(image, radius, params.get("angle", 0))
        return image
    
    def _apply_color_grading(self, image: Image.Image,
                            params: Dict[str, Any]) -> Image.Image:
        """Apply color grading effect."""
        intensity = params.get("intensity", 
                             self.vfx_config["effect_types"]["color_grade"]["intensity"])
        
        # Apply color adjustments
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1 + intensity)
        
        # Apply contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1 + intensity * 0.5)
        
        return image
    
    def _generate_particles(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate particle system data."""
        max_particles = params.get("max_particles", 
                                 self.vfx_config["effect_types"]["particle"]["max_particles"])
        
        particles = []
        for _ in range(max_particles):
            particles.append({
                "position": (np.random.rand(2) * 100).tolist(),
                "velocity": (np.random.rand(2) - 0.5).tolist(),
                "size": np.random.rand() * 10,
                "lifetime": np.random.rand() * params.get("lifetime", 2.0),
                "color": [int(x) for x in np.random.rand(4) * 255]
            })
        
        return particles
    
    def _render_particle(self, layer: Image.Image, particle: Dict[str, Any]) -> None:
        """Render a single particle onto the layer."""
        draw = ImageDraw.Draw(layer)
        pos = particle["position"]
        size = particle["size"]
        color = tuple(particle["color"])
        
        draw.ellipse([pos[0] - size, pos[1] - size,
                     pos[0] + size, pos[1] + size],
                    fill=color)
    
    async def _save_result(self, result: Any, sequence_id: str) -> Path:
        """Save VFX result."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.vfx_config["output_dir"] / sequence_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if isinstance(result, Image.Image):
            output_path = output_dir / f"vfx_{timestamp}.png"
            result.save(output_path, "PNG")
        else:
            # Handle sequence output
            output_path = output_dir / f"vfx_{timestamp}"
            output_path.mkdir(exist_ok=True)
            for i, frame in enumerate(result):
                frame_path = output_path / f"frame_{i:04d}.png"
                frame.save(frame_path, "PNG")
        
        return output_path
    
    def _create_vfx_metadata(self, effects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create metadata for applied effects."""
        return {
            "timestamp": datetime.now().isoformat(),
            "effects": effects,
            "vfx_config": self.vfx_config["effect_types"]
        }
    
    async def initialize(self) -> None:
        """Initialize VFX coordinator resources."""
        self.vfx_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.vfx_config["cache_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup VFX coordinator resources."""
        self.active_effects.clear() 