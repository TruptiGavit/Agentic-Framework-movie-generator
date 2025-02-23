from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
import asyncio
from pathlib import Path
import json
from datetime import datetime
import aiofiles

class RenderFarmManager(BaseVisualAgent):
    """Agent responsible for managing distributed rendering tasks."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.farm_config = {
            "output_dir": Path("outputs/render_farm"),
            "temp_dir": Path("temp/render_farm"),
            "nodes_dir": Path("config/render_nodes"),
            "node_configs": {
                "default": {
                    "max_tasks": 4,
                    "priority_levels": ["high", "medium", "low"],
                    "resource_limits": {
                        "cpu_percent": 80,
                        "memory_percent": 70,
                        "gpu_memory": 0.8
                    }
                }
            },
            "task_priorities": {
                "high": {"weight": 3, "timeout": 7200},
                "medium": {"weight": 2, "timeout": 14400},
                "low": {"weight": 1, "timeout": 28800}
            }
        }
        self.active_nodes: Dict[str, Dict[str, Any]] = {}
        self.render_queue: Dict[str, List[Dict[str, Any]]] = {
            "high": [],
            "medium": [],
            "low": []
        }
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "submit_render_task":
            return await self._submit_render_task(message)
        elif message.message_type == "node_status_update":
            return await self._handle_node_status(message)
        elif message.message_type == "task_status_update":
            return await self._handle_task_status(message)
        return None
    
    async def _submit_render_task(self, message: Message) -> Message:
        """Submit a new render task to the farm."""
        task_data = message.content.get("task_data", {})
        priority = message.content.get("priority", "medium")
        task_id = message.content.get("task_id", "")
        
        try:
            submission_result = await self._process_task_submission(
                task_data, priority, task_id
            )
            
            return Message(
                message_id=f"submit_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="task_submitted",
                content={"submission_result": submission_result},
                context=message.context,
                metadata={"task_id": task_id}
            )
        except Exception as e:
            return Message(
                message_id=f"submit_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="task_submission_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_task_submission(self, task_data: Dict[str, Any],
                                     priority: str,
                                     task_id: str) -> Dict[str, Any]:
        """Process render task submission."""
        # Validate task data
        self._validate_task_data(task_data)
        
        # Create task record
        task_record = {
            "id": task_id,
            "data": task_data,
            "priority": priority,
            "status": "pending",
            "submitted_at": datetime.now().isoformat(),
            "config": self.farm_config["task_priorities"][priority]
        }
        
        # Add to queue
        self.render_queue[priority].append(task_record)
        
        # Try to assign task immediately if possible
        assigned_node = await self._try_assign_task(task_record)
        
        return {
            "task_id": task_id,
            "queue_position": len(self.render_queue[priority]),
            "assigned_node": assigned_node,
            "estimated_start": self._estimate_start_time(task_record)
        }
    
    async def _try_assign_task(self, task_record: Dict[str, Any]) -> Optional[str]:
        """Try to assign task to an available node."""
        available_nodes = self._get_available_nodes()
        
        for node_id, node_info in available_nodes.items():
            if self._can_handle_task(node_info, task_record):
                await self._assign_task_to_node(task_record, node_id)
                return node_id
        
        return None
    
    def _get_available_nodes(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available render nodes."""
        available = {}
        
        for node_id, node_info in self.active_nodes.items():
            if (node_info["status"] == "online" and
                len(node_info["current_tasks"]) < node_info["config"]["max_tasks"]):
                available[node_id] = node_info
        
        return available
    
    def _can_handle_task(self, node_info: Dict[str, Any],
                        task_record: Dict[str, Any]) -> bool:
        """Check if node can handle the task."""
        # Check resource requirements
        task_resources = task_record["data"].get("resource_requirements", {})
        node_resources = node_info["resources"]
        
        for resource, required in task_resources.items():
            if resource not in node_resources:
                return False
            if node_resources[resource] < required:
                return False
        
        return True
    
    async def _assign_task_to_node(self, task_record: Dict[str, Any],
                                 node_id: str) -> None:
        """Assign task to render node."""
        # Update task status
        task_record["status"] = "assigned"
        task_record["assigned_node"] = node_id
        task_record["assigned_at"] = datetime.now().isoformat()
        
        # Update node record
        self.active_nodes[node_id]["current_tasks"].append(task_record["id"])
        
        # Move task to active tasks
        self.active_tasks[task_record["id"]] = task_record
        
        # Remove from queue
        queue = self.render_queue[task_record["priority"]]
        queue.remove(task_record)
        
        # Notify node
        await self._notify_node_of_assignment(node_id, task_record)
    
    async def _handle_node_status(self, message: Message) -> Message:
        """Handle node status update."""
        node_id = message.content.get("node_id", "")
        status_data = message.content.get("status_data", {})
        
        try:
            update_result = await self._process_node_status(node_id, status_data)
            
            return Message(
                message_id=f"status_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="node_status_processed",
                content={"update_result": update_result},
                context=message.context,
                metadata={"node_id": node_id}
            )
        except Exception as e:
            return Message(
                message_id=f"status_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="node_status_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_node_status(self, node_id: str,
                                 status_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process node status update."""
        if node_id not in self.active_nodes:
            self.active_nodes[node_id] = {
                "id": node_id,
                "config": self.farm_config["node_configs"]["default"].copy(),
                "current_tasks": [],
                "status": "unknown"
            }
        
        node_record = self.active_nodes[node_id]
        node_record.update({
            "status": status_data.get("status", "unknown"),
            "resources": status_data.get("resources", {}),
            "last_update": datetime.now().isoformat()
        })
        
        # Check for completed tasks
        completed_tasks = status_data.get("completed_tasks", [])
        for task_id in completed_tasks:
            await self._handle_task_completion(task_id, node_id)
        
        return {
            "node_id": node_id,
            "status": node_record["status"],
            "active_tasks": len(node_record["current_tasks"])
        }
    
    async def initialize(self) -> None:
        """Initialize render farm manager resources."""
        self.farm_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.farm_config["temp_dir"].mkdir(parents=True, exist_ok=True)
        self.farm_config["nodes_dir"].mkdir(parents=True, exist_ok=True)
        
        # Load node configurations
        await self._load_node_configs()
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_tasks())
    
    async def cleanup(self) -> None:
        """Cleanup render farm manager resources."""
        # Save final state
        await self._save_farm_state()
        
        # Clear active records
        self.active_nodes.clear()
        self.active_tasks.clear()
        for queue in self.render_queue.values():
            queue.clear() 