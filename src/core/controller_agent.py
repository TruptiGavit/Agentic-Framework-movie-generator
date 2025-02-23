from typing import Dict, Any, Optional, List
from src.core.base_agent import BaseAgent, Message
from src.core.message_bus import MessageBus
from src.core.task_scheduler import TaskScheduler
from src.core.error_handler import ErrorHandler, ErrorContext
from datetime import datetime
import logging
import json
from pathlib import Path
import asyncio

class ControllerAgent(BaseAgent):
    """Main orchestrator for the AI Movie Generation system."""
    
    def __init__(self, agent_id: str,
                 message_bus: MessageBus,
                 task_scheduler: TaskScheduler,
                 error_handler: ErrorHandler):
        super().__init__(agent_id)
        self.message_bus = message_bus
        self.task_scheduler = task_scheduler
        self.error_handler = error_handler
        self.logger = logging.getLogger(__name__)
        
        # Project state management
        self.active_projects: Dict[str, Dict[str, Any]] = {}
        self.project_queues: Dict[str, List[Dict[str, Any]]] = {}
        self.context_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Pipeline stages
        self.pipeline_stages = {
            "analysis": ["analyze_requirements", "determine_style", "create_brief"],
            "story": ["generate_plot", "plan_scenes", "develop_characters"],
            "visual": ["interpret_scenes", "generate_images", "create_animations"],
            "audio": ["compose_music", "generate_speech", "mix_audio"],
            "quality": ["check_continuity", "validate_technical", "moderate_content"]
        }
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        try:
            if message.message_type == "create_project":
                return await self._handle_project_creation(message)
            elif message.message_type == "generate_scene":
                return await self._handle_scene_generation(message)
            elif message.message_type == "update_project":
                return await self._handle_project_update(message)
            elif message.message_type == "stage_complete":
                return await self._handle_stage_completion(message)
        except Exception as e:
            await self._handle_error(e, "process_message")
        return None
    
    async def _handle_project_creation(self, message: Message) -> Message:
        """Handle new project creation request."""
        project_data = message.content.get("project_data", {})
        project_id = project_data.get("project_id", str(datetime.now().timestamp()))
        
        try:
            # Initialize project state
            self.active_projects[project_id] = {
                "status": "initializing",
                "data": project_data,
                "current_stage": "analysis",
                "assets": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            }
            
            # Create project queue
            self.project_queues[project_id] = []
            
            # Start analysis stage
            await self._start_analysis_stage(project_id, project_data)
            
            return Message(
                message_id=f"proj_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="project_created",
                content={"project_id": project_id},
                context={"project_id": project_id}
            )
            
        except Exception as e:
            await self._handle_error(e, "project_creation")
            raise
    
    async def _start_analysis_stage(self, project_id: str, project_data: Dict[str, Any]):
        """Start the analysis stage of the pipeline."""
        analysis_tasks = [
            {
                "task_type": task,
                "agent_id": "analysis_agent",
                "payload": {
                    "project_id": project_id,
                    "project_data": project_data
                }
            }
            for task in self.pipeline_stages["analysis"]
        ]
        
        for task in analysis_tasks:
            await self.task_scheduler.schedule_task(task)
    
    async def _handle_scene_generation(self, message: Message) -> Message:
        """Handle scene generation request."""
        scene_data = message.content.get("scene_data", {})
        project_id = message.context.get("project_id")
        
        try:
            # Validate project exists
            if project_id not in self.active_projects:
                raise ValueError(f"Project {project_id} not found")
            
            # Create scene generation pipeline
            pipeline = await self._create_scene_pipeline(scene_data, project_id)
            
            # Schedule scene generation tasks
            for task in pipeline:
                await self.task_scheduler.schedule_task(task)
            
            return Message(
                message_id=f"scene_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="scene_generation_started",
                content={"scene_id": scene_data.get("scene_id")},
                context={"project_id": project_id}
            )
            
        except Exception as e:
            await self._handle_error(e, "scene_generation")
            raise
    
    async def _create_scene_pipeline(self, scene_data: Dict[str, Any],
                                   project_id: str) -> List[Dict[str, Any]]:
        """Create the scene generation pipeline tasks."""
        pipeline = []
        
        # Scene interpretation task
        pipeline.append({
            "task_type": "interpret_scene",
            "agent_id": "scene_interpreter",
            "payload": {"scene_data": scene_data}
        })
        
        # Prompt engineering task
        pipeline.append({
            "task_type": "generate_prompt",
            "agent_id": "prompt_engineer",
            "payload": {"scene_data": scene_data},
            "dependencies": [pipeline[-1]["task_id"]]
        })
        
        # Image generation task
        pipeline.append({
            "task_type": "generate_image",
            "agent_id": "image_generator",
            "payload": {"scene_data": scene_data},
            "dependencies": [pipeline[-1]["task_id"]]
        })
        
        return pipeline
    
    async def _handle_stage_completion(self, message: Message) -> Optional[Message]:
        """Handle stage completion notification."""
        project_id = message.context.get("project_id")
        stage = message.content.get("stage")
        results = message.content.get("results", {})
        
        try:
            # Update project state
            project = self.active_projects.get(project_id)
            if project:
                project["status"] = "in_progress"
                project["metadata"]["updated_at"] = datetime.now().isoformat()
                
                # Store results
                if "assets" not in project:
                    project["assets"] = {}
                project["assets"][stage] = results
                
                # Determine next stage
                next_stage = self._determine_next_stage(project, stage)
                if next_stage:
                    await self._start_stage(project_id, next_stage)
                else:
                    project["status"] = "completed"
                    
            return Message(
                message_id=f"comp_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="stage_processed",
                content={"status": project["status"]},
                context={"project_id": project_id}
            )
            
        except Exception as e:
            await self._handle_error(e, "stage_completion")
            raise
    
    def _determine_next_stage(self, project: Dict[str, Any], 
                            current_stage: str) -> Optional[str]:
        """Determine the next pipeline stage."""
        stages = list(self.pipeline_stages.keys())
        try:
            current_index = stages.index(current_stage)
            if current_index < len(stages) - 1:
                return stages[current_index + 1]
        except ValueError:
            pass
        return None
    
    async def _handle_error(self, error: Exception, operation: str):
        """Handle errors in the controller."""
        context = ErrorContext(
            component="controller",
            operation=operation,
            timestamp=datetime.now(),
            details={},
            traceback=error.__traceback__.tb_frame.f_code.co_filename
        )
        await self.error_handler.handle_error(error, context) 