from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import aiofiles

class RenderOptimizer(BaseVisualAgent):
    """Agent responsible for optimizing render settings and performance."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.optimizer_config = {
            "output_dir": Path("outputs/render_optimizer"),
            "profile_dir": Path("profiles/render_settings"),
            "optimization_profiles": {
                "quality": {
                    "samples": {
                        "min": 128,
                        "max": 4096,
                        "adaptive": True
                    },
                    "resolution": {
                        "min": (1920, 1080),
                        "max": (3840, 2160),
                        "scaling": 1.0
                    },
                    "denoising": {
                        "strength": 0.8,
                        "features": ["albedo", "normal"]
                    }
                },
                "balanced": {
                    "samples": {
                        "min": 64,
                        "max": 1024,
                        "adaptive": True
                    },
                    "resolution": {
                        "min": (1280, 720),
                        "max": (1920, 1080),
                        "scaling": 1.0
                    },
                    "denoising": {
                        "strength": 0.6,
                        "features": ["albedo"]
                    }
                },
                "performance": {
                    "samples": {
                        "min": 32,
                        "max": 256,
                        "adaptive": True
                    },
                    "resolution": {
                        "min": (1280, 720),
                        "max": (1280, 720),
                        "scaling": 0.8
                    },
                    "denoising": {
                        "strength": 0.4,
                        "features": []
                    }
                }
            },
            "scene_complexity_weights": {
                "geometry": 0.3,
                "materials": 0.2,
                "lighting": 0.3,
                "effects": 0.2
            }
        }
        self.active_optimizations: Dict[str, Dict[str, Any]] = {}
        self.performance_history: List[Dict[str, Any]] = []
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "optimize_settings":
            return await self._optimize_settings(message)
        elif message.message_type == "adjust_performance":
            return await self._adjust_performance(message)
        elif message.message_type == "get_optimization_profile":
            return await self._get_optimization_profile(message)
        return None
    
    async def _optimize_settings(self, message: Message) -> Message:
        """Optimize render settings for a scene."""
        scene_data = message.content.get("scene_data", {})
        profile_name = message.content.get("profile", "balanced")
        optimization_id = message.content.get("optimization_id", "")
        
        try:
            optimization_result = await self._process_optimization(
                scene_data, profile_name, optimization_id
            )
            
            return Message(
                message_id=f"opt_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="settings_optimized",
                content={"optimization_result": optimization_result},
                context=message.context,
                metadata={"optimization_id": optimization_id}
            )
        except Exception as e:
            return Message(
                message_id=f"opt_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="optimization_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_optimization(self, scene_data: Dict[str, Any],
                                  profile_name: str,
                                  optimization_id: str) -> Dict[str, Any]:
        """Process render settings optimization."""
        # Analyze scene complexity
        complexity = self._analyze_scene_complexity(scene_data)
        
        # Get base profile settings
        profile = self.optimizer_config["optimization_profiles"][profile_name]
        
        # Optimize settings based on complexity
        optimized_settings = self._optimize_render_settings(profile, complexity)
        
        # Validate settings against resource constraints
        validated_settings = await self._validate_settings(optimized_settings, scene_data)
        
        # Store optimization details
        self.active_optimizations[optimization_id] = {
            "scene_data": scene_data,
            "profile": profile_name,
            "complexity": complexity,
            "settings": validated_settings,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "settings": validated_settings,
            "complexity_analysis": complexity,
            "estimated_performance": self._estimate_performance(validated_settings),
            "metadata": self._create_optimization_metadata(scene_data, profile_name)
        }
    
    def _analyze_scene_complexity(self, scene_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze scene complexity for optimization."""
        weights = self.optimizer_config["scene_complexity_weights"]
        
        return {
            "geometry": self._calculate_geometry_complexity(scene_data) * weights["geometry"],
            "materials": self._calculate_material_complexity(scene_data) * weights["materials"],
            "lighting": self._calculate_lighting_complexity(scene_data) * weights["lighting"],
            "effects": self._calculate_effects_complexity(scene_data) * weights["effects"]
        }
    
    def _calculate_geometry_complexity(self, scene_data: Dict[str, Any]) -> float:
        """Calculate geometry complexity score."""
        geometry_data = scene_data.get("geometry", {})
        
        factors = [
            len(geometry_data.get("objects", [])) / 100,  # Normalize by typical scene size
            geometry_data.get("total_vertices", 0) / 1000000,  # Per million vertices
            geometry_data.get("total_polygons", 0) / 1000000  # Per million polygons
        ]
        
        return np.clip(np.mean(factors), 0, 1)
    
    def _optimize_render_settings(self, profile: Dict[str, Any],
                                complexity: Dict[str, float]) -> Dict[str, Any]:
        """Optimize render settings based on complexity analysis."""
        total_complexity = sum(complexity.values())
        
        # Adjust samples based on complexity
        samples = self._calculate_optimal_samples(
            profile["samples"],
            total_complexity
        )
        
        # Adjust resolution based on complexity and content
        resolution = self._calculate_optimal_resolution(
            profile["resolution"],
            complexity
        )
        
        # Adjust denoising based on complexity
        denoising = self._adjust_denoising_settings(
            profile["denoising"],
            complexity
        )
        
        return {
            "samples": samples,
            "resolution": resolution,
            "denoising": denoising,
            "optimization_level": self._determine_optimization_level(total_complexity)
        }
    
    def _calculate_optimal_samples(self, sample_config: Dict[str, Any],
                                 complexity: float) -> Dict[str, Any]:
        """Calculate optimal sample settings."""
        base_samples = int(
            sample_config["min"] + (sample_config["max"] - sample_config["min"]) * complexity
        )
        
        return {
            "count": base_samples,
            "adaptive": sample_config["adaptive"],
            "threshold": 0.01 * (1 + complexity)
        }
    
    def _create_optimization_metadata(self, scene_data: Dict[str, Any],
                                   profile_name: str) -> Dict[str, Any]:
        """Create metadata for optimization."""
        return {
            "timestamp": datetime.now().isoformat(),
            "scene_id": scene_data.get("id", ""),
            "profile": profile_name,
            "config": self.optimizer_config["optimization_profiles"][profile_name]
        }
    
    async def initialize(self) -> None:
        """Initialize render optimizer resources."""
        self.optimizer_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.optimizer_config["profile_dir"].mkdir(parents=True, exist_ok=True)
        
        # Load optimization profiles
        await self._load_optimization_profiles()
    
    async def cleanup(self) -> None:
        """Cleanup render optimizer resources."""
        # Save optimization history
        await self._save_optimization_history()
        
        # Clear active optimizations
        self.active_optimizations.clear()
        self.performance_history.clear() 