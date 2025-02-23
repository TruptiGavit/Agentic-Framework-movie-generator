from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

@dataclass
class PerformanceMetric:
    """Performance metric data."""
    name: str
    value: float
    timestamp: datetime
    context: Dict[str, Any]

class PerformanceOptimizer:
    """Optimizes system performance based on metrics and usage patterns."""
    
    def __init__(self):
        self.logger = logging.getLogger("movie_generator.performance")
        
        # Performance metrics history
        self.metrics_history: Dict[str, List[PerformanceMetric]] = {}
        
        # Optimization thresholds
        self.thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "gpu_memory": 90.0,
            "task_queue_size": 100
        }
        
        # Resource allocation
        self.resource_allocation = {
            "gpu_memory_per_task": "2GB",
            "cpu_threads_per_task": 2,
            "max_concurrent_tasks": 10
        }
        
        # Optimization state
        self.is_optimizing = False
        self._optimization_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start performance optimization."""
        self.is_optimizing = True
        self._optimization_task = asyncio.create_task(self._optimize_loop())
    
    async def stop(self):
        """Stop performance optimization."""
        self.is_optimizing = False
        if self._optimization_task:
            self._optimization_task.cancel()
    
    async def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric."""
        if metric.name not in self.metrics_history:
            self.metrics_history[metric.name] = []
        self.metrics_history[metric.name].append(metric)
        
        # Trim old metrics
        cutoff = datetime.now() - timedelta(hours=24)
        self.metrics_history[metric.name] = [
            m for m in self.metrics_history[metric.name]
            if m.timestamp > cutoff
        ]
    
    async def _optimize_loop(self):
        """Main optimization loop."""
        while self.is_optimizing:
            try:
                # Analyze current performance
                analysis = await self._analyze_performance()
                
                # Apply optimizations if needed
                if analysis["needs_optimization"]:
                    await self._apply_optimizations(analysis["recommendations"])
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in optimization loop: {str(e)}")
                await asyncio.sleep(5)
    
    async def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze current performance metrics."""
        analysis = {
            "needs_optimization": False,
            "recommendations": []
        }
        
        # Check CPU usage
        if "cpu_usage" in self.metrics_history:
            cpu_metrics = self.metrics_history["cpu_usage"][-10:]  # Last 10 readings
            avg_cpu = np.mean([m.value for m in cpu_metrics])
            
            if avg_cpu > self.thresholds["cpu_usage"]:
                analysis["needs_optimization"] = True
                analysis["recommendations"].append({
                    "type": "cpu",
                    "action": "reduce_concurrent_tasks",
                    "current_value": avg_cpu
                })
        
        # Similar checks for memory, GPU, etc.
        return analysis
    
    async def _apply_optimizations(self, recommendations: List[Dict[str, Any]]):
        """Apply performance optimizations."""
        for rec in recommendations:
            try:
                if rec["type"] == "cpu":
                    await self._optimize_cpu_usage(rec)
                elif rec["type"] == "memory":
                    await self._optimize_memory_usage(rec)
                elif rec["type"] == "gpu":
                    await self._optimize_gpu_usage(rec)
                
                self.logger.info(f"Applied optimization: {rec}")
                
            except Exception as e:
                self.logger.error(f"Error applying optimization: {str(e)}") 