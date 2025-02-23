from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from PIL import Image
import numpy as np
import cv2
import ffmpeg
from pathlib import Path
import json
from datetime import datetime

class FormatAdapter(BaseVisualAgent):
    """Agent responsible for adapting content between different formats and specifications."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.format_config = {
            "output_dir": Path("outputs/format_adapter"),
            "cache_dir": Path("cache/format_adapter"),
            "supported_formats": {
                "image": ["png", "jpg", "exr", "tiff"],
                "video": ["mp4", "mov", "webm", "gif"],
                "sequence": ["png", "exr", "jpg"],
                "3d": ["fbx", "obj", "blend", "usd"]
            },
            "codecs": {
                "h264": {
                    "preset": "slow",
                    "crf": 18,
                    "pixel_format": "yuv420p"
                },
                "prores": {
                    "profile": 3,  # ProRes 422 HQ
                    "pixel_format": "yuv422p10le"
                },
                "vp9": {
                    "crf": 31,
                    "pixel_format": "yuv420p"
                }
            },
            "color_spaces": {
                "srgb": {"gamma": 2.2, "primaries": "bt709"},
                "rec709": {"gamma": 2.4, "primaries": "bt709"},
                "linear": {"gamma": 1.0, "primaries": "bt709"}
            }
        }
        self.active_conversions: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "convert_format":
            return await self._convert_format(message)
        elif message.message_type == "batch_convert":
            return await self._batch_convert(message)
        elif message.message_type == "validate_format":
            return await self._validate_format(message)
        return None
    
    async def _convert_format(self, message: Message) -> Message:
        """Convert content to specified format."""
        content = message.content.get("content", {})
        target_format = message.content.get("target_format", {})
        conversion_id = message.content.get("conversion_id", "")
        
        try:
            conversion_result = await self._process_conversion(
                content, target_format, conversion_id
            )
            
            return Message(
                message_id=f"conv_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="format_converted",
                content={"conversion_result": conversion_result},
                context=message.context,
                metadata={"conversion_id": conversion_id}
            )
        except Exception as e:
            return Message(
                message_id=f"conv_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="conversion_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_conversion(self, content: Dict[str, Any],
                                target_format: Dict[str, Any],
                                conversion_id: str) -> Dict[str, Any]:
        """Process format conversion."""
        # Determine content type and current format
        content_type = self._determine_content_type(content)
        current_format = content.get("format", {})
        
        # Validate format compatibility
        self._validate_format_compatibility(content_type, current_format, target_format)
        
        # Perform conversion
        if content_type == "image":
            result = await self._convert_image(content, target_format)
        elif content_type == "video":
            result = await self._convert_video(content, target_format)
        elif content_type == "sequence":
            result = await self._convert_sequence(content, target_format)
        elif content_type == "3d":
            result = await self._convert_3d(content, target_format)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
        
        # Store conversion details
        self.active_conversions[conversion_id] = {
            "content_type": content_type,
            "original_format": current_format,
            "target_format": target_format,
            "conversion_time": datetime.now().isoformat()
        }
        
        return {
            "converted_content": result,
            "format_info": self._get_format_info(target_format),
            "metadata": self._create_conversion_metadata(content, target_format)
        }
    
    async def _convert_image(self, content: Dict[str, Any],
                           target_format: Dict[str, Any]) -> Dict[str, Any]:
        """Convert image to target format."""
        image = self._load_image(content)
        
        # Apply color space conversion if needed
        if target_format.get("color_space"):
            image = self._convert_color_space(
                image,
                content.get("format", {}).get("color_space", "srgb"),
                target_format["color_space"]
            )
        
        # Apply bit depth conversion if needed
        if target_format.get("bit_depth"):
            image = self._convert_bit_depth(image, target_format["bit_depth"])
        
        # Save in target format
        output_path = self._save_image(
            image,
            target_format["format"],
            target_format.get("quality", 95)
        )
        
        return {
            "path": str(output_path),
            "format": target_format["format"],
            "dimensions": image.size
        }
    
    async def _convert_video(self, content: Dict[str, Any],
                           target_format: Dict[str, Any]) -> Dict[str, Any]:
        """Convert video to target format."""
        input_path = content.get("path")
        codec_config = self.format_config["codecs"][target_format.get("codec", "h264")]
        
        output_path = self.format_config["output_dir"] / f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{target_format['format']}"
        
        # Setup ffmpeg stream
        stream = ffmpeg.input(input_path)
        
        # Apply video filters if needed
        if target_format.get("resolution"):
            stream = stream.filter("scale", *target_format["resolution"])
        
        # Setup output with codec configuration
        stream = ffmpeg.output(
            stream,
            str(output_path),
            **codec_config,
            acodec="aac" if target_format.get("audio", True) else "none"
        )
        
        # Run conversion
        await self._run_ffmpeg(stream)
        
        return {
            "path": str(output_path),
            "format": target_format["format"],
            "codec": target_format.get("codec", "h264")
        }
    
    def _convert_color_space(self, image: Image.Image,
                           source_space: str,
                           target_space: str) -> Image.Image:
        """Convert image between color spaces."""
        source_config = self.format_config["color_spaces"][source_space]
        target_config = self.format_config["color_spaces"][target_space]
        
        # Convert to linear space
        if source_config["gamma"] != 1.0:
            image = self._apply_gamma(image, 1.0 / source_config["gamma"])
        
        # Convert primaries if needed
        if source_config["primaries"] != target_config["primaries"]:
            image = self._convert_primaries(
                image,
                source_config["primaries"],
                target_config["primaries"]
            )
        
        # Apply target gamma
        if target_config["gamma"] != 1.0:
            image = self._apply_gamma(image, target_config["gamma"])
        
        return image
    
    def _create_conversion_metadata(self, content: Dict[str, Any],
                                  target_format: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for format conversion."""
        return {
            "timestamp": datetime.now().isoformat(),
            "original_format": content.get("format", {}),
            "target_format": target_format,
            "conversion_settings": {
                "color_space": target_format.get("color_space"),
                "codec": target_format.get("codec"),
                "quality": target_format.get("quality")
            }
        }
    
    async def initialize(self) -> None:
        """Initialize format adapter resources."""
        self.format_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.format_config["cache_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup format adapter resources."""
        self.active_conversions.clear() 