from typing import Optional, Dict, Any, List
from src.agents.3d.base_3d_agent import Base3DAgent
from src.core.base_agent import Message
import bpy
import numpy as np

class ModelGenerator(Base3DAgent):
    """Agent responsible for generating 3D models."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.model_library: Dict[str, Any] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "generate_model":
            return await self._generate_model(message)
        elif message.message_type == "modify_model":
            return await self._modify_model(message)
        return None
    
    async def _generate_model(self, message: Message) -> Message:
        """Generate 3D model based on requirements."""
        model_type = message.content.get("model_type", "")
        parameters = message.content.get("parameters", {})
        
        model_data = await self._create_model(model_type, parameters)
        
        return Message(
            message_id=f"model_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="model_generated",
            content={"model_data": model_data},
            context=message.context,
            metadata={"model_type": model_type}
        )
    
    async def _create_model(self, model_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a 3D model using Blender."""
        try:
            # Clear existing objects
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()
            
            if model_type == "character":
                model = self._create_character_model(parameters)
            elif model_type == "prop":
                model = self._create_prop_model(parameters)
            elif model_type == "environment":
                model = self._create_environment_model(parameters)
            else:
                model = self._create_basic_model(parameters)
            
            return {
                "model_name": model.name,
                "vertices": len(model.data.vertices),
                "faces": len(model.data.polygons),
                "parameters": parameters
            }
            
        except Exception as e:
            print(f"Error generating model: {str(e)}")
            return {}
    
    def _create_character_model(self, parameters: Dict[str, Any]) -> bpy.types.Object:
        """Create a character model."""
        # Add basic character mesh
        bpy.ops.mesh.primitive_cylinder_add()
        body = bpy.context.active_object
        
        # Add character features based on parameters
        height = parameters.get("height", 1.8)
        build = parameters.get("build", "average")
        
        # Scale the base mesh
        body.scale = (1.0, 1.0, height)
        
        return body
    
    def _create_prop_model(self, parameters: Dict[str, Any]) -> bpy.types.Object:
        """Create a prop model."""
        # Basic prop creation logic
        bpy.ops.mesh.primitive_cube_add()
        prop = bpy.context.active_object
        return prop
    
    def _create_environment_model(self, parameters: Dict[str, Any]) -> bpy.types.Object:
        """Create an environment model."""
        # Basic environment creation logic
        bpy.ops.mesh.primitive_plane_add()
        env = bpy.context.active_object
        return env
    
    def _create_basic_model(self, parameters: Dict[str, Any]) -> bpy.types.Object:
        """Create a basic geometric model."""
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        return obj
    
    async def initialize(self) -> None:
        """Initialize model generation resources."""
        # Set up Blender environment
        bpy.context.scene.render.engine = 'CYCLES'
        
    async def cleanup(self) -> None:
        """Cleanup model generation resources."""
        # Clear Blender scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete() 