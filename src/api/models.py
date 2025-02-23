from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class ProjectType(str, Enum):
    ANIMATION = "animation"
    LIVE_ACTION = "live_action"
    DOCUMENTARY = "documentary"

class ProjectCreate(BaseModel):
    """Project creation request model."""
    title: str
    description: str
    type: ProjectType
    requirements: Dict[str, Any]
    story_elements: Optional[Dict[str, Any]]
    technical_requirements: Optional[Dict[str, Any]]

class ProjectStatus(BaseModel):
    """Project status response model."""
    status: str
    current_stage: str
    progress: float
    estimated_completion: Optional[datetime]
    current_task: Optional[str]
    errors: List[str] = Field(default_factory=list)

class ProjectUpdate(BaseModel):
    """Project update request model."""
    requirements: Optional[Dict[str, Any]]
    story_elements: Optional[Dict[str, Any]]
    technical_requirements: Optional[Dict[str, Any]]

class ExportSettings(BaseModel):
    """Export settings model."""
    format: str
    output_path: str
    resolution: Optional[str] = "1920x1080"
    framerate: Optional[int] = 30
    quality: Optional[str] = "high"

class BackupCreate(BaseModel):
    """Backup creation request model."""
    type: str = "manual"
    include_temp_files: bool = False

class SystemMetrics(BaseModel):
    """System metrics response model."""
    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    gpu: Dict[str, Any]
    storage: Dict[str, Any]
    network: Dict[str, Any] 