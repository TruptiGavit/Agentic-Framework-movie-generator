from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from PIL import Image
import numpy as np
import cv2
import torch
from pathlib import Path
import json
from datetime import datetime

class RenderQualityManager(BaseVisualAgent):
    """Agent responsible for managing render quality and optimization."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.render_config = {
            "output_dir": Path("outputs/render_quality"),
            "cache_dir": Path("cache/render_quality"),
            "quality_presets": {
                "preview": {
                    "resolution": (1280, 720),
                    "samples": 32,
                    "denoising": 0.5,
                    "compression": "medium"
                },
                "final": {
                    "resolution": (1920, 1080),
                    "samples": 128,
                    "denoising": 0.8,
                    "compression": "low"
                },
                "high_quality": {
                    "resolution": (3840, 2160),
                    "samples": 256,
                    "denoising": 0.9,
                    "compression": "none"
                }
            },
            "performance_targets": {
                "max_memory_usage": 0.8,  # 80% of available memory
                "target_fps": 30,
                "max_render_time": 300  # seconds per frame
            }
        }
        self.active_renders: Dict[str, Dict[str, Any]] = {}
        self.quality_metrics: Dict[str, List[float]] = {
            "psnr": [],
            "ssim": [],
            "render_times": []
        }
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "optimize_render":
            return await self._optimize_render(message)
        elif message.message_type == "check_quality":
            return await self._check_quality(message)
        elif message.message_type == "adjust_settings":
            return await self._adjust_settings(message)
        return None
    
    async def _optimize_render(self, message: Message) -> Message:
        """Optimize render settings for a scene."""
        scene_data = message.content.get("scene_data", {})
        quality_preset = message.content.get("quality_preset", "final")
        render_id = message.content.get("render_id", "")
        
        try:
            optimization_result = await self._process_optimization(
                scene_data, quality_preset, render_id
            )
            
            return Message(
                message_id=f"opt_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="render_optimized",
                content={"optimization_result": optimization_result},
                context=message.context,
                metadata={"render_id": render_id}
            )
        except Exception as e:
            return Message(
                message_id=f"opt_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="render_optimization_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_optimization(self, scene_data: Dict[str, Any],
                                  quality_preset: str,
                                  render_id: str) -> Dict[str, Any]:
        """Process render optimization."""
        # Get base settings from preset
        settings = self.render_config["quality_presets"][quality_preset].copy()
        
        # Analyze scene complexity
        complexity = self._analyze_scene_complexity(scene_data)
        
        # Adjust settings based on complexity
        optimized_settings = self._optimize_settings(settings, complexity)
        
        # Validate against performance targets
        validated_settings = self._validate_performance(optimized_settings, scene_data)
        
        # Store active render settings
        self.active_renders[render_id] = {
            "settings": validated_settings,
            "scene_data": scene_data,
            "quality_preset": quality_preset,
            "optimization_time": datetime.now().isoformat()
        }
        
        return {
            "settings": validated_settings,
            "complexity_analysis": complexity,
            "performance_estimates": self._estimate_performance(validated_settings),
            "metadata": self._create_optimization_metadata(scene_data, quality_preset)
        }
    
    def _analyze_scene_complexity(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze scene complexity for optimization."""
        return {
            "geometry_complexity": self._calculate_geometry_complexity(scene_data),
            "texture_complexity": self._calculate_texture_complexity(scene_data),
            "lighting_complexity": self._calculate_lighting_complexity(scene_data),
            "effects_complexity": self._calculate_effects_complexity(scene_data)
        }
    
    def _optimize_settings(self, base_settings: Dict[str, Any],
                         complexity: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize render settings based on scene complexity."""
        settings = base_settings.copy()
        
        # Adjust samples based on complexity
        total_complexity = sum(complexity.values()) / len(complexity)
        settings["samples"] = int(settings["samples"] * (1 + total_complexity * 0.5))
        
        # Adjust denoising strength
        settings["denoising"] = min(0.95, settings["denoising"] + total_complexity * 0.1)
        
        # Adjust other parameters based on specific complexities
        if complexity["lighting_complexity"] > 0.7:
            settings["samples"] = int(settings["samples"] * 1.5)
        
        if complexity["effects_complexity"] > 0.5:
            settings["denoising"] = min(0.95, settings["denoising"] + 0.1)
        
        return settings
    
    def _validate_performance(self, settings: Dict[str, Any],
                            scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate settings against performance targets."""
        validated = settings.copy()
        targets = self.render_config["performance_targets"]
        
        # Estimate memory usage
        estimated_memory = self._estimate_memory_usage(validated, scene_data)
        if estimated_memory > targets["max_memory_usage"]:
            # Adjust settings to reduce memory usage
            validated = self._reduce_memory_usage(validated, estimated_memory)
        
        # Estimate render time
        estimated_time = self._estimate_render_time(validated, scene_data)
        if estimated_time > targets["max_render_time"]:
            # Adjust settings to reduce render time
            validated = self._reduce_render_time(validated, estimated_time)
        
        return validated
    
    def _estimate_performance(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate performance metrics for settings."""
        return {
            "estimated_memory": self._estimate_memory_usage(settings, {}),
            "estimated_time": self._estimate_render_time(settings, {}),
            "estimated_quality": self._estimate_quality_score(settings)
        }
    
    def _create_optimization_metadata(self, scene_data: Dict[str, Any],
                                   quality_preset: str) -> Dict[str, Any]:
        """Create metadata for optimization."""
        return {
            "timestamp": datetime.now().isoformat(),
            "scene_id": scene_data.get("id", ""),
            "quality_preset": quality_preset,
            "performance_targets": self.render_config["performance_targets"]
        }
    
    async def _check_quality(self, message: Message) -> Message:
        """Check render quality against reference."""
        render_data = message.content.get("render_data", {})
        reference_data = message.content.get("reference_data", {})
        
        quality_result = await self._analyze_quality(render_data, reference_data)
        
        return Message(
            message_id=f"check_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="quality_checked",
            content={"quality_result": quality_result},
            context=message.context
        )
    
    async def initialize(self) -> None:
        """Initialize render quality manager resources."""
        self.render_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.render_config["cache_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup render quality manager resources."""
        self.active_renders.clear()
        self.quality_metrics.clear() 