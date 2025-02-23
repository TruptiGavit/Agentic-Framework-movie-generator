from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from pathlib import Path
import json
import shutil
import hashlib
from datetime import datetime
import aiofiles

class ArchiveManager(BaseVisualAgent):
    """Agent responsible for managing and organizing rendered content archives."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.archive_config = {
            "archive_dir": Path("archives"),
            "backup_dir": Path("backups/archives"),
            "storage_structure": {
                "renders": {
                    "final": "final_renders",
                    "preview": "preview_renders",
                    "wip": "work_in_progress"
                },
                "assets": {
                    "source": "source_assets",
                    "processed": "processed_assets",
                    "cached": "cached_assets"
                },
                "metadata": {
                    "project": "project_metadata",
                    "render": "render_metadata",
                    "version": "version_history"
                }
            },
            "retention_policy": {
                "final_renders": "permanent",
                "preview_renders": "30_days",
                "wip": "7_days",
                "cached_assets": "project_duration"
            }
        }
        self.active_archives: Dict[str, Dict[str, Any]] = {}
        self.archive_index: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "archive_content":
            return await self._archive_content(message)
        elif message.message_type == "retrieve_archived":
            return await self._retrieve_archived(message)
        elif message.message_type == "manage_archives":
            return await self._manage_archives(message)
        return None
    
    async def _archive_content(self, message: Message) -> Message:
        """Archive rendered content and associated data."""
        content = message.content.get("content", {})
        archive_type = message.content.get("archive_type", "final")
        archive_id = message.content.get("archive_id", "")
        
        try:
            archive_result = await self._process_archival(
                content, archive_type, archive_id
            )
            
            return Message(
                message_id=f"arch_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="content_archived",
                content={"archive_result": archive_result},
                context=message.context,
                metadata={"archive_id": archive_id}
            )
        except Exception as e:
            return Message(
                message_id=f"arch_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="archival_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_archival(self, content: Dict[str, Any],
                              archive_type: str,
                              archive_id: str) -> Dict[str, Any]:
        """Process content archival."""
        # Create archive structure
        archive_path = self._create_archive_structure(archive_id, archive_type)
        
        # Archive content files
        content_result = await self._archive_files(
            content, archive_path, archive_type
        )
        
        # Archive metadata
        metadata_result = await self._archive_metadata(
            content, archive_path, archive_type
        )
        
        # Update archive index
        await self._update_archive_index(archive_id, {
            "type": archive_type,
            "content": content_result,
            "metadata": metadata_result,
            "archived_at": datetime.now().isoformat()
        })
        
        return {
            "archive_id": archive_id,
            "archive_path": str(archive_path),
            "content_result": content_result,
            "metadata_result": metadata_result
        }
    
    def _create_archive_structure(self, archive_id: str,
                                archive_type: str) -> Path:
        """Create archive directory structure."""
        base_path = self.archive_config["archive_dir"]
        structure = self.archive_config["storage_structure"]
        
        # Create main archive directory
        archive_path = base_path / structure["renders"][archive_type] / archive_id
        archive_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (archive_path / "content").mkdir(exist_ok=True)
        (archive_path / "metadata").mkdir(exist_ok=True)
        (archive_path / "assets").mkdir(exist_ok=True)
        
        return archive_path
    
    async def _archive_files(self, content: Dict[str, Any],
                           archive_path: Path,
                           archive_type: str) -> Dict[str, Any]:
        """Archive content files."""
        content_path = archive_path / "content"
        archived_files = {}
        
        for file_type, file_path in content.get("files", {}).items():
            source_path = Path(file_path)
            if source_path.exists():
                # Generate unique filename
                file_hash = self._generate_file_hash(source_path)
                dest_path = content_path / f"{file_type}_{file_hash}{source_path.suffix}"
                
                # Copy file
                shutil.copy2(source_path, dest_path)
                archived_files[file_type] = str(dest_path.relative_to(self.archive_config["archive_dir"]))
        
        return {
            "files": archived_files,
            "archive_type": archive_type
        }
    
    async def _archive_metadata(self, content: Dict[str, Any],
                              archive_path: Path,
                              archive_type: str) -> Dict[str, Any]:
        """Archive content metadata."""
        metadata_path = archive_path / "metadata"
        
        # Create metadata record
        metadata = {
            "content_info": content.get("metadata", {}),
            "archive_type": archive_type,
            "archived_at": datetime.now().isoformat(),
            "archive_version": "1.0"
        }
        
        # Save metadata
        async with aiofiles.open(metadata_path / "content_metadata.json", 'w') as f:
            await f.write(json.dumps(metadata, indent=2))
        
        return metadata
    
    async def _update_archive_index(self, archive_id: str,
                                  archive_info: Dict[str, Any]) -> None:
        """Update archive index with new entry."""
        self.archive_index[archive_id] = archive_info
        
        # Save index to disk
        index_path = self.archive_config["archive_dir"] / "archive_index.json"
        async with aiofiles.open(index_path, 'w') as f:
            await f.write(json.dumps(self.archive_index, indent=2))
    
    def _generate_file_hash(self, file_path: Path) -> str:
        """Generate hash for file identification."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        return hasher.hexdigest()[:12]
    
    async def _retrieve_archived(self, message: Message) -> Message:
        """Retrieve archived content."""
        archive_id = message.content.get("archive_id", "")
        retrieval_type = message.content.get("retrieval_type", "full")
        
        try:
            if archive_id not in self.archive_index:
                raise ValueError(f"Archive not found: {archive_id}")
            
            retrieval_result = await self._process_retrieval(
                archive_id, retrieval_type
            )
            
            return Message(
                message_id=f"ret_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="archive_retrieved",
                content={"retrieval_result": retrieval_result},
                context=message.context,
                metadata={"archive_id": archive_id}
            )
        except Exception as e:
            return Message(
                message_id=f"ret_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="retrieval_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def initialize(self) -> None:
        """Initialize archive manager resources."""
        # Create archive directories
        self.archive_config["archive_dir"].mkdir(parents=True, exist_ok=True)
        self.archive_config["backup_dir"].mkdir(parents=True, exist_ok=True)
        
        # Load archive index
        await self._load_archive_index()
    
    async def cleanup(self) -> None:
        """Cleanup archive manager resources."""
        # Save final state of archive index
        await self._update_archive_index(
            "final_state",
            {"cleanup_time": datetime.now().isoformat()}
        )
        
        self.active_archives.clear() 