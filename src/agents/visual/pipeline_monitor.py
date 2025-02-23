from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from pathlib import Path
import json
from datetime import datetime
import asyncio
import aiofiles
import time

class PipelineMonitor(BaseVisualAgent):
    """Agent responsible for monitoring render pipeline execution."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.monitor_config = {
            "output_dir": Path("outputs/pipeline_monitor"),
            "log_dir": Path("logs/pipeline_monitor"),
            "monitoring_intervals": {
                "pipeline_status": 5,    # seconds
                "resource_usage": 10,    # seconds
                "performance_metrics": 30 # seconds
            },
            "alert_thresholds": {
                "stage_duration": {
                    "warning": 3600,  # 1 hour
                    "critical": 7200  # 2 hours
                },
                "pipeline_duration": {
                    "warning": 14400,  # 4 hours
                    "critical": 28800  # 8 hours
                },
                "error_rate": {
                    "warning": 0.1,  # 10% error rate
                    "critical": 0.2  # 20% error rate
                }
            }
        }
        self.active_pipelines: Dict[str, Dict[str, Any]] = {}
        self.stage_metrics: Dict[str, Dict[str, List[float]]] = {}
        self.performance_history: List[Dict[str, Any]] = []
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "monitor_pipeline":
            return await self._monitor_pipeline(message)
        elif message.message_type == "pipeline_event":
            return await self._handle_pipeline_event(message)
        elif message.message_type == "get_pipeline_metrics":
            return await self._get_pipeline_metrics(message)
        return None
    
    async def _monitor_pipeline(self, message: Message) -> Message:
        """Start monitoring a pipeline."""
        pipeline_id = message.content.get("pipeline_id", "")
        monitoring_config = message.content.get("monitoring_config", {})
        
        try:
            monitoring_result = await self._start_pipeline_monitoring(
                pipeline_id, monitoring_config
            )
            
            return Message(
                message_id=f"mon_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="monitoring_started",
                content={"monitoring_result": monitoring_result},
                context=message.context,
                metadata={"pipeline_id": pipeline_id}
            )
        except Exception as e:
            return Message(
                message_id=f"mon_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="monitoring_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _start_pipeline_monitoring(self, pipeline_id: str,
                                       monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize and start pipeline monitoring."""
        # Create monitoring record
        monitor_record = {
            "pipeline_id": pipeline_id,
            "config": monitoring_config,
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "metrics": {
                "stage_durations": {},
                "error_counts": {},
                "resource_usage": [],
                "performance_metrics": []
            },
            "alerts": []
        }
        
        # Initialize metrics tracking
        self.stage_metrics[pipeline_id] = {
            "durations": [],
            "error_rates": [],
            "resource_usage": []
        }
        
        # Store monitoring record
        self.active_pipelines[pipeline_id] = monitor_record
        
        # Start monitoring tasks
        await self._start_monitoring_tasks(pipeline_id)
        
        return {
            "pipeline_id": pipeline_id,
            "monitoring_status": "active",
            "metrics_initialized": list(monitor_record["metrics"].keys())
        }
    
    async def _start_monitoring_tasks(self, pipeline_id: str) -> None:
        """Start monitoring tasks for pipeline."""
        tasks = [
            self._monitor_pipeline_status(pipeline_id),
            self._monitor_resource_usage(pipeline_id),
            self._monitor_performance_metrics(pipeline_id)
        ]
        
        # Start tasks
        for task in tasks:
            asyncio.create_task(task)
    
    async def _monitor_pipeline_status(self, pipeline_id: str) -> None:
        """Monitor pipeline execution status."""
        interval = self.monitor_config["monitoring_intervals"]["pipeline_status"]
        
        while pipeline_id in self.active_pipelines:
            try:
                status = await self._check_pipeline_status(pipeline_id)
                await self._update_pipeline_metrics(pipeline_id, "status", status)
                
                if status.get("status") == "completed":
                    await self._handle_pipeline_completion(pipeline_id)
                    break
                
                await asyncio.sleep(interval)
            except Exception as e:
                await self._log_monitoring_error(pipeline_id, "status_check", str(e))
    
    async def _monitor_resource_usage(self, pipeline_id: str) -> None:
        """Monitor resource usage during pipeline execution."""
        interval = self.monitor_config["monitoring_intervals"]["resource_usage"]
        
        while pipeline_id in self.active_pipelines:
            try:
                usage = await self._collect_resource_metrics(pipeline_id)
                await self._update_pipeline_metrics(pipeline_id, "resources", usage)
                
                # Check resource thresholds
                await self._check_resource_thresholds(pipeline_id, usage)
                
                await asyncio.sleep(interval)
            except Exception as e:
                await self._log_monitoring_error(pipeline_id, "resource_monitor", str(e))
    
    async def _update_pipeline_metrics(self, pipeline_id: str,
                                     metric_type: str,
                                     metrics: Dict[str, Any]) -> None:
        """Update pipeline metrics."""
        pipeline = self.active_pipelines[pipeline_id]
        timestamp = datetime.now().isoformat()
        
        # Add timestamp to metrics
        metrics["timestamp"] = timestamp
        
        # Update specific metric type
        if metric_type in pipeline["metrics"]:
            if isinstance(pipeline["metrics"][metric_type], list):
                pipeline["metrics"][metric_type].append(metrics)
            else:
                pipeline["metrics"][metric_type].update(metrics)
        
        # Update stage metrics if applicable
        if metric_type == "status" and "current_stage" in metrics:
            stage = metrics["current_stage"]
            if stage not in self.stage_metrics[pipeline_id]["durations"]:
                self.stage_metrics[pipeline_id]["durations"].append({
                    "stage": stage,
                    "start_time": timestamp
                })
    
    async def _check_resource_thresholds(self, pipeline_id: str,
                                       usage: Dict[str, Any]) -> None:
        """Check resource usage against thresholds."""
        thresholds = self.monitor_config["alert_thresholds"]
        
        # Check stage duration
        current_stage = self.active_pipelines[pipeline_id].get("current_stage")
        if current_stage:
            stage_start = self.stage_metrics[pipeline_id]["durations"][-1]["start_time"]
            duration = time.time() - datetime.fromisoformat(stage_start).timestamp()
            
            if duration > thresholds["stage_duration"]["critical"]:
                await self._create_alert(pipeline_id, "critical", 
                    f"Stage {current_stage} duration exceeded critical threshold")
            elif duration > thresholds["stage_duration"]["warning"]:
                await self._create_alert(pipeline_id, "warning",
                    f"Stage {current_stage} duration exceeded warning threshold")
    
    async def _create_alert(self, pipeline_id: str,
                          level: str,
                          message: str) -> None:
        """Create monitoring alert."""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "pipeline_id": pipeline_id
        }
        
        self.active_pipelines[pipeline_id]["alerts"].append(alert)
        await self._log_alert(alert)
    
    async def _log_alert(self, alert: Dict[str, Any]) -> None:
        """Log monitoring alert."""
        log_path = self.monitor_config["log_dir"] / "alerts.log"
        async with aiofiles.open(log_path, 'a') as f:
            await f.write(json.dumps(alert) + "\n")
    
    async def initialize(self) -> None:
        """Initialize pipeline monitor resources."""
        self.monitor_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.monitor_config["log_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup pipeline monitor resources."""
        # Save monitoring history
        for pipeline_id, pipeline in self.active_pipelines.items():
            self.performance_history.append({
                "pipeline_id": pipeline_id,
                "monitoring_data": pipeline,
                "archived_at": datetime.now().isoformat()
            })
        
        # Clear active monitoring
        self.active_pipelines.clear()
        self.stage_metrics.clear() 