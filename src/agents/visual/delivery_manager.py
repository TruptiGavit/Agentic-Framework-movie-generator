from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from pathlib import Path
import json
import shutil
from datetime import datetime
import aiofiles
import zipfile
import hashlib

class DeliveryPackageManager(BaseVisualAgent):
    """Agent responsible for managing final delivery packages."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.delivery_config = {
            "output_dir": Path("outputs/delivery"),
            "package_dir": Path("packages"),
            "delivery_types": {
                "theatrical": {
                    "required_files": [
                        "main_feature.mxf",
                        "audio_5.1.wav",
                        "subtitles.xml",
                        "kdm_certificates"
                    ],
                    "metadata": ["cpl.xml", "pkl.xml", "assetmap.xml"],
                    "validation": ["dcp_compliance", "audio_levels", "subtitle_sync"]
                },
                "broadcast": {
                    "required_files": [
                        "program.mxf",
                        "audio_stereo.wav",
                        "captions.scc",
                        "metadata.xml"
                    ],
                    "metadata": ["as11_core.xml", "technical_metadata.xml"],
                    "validation": ["broadcast_specs", "loudness", "caption_timing"]
                },
                "streaming": {
                    "required_files": [
                        "video_h264.mp4",
                        "audio_aac.m4a",
                        "subtitles.vtt",
                        "thumbnails"
                    ],
                    "metadata": ["manifest.json", "media_info.xml"],
                    "validation": ["streaming_compliance", "bitrate_validation"]
                }
            }
        }
        self.active_deliveries: Dict[str, Dict[str, Any]] = {}
        self.delivery_history: List[Dict[str, Any]] = []
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "create_package":
            return await self._create_package(message)
        elif message.message_type == "validate_package":
            return await self._validate_package(message)
        elif message.message_type == "deliver_package":
            return await self._deliver_package(message)
        return None
    
    async def _create_package(self, message: Message) -> Message:
        """Create a delivery package."""
        content = message.content.get("content", {})
        delivery_type = message.content.get("delivery_type", "streaming")
        package_id = message.content.get("package_id", "")
        
        try:
            package_result = await self._process_package_creation(
                content, delivery_type, package_id
            )
            
            return Message(
                message_id=f"pkg_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="package_created",
                content={"package_result": package_result},
                context=message.context,
                metadata={"package_id": package_id}
            )
        except Exception as e:
            return Message(
                message_id=f"pkg_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="package_creation_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_package_creation(self, content: Dict[str, Any],
                                      delivery_type: str,
                                      package_id: str) -> Dict[str, Any]:
        """Process delivery package creation."""
        # Create package directory
        package_dir = self._create_package_directory(package_id)
        
        # Collect and organize required files
        file_results = await self._collect_package_files(
            content, delivery_type, package_dir
        )
        
        # Generate package metadata
        metadata = await self._generate_package_metadata(
            content, delivery_type, file_results
        )
        
        # Create package manifest
        manifest = self._create_package_manifest(
            file_results, metadata, delivery_type
        )
        
        # Store delivery details
        self.active_deliveries[package_id] = {
            "content": content,
            "delivery_type": delivery_type,
            "package_dir": package_dir,
            "manifest": manifest,
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "package_id": package_id,
            "delivery_type": delivery_type,
            "package_path": str(package_dir),
            "manifest": manifest
        }
    
    async def _collect_package_files(self, content: Dict[str, Any],
                                   delivery_type: str,
                                   package_dir: Path) -> Dict[str, Any]:
        """Collect and organize files for the package."""
        required_files = self.delivery_config["delivery_types"][delivery_type]["required_files"]
        file_results = {}
        
        for file_type in required_files:
            source_path = content.get("files", {}).get(file_type)
            if source_path:
                dest_path = package_dir / file_type
                await self._copy_and_verify_file(Path(source_path), dest_path)
                file_results[file_type] = {
                    "path": str(dest_path.relative_to(package_dir)),
                    "size": dest_path.stat().st_size,
                    "checksum": await self._calculate_file_hash(dest_path)
                }
        
        return file_results
    
    async def _generate_package_metadata(self, content: Dict[str, Any],
                                       delivery_type: str,
                                       file_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata for the package."""
        metadata = {
            "package_info": {
                "created_at": datetime.now().isoformat(),
                "delivery_type": delivery_type,
                "content_id": content.get("id", ""),
                "version": content.get("version", "1.0")
            },
            "technical_info": {
                "files": file_results,
                "total_size": sum(f["size"] for f in file_results.values()),
                "specifications": self.delivery_config["delivery_types"][delivery_type]
            },
            "content_info": {
                "title": content.get("title", ""),
                "duration": content.get("duration", 0),
                "format": content.get("format", {}),
                "metadata": content.get("metadata", {})
            }
        }
        
        return metadata
    
    def _create_package_manifest(self, file_results: Dict[str, Any],
                               metadata: Dict[str, Any],
                               delivery_type: str) -> Dict[str, Any]:
        """Create package manifest."""
        return {
            "manifest_version": "1.0",
            "package_type": delivery_type,
            "files": file_results,
            "metadata": metadata,
            "validation_requirements": self.delivery_config["delivery_types"][delivery_type]["validation"]
        }
    
    async def _copy_and_verify_file(self, source: Path, destination: Path) -> None:
        """Copy file and verify integrity."""
        # Copy file
        shutil.copy2(source, destination)
        
        # Verify copy
        source_hash = await self._calculate_file_hash(source)
        dest_hash = await self._calculate_file_hash(destination)
        
        if source_hash != dest_hash:
            raise ValueError(f"File verification failed for {source}")
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        hasher = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _create_package_directory(self, package_id: str) -> Path:
        """Create and return package directory."""
        package_dir = self.delivery_config["package_dir"] / package_id
        package_dir.mkdir(parents=True, exist_ok=True)
        return package_dir
    
    async def initialize(self) -> None:
        """Initialize delivery package manager resources."""
        self.delivery_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.delivery_config["package_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup delivery package manager resources."""
        # Archive active deliveries
        for package_id, delivery in self.active_deliveries.items():
            self.delivery_history.append({
                "package_id": package_id,
                "status": "archived",
                "archived_at": datetime.now().isoformat(),
                **delivery
            })
        
        # Clear active deliveries
        self.active_deliveries.clear() 