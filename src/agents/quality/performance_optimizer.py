from typing import Optional, Dict, Any, List
from src.agents.quality.base_quality_agent import BaseQualityAgent
from src.core.base_agent import Message
import bpy
import psutil
import torch
import time
from pathlib import Path

class PerformanceOptimizer(BaseQualityAgent):
    """Agent responsible for optimizing performance and resource usage."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.performance_metrics: Dict[str, Any] = {}
        self.optimization_targets = {
            "max_memory_usage": 0.8,  # 80% of available RAM
            "max_gpu_memory": 0.9,    # 90% of GPU memory
            "target_render_time": 60,  # seconds per frame
            "max_polygon_count": 1_000_000
        }
        self.profiling_data: Dict[str, List[float]] = {
            "render_times": [],
            "memory_usage": [],
            "gpu_usage": []
        }
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "optimize_performance":
            return await self._optimize_performance(message)
        elif message.message_type == "profile_resource_usage":
            return await self._profile_resources(message)
        elif message.message_type == "optimize_memory":
            return await self._optimize_memory(message)
        return None
    
    async def _optimize_performance(self, message: Message) -> Message:
        """Analyze and optimize performance."""
        scene_data = message.content.get("scene_data", {})
        optimization_type = message.content.get("optimization_type", "all")
        
        optimization_report = await self._analyze_and_optimize(scene_data, optimization_type)
        
        return Message(
            message_id=f"opt_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="performance_optimized",
            content={"optimization_report": optimization_report},
            context=message.context,
            metadata={"optimization_type": optimization_type}
        )
    
    async def _analyze_and_optimize(self, scene_data: Dict[str, Any], optimization_type: str) -> Dict[str, Any]:
        """Analyze performance and apply optimizations."""
        optimizations = []
        
        # Profile current performance
        profile_data = await self._profile_scene(scene_data)
        
        # Apply optimizations based on type
        if optimization_type in ["all", "memory"]:
            memory_opts = self._optimize_memory_usage(scene_data)
            optimizations.extend(memory_opts)
        
        if optimization_type in ["all", "render"]:
            render_opts = self._optimize_render_settings(scene_data)
            optimizations.extend(render_opts)
        
        if optimization_type in ["all", "gpu"]:
            gpu_opts = self._optimize_gpu_usage(scene_data)
            optimizations.extend(gpu_opts)
        
        # Measure impact of optimizations
        optimized_profile = await self._profile_scene(scene_data)
        
        return {
            "original_profile": profile_data,
            "optimized_profile": optimized_profile,
            "optimizations_applied": optimizations,
            "improvement_metrics": self._calculate_improvements(profile_data, optimized_profile)
        }
    
    async def _profile_scene(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Profile scene performance and resource usage."""
        profile = {
            "memory_usage": self._measure_memory_usage(),
            "gpu_usage": self._measure_gpu_usage(),
            "render_time": self._estimate_render_time(scene_data),
            "polygon_count": self._count_polygons(),
            "texture_memory": self._measure_texture_memory(),
            "scene_complexity": self._analyze_scene_complexity(scene_data)
        }
        
        return profile
    
    def _optimize_memory_usage(self, scene_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize memory usage."""
        optimizations = []
        
        # Check and optimize texture sizes
        texture_optimizations = self._optimize_textures()
        optimizations.extend(texture_optimizations)
        
        # Optimize mesh data
        mesh_optimizations = self._optimize_meshes()
        optimizations.extend(mesh_optimizations)
        
        # Clean up unused data
        cleanup_optimizations = self._cleanup_unused_data()
        optimizations.extend(cleanup_optimizations)
        
        return optimizations
    
    def _optimize_render_settings(self, scene_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize render settings for better performance."""
        optimizations = []
        render = bpy.context.scene.render
        
        # Adjust sampling based on scene complexity
        if render.engine == 'CYCLES':
            original_samples = render.cycles.samples
            optimal_samples = self._calculate_optimal_samples(scene_data)
            
            if optimal_samples < original_samples:
                render.cycles.samples = optimal_samples
                optimizations.append({
                    "type": "render_samples",
                    "description": f"Reduced samples from {original_samples} to {optimal_samples}",
                    "impact": "Faster rendering with minimal quality loss"
                })
        
        # Optimize tile size
        if torch.cuda.is_available():
            render.tile_x = 256
            render.tile_y = 256
            optimizations.append({
                "type": "tile_size",
                "description": "Optimized tile size for GPU rendering",
                "impact": "Improved render performance"
            })
        
        return optimizations
    
    def _optimize_gpu_usage(self, scene_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize GPU resource usage."""
        optimizations = []
        
        if torch.cuda.is_available():
            # Measure current GPU memory usage
            current_usage = torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated()
            
            if current_usage > self.optimization_targets["max_gpu_memory"]:
                # Apply GPU memory optimizations
                optimizations.extend(self._reduce_gpu_memory_usage())
        
        return optimizations
    
    def _measure_memory_usage(self) -> Dict[str, float]:
        """Measure current memory usage."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss": memory_info.rss / (1024 * 1024),  # MB
            "vms": memory_info.vms / (1024 * 1024),  # MB
            "percent": process.memory_percent()
        }
    
    def _measure_gpu_usage(self) -> Dict[str, float]:
        """Measure GPU resource usage."""
        if torch.cuda.is_available():
            return {
                "allocated": torch.cuda.memory_allocated() / (1024 * 1024),  # MB
                "cached": torch.cuda.memory_reserved() / (1024 * 1024),      # MB
                "utilization": torch.cuda.utilization()
            }
        return {}
    
    def _optimize_textures(self) -> List[Dict[str, Any]]:
        """Optimize texture memory usage."""
        optimizations = []
        
        for image in bpy.data.images:
            if image.size[0] > 4096 or image.size[1] > 4096:
                original_size = image.size[:]
                image.scale(4096, 4096)
                optimizations.append({
                    "type": "texture_size",
                    "asset": image.name,
                    "description": f"Reduced texture size from {original_size} to {image.size}",
                    "impact": "Reduced memory usage"
                })
        
        return optimizations
    
    def _optimize_meshes(self) -> List[Dict[str, Any]]:
        """Optimize mesh data for better performance."""
        optimizations = []
        
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                if len(obj.data.vertices) > 10000:
                    original_verts = len(obj.data.vertices)
                    # Apply decimate modifier
                    decimate = obj.modifiers.new(name="Decimate", type='DECIMATE')
                    decimate.ratio = 0.5
                    
                    optimizations.append({
                        "type": "mesh_optimization",
                        "asset": obj.name,
                        "description": f"Reduced vertex count from {original_verts}",
                        "impact": "Improved performance"
                    })
        
        return optimizations
    
    def _calculate_improvements(self, original: Dict[str, Any], optimized: Dict[str, Any]) -> Dict[str, float]:
        """Calculate improvement metrics."""
        return {
            "memory_reduction": (original["memory_usage"]["rss"] - optimized["memory_usage"]["rss"]) / original["memory_usage"]["rss"] * 100,
            "render_time_improvement": (original["render_time"] - optimized["render_time"]) / original["render_time"] * 100,
            "gpu_memory_reduction": (original["gpu_usage"].get("allocated", 0) - optimized["gpu_usage"].get("allocated", 0)) / max(original["gpu_usage"].get("allocated", 1), 1) * 100
        }
    
    async def initialize(self) -> None:
        """Initialize performance optimizer resources."""
        # Load optimization targets from configuration
        await self._load_optimization_targets()
    
    async def _load_optimization_targets(self) -> None:
        """Load optimization targets from configuration."""
        # Load targets from configuration or database
        pass
    
    async def cleanup(self) -> None:
        """Cleanup performance optimizer resources."""
        self.performance_metrics.clear()
        self.profiling_data.clear() 