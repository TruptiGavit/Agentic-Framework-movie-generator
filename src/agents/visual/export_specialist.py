from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from PIL import Image
import numpy as np
import cv2
import ffmpeg
from pathlib import Path
import json
import shutil
from datetime import datetime

class ExportSpecialist(BaseVisualAgent):
    """Agent responsible for preparing and exporting final content."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.export_config = {
            "output_dir": Path("outputs/exports"),
            "temp_dir": Path("temp/exports"),
            "delivery_formats": {
                "cinema": {
                    "video": {
                        "format": "mov",
                        "codec": "prores_422_hq",
                        "resolution": (4096, 2160),
                        "fps": 24,
                        "color_space": "rec709",
                        "bit_depth": 10
                    },
                    "audio": {
                        "format": "wav",
                        "sample_rate": 48000,
                        "bit_depth": 24,
                        "channels": 6
                    }
                },
                "streaming": {
                    "video": {
                        "format": "mp4",
                        "codec": "h264",
                        "resolution": (1920, 1080),
                        "fps": 30,
                        "color_space": "rec709",
                        "bit_depth": 8
                    },
                    "audio": {
                        "format": "aac",
                        "sample_rate": 48000,
                        "bit_rate": "320k",
                        "channels": 2
                    }
                },
                "web": {
                    "video": {
                        "format": "webm",
                        "codec": "vp9",
                        "resolution": (1920, 1080),
                        "fps": 30,
                        "color_space": "srgb",
                        "bit_depth": 8
                    },
                    "audio": {
                        "format": "opus",
                        "sample_rate": 48000,
                        "bit_rate": "192k",
                        "channels": 2
                    }
                }
            }
        }
        self.active_exports: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "prepare_export":
            return await self._prepare_export(message)
        elif message.message_type == "export_content":
            return await self._export_content(message)
        elif message.message_type == "package_delivery":
            return await self._package_delivery(message)
        return None
    
    async def _prepare_export(self, message: Message) -> Message:
        """Prepare content for export."""
        content = message.content.get("content", {})
        delivery_format = message.content.get("delivery_format", "streaming")
        export_id = message.content.get("export_id", "")
        
        try:
            preparation_result = await self._process_export_preparation(
                content, delivery_format, export_id
            )
            
            return Message(
                message_id=f"prep_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="export_prepared",
                content={"preparation_result": preparation_result},
                context=message.context,
                metadata={"export_id": export_id}
            )
        except Exception as e:
            return Message(
                message_id=f"prep_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="export_preparation_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_export_preparation(self, content: Dict[str, Any],
                                        delivery_format: str,
                                        export_id: str) -> Dict[str, Any]:
        """Process and prepare content for export."""
        format_config = self.export_config["delivery_formats"][delivery_format]
        
        # Create temporary working directory
        work_dir = self._create_work_directory(export_id)
        
        # Prepare video content
        video_result = await self._prepare_video_content(
            content.get("video", {}),
            format_config["video"],
            work_dir
        )
        
        # Prepare audio content
        audio_result = await self._prepare_audio_content(
            content.get("audio", {}),
            format_config["audio"],
            work_dir
        )
        
        # Store export details
        self.active_exports[export_id] = {
            "content": content,
            "delivery_format": delivery_format,
            "work_dir": work_dir,
            "preparation_time": datetime.now().isoformat()
        }
        
        return {
            "video_preparation": video_result,
            "audio_preparation": audio_result,
            "work_dir": str(work_dir),
            "format_config": format_config
        }
    
    async def _prepare_video_content(self, video_content: Dict[str, Any],
                                   video_config: Dict[str, Any],
                                   work_dir: Path) -> Dict[str, Any]:
        """Prepare video content for export."""
        # Setup video processing pipeline
        input_path = video_content.get("path")
        temp_output = work_dir / f"prepared_video.{video_config['format']}"
        
        # Configure video processing
        stream = ffmpeg.input(input_path)
        
        # Apply format-specific processing
        stream = self._apply_video_processing(stream, video_config)
        
        # Setup output with format configuration
        stream = ffmpeg.output(
            stream,
            str(temp_output),
            **self._get_video_output_args(video_config)
        )
        
        # Run processing
        await self._run_ffmpeg(stream)
        
        return {
            "processed_path": str(temp_output),
            "config": video_config
        }
    
    def _apply_video_processing(self, stream: Any,
                              video_config: Dict[str, Any]) -> Any:
        """Apply video processing filters."""
        # Apply resolution scaling
        if video_config.get("resolution"):
            stream = stream.filter("scale", *video_config["resolution"])
        
        # Apply framerate conversion
        if video_config.get("fps"):
            stream = stream.filter("fps", fps=video_config["fps"])
        
        # Apply color space conversion
        if video_config.get("color_space"):
            stream = self._apply_color_space_conversion(
                stream, video_config["color_space"]
            )
        
        return stream
    
    def _get_video_output_args(self, video_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get ffmpeg output arguments for video configuration."""
        args = {
            "codec": video_config["codec"],
            "pix_fmt": f"yuv420p{video_config['bit_depth']}" 
                      if video_config["bit_depth"] > 8 else "yuv420p"
        }
        
        # Add format-specific arguments
        if video_config["codec"] == "h264":
            args.update({
                "preset": "slow",
                "crf": 18
            })
        elif video_config["codec"] == "prores_422_hq":
            args.update({
                "profile:v": 3,
                "qscale:v": 9
            })
        elif video_config["codec"] == "vp9":
            args.update({
                "crf": 31,
                "row-mt": 1
            })
        
        return args
    
    def _create_work_directory(self, export_id: str) -> Path:
        """Create temporary working directory for export."""
        work_dir = self.export_config["temp_dir"] / export_id
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir
    
    async def _package_delivery(self, message: Message) -> Message:
        """Package content for delivery."""
        export_id = message.content.get("export_id", "")
        delivery_format = message.content.get("delivery_format", "streaming")
        
        try:
            if export_id not in self.active_exports:
                raise ValueError(f"Export not found: {export_id}")
            
            package_result = await self._create_delivery_package(
                export_id, delivery_format
            )
            
            return Message(
                message_id=f"pack_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="delivery_packaged",
                content={"package_result": package_result},
                context=message.context,
                metadata={"export_id": export_id}
            )
        except Exception as e:
            return Message(
                message_id=f"pack_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="packaging_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def initialize(self) -> None:
        """Initialize export specialist resources."""
        self.export_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.export_config["temp_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup export specialist resources."""
        # Clear active exports
        self.active_exports.clear()
        
        # Remove temporary files
        if self.export_config["temp_dir"].exists():
            shutil.rmtree(self.export_config["temp_dir"]) 