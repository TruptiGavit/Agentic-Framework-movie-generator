from typing import Optional, Dict, Any, List
from src.agents.quality.base_quality_agent import BaseQualityAgent
from src.core.base_agent import Message
import asyncio
from datetime import datetime
import json
from pathlib import Path

class QualityDashboard(BaseQualityAgent):
    """Agent responsible for aggregating and presenting quality control data."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.quality_reports: Dict[str, Any] = {}
        self.active_monitors: Dict[str, Any] = {}
        self.report_history: List[Dict[str, Any]] = []
        self.dashboard_config = {
            "update_interval": 5.0,  # seconds
            "max_history": 1000,
            "report_path": Path("reports/quality")
        }
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "update_dashboard":
            return await self._update_dashboard(message)
        elif message.message_type == "get_quality_report":
            return await self._get_quality_report(message)
        elif message.message_type == "start_monitoring":
            return await self._start_monitoring(message)
        return None
    
    async def _update_dashboard(self, message: Message) -> Message:
        """Update dashboard with new quality control data."""
        quality_data = message.content.get("quality_data", {})
        update_type = message.content.get("update_type", "all")
        
        dashboard_update = await self._process_quality_update(quality_data, update_type)
        
        return Message(
            message_id=f"dash_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="dashboard_updated",
            content={"dashboard_update": dashboard_update},
            context=message.context,
            metadata={"update_type": update_type}
        )
    
    async def _process_quality_update(self, quality_data: Dict[str, Any], update_type: str) -> Dict[str, Any]:
        """Process and organize quality control data."""
        timestamp = datetime.now().isoformat()
        
        # Process different types of quality data
        processed_data = {
            "timestamp": timestamp,
            "technical": self._process_technical_data(quality_data.get("technical", {})),
            "content": self._process_content_data(quality_data.get("content", {})),
            "performance": self._process_performance_data(quality_data.get("performance", {})),
            "summary": self._generate_quality_summary(quality_data)
        }
        
        # Update history
        self.report_history.append(processed_data)
        if len(self.report_history) > self.dashboard_config["max_history"]:
            self.report_history.pop(0)
        
        # Save report
        await self._save_quality_report(processed_data)
        
        return processed_data
    
    def _process_technical_data(self, technical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process technical validation data."""
        return {
            "validation_status": self._aggregate_validation_status(technical_data),
            "issues_summary": self._summarize_issues(technical_data.get("issues", [])),
            "metrics": {
                "polygon_count": technical_data.get("polygon_count", 0),
                "texture_memory": technical_data.get("texture_memory", 0),
                "render_settings": technical_data.get("render_settings", {})
            }
        }
    
    def _process_content_data(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process content moderation data."""
        return {
            "moderation_status": content_data.get("status", "unknown"),
            "age_rating": content_data.get("age_rating", "unrated"),
            "content_warnings": content_data.get("warnings", []),
            "cultural_sensitivity": content_data.get("cultural_sensitivity", {})
        }
    
    def _process_performance_data(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process performance optimization data."""
        return {
            "optimization_status": performance_data.get("status", "unknown"),
            "resource_usage": {
                "memory": performance_data.get("memory_usage", {}),
                "gpu": performance_data.get("gpu_usage", {}),
                "render_time": performance_data.get("render_time", 0)
            },
            "optimizations": performance_data.get("optimizations", [])
        }
    
    def _generate_quality_summary(self, quality_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall quality summary."""
        total_issues = sum(len(data.get("issues", [])) for data in quality_data.values())
        critical_issues = sum(
            len([i for i in data.get("issues", []) if i.get("severity") == "high"])
            for data in quality_data.values()
        )
        
        return {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "overall_status": "pass" if critical_issues == 0 else "fail",
            "recommendations": self._generate_recommendations(quality_data)
        }
    
    def _generate_recommendations(self, quality_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on quality data."""
        recommendations = []
        
        # Analyze issues and generate specific recommendations
        for category, data in quality_data.items():
            for issue in data.get("issues", []):
                if issue.get("severity") in ["high", "medium"]:
                    recommendations.append({
                        "category": category,
                        "priority": issue["severity"],
                        "description": issue.get("description", ""),
                        "action": self._suggest_action(issue)
                    })
        
        return sorted(recommendations, key=lambda x: x["priority"] == "high", reverse=True)
    
    async def _save_quality_report(self, report_data: Dict[str, Any]) -> None:
        """Save quality report to file."""
        try:
            self.dashboard_config["report_path"].mkdir(parents=True, exist_ok=True)
            report_file = self.dashboard_config["report_path"] / f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            async with aiofiles.open(report_file, 'w') as f:
                await f.write(json.dumps(report_data, indent=2))
        except Exception as e:
            print(f"Error saving quality report: {str(e)}")
    
    async def _start_monitoring(self, message: Message) -> Message:
        """Start continuous quality monitoring."""
        monitor_config = message.content.get("monitor_config", {})
        
        # Start monitoring tasks
        monitor_task = asyncio.create_task(self._monitor_quality(monitor_config))
        self.active_monitors[message.message_id] = monitor_task
        
        return Message(
            message_id=f"mon_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="monitoring_started",
            content={"monitor_id": message.message_id},
            context=message.context
        )
    
    async def _monitor_quality(self, config: Dict[str, Any]) -> None:
        """Continuous quality monitoring loop."""
        while True:
            try:
                # Collect quality metrics
                quality_data = await self._collect_quality_metrics()
                
                # Process and update dashboard
                await self._process_quality_update(quality_data, "monitoring")
                
                # Wait for next update interval
                await asyncio.sleep(self.dashboard_config["update_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in quality monitoring: {str(e)}")
                await asyncio.sleep(self.dashboard_config["update_interval"])
    
    async def initialize(self) -> None:
        """Initialize dashboard resources."""
        self.dashboard_config["report_path"].mkdir(parents=True, exist_ok=True)
        # Load any saved reports or configuration
    
    async def cleanup(self) -> None:
        """Cleanup dashboard resources."""
        # Cancel all active monitoring tasks
        for monitor in self.active_monitors.values():
            monitor.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.active_monitors.values(), return_exceptions=True)
        
        self.quality_reports.clear()
        self.active_monitors.clear()
        self.report_history.clear() 