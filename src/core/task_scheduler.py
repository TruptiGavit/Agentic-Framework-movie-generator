from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging
import uuid

@dataclass
class Task:
    """Represents a scheduled task."""
    task_id: str
    agent_id: str
    task_type: str
    payload: Any
    scheduled_time: datetime
    priority: int = 0
    dependencies: List[str] = None
    status: str = "pending"
    retries: int = 0
    max_retries: int = 3

class TaskScheduler:
    """Manages task scheduling and resource allocation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Performance settings
        self.performance_settings = {
            "max_concurrent_tasks": 10,
            "task_timeout": 300,  # seconds
            "retry_limit": 3
        }
        
        # Pipeline configurations
        self.pipeline_configs: Dict[str, Dict[str, Any]] = {}
        
        # Resource settings
        self.gpu_settings = {
            "allocation_strategy": "dynamic",
            "memory_buffer": "2GB",
            "enabled": True
        }
        
        self.cpu_settings = {
            "max_threads": 8,
            "priority": "normal"
        }
        
        # Cleanup settings
        self.cleanup_interval = 3600  # seconds
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Active tasks
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Task queue
        self.task_queue: asyncio.Queue = asyncio.Queue()
        
        # Scheduler state
        self.is_running = False
        
        # Task status tracking
        self.completed_tasks: List[str] = []
        self.failed_tasks: List[str] = []
        
        # Task handlers
        self.task_handlers: Dict[str, Callable] = {}
    
    async def start(self):
        """Start the task scheduler."""
        self.is_running = True
        asyncio.create_task(self._process_task_queue())
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def stop(self):
        """Stop the task scheduler."""
        self.is_running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Cancel all active tasks
        for task in self.active_tasks.values():
            if not task.done():
                task.cancel()
    
    async def update_settings(self, settings: Dict[str, Any]):
        """Update scheduler performance settings."""
        self.logger.info("Updating scheduler settings...")
        
        if "max_concurrent_tasks" in settings:
            self.performance_settings["max_concurrent_tasks"] = settings["max_concurrent_tasks"]
        
        if "task_timeout" in settings:
            self.performance_settings["task_timeout"] = settings["task_timeout"]
        
        if "retry_limit" in settings:
            self.performance_settings["retry_limit"] = settings["retry_limit"]
    
    async def update_pipeline_config(self, pipeline_type: str, config: Dict[str, Any]):
        """Update pipeline configuration."""
        self.logger.info(f"Updating pipeline configuration for {pipeline_type}")
        
        self.pipeline_configs[pipeline_type] = config
        
        # Update existing tasks with new timeouts
        for stage in config.get("stages", []):
            stage_name = stage.get("name")
            timeout = stage.get("timeout")
            if stage_name and timeout:
                await self._update_stage_timeouts(pipeline_type, stage_name, timeout)
    
    async def update_gpu_settings(self, settings: Dict[str, Any]):
        """Update GPU resource settings."""
        self.logger.info("Updating GPU settings...")
        
        if "allocation_strategy" in settings:
            self.gpu_settings["allocation_strategy"] = settings["allocation_strategy"]
        
        if "memory_buffer" in settings:
            self.gpu_settings["memory_buffer"] = settings["memory_buffer"]
        
        if "enabled" in settings:
            self.gpu_settings["enabled"] = settings["enabled"]
            
        # Adjust active tasks based on new settings
        await self._rebalance_gpu_resources()
    
    async def update_cpu_settings(self, settings: Dict[str, Any]):
        """Update CPU resource settings."""
        self.logger.info("Updating CPU settings...")
        
        if "max_threads" in settings:
            self.cpu_settings["max_threads"] = settings["max_threads"]
        
        if "priority" in settings:
            self.cpu_settings["priority"] = settings["priority"]
            
        # Adjust active tasks based on new settings
        await self._rebalance_cpu_resources()
    
    async def update_cleanup_interval(self, interval: int):
        """Update cleanup interval."""
        self.logger.info(f"Updating cleanup interval to {interval} seconds")
        
        self.cleanup_interval = interval
        
        # Restart cleanup task with new interval
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _update_stage_timeouts(self, pipeline_type: str, stage_name: str, timeout: int):
        """Update timeouts for pipeline stage tasks."""
        for task_id, task in self.active_tasks.items():
            if (task_id.startswith(f"{pipeline_type}_{stage_name}") and 
                not task.done()):
                # Create new task with updated timeout
                new_task = asyncio.create_task(
                    asyncio.wait_for(task, timeout)
                )
                self.active_tasks[task_id] = new_task
                task.cancel()
    
    async def _rebalance_gpu_resources(self):
        """Rebalance GPU resource allocation."""
        if not self.gpu_settings["enabled"]:
            # Move GPU tasks to CPU
            await self._migrate_gpu_tasks_to_cpu()
        else:
            # Reallocate GPU resources based on new settings
            await self._reallocate_gpu_resources()
    
    async def _rebalance_cpu_resources(self):
        """Rebalance CPU resource allocation."""
        # Adjust thread pool
        await self._adjust_thread_pool()
        
        # Update task priorities
        await self._update_task_priorities()
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of completed tasks and temporary resources."""
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_completed_tasks()
                await self._cleanup_temp_resources()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic cleanup: {str(e)}")
                await asyncio.sleep(60)  # Retry after delay
    
    async def schedule_task(self, task: Task) -> str:
        """Schedule a new task."""
        if not task.task_id:
            task.task_id = str(uuid.uuid4())
        
        # Check dependencies
        if task.dependencies:
            for dep_id in task.dependencies:
                if dep_id not in self.completed_tasks:
                    raise ValueError(f"Dependency {dep_id} not completed")
        
        self.tasks[task.task_id] = task
        await self.task_queue.put((task.priority, task))
        
        return task.task_id
    
    async def cancel_task(self, task_id: str):
        """Cancel a scheduled task."""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            del self.active_tasks[task_id]
        if task_id in self.tasks:
            self.tasks[task_id].status = "cancelled"
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """Register a handler for a task type."""
        self.task_handlers[task_type] = handler
    
    async def _process_tasks(self):
        """Process tasks from the queue."""
        while self.is_running:
            try:
                _, task = await self.task_queue.get()
                if self._should_execute_task(task):
                    await self._execute_task(task)
                else:
                    # Reschedule if not ready
                    await self.task_queue.put((task.priority, task))
                await asyncio.sleep(0.1)  # Prevent CPU overload
            except Exception as e:
                self.logger.error(f"Error processing task: {str(e)}")
    
    def _should_execute_task(self, task: Task) -> bool:
        """Check if a task should be executed."""
        # Check time
        if task.scheduled_time > datetime.now():
            return False
        
        # Check dependencies
        if task.dependencies:
            return all(dep in self.completed_tasks for dep in task.dependencies)
        
        return True
    
    async def _execute_task(self, task: Task):
        """Execute a task."""
        try:
            task.status = "running"
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler for task type {task.task_type}")
            
            # Create and store task coroutine
            coro = handler(task.payload)
            self.active_tasks[task.task_id] = asyncio.create_task(coro)
            
            # Wait for completion
            await self.active_tasks[task.task_id]
            
            # Update task status
            task.status = "completed"
            self.completed_tasks.append(task.task_id)
            
        except Exception as e:
            self.logger.error(f"Task {task.task_id} failed: {str(e)}")
            task.retries += 1
            if task.retries < task.max_retries:
                # Reschedule with delay
                task.scheduled_time = datetime.now() + timedelta(seconds=5)
                await self.task_queue.put((task.priority, task))
            else:
                task.status = "failed"
                self.failed_tasks.append(task.task_id)
        finally:
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get the status of a task."""
        if task_id in self.tasks:
            return self.tasks[task_id].status
        return None 