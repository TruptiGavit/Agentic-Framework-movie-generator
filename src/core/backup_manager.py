from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
import asyncio
import json
import shutil
import zipfile
from datetime import datetime, timedelta
import hashlib

class BackupManager:
    """Manages project backups and recovery."""
    
    def __init__(self, backup_dir: str = "backups"):
        self.logger = logging.getLogger("movie_generator.backup")
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup settings
        self.settings = {
            "auto_backup_interval": 300,  # 5 minutes
            "max_backups_per_project": 5,
            "compression_level": 9,
            "include_temp_files": False
        }
        
        # Active backup tasks
        self._backup_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
    
    async def start(self):
        """Start backup manager."""
        self.is_running = True
        asyncio.create_task(self._auto_backup_loop())
    
    async def stop(self):
        """Stop backup manager."""
        self.is_running = False
        for task in self._backup_tasks.values():
            if not task.done():
                task.cancel()
    
    async def create_backup(self, project_id: str, backup_type: str = "auto") -> Dict[str, Any]:
        """Create a project backup."""
        try:
            # Generate backup ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"{project_id}_{backup_type}_{timestamp}"
            
            # Create backup directory
            backup_path = self.backup_dir / project_id / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Collect project files
            project_files = await self._collect_project_files(project_id)
            
            # Create backup archive
            archive_path = backup_path / f"{backup_id}.zip"
            metadata = await self._create_backup_archive(project_files, archive_path)
            
            # Cleanup old backups
            await self._cleanup_old_backups(project_id)
            
            return {
                "backup_id": backup_id,
                "timestamp": timestamp,
                "type": backup_type,
                "path": str(archive_path),
                "metadata": metadata
            }
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            raise
    
    async def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """Restore project from backup."""
        try:
            # Find backup archive
            project_id = backup_id.split('_')[0]
            archive_path = self.backup_dir / project_id / backup_id / f"{backup_id}.zip"
            
            if not archive_path.exists():
                raise FileNotFoundError(f"Backup archive not found: {archive_path}")
            
            # Verify backup integrity
            await self._verify_backup_integrity(archive_path)
            
            # Restore project files
            restore_path = await self._restore_backup_archive(archive_path)
            
            return {
                "success": True,
                "project_id": project_id,
                "restore_path": str(restore_path),
                "backup_id": backup_id
            }
            
        except Exception as e:
            self.logger.error(f"Backup restoration failed: {str(e)}")
            raise
    
    async def _auto_backup_loop(self):
        """Automatic backup loop."""
        while self.is_running:
            try:
                # Get active projects
                active_projects = await self._get_active_projects()
                
                # Create backups
                for project_id in active_projects:
                    if project_id not in self._backup_tasks or self._backup_tasks[project_id].done():
                        self._backup_tasks[project_id] = asyncio.create_task(
                            self.create_backup(project_id, "auto")
                        )
                
                await asyncio.sleep(self.settings["auto_backup_interval"])
                
            except Exception as e:
                self.logger.error(f"Auto backup error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _collect_project_files(self, project_id: str) -> List[Path]:
        """Collect all project files for backup."""
        project_dir = Path(f"projects/{project_id}")
        files = []
        
        for item in project_dir.rglob("*"):
            if item.is_file():
                if self.settings["include_temp_files"] or not self._is_temp_file(item):
                    files.append(item)
        
        return files
    
    async def _create_backup_archive(self, files: List[Path], archive_path: Path) -> Dict[str, Any]:
        """Create backup archive with metadata."""
        metadata = {
            "files": [],
            "checksums": {},
            "timestamp": datetime.now().isoformat()
        }
        
        with zipfile.ZipFile(archive_path, 'w', 
                           compression=zipfile.ZIP_DEFLATED,
                           compresslevel=self.settings["compression_level"]) as zf:
            for file in files:
                # Calculate checksum
                checksum = await self._calculate_checksum(file)
                metadata["checksums"][str(file)] = checksum
                
                # Add to archive
                zf.write(file)
                metadata["files"].append(str(file))
            
            # Add metadata to archive
            zf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
        
        return metadata
    
    async def _verify_backup_integrity(self, archive_path: Path):
        """Verify backup archive integrity."""
        with zipfile.ZipFile(archive_path, 'r') as zf:
            # Check archive integrity
            if zf.testzip() is not None:
                raise ValueError("Backup archive is corrupted")
            
            # Load and verify metadata
            try:
                metadata = json.loads(zf.read("backup_metadata.json"))
            except Exception:
                raise ValueError("Backup metadata is corrupted")
            
            # Verify all files are present
            for file_path in metadata["files"]:
                if file_path not in zf.namelist():
                    raise ValueError(f"Missing file in backup: {file_path}")
    
    @staticmethod
    async def _calculate_checksum(file_path: Path) -> str:
        """Calculate file checksum."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    @staticmethod
    def _is_temp_file(file_path: Path) -> bool:
        """Check if file is temporary."""
        return (
            file_path.name.startswith('.') or
            file_path.name.endswith('.tmp') or
            'temp' in file_path.parts
        ) 