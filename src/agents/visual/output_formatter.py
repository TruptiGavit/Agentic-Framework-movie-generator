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
import aiofiles

class OutputFormatter(BaseVisualAgent):
    """Agent responsible for formatting and preparing final outputs."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.format_config = {
            "output_dir": Path("outputs/formatted"),
            "temp_dir": Path("temp/formatting"),
            "delivery_formats": {
                "digital_cinema": {
                    "video": {
                        "container": "mxf",
                        "codec": "jpeg2000",
                        "resolution": (4096, 2160),
                        "framerate": 24,
                        "color_space": "xyz",
                        "bit_depth": 12
                    },
                    "audio": {
                        "codec": "pcm_s24le",
                        "channels": 6,
                        "sample_rate": 48000
                    }
                },
                "broadcast": {
                    "video": {
                        "container": "mxf",
                        "codec": "xdcam_hd422",
                        "resolution": (1920, 1080),
                        "framerate": 29.97,
                        "color_space": "rec709",
                        "bit_depth": 10
                    },
                    "audio": {
                        "codec": "pcm_s24le",
                        "channels": 8,
                        "sample_rate": 48000
                    }
                },
                "streaming": {
                    "video": {
                        "container": "mp4",
                        "codec": "h264",
                        "resolution": (1920, 1080),
                        "framerate": 30,
                        "color_space": "rec709",
                        "bit_depth": 8,
                        "profiles": ["main", "high"]
                    },
                    "audio": {
                        "codec": "aac",
                        "channels": 2,
                        "sample_rate": 48000,
                        "bitrate": "320k"
                    }
                }
            },
            "metadata_standards": {
                "digital_cinema": "interop",
                "broadcast": "as11",
                "streaming": "movflags"
            }
        }
        self.active_formats: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "format_output":
            return await self._format_output(message)
        elif message.message_type == "prepare_delivery":
            return await self._prepare_delivery(message)
        elif message.message_type == "validate_format":
            return await self._validate_format(message)
        return None
    
    async def _format_output(self, message: Message) -> Message:
        """Format output content for delivery."""
        content = message.content.get("content", {})
        delivery_format = message.content.get("delivery_format", "streaming")
        format_id = message.content.get("format_id", "")
        
        try:
            format_result = await self._process_formatting(
                content, delivery_format, format_id
            )
            
            return Message(
                message_id=f"fmt_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="output_formatted",
                content={"format_result": format_result},
                context=message.context,
                metadata={"format_id": format_id}
            )
        except Exception as e:
            return Message(
                message_id=f"fmt_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="formatting_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_formatting(self, content: Dict[str, Any],
                                delivery_format: str,
                                format_id: str) -> Dict[str, Any]:
        """Process output formatting."""
        format_config = self.format_config["delivery_formats"][delivery_format]
        
        # Create working directory
        work_dir = self._create_work_directory(format_id)
        
        # Format video content
        video_result = await self._format_video_content(
            content.get("video", {}),
            format_config["video"],
            work_dir
        )
        
        # Format audio content
        audio_result = await self._format_audio_content(
            content.get("audio", {}),
            format_config["audio"],
            work_dir
        )
        
        # Combine and package content
        package_result = await self._package_content(
            video_result,
            audio_result,
            format_config,
            work_dir
        )
        
        # Store format details
        self.active_formats[format_id] = {
            "content": content,
            "delivery_format": delivery_format,
            "work_dir": work_dir,
            "results": {
                "video": video_result,
                "audio": audio_result,
                "package": package_result
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "format_id": format_id,
            "delivery_format": delivery_format,
            "output_path": str(package_result["output_path"]),
            "metadata": self._create_format_metadata(content, delivery_format)
        }
    
    async def _format_video_content(self, video_content: Dict[str, Any],
                                  video_config: Dict[str, Any],
                                  work_dir: Path) -> Dict[str, Any]:
        """Format video content according to delivery specifications."""
        input_path = video_content.get("path")
        temp_output = work_dir / f"formatted_video.{video_config['container']}"
        
        # Configure video processing
        stream = ffmpeg.input(input_path)
        
        # Apply format-specific processing
        stream = self._apply_video_formatting(stream, video_config)
        
        # Setup output with format configuration
        stream = ffmpeg.output(
            stream,
            str(temp_output),
            **self._get_video_format_args(video_config)
        )
        
        # Run processing
        await self._run_ffmpeg(stream)
        
        return {
            "output_path": temp_output,
            "config": video_config
        }
    
    def _apply_video_formatting(self, stream: Any,
                              video_config: Dict[str, Any]) -> Any:
        """Apply video formatting filters."""
        # Scale to target resolution
        stream = stream.filter("scale", *video_config["resolution"])
        
        # Convert framerate
        stream = stream.filter("fps", fps=video_config["framerate"])
        
        # Apply color space conversion
        stream = self._apply_color_space_conversion(
            stream, video_config["color_space"]
        )
        
        return stream
    
    def _create_work_directory(self, format_id: str) -> Path:
        """Create temporary working directory."""
        work_dir = self.format_config["temp_dir"] / format_id
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir
    
    def _create_format_metadata(self, content: Dict[str, Any],
                              delivery_format: str) -> Dict[str, Any]:
        """Create metadata for formatted output."""
        return {
            "timestamp": datetime.now().isoformat(),
            "content_id": content.get("id", ""),
            "delivery_format": delivery_format,
            "format_config": self.format_config["delivery_formats"][delivery_format],
            "metadata_standard": self.format_config["metadata_standards"][delivery_format]
        }
    
    async def initialize(self) -> None:
        """Initialize output formatter resources."""
        self.format_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.format_config["temp_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup output formatter resources."""
        # Clear temporary files
        if self.format_config["temp_dir"].exists():
            for work_dir in self.format_config["temp_dir"].iterdir():
                if work_dir.is_dir():
                    for file in work_dir.iterdir():
                        file.unlink()
                    work_dir.rmdir()
        
        # Clear active formats
        self.active_formats.clear() 