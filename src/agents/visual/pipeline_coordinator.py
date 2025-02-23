from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from pathlib import Path
import json
from datetime import datetime
import asyncio
import aiofiles

class RenderPipelineCoordinator(BaseVisualAgent):
    """Agent responsible for coordinating the entire render pipeline."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.pipeline_config = {
            "output_dir": Path("outputs/pipeline"),
            "log_dir": Path("logs/pipeline"),
            "pipeline_stages": {
                "pre_render": [
                    "scene_interpretation",
                    "prompt_engineering",
                    "style_checking"
                ],
                "render": [
                    "image_generation",
                    "animation_control",
                    "camera_movement"
                ],
                "post_render": [
                    "quality_assurance",
                    "color_grading",
                    "format_adaptation"
                ],
                "delivery": [
                    "output_formatting",
                    "archive_management"
                ]
            },
            "stage_dependencies": {
                "scene_interpretation": [],
                "prompt_engineering": ["scene_interpretation"],
                "style_checking": ["scene_interpretation"],
                "image_generation": ["prompt_engineering", "style_checking"],
                "animation_control": ["image_generation"],
                "camera_movement": ["scene_interpretation"],
                "quality_assurance": ["image_generation", "animation_control"],
                "color_grading": ["quality_assurance"],
                "format_adaptation": ["color_grading"],
                "output_formatting": ["format_adaptation"],
                "archive_management": ["output_formatting"]
            }
        }
        self.active_pipelines: Dict[str, Dict[str, Any]] = {}
        self.stage_status: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "start_pipeline":
            return await self._start_pipeline(message)
        elif message.message_type == "stage_complete":
            return await self._handle_stage_completion(message)
        elif message.message_type == "pipeline_status":
            return await self._get_pipeline_status(message)
        return None
    
    async def _start_pipeline(self, message: Message) -> Message:
        """Start a new render pipeline."""
        pipeline_data = message.content.get("pipeline_data", {})
        pipeline_id = message.content.get("pipeline_id", "")
        
        try:
            pipeline_result = await self._initialize_pipeline(
                pipeline_data, pipeline_id
            )
            
            return Message(
                message_id=f"pipe_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="pipeline_started",
                content={"pipeline_result": pipeline_result},
                context=message.context,
                metadata={"pipeline_id": pipeline_id}
            )
        except Exception as e:
            return Message(
                message_id=f"pipe_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="pipeline_start_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _initialize_pipeline(self, pipeline_data: Dict[str, Any],
                                 pipeline_id: str) -> Dict[str, Any]:
        """Initialize pipeline and start first stage."""
        # Create pipeline record
        pipeline_record = {
            "id": pipeline_id,
            "data": pipeline_data,
            "status": "initializing",
            "current_stage": None,
            "completed_stages": [],
            "stage_results": {},
            "started_at": datetime.now().isoformat()
        }
        
        # Initialize stage tracking
        self.stage_status[pipeline_id] = {
            stage: {"status": "pending", "dependencies_met": False}
            for stage in self._get_all_stages()
        }
        
        # Store pipeline record
        self.active_pipelines[pipeline_id] = pipeline_record
        
        # Start initial stages (those with no dependencies)
        initial_stages = self._get_initial_stages()
        for stage in initial_stages:
            await self._start_stage(stage, pipeline_id)
        
        pipeline_record["status"] = "running"
        pipeline_record["current_stage"] = initial_stages
        
        return {
            "pipeline_id": pipeline_id,
            "initial_stages": initial_stages,
            "status": "running",
            "metadata": self._create_pipeline_metadata(pipeline_data)
        }
    
    async def _start_stage(self, stage: str, pipeline_id: str) -> None:
        """Start execution of a pipeline stage."""
        pipeline = self.active_pipelines[pipeline_id]
        stage_data = pipeline["data"].get("stages", {}).get(stage, {})
        
        # Update stage status
        self.stage_status[pipeline_id][stage]["status"] = "running"
        
        # Create and send stage initialization message
        stage_message = Message(
            message_id=f"stage_{pipeline_id}_{stage}",
            sender=self.agent_id,
            receiver=f"{stage}_agent",  # Assuming standardized agent naming
            message_type="initialize_stage",
            content={
                "stage_data": stage_data,
                "pipeline_context": self._get_pipeline_context(pipeline_id, stage)
            },
            metadata={"pipeline_id": pipeline_id, "stage": stage}
        )
        
        # Send message to stage agent
        await self._send_stage_message(stage_message)
    
    def _get_initial_stages(self) -> List[str]:
        """Get stages that can start immediately (no dependencies)."""
        return [
            stage for stage, deps in self.pipeline_config["stage_dependencies"].items()
            if not deps
        ]
    
    def _get_pipeline_context(self, pipeline_id: str, stage: str) -> Dict[str, Any]:
        """Get relevant context data for a pipeline stage."""
        pipeline = self.active_pipelines[pipeline_id]
        return {
            "pipeline_id": pipeline_id,
            "stage": stage,
            "previous_results": {
                prev_stage: pipeline["stage_results"].get(prev_stage, {})
                for prev_stage in self.pipeline_config["stage_dependencies"][stage]
            },
            "global_settings": pipeline["data"].get("settings", {})
        }
    
    async def _handle_stage_completion(self, message: Message) -> Message:
        """Handle completion of a pipeline stage."""
        pipeline_id = message.metadata.get("pipeline_id", "")
        stage = message.metadata.get("stage", "")
        stage_result = message.content.get("stage_result", {})
        
        try:
            completion_result = await self._process_stage_completion(
                pipeline_id, stage, stage_result
            )
            
            return Message(
                message_id=f"comp_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="completion_processed",
                content={"completion_result": completion_result},
                context=message.context,
                metadata={"pipeline_id": pipeline_id, "stage": stage}
            )
        except Exception as e:
            return Message(
                message_id=f"comp_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="completion_processing_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    def _create_pipeline_metadata(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for pipeline execution."""
        return {
            "timestamp": datetime.now().isoformat(),
            "stages": list(self._get_all_stages()),
            "dependencies": self.pipeline_config["stage_dependencies"],
            "configuration": pipeline_data.get("settings", {})
        }
    
    async def initialize(self) -> None:
        """Initialize pipeline coordinator resources."""
        self.pipeline_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.pipeline_config["log_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup pipeline coordinator resources."""
        # Save final pipeline states
        await self._save_pipeline_states()
        
        # Clear active pipelines and status
        self.active_pipelines.clear()
        self.stage_status.clear() 