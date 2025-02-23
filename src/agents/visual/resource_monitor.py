from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
import psutil
import GPUtil
import asyncio
from pathlib import Path
import json
from datetime import datetime
import aiofiles

class ResourceMonitor(BaseVisualAgent):
    """Agent responsible for monitoring and managing system resources."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.monitor_config = {
            "output_dir": Path("outputs/resource_monitor"),
            "log_dir": Path("logs/resources"),
            "thresholds": {
                "cpu": {
                    "warning": 80.0,  # percentage
                    "critical": 90.0
                },
                "memory": {
                    "warning": 75.0,  # percentage
                    "critical": 85.0
                },
                "gpu": {
                    "memory_warning": 80.0,  # percentage
                    "memory_critical": 90.0,
                    "temp_warning": 80.0,  # celsius
                    "temp_critical": 85.0
                },
                "disk": {
                    "warning": 85.0,  # percentage
                    "critical": 95.0
                }
            },
            "monitoring_interval": 5,  # seconds
            "history_retention": 3600  # seconds
        }
        self.resource_history: Dict[str, List[Dict[str, Any]]] = {
            "cpu": [],
            "memory": [],
            "gpu": [],
            "disk": []
        }
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "get_resource_status":
            return await self._get_resource_status(message)
        elif message.message_type == "check_resource_availability":
            return await self._check_resource_availability(message)
        elif message.message_type == "resource_alert":
            return await self._handle_resource_alert(message)
        return None
    
    async def _get_resource_status(self, message: Message) -> Message:
        """Get current resource status."""
        resource_type = message.content.get("resource_type", "all")
        
        try:
            status_result = await self._collect_resource_status(resource_type)
            
            return Message(
                message_id=f"status_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="resource_status",
                content={"status_result": status_result},
                context=message.context
            )
        except Exception as e:
            return Message(
                message_id=f"status_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="status_check_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _collect_resource_status(self, resource_type: str) -> Dict[str, Any]:
        """Collect current resource status information."""
        if resource_type == "all":
            return {
                "cpu": await self._get_cpu_status(),
                "memory": await self._get_memory_status(),
                "gpu": await self._get_gpu_status(),
                "disk": await self._get_disk_status(),
                "timestamp": datetime.now().isoformat()
            }
        else:
            status_methods = {
                "cpu": self._get_cpu_status,
                "memory": self._get_memory_status,
                "gpu": self._get_gpu_status,
                "disk": self._get_disk_status
            }
            return {
                resource_type: await status_methods[resource_type](),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _get_cpu_status(self) -> Dict[str, Any]:
        """Get CPU status information."""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        
        return {
            "usage_percent": cpu_percent,
            "average_usage": sum(cpu_percent) / len(cpu_percent),
            "frequency": {
                "current": cpu_freq.current,
                "min": cpu_freq.min,
                "max": cpu_freq.max
            },
            "core_count": psutil.cpu_count(),
            "status": self._determine_resource_status("cpu", sum(cpu_percent) / len(cpu_percent))
        }
    
    async def _get_memory_status(self) -> Dict[str, Any]:
        """Get memory status information."""
        memory = psutil.virtual_memory()
        
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent,
            "status": self._determine_resource_status("memory", memory.percent)
        }
    
    async def _get_gpu_status(self) -> Dict[str, Any]:
        """Get GPU status information."""
        try:
            gpus = GPUtil.getGPUs()
            gpu_stats = []
            
            for gpu in gpus:
                gpu_stat = {
                    "id": gpu.id,
                    "name": gpu.name,
                    "load": gpu.load * 100,
                    "memory": {
                        "total": gpu.memoryTotal,
                        "used": gpu.memoryUsed,
                        "free": gpu.memoryFree,
                        "percent": (gpu.memoryUsed / gpu.memoryTotal) * 100
                    },
                    "temperature": gpu.temperature,
                    "status": self._determine_gpu_status(gpu)
                }
                gpu_stats.append(gpu_stat)
            
            return {
                "gpus": gpu_stats,
                "available_count": len(gpus)
            }
        except Exception:
            return {"error": "No GPU information available"}
    
    async def _get_disk_status(self) -> Dict[str, Any]:
        """Get disk status information."""
        disk_stats = {}
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_stats[partition.mountpoint] = {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent,
                    "status": self._determine_resource_status("disk", usage.percent)
                }
            except Exception:
                continue
        
        return disk_stats
    
    def _determine_resource_status(self, resource_type: str, value: float) -> str:
        """Determine resource status based on thresholds."""
        thresholds = self.monitor_config["thresholds"][resource_type]
        
        if value >= thresholds["critical"]:
            return "critical"
        elif value >= thresholds["warning"]:
            return "warning"
        return "normal"
    
    def _determine_gpu_status(self, gpu: Any) -> str:
        """Determine GPU status based on memory and temperature."""
        thresholds = self.monitor_config["thresholds"]["gpu"]
        memory_percent = (gpu.memoryUsed / gpu.memoryTotal) * 100
        
        if (memory_percent >= thresholds["memory_critical"] or
            gpu.temperature >= thresholds["temp_critical"]):
            return "critical"
        elif (memory_percent >= thresholds["memory_warning"] or
              gpu.temperature >= thresholds["temp_warning"]):
            return "warning"
        return "normal"
    
    async def _monitor_resources(self) -> None:
        """Continuously monitor resource usage."""
        while True:
            try:
                status = await self._collect_resource_status("all")
                await self._update_resource_history(status)
                await self._check_resource_alerts(status)
                await asyncio.sleep(self.monitor_config["monitoring_interval"])
            except Exception as e:
                # Log monitoring error
                await self._log_error(f"Resource monitoring error: {str(e)}")
    
    async def _update_resource_history(self, status: Dict[str, Any]) -> None:
        """Update resource history and maintain retention period."""
        current_time = datetime.now()
        retention_limit = current_time.timestamp() - self.monitor_config["history_retention"]
        
        for resource_type in self.resource_history:
            # Add new status
            if resource_type in status:
                self.resource_history[resource_type].append({
                    "timestamp": current_time.isoformat(),
                    "data": status[resource_type]
                })
            
            # Remove old entries
            self.resource_history[resource_type] = [
                entry for entry in self.resource_history[resource_type]
                if datetime.fromisoformat(entry["timestamp"]).timestamp() > retention_limit
            ]
    
    async def initialize(self) -> None:
        """Initialize resource monitor."""
        self.monitor_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.monitor_config["log_dir"].mkdir(parents=True, exist_ok=True)
        
        # Start resource monitoring
        asyncio.create_task(self._monitor_resources())
    
    async def cleanup(self) -> None:
        """Cleanup resource monitor."""
        # Save final resource state
        await self._save_resource_state()
        
        # Clear history
        self.resource_history.clear()
        self.active_alerts.clear() 