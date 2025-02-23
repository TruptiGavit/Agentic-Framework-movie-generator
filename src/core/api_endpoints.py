from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
import logging
from datetime import datetime

from src.core.agent_manager import AgentManager
from src.core.task_scheduler import TaskScheduler
from src.core.system_monitor import SystemMonitor
from src.core.message_bus import MessageBus

class GenerationRequest(BaseModel):
    """Model for generation request."""
    scene_description: str
    style_preferences: Dict[str, Any]
    output_settings: Dict[str, Any]
    priority: int = 0

class TaskRequest(BaseModel):
    """Model for task request."""
    task_type: str
    payload: Dict[str, Any]
    scheduled_time: Optional[datetime] = None
    priority: int = 0

app = FastAPI(title="AI Movie Generation API")
logger = logging.getLogger(__name__)

class APIEndpoints:
    """API endpoints for system interaction."""
    
    def __init__(self, 
                 agent_manager: AgentManager,
                 task_scheduler: TaskScheduler,
                 system_monitor: SystemMonitor,
                 message_bus: MessageBus):
        self.agent_manager = agent_manager
        self.task_scheduler = task_scheduler
        self.system_monitor = system_monitor
        self.message_bus = message_bus
        self.setup_routes()
    
    def setup_routes(self):
        """Set up API routes."""
        
        @app.post("/generate")
        async def generate_content(request: GenerationRequest, 
                                 background_tasks: BackgroundTasks):
            """Start content generation process."""
            try:
                # Create generation task
                task_id = await self._create_generation_task(request)
                
                # Schedule task execution
                background_tasks.add_task(self._execute_generation, task_id)
                
                return {"task_id": task_id, "status": "scheduled"}
            except Exception as e:
                logger.error(f"Generation request failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/status/{task_id}")
        async def get_task_status(task_id: str):
            """Get status of a task."""
            status = self.task_scheduler.get_task_status(task_id)
            if status is None:
                raise HTTPException(status_code=404, detail="Task not found")
            return {"task_id": task_id, "status": status}
        
        @app.get("/system/metrics")
        async def get_system_metrics():
            """Get current system metrics."""
            metrics = self.system_monitor.get_current_metrics()
            if metrics is None:
                raise HTTPException(status_code=503, 
                                  detail="System metrics not available")
            return metrics
        
        @app.get("/system/alerts")
        async def get_system_alerts():
            """Get active system alerts."""
            return {"alerts": self.system_monitor.get_active_alerts()}
        
        @app.post("/tasks")
        async def schedule_task(request: TaskRequest):
            """Schedule a new task."""
            try:
                task_id = await self._schedule_custom_task(request)
                return {"task_id": task_id, "status": "scheduled"}
            except Exception as e:
                logger.error(f"Task scheduling failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.delete("/tasks/{task_id}")
        async def cancel_task(task_id: str):
            """Cancel a scheduled task."""
            try:
                await self.task_scheduler.cancel_task(task_id)
                return {"status": "cancelled"}
            except Exception as e:
                logger.error(f"Task cancellation failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _create_generation_task(self, request: GenerationRequest) -> str:
        """Create a generation task from request."""
        # Create task for scene interpretation
        scene_task = await self.task_scheduler.schedule_task(Task(
            task_id="",  # Will be generated
            agent_id="scene_interpreter",
            task_type="interpret_scene",
            payload={"scene_description": request.scene_description},
            scheduled_time=datetime.now(),
            priority=request.priority
        ))
        
        # Create subsequent tasks with dependencies
        style_task = await self.task_scheduler.schedule_task(Task(
            task_id="",
            agent_id="style_checker",
            task_type="check_style",
            payload={"style_preferences": request.style_preferences},
            scheduled_time=datetime.now(),
            priority=request.priority,
            dependencies=[scene_task]
        ))
        
        return scene_task  # Return initial task ID for tracking
    
    async def _execute_generation(self, task_id: str):
        """Execute generation pipeline."""
        try:
            # Monitor task execution
            while True:
                status = self.task_scheduler.get_task_status(task_id)
                if status in ["completed", "failed"]:
                    break
                await asyncio.sleep(1)
            
            if status == "failed":
                logger.error(f"Generation task {task_id} failed")
                
        except Exception as e:
            logger.error(f"Error executing generation: {str(e)}")
    
    async def _schedule_custom_task(self, request: TaskRequest) -> str:
        """Schedule a custom task."""
        task = Task(
            task_id="",
            agent_id="custom",
            task_type=request.task_type,
            payload=request.payload,
            scheduled_time=request.scheduled_time or datetime.now(),
            priority=request.priority
        )
        return await self.task_scheduler.schedule_task(task) 