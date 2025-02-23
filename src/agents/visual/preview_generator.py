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

class PreviewGenerator(BaseVisualAgent):
    """Agent responsible for generating various types of content previews."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.preview_config = {
            "output_dir": Path("outputs/previews"),
            "cache_dir": Path("cache/previews"),
            "preview_types": {
                "thumbnail": {
                    "sizes": [(256, 256), (512, 512), (1024, 1024)],
                    "format": "jpg",
                    "quality": 85
                },
                "proxy": {
                    "resolution": (1280, 720),
                    "format": "mp4",
                    "codec": "h264",
                    "crf": 23,
                    "fps": 24
                },
                "gif": {
                    "max_size": (480, 270),
                    "fps": 12,
                    "quality": 70
                },
                "contact_sheet": {
                    "columns": 4,
                    "rows": 3,
                    "spacing": 10,
                    "include_timecode": True
                }
            }
        }
        self.active_previews: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "generate_preview":
            return await self._generate_preview(message)
        elif message.message_type == "batch_preview":
            return await self._batch_preview(message)
        elif message.message_type == "update_preview":
            return await self._update_preview(message)
        return None
    
    async def _generate_preview(self, message: Message) -> Message:
        """Generate preview for content."""
        content = message.content.get("content", {})
        preview_type = message.content.get("preview_type", "thumbnail")
        preview_id = message.content.get("preview_id", "")
        
        try:
            preview_result = await self._process_preview_generation(
                content, preview_type, preview_id
            )
            
            return Message(
                message_id=f"prev_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="preview_generated",
                content={"preview_result": preview_result},
                context=message.context,
                metadata={"preview_id": preview_id}
            )
        except Exception as e:
            return Message(
                message_id=f"prev_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="preview_generation_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_preview_generation(self, content: Dict[str, Any],
                                        preview_type: str,
                                        preview_id: str) -> Dict[str, Any]:
        """Process preview generation."""
        if preview_type == "thumbnail":
            result = await self._generate_thumbnails(content)
        elif preview_type == "proxy":
            result = await self._generate_proxy(content)
        elif preview_type == "gif":
            result = await self._generate_gif(content)
        elif preview_type == "contact_sheet":
            result = await self._generate_contact_sheet(content)
        else:
            raise ValueError(f"Unsupported preview type: {preview_type}")
        
        # Store preview details
        self.active_previews[preview_id] = {
            "type": preview_type,
            "content_id": content.get("id"),
            "result": result,
            "generated_at": datetime.now().isoformat()
        }
        
        return {
            "preview_id": preview_id,
            "type": preview_type,
            "result": result,
            "metadata": self._create_preview_metadata(content, preview_type)
        }
    
    async def _generate_thumbnails(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate thumbnails at different sizes."""
        source_path = Path(content.get("path", ""))
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        thumbnails = {}
        config = self.preview_config["preview_types"]["thumbnail"]
        
        # Load source image
        with Image.open(source_path) as img:
            for size in config["sizes"]:
                # Create thumbnail
                thumb = img.copy()
                thumb.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                output_path = self._get_preview_path(
                    content, f"thumb_{size[0]}x{size[1]}.{config['format']}"
                )
                thumb.save(output_path, quality=config["quality"])
                
                thumbnails[f"{size[0]}x{size[1]}"] = str(output_path)
        
        return {
            "thumbnails": thumbnails,
            "format": config["format"],
            "quality": config["quality"]
        }
    
    async def _generate_proxy(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate proxy video."""
        source_path = content.get("path")
        config = self.preview_config["preview_types"]["proxy"]
        
        output_path = self._get_preview_path(
            content, f"proxy.{config['format']}"
        )
        
        # Setup ffmpeg stream
        stream = ffmpeg.input(source_path)
        
        # Apply proxy settings
        stream = stream.filter("scale", *config["resolution"])
        
        # Setup output
        stream = ffmpeg.output(
            stream,
            str(output_path),
            **{
                "c:v": config["codec"],
                "crf": config["crf"],
                "r": config["fps"],
                "pix_fmt": "yuv420p"
            }
        )
        
        # Run conversion
        await self._run_ffmpeg(stream)
        
        return {
            "proxy_path": str(output_path),
            "resolution": config["resolution"],
            "fps": config["fps"]
        }
    
    async def _generate_contact_sheet(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate contact sheet from video frames."""
        source_path = content.get("path")
        config = self.preview_config["preview_types"]["contact_sheet"]
        
        # Extract frames
        frames = await self._extract_frames(
            source_path,
            config["rows"] * config["columns"]
        )
        
        # Create contact sheet
        sheet = self._create_contact_sheet(frames, config)
        
        # Save contact sheet
        output_path = self._get_preview_path(content, "contact_sheet.jpg")
        sheet.save(output_path, quality=85)
        
        return {
            "sheet_path": str(output_path),
            "frame_count": len(frames),
            "layout": f"{config['rows']}x{config['columns']}"
        }
    
    def _get_preview_path(self, content: Dict[str, Any], filename: str) -> Path:
        """Get path for preview file."""
        content_id = content.get("id", "unknown")
        preview_dir = self.preview_config["output_dir"] / content_id
        preview_dir.mkdir(parents=True, exist_ok=True)
        return preview_dir / filename
    
    def _create_preview_metadata(self, content: Dict[str, Any],
                               preview_type: str) -> Dict[str, Any]:
        """Create metadata for preview."""
        return {
            "timestamp": datetime.now().isoformat(),
            "content_id": content.get("id"),
            "preview_type": preview_type,
            "config": self.preview_config["preview_types"][preview_type]
        }
    
    async def initialize(self) -> None:
        """Initialize preview generator resources."""
        self.preview_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.preview_config["cache_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup preview generator resources."""
        self.active_previews.clear() 