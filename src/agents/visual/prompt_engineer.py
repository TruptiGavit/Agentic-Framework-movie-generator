from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from pathlib import Path
import json
from datetime import datetime

class PromptEngineer(BaseVisualAgent):
    """Agent responsible for generating optimized prompts for image generation."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.prompt_config = {
            "output_dir": Path("outputs/prompt_engineer"),
            "prompt_components": {
                "subject": {
                    "weight": 1.0,
                    "required": True
                },
                "action": {
                    "weight": 0.8,
                    "required": True
                },
                "environment": {
                    "weight": 0.7,
                    "required": True
                },
                "lighting": {
                    "weight": 0.6,
                    "required": False
                },
                "style": {
                    "weight": 0.5,
                    "required": False
                }
            }
        }
        self.active_prompts: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "generate_prompt":
            return await self._generate_prompt(message)
        elif message.message_type == "refine_prompt":
            return await self._refine_prompt(message)
        return None
    
    async def _generate_prompt(self, message: Message) -> Message:
        """Generate optimized prompt from scene interpretation."""
        scene_data = message.content.get("scene_interpretation", {})
        prompt_id = message.content.get("prompt_id", "")
        
        try:
            prompt = await self._process_prompt_generation(
                scene_data, prompt_id
            )
            
            return Message(
                message_id=f"prompt_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="prompt_generated",
                content={"prompt": prompt},
                context=message.context,
                metadata={"prompt_id": prompt_id}
            )
        except Exception as e:
            return Message(
                message_id=f"prompt_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="prompt_generation_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_prompt_generation(self, scene_data: Dict[str, Any],
                                       prompt_id: str) -> Dict[str, Any]:
        """Process scene data into optimized prompt."""
        # Extract components from scene data
        components = self._extract_prompt_components(scene_data)
        
        # Build main prompt
        main_prompt = self._build_main_prompt(components)
        
        # Generate negative prompt
        negative_prompt = self._generate_negative_prompt(scene_data)
        
        # Create prompt structure
        prompt = {
            "main_prompt": main_prompt,
            "negative_prompt": negative_prompt,
            "components": components,
            "metadata": {
                "prompt_id": prompt_id,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        
        # Store active prompt
        self.active_prompts[prompt_id] = {
            "data": prompt,
            "scene_data": scene_data,
            "created_at": datetime.now().isoformat()
        }
        
        return prompt
    
    def _extract_prompt_components(self, scene_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract prompt components from scene data."""
        components = {}
        
        # Extract subject details
        if "characters" in scene_data:
            components["subject"] = self._format_character_description(
                scene_data["characters"]
            )
        
        # Extract action/pose
        if "composition" in scene_data:
            components["action"] = self._format_composition_description(
                scene_data["composition"]
            )
        
        # Extract environment details
        if "environment" in scene_data:
            components["environment"] = self._format_environment_description(
                scene_data["environment"]
            )
        
        # Extract lighting
        if "environment" in scene_data and "lighting" in scene_data["environment"]:
            components["lighting"] = scene_data["environment"]["lighting"]
        
        # Extract style
        if "atmosphere" in scene_data:
            components["style"] = self._format_style_description(
                scene_data["atmosphere"]
            )
        
        return components
    
    def _build_main_prompt(self, components: Dict[str, Any]) -> str:
        """Build main prompt from components."""
        prompt_parts = []
        
        # Add components in order of importance
        for component, config in self.prompt_config["prompt_components"].items():
            if component in components:
                if config["required"] or components[component]:
                    prompt_parts.append(components[component])
        
        return ", ".join(filter(None, prompt_parts))
    
    def _generate_negative_prompt(self, scene_data: Dict[str, Any]) -> str:
        """Generate negative prompt to avoid unwanted elements."""
        # Basic negative prompt elements
        negative_elements = [
            "blurry", "low quality", "distorted",
            "watermark", "signature", "text"
        ]
        
        # Add scene-specific negative elements
        if "atmosphere" in scene_data:
            style = scene_data["atmosphere"].get("style", "")
            if style == "realistic":
                negative_elements.extend(["cartoon", "anime", "illustration"])
            elif style == "artistic":
                negative_elements.extend(["photorealistic", "photograph"])
        
        return ", ".join(negative_elements)
    
    async def initialize(self) -> None:
        """Initialize prompt engineer resources."""
        self.prompt_config["output_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup prompt engineer resources."""
        self.active_prompts.clear() 