from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from pathlib import Path
import json
from datetime import datetime

class ImageGenerator(BaseVisualAgent):
    """Agent responsible for generating images based on prompts and specifications."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.generator_config = {
            "output_dir": Path("outputs/images"),
            "cache_dir": Path("cache/images"),
            "generation_settings": {
                "resolutions": {
                    "preview": (512, 512),
                    "standard": (1024, 1024),
                    "high_res": (2048, 2048)
                },
                "sampling_methods": [
                    "euler_a",
                    "ddim",
                    "plms",
                    "dpm_solver"
                ],
                "inference_steps": {
                    "fast": 20,
                    "balanced": 30,
                    "quality": 50
                }
            }
        }
        self.active_generations: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "generate_image":
            return await self._generate_image(message)
        elif message.message_type == "modify_image":
            return await self._modify_image(message)
        elif message.message_type == "get_generation_status":
            return await self._get_generation_status(message)
        return None
    
    async def _generate_image(self, message: Message) -> Message:
        """Generate image from prompt and specifications."""
        generation_data = message.content.get("generation_data", {})
        generation_id = message.content.get("generation_id", "")
        
        try:
            generation_result = await self._process_image_generation(
                generation_data, generation_id
            )
            
            return Message(
                message_id=f"gen_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="image_generated",
                content={"generation_result": generation_result},
                context=message.context,
                metadata={"generation_id": generation_id}
            )
        except Exception as e:
            return Message(
                message_id=f"gen_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="generation_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_image_generation(self, generation_data: Dict[str, Any],
                                      generation_id: str) -> Dict[str, Any]:
        """Process image generation request."""
        # Prepare generation parameters
        params = self._prepare_generation_params(generation_data)
        
        # Set up generation settings
        settings = self._setup_generation_settings(generation_data)
        
        # Generate image
        image_result = await self._execute_generation(params, settings)
        
        # Process and save result
        result = {
            "generation_id": generation_id,
            "output_path": image_result["path"],
            "parameters": params,
            "settings": settings,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "status": "completed"
            }
        }
        
        # Store generation record
        self.active_generations[generation_id] = {
            "data": result,
            "original_request": generation_data,
            "status": "completed",
            "created_at": datetime.now().isoformat()
        }
        
        return result
    
    def _prepare_generation_params(self, generation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters for image generation."""
        return {
            "prompt": generation_data.get("prompt", ""),
            "negative_prompt": generation_data.get("negative_prompt", ""),
            "width": generation_data.get("width", 
                self.generator_config["generation_settings"]["resolutions"]["standard"][0]),
            "height": generation_data.get("height",
                self.generator_config["generation_settings"]["resolutions"]["standard"][1]),
            "num_inference_steps": generation_data.get("num_inference_steps",
                self.generator_config["generation_settings"]["inference_steps"]["balanced"]),
            "guidance_scale": generation_data.get("guidance_scale", 7.5),
            "seed": generation_data.get("seed", None)
        }
    
    def _setup_generation_settings(self, generation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up generation settings."""
        quality_preset = generation_data.get("quality_preset", "balanced")
        return {
            "sampling_method": generation_data.get("sampling_method",
                self.generator_config["sampling_methods"][0]),
            "inference_steps": self.generator_config["generation_settings"]["inference_steps"][quality_preset],
            "resolution": self._get_resolution_setting(generation_data),
            "output_format": generation_data.get("output_format", "png")
        }
    
    def _get_resolution_setting(self, generation_data: Dict[str, Any]) -> tuple:
        """Get resolution setting based on quality preset."""
        resolution_preset = generation_data.get("resolution_preset", "standard")
        return self.generator_config["generation_settings"]["resolutions"][resolution_preset]
    
    async def _execute_generation(self, params: Dict[str, Any],
                                settings: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the image generation process."""
        # This would integrate with the actual image generation model
        # For now, return a placeholder result
        output_path = self.generator_config["output_dir"] / f"generated_{datetime.now().timestamp()}.png"
        
        return {
            "path": output_path,
            "status": "success"
        }
    
    async def initialize(self) -> None:
        """Initialize image generator resources."""
        self.generator_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.generator_config["cache_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup image generator resources."""
        self.active_generations.clear() 