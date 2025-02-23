from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pathlib import Path
import json
from datetime import datetime

class CreditsGenerator(BaseVisualAgent):
    """Agent responsible for generating and formatting credits sequences."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.credits_config = {
            "output_dir": Path("outputs/credits"),
            "cache_dir": Path("cache/credits"),
            "fonts_dir": Path("resources/fonts"),
            "templates": {
                "standard": {
                    "resolution": (1920, 1080),
                    "background": "black",
                    "scroll_speed": 1.0,
                    "fade_duration": 1.0
                },
                "modern": {
                    "resolution": (3840, 2160),
                    "background": "gradient",
                    "scroll_speed": 1.2,
                    "fade_duration": 1.5
                },
                "minimal": {
                    "resolution": (1920, 1080),
                    "background": "transparent",
                    "scroll_speed": 0.8,
                    "fade_duration": 0.8
                }
            },
            "text_styles": {
                "header": {
                    "font": "Helvetica-Bold",
                    "size": 60,
                    "color": "#FFFFFF",
                    "spacing": 1.5
                },
                "subheader": {
                    "font": "Helvetica",
                    "size": 48,
                    "color": "#E0E0E0",
                    "spacing": 1.3
                },
                "body": {
                    "font": "Helvetica",
                    "size": 36,
                    "color": "#CCCCCC",
                    "spacing": 1.2
                }
            }
        }
        self.active_sequences: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "generate_credits":
            return await self._generate_credits(message)
        elif message.message_type == "update_credits":
            return await self._update_credits(message)
        elif message.message_type == "preview_credits":
            return await self._preview_credits(message)
        return None
    
    async def _generate_credits(self, message: Message) -> Message:
        """Generate credits sequence."""
        credits_data = message.content.get("credits_data", {})
        template_name = message.content.get("template", "standard")
        sequence_id = message.content.get("sequence_id", "")
        
        try:
            credits_result = await self._process_credits_generation(
                credits_data, template_name, sequence_id
            )
            
            return Message(
                message_id=f"cred_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="credits_generated",
                content={"credits_result": credits_result},
                context=message.context,
                metadata={"sequence_id": sequence_id}
            )
        except Exception as e:
            return Message(
                message_id=f"cred_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="credits_generation_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_credits_generation(self, credits_data: Dict[str, Any],
                                        template_name: str,
                                        sequence_id: str) -> Dict[str, Any]:
        """Process credits sequence generation."""
        template = self.credits_config["templates"][template_name]
        
        # Format credits data
        formatted_credits = self._format_credits_data(credits_data)
        
        # Generate frames
        frames = await self._generate_credit_frames(formatted_credits, template)
        
        # Apply animations
        animated_sequence = await self._apply_credit_animations(frames, template)
        
        # Store sequence details
        self.active_sequences[sequence_id] = {
            "template": template_name,
            "frames": frames,
            "animated_sequence": animated_sequence,
            "generated_at": datetime.now().isoformat()
        }
        
        return {
            "sequence_id": sequence_id,
            "frame_count": len(frames),
            "duration": self._calculate_sequence_duration(frames, template),
            "metadata": self._create_credits_metadata(credits_data, template_name)
        }
    
    def _format_credits_data(self, credits_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format credits data into renderable sections."""
        formatted_sections = []
        
        for section in credits_data.get("sections", []):
            formatted_section = {
                "title": section.get("title", ""),
                "style": section.get("style", "header"),
                "entries": self._format_section_entries(section.get("entries", []))
            }
            formatted_sections.append(formatted_section)
        
        return formatted_sections
    
    def _format_section_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format individual credit entries."""
        formatted_entries = []
        
        for entry in entries:
            formatted_entry = {
                "role": entry.get("role", ""),
                "names": entry.get("names", []),
                "style": entry.get("style", "body"),
                "spacing": entry.get("spacing", 1.0)
            }
            formatted_entries.append(formatted_entry)
        
        return formatted_entries
    
    async def _generate_credit_frames(self, formatted_credits: List[Dict[str, Any]],
                                    template: Dict[str, Any]) -> List[Image.Image]:
        """Generate individual frames for credits sequence."""
        frames = []
        resolution = template["resolution"]
        
        # Create base frame
        base_frame = self._create_base_frame(resolution, template["background"])
        
        for section in formatted_credits:
            # Create section frame
            section_frame = base_frame.copy()
            draw = ImageDraw.Draw(section_frame)
            
            # Draw section content
            y_offset = self._draw_section(
                draw,
                section,
                resolution,
                self.credits_config["text_styles"]
            )
            
            frames.append(section_frame)
        
        return frames
    
    def _create_base_frame(self, resolution: tuple[int, int],
                          background: str) -> Image.Image:
        """Create base frame with background."""
        if background == "gradient":
            return self._create_gradient_background(resolution)
        elif background == "transparent":
            return Image.new("RGBA", resolution, (0, 0, 0, 0))
        else:
            return Image.new("RGB", resolution, background)
    
    def _draw_section(self, draw: ImageDraw.ImageDraw,
                     section: Dict[str, Any],
                     resolution: tuple[int, int],
                     text_styles: Dict[str, Any]) -> int:
        """Draw a credits section and return final y-offset."""
        y_offset = resolution[1] // 4
        
        # Draw section title
        title_style = text_styles[section["style"]]
        font = self._load_font(title_style["font"], title_style["size"])
        
        draw.text(
            (resolution[0] // 2, y_offset),
            section["title"],
            font=font,
            fill=title_style["color"],
            anchor="mm"
        )
        
        y_offset += title_style["size"] * title_style["spacing"]
        
        # Draw entries
        for entry in section["entries"]:
            y_offset = self._draw_entry(draw, entry, resolution, text_styles, y_offset)
        
        return y_offset
    
    def _load_font(self, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        """Load font from fonts directory."""
        font_path = self.credits_config["fonts_dir"] / f"{font_name}.ttf"
        return ImageFont.truetype(str(font_path), size)
    
    def _create_credits_metadata(self, credits_data: Dict[str, Any],
                               template_name: str) -> Dict[str, Any]:
        """Create metadata for credits sequence."""
        return {
            "timestamp": datetime.now().isoformat(),
            "template": template_name,
            "config": self.credits_config["templates"][template_name],
            "sections": len(credits_data.get("sections", []))
        }
    
    async def initialize(self) -> None:
        """Initialize credits generator resources."""
        self.credits_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.credits_config["cache_dir"].mkdir(parents=True, exist_ok=True)
        self.credits_config["fonts_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup credits generator resources."""
        self.active_sequences.clear() 