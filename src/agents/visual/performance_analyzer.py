from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from pathlib import Path
import json
import numpy as np
from datetime import datetime
import aiofiles
import pandas as pd
from collections import defaultdict

class PerformanceAnalyzer(BaseVisualAgent):
    """Agent responsible for analyzing and optimizing pipeline performance."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.analyzer_config = {
            "output_dir": Path("outputs/performance"),
            "analysis_dir": Path("analysis/performance"),
            "metrics": {
                "pipeline": {
                    "total_duration": {"unit": "seconds", "threshold": 3600},
                    "stage_distribution": {"unit": "percentage", "threshold": 30},
                    "resource_utilization": {"unit": "percentage", "threshold": 80},
                    "error_rate": {"unit": "percentage", "threshold": 5}
                },
                "stage": {
                    "processing_time": {"unit": "seconds", "threshold": 600},
                    "memory_usage": {"unit": "megabytes", "threshold": 2048},
                    "cpu_utilization": {"unit": "percentage", "threshold": 90},
                    "gpu_utilization": {"unit": "percentage", "threshold": 85}
                },
                "resource": {
                    "memory_efficiency": {"unit": "ratio", "threshold": 0.7},
                    "cpu_efficiency": {"unit": "ratio", "threshold": 0.75},
                    "io_throughput": {"unit": "MB/s", "threshold": 100},
                    "gpu_memory_efficiency": {"unit": "ratio", "threshold": 0.8}
                }
            },
            "analysis_intervals": {
                "real_time": 10,      # seconds
                "short_term": 300,     # 5 minutes
                "long_term": 3600      # 1 hour
            }
        }
        self.active_analyses: Dict[str, Dict[str, Any]] = {}
        self.performance_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.optimization_history: List[Dict[str, Any]] = []
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "analyze_performance":
            return await self._analyze_performance(message)
        elif message.message_type == "optimize_pipeline":
            return await self._optimize_pipeline(message)
        elif message.message_type == "get_performance_report":
            return await self._get_performance_report(message)
        return None
    
    async def _analyze_performance(self, message: Message) -> Message:
        """Analyze pipeline performance."""
        pipeline_id = message.content.get("pipeline_id", "")
        analysis_type = message.content.get("analysis_type", "real_time")
        
        try:
            analysis_result = await self._process_performance_analysis(
                pipeline_id, analysis_type
            )
            
            return Message(
                message_id=f"perf_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="performance_analyzed",
                content={"analysis_result": analysis_result},
                context=message.context,
                metadata={"pipeline_id": pipeline_id}
            )
        except Exception as e:
            return Message(
                message_id=f"perf_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="analysis_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_performance_analysis(self, pipeline_id: str,
                                          analysis_type: str) -> Dict[str, Any]:
        """Process pipeline performance analysis."""
        # Get performance data
        performance_data = self._get_performance_data(pipeline_id, analysis_type)
        
        # Analyze pipeline metrics
        pipeline_metrics = self._analyze_pipeline_metrics(performance_data)
        
        # Analyze stage metrics
        stage_metrics = self._analyze_stage_metrics(performance_data)
        
        # Analyze resource utilization
        resource_metrics = self._analyze_resource_metrics(performance_data)
        
        # Generate optimization recommendations
        recommendations = self._generate_recommendations(
            pipeline_metrics,
            stage_metrics,
            resource_metrics
        )
        
        # Create analysis report
        analysis_report = self._create_analysis_report(
            pipeline_id,
            analysis_type,
            pipeline_metrics,
            stage_metrics,
            resource_metrics,
            recommendations
        )
        
        # Store analysis results
        self.active_analyses[pipeline_id] = {
            "type": analysis_type,
            "report": analysis_report,
            "timestamp": datetime.now().isoformat()
        }
        
        return analysis_report
    
    def _analyze_pipeline_metrics(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall pipeline metrics."""
        df = pd.DataFrame(performance_data)
        
        metrics = {
            "total_duration": df["duration"].sum(),
            "stage_distribution": df.groupby("stage")["duration"].sum().to_dict(),
            "resource_utilization": {
                "cpu": df["cpu_usage"].mean(),
                "memory": df["memory_usage"].mean(),
                "gpu": df["gpu_usage"].mean() if "gpu_usage" in df else None
            },
            "error_rate": (df["status"] == "error").mean() * 100
        }
        
        # Add performance indicators
        metrics["indicators"] = self._calculate_performance_indicators(metrics)
        
        return metrics
    
    def _analyze_stage_metrics(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze individual stage metrics."""
        df = pd.DataFrame(performance_data)
        stage_metrics = {}
        
        for stage in df["stage"].unique():
            stage_df = df[df["stage"] == stage]
            stage_metrics[stage] = {
                "processing_time": {
                    "mean": stage_df["duration"].mean(),
                    "std": stage_df["duration"].std(),
                    "min": stage_df["duration"].min(),
                    "max": stage_df["duration"].max()
                },
                "resource_usage": {
                    "cpu": stage_df["cpu_usage"].mean(),
                    "memory": stage_df["memory_usage"].mean(),
                    "gpu": stage_df["gpu_usage"].mean() if "gpu_usage" in stage_df else None
                },
                "efficiency": self._calculate_stage_efficiency(stage_df)
            }
        
        return stage_metrics
    
    def _calculate_stage_efficiency(self, stage_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate efficiency metrics for a stage."""
        return {
            "cpu_efficiency": stage_data["cpu_usage"].mean() / 100,
            "memory_efficiency": stage_data["memory_usage"].mean() / stage_data["memory_allocated"].mean(),
            "time_efficiency": 1 - (stage_data["idle_time"].sum() / stage_data["duration"].sum())
        }
    
    def _generate_recommendations(self, pipeline_metrics: Dict[str, Any],
                                stage_metrics: Dict[str, Any],
                                resource_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Check pipeline-level metrics
        if pipeline_metrics["error_rate"] > self.analyzer_config["metrics"]["pipeline"]["error_rate"]["threshold"]:
            recommendations.append({
                "level": "pipeline",
                "type": "error_rate",
                "severity": "high",
                "description": "High error rate detected in pipeline execution",
                "suggestion": "Review error logs and implement additional error handling"
            })
        
        # Check stage-level metrics
        for stage, metrics in stage_metrics.items():
            if metrics["processing_time"]["mean"] > self.analyzer_config["metrics"]["stage"]["processing_time"]["threshold"]:
                recommendations.append({
                    "level": "stage",
                    "stage": stage,
                    "type": "processing_time",
                    "severity": "medium",
                    "description": f"High processing time in stage {stage}",
                    "suggestion": "Consider parallelizing tasks or optimizing algorithms"
                })
        
        return recommendations
    
    def _create_analysis_report(self, pipeline_id: str,
                              analysis_type: str,
                              pipeline_metrics: Dict[str, Any],
                              stage_metrics: Dict[str, Any],
                              resource_metrics: Dict[str, Any],
                              recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create comprehensive performance analysis report."""
        return {
            "pipeline_id": pipeline_id,
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "pipeline": pipeline_metrics,
                "stages": stage_metrics,
                "resources": resource_metrics
            },
            "recommendations": recommendations,
            "summary": self._create_analysis_summary(
                pipeline_metrics,
                stage_metrics,
                resource_metrics
            )
        }
    
    async def initialize(self) -> None:
        """Initialize performance analyzer resources."""
        self.analyzer_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.analyzer_config["analysis_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup performance analyzer resources."""
        # Save analysis history
        for pipeline_id, analysis in self.active_analyses.items():
            self.optimization_history.append({
                "pipeline_id": pipeline_id,
                "archived_at": datetime.now().isoformat(),
                **analysis
            })
        
        # Clear active analyses and performance data
        self.active_analyses.clear()
        self.performance_data.clear() 