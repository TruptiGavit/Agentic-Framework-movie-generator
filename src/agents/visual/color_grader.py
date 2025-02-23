from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from PIL import Image, ImageEnhance
import numpy as np
import cv2
from pathlib import Path
import json
from datetime import datetime

class ColorGradingSpecialist(BaseVisualAgent):
    """Agent responsible for color grading and color correction."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.grading_config = {
            "output_dir": Path("outputs/color_grading"),
            "cache_dir": Path("cache/color_grading"),
            "lut_dir": Path("resources/luts"),
            "color_profiles": {
                "cinematic": {
                    "contrast": 1.2,
                    "saturation": 0.9,
                    "temperature": 5500,
                    "tint": 0,
                    "shadows": (0.1, 0.1, 0.2),
                    "midtones": (1.0, 1.0, 1.0),
                    "highlights": (1.0, 0.95, 0.9)
                },
                "dramatic": {
                    "contrast": 1.4,
                    "saturation": 0.8,
                    "temperature": 5000,
                    "tint": 5,
                    "shadows": (0.2, 0.1, 0.3),
                    "midtones": (0.9, 0.9, 1.0),
                    "highlights": (1.1, 1.0, 0.9)
                }
            }
        }
        self.active_grades: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "apply_color_grade":
            return await self._apply_color_grade(message)
        elif message.message_type == "create_color_profile":
            return await self._create_color_profile(message)
        elif message.message_type == "match_colors":
            return await self._match_colors(message)
        return None
    
    async def _apply_color_grade(self, message: Message) -> Message:
        """Apply color grading to images or sequences."""
        content = message.content.get("content", {})
        grade_profile = message.content.get("grade_profile", {})
        sequence_id = message.content.get("sequence_id", "")
        
        try:
            grading_result = await self._process_color_grading(
                content, grade_profile, sequence_id
            )
            
            return Message(
                message_id=f"grade_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="color_grade_applied",
                content={"grading_result": grading_result},
                context=message.context,
                metadata={"sequence_id": sequence_id}
            )
        except Exception as e:
            return Message(
                message_id=f"grade_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="color_grade_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_color_grading(self, content: Dict[str, Any],
                                   grade_profile: Dict[str, Any],
                                   sequence_id: str) -> Dict[str, Any]:
        """Process and apply color grading."""
        # Load content
        if "image" in content:
            result = await self._grade_image(content["image"], grade_profile)
        elif "sequence" in content:
            result = await self._grade_sequence(content["sequence"], grade_profile)
        else:
            raise ValueError("No valid content provided")
        
        # Save result
        output_path = await self._save_graded_result(result, sequence_id)
        
        return {
            "status": "success",
            "output_path": str(output_path),
            "grade_profile": grade_profile,
            "metadata": self._create_grading_metadata(grade_profile)
        }
    
    async def _grade_image(self, image: Image.Image,
                          profile: Dict[str, Any]) -> Image.Image:
        """Apply color grading to a single image."""
        # Convert to numpy array for processing
        img_array = np.array(image)
        
        # Apply basic adjustments
        img_array = self._apply_basic_adjustments(img_array, profile)
        
        # Apply color balance
        img_array = self._apply_color_balance(img_array, profile)
        
        # Apply tone mapping
        img_array = self._apply_tone_mapping(img_array, profile)
        
        # Convert back to PIL Image
        return Image.fromarray(img_array)
    
    def _apply_basic_adjustments(self, img: np.ndarray,
                               profile: Dict[str, Any]) -> np.ndarray:
        """Apply basic color adjustments."""
        # Convert to float32 for processing
        img = img.astype(np.float32) / 255.0
        
        # Apply contrast
        contrast = profile.get("contrast", 1.0)
        img = np.clip((img - 0.5) * contrast + 0.5, 0, 1)
        
        # Apply saturation
        saturation = profile.get("saturation", 1.0)
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        hsv[..., 1] *= saturation
        img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        
        return (np.clip(img, 0, 1) * 255).astype(np.uint8)
    
    def _apply_color_balance(self, img: np.ndarray,
                           profile: Dict[str, Any]) -> np.ndarray:
        """Apply color balance adjustments."""
        # Convert to float32
        img = img.astype(np.float32) / 255.0
        
        # Apply temperature adjustment
        temp = profile.get("temperature", 5500)
        img = self._adjust_temperature(img, temp)
        
        # Apply tint
        tint = profile.get("tint", 0)
        img = self._adjust_tint(img, tint)
        
        return (np.clip(img, 0, 1) * 255).astype(np.uint8)
    
    def _apply_tone_mapping(self, img: np.ndarray,
                          profile: Dict[str, Any]) -> np.ndarray:
        """Apply tone mapping adjustments."""
        # Split into shadows, midtones, and highlights
        shadows = profile.get("shadows", (1.0, 1.0, 1.0))
        midtones = profile.get("midtones", (1.0, 1.0, 1.0))
        highlights = profile.get("highlights", (1.0, 1.0, 1.0))
        
        # Convert to float32
        img = img.astype(np.float32) / 255.0
        
        # Apply tone mapping per channel
        for i in range(3):
            img[..., i] = self._tone_map_channel(
                img[..., i], shadows[i], midtones[i], highlights[i]
            )
        
        return (np.clip(img, 0, 1) * 255).astype(np.uint8)
    
    def _tone_map_channel(self, channel: np.ndarray,
                         shadow: float,
                         midtone: float,
                         highlight: float) -> np.ndarray:
        """Apply tone mapping to a single channel."""
        # Split into tonal ranges
        shadows_mask = channel < 0.333
        midtones_mask = (channel >= 0.333) & (channel < 0.666)
        highlights_mask = channel >= 0.666
        
        # Apply adjustments
        channel[shadows_mask] *= shadow
        channel[midtones_mask] *= midtone
        channel[highlights_mask] *= highlight
        
        return np.clip(channel, 0, 1)
    
    def _adjust_temperature(self, img: np.ndarray, temperature: float) -> np.ndarray:
        """Adjust color temperature."""
        # Convert temperature to RGB multipliers
        # This is a simplified version; real implementation would use proper color science
        r_mult = 1.0 + (temperature - 5500) / 10000
        b_mult = 1.0 - (temperature - 5500) / 10000
        
        img[..., 0] *= r_mult  # Red channel
        img[..., 2] *= b_mult  # Blue channel
        
        return np.clip(img, 0, 1)
    
    def _adjust_tint(self, img: np.ndarray, tint: float) -> np.ndarray:
        """Adjust green-magenta tint."""
        g_mult = 1.0 + tint / 100
        img[..., 1] *= g_mult  # Green channel
        
        return np.clip(img, 0, 1)
    
    async def _save_graded_result(self, result: Any, sequence_id: str) -> Path:
        """Save color graded result."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.grading_config["output_dir"] / sequence_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if isinstance(result, Image.Image):
            output_path = output_dir / f"graded_{timestamp}.png"
            result.save(output_path, "PNG")
        else:
            # Handle sequence output
            output_path = output_dir / f"graded_{timestamp}"
            output_path.mkdir(exist_ok=True)
            for i, frame in enumerate(result):
                frame_path = output_path / f"frame_{i:04d}.png"
                frame.save(frame_path, "PNG")
        
        return output_path
    
    def _create_grading_metadata(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for color grading."""
        return {
            "timestamp": datetime.now().isoformat(),
            "grade_profile": profile,
            "color_profiles": self.grading_config["color_profiles"]
        }
    
    async def initialize(self) -> None:
        """Initialize color grading resources."""
        self.grading_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.grading_config["cache_dir"].mkdir(parents=True, exist_ok=True)
        self.grading_config["lut_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup color grading resources."""
        self.active_grades.clear() 