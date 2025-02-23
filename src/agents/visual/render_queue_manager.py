from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
import asyncio
from pathlib import Path
import json
from datetime import datetime
import aiofiles

class RenderQueueManager(BaseVisualAgent):
    """Agent responsible for managing and scheduling render jobs."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.queue_config = {
            "output_dir": Path("outputs/render_queue"),
            "cache_dir": Path("cache/render_queue"),
            "queue_types": {
                "main": {
                    "max_concurrent": 5,
                    "priority_weights": {
                        "critical": 10,
                        "high": 5,
                        "normal": 2,
                        "low": 1
                    }
                },
                "preview": {
                    "max_concurrent": 3,
                    "priority_weights": {
                        "high": 3,
                        "normal": 1
                    }
                }
            },
            "scheduling_rules": {
                "time_slice": 300,  # 5 minutes
                "preemption_enabled": True,
                "fairness_threshold": 0.7
            }
        }
        self.job_queues: Dict[str, List[Dict[str, Any]]] = {
            "main": [],
            "preview": []
        }
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.job_history: List[Dict[str, Any]] = []
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "submit_job":
            return await self._submit_job(message)
        elif message.message_type == "update_job_status":
            return await self._update_job_status(message)
        elif message.message_type == "query_queue":
            return await self._query_queue(message)
        return None
    
    async def _submit_job(self, message: Message) -> Message:
        """Submit a new render job to the queue."""
        job_data = message.content.get("job_data", {})
        queue_type = message.content.get("queue_type", "main")
        job_id = message.content.get("job_id", "")
        
        try:
            submission_result = await self._process_job_submission(
                job_data, queue_type, job_id
            )
            
            return Message(
                message_id=f"submit_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="job_submitted",
                content={"submission_result": submission_result},
                context=message.context,
                metadata={"job_id": job_id}
            )
        except Exception as e:
            return Message(
                message_id=f"submit_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="job_submission_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_job_submission(self, job_data: Dict[str, Any],
                                    queue_type: str,
                                    job_id: str) -> Dict[str, Any]:
        """Process job submission and queue placement."""
        # Validate job data
        self._validate_job_data(job_data)
        
        # Create job record
        job_record = {
            "id": job_id,
            "data": job_data,
            "queue_type": queue_type,
            "priority": job_data.get("priority", "normal"),
            "status": "queued",
            "submitted_at": datetime.now().isoformat(),
            "estimated_duration": job_data.get("estimated_duration", 3600)
        }
        
        # Add to appropriate queue
        queue = self.job_queues[queue_type]
        insert_position = self._determine_queue_position(job_record, queue)
        queue.insert(insert_position, job_record)
        
        # Try to start job if possible
        started = await self._try_start_job(job_record)
        
        return {
            "job_id": job_id,
            "queue_position": insert_position + 1,
            "started": started,
            "estimated_start": self._estimate_start_time(job_record, queue)
        }
    
    def _determine_queue_position(self, job_record: Dict[str, Any],
                                queue: List[Dict[str, Any]]) -> int:
        """Determine optimal queue position based on priority and fairness."""
        priority_weight = self.queue_config["queue_types"][job_record["queue_type"]]["priority_weights"]
        job_weight = priority_weight[job_record["priority"]]
        
        # Find position based on priority
        for i, queued_job in enumerate(queue):
            queued_weight = priority_weight[queued_job["priority"]]
            if job_weight > queued_weight:
                return i
        
        return len(queue)
    
    async def _try_start_job(self, job_record: Dict[str, Any]) -> bool:
        """Try to start a job if resources are available."""
        queue_type = job_record["queue_type"]
        max_concurrent = self.queue_config["queue_types"][queue_type]["max_concurrent"]
        
        # Count current active jobs for this queue
        active_count = sum(1 for job in self.active_jobs.values()
                         if job["queue_type"] == queue_type)
        
        if active_count < max_concurrent:
            await self._start_job(job_record)
            return True
        
        return False
    
    async def _start_job(self, job_record: Dict[str, Any]) -> None:
        """Start a render job."""
        job_record["status"] = "running"
        job_record["started_at"] = datetime.now().isoformat()
        
        # Move to active jobs
        self.active_jobs[job_record["id"]] = job_record
        
        # Remove from queue
        queue = self.job_queues[job_record["queue_type"]]
        queue.remove(job_record)
        
        # Start job monitoring
        asyncio.create_task(self._monitor_job(job_record["id"]))
    
    async def _monitor_job(self, job_id: str) -> None:
        """Monitor job progress and handle completion."""
        job_record = self.active_jobs[job_id]
        
        try:
            # Monitor job status
            while True:
                status = await self._check_job_status(job_id)
                if status in ["completed", "failed"]:
                    await self._handle_job_completion(job_id, status)
                    break
                await asyncio.sleep(10)  # Check every 10 seconds
        except Exception as e:
            # Handle monitoring failure
            await self._handle_job_completion(job_id, "failed")
    
    def _create_queue_metadata(self, job_record: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for job queue entry."""
        return {
            "timestamp": datetime.now().isoformat(),
            "queue_type": job_record["queue_type"],
            "priority": job_record["priority"],
            "config": self.queue_config["queue_types"][job_record["queue_type"]]
        }
    
    async def initialize(self) -> None:
        """Initialize render queue manager resources."""
        self.queue_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.queue_config["cache_dir"].mkdir(parents=True, exist_ok=True)
        
        # Load saved queue state if exists
        await self._load_queue_state()
        
        # Start queue monitoring
        asyncio.create_task(self._monitor_queues())
    
    async def cleanup(self) -> None:
        """Cleanup render queue manager resources."""
        # Save queue state
        await self._save_queue_state()
        
        # Clear queues
        self.job_queues.clear()
        self.active_jobs.clear() 