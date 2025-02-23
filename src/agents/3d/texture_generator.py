from typing import Optional, Dict, Any, List
from src.agents.3d.base_3d_agent import Base3DAgent
from src.core.base_agent import Message
import bpy
from pathlib import Path
import numpy as np

class TextureGenerator(Base3DAgent):
    """Agent responsible for generating and applying textures to 3D models."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.texture_library: Dict[str, Any] = {}
        self.material_presets: Dict[str, Any] = {}
        self.texture_cache_path = Path("assets/textures")
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "generate_texture":
            return await self._generate_texture(message)
        elif message.message_type == "apply_material":
            return await self._apply_material(message)
        elif message.message_type == "modify_texture":
            return await self._modify_texture(message)
        return None
    
    async def _generate_texture(self, message: Message) -> Message:
        """Generate textures for a 3D model."""
        model_data = message.content.get("model_data", {})
        texture_requirements = message.content.get("texture_requirements", {})
        
        texture_data = await self._create_textures(model_data, texture_requirements)
        
        return Message(
            message_id=f"tex_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="textures_generated",
            content={"texture_data": texture_data},
            context=message.context,
            metadata={"requirements": texture_requirements}
        )
    
    async def _create_textures(self, model_data: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create texture maps for the model."""
        try:
            model_name = model_data.get("model_name", "")
            model = bpy.data.objects.get(model_name)
            
            if not model:
                raise ValueError(f"Model {model_name} not found")
            
            # Create material
            material = self._create_material(requirements)
            
            # Generate texture maps
            texture_maps = {
                "diffuse": self._generate_diffuse_map(requirements),
                "normal": self._generate_normal_map(requirements),
                "roughness": self._generate_roughness_map(requirements),
                "metallic": self._generate_metallic_map(requirements)
            }
            
            # Apply textures to material
            self._apply_textures_to_material(material, texture_maps)
            
            # Apply material to model
            if model.data.materials:
                model.data.materials[0] = material
            else:
                model.data.materials.append(material)
            
            return {
                "material_name": material.name,
                "texture_maps": {name: path for name, path in texture_maps.items()},
                "parameters": requirements
            }
            
        except Exception as e:
            print(f"Error generating textures: {str(e)}")
            return {}
    
    def _create_material(self, requirements: Dict[str, Any]) -> bpy.types.Material:
        """Create a new material with specified properties."""
        material_type = requirements.get("material_type", "standard")
        material = bpy.data.materials.new(name=f"material_{material_type}")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        
        # Clear default nodes
        nodes.clear()
        
        # Create basic PBR setup
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        output = nodes.new('ShaderNodeOutputMaterial')
        material.node_tree.links.new(principled.outputs[0], output.inputs[0])
        
        return material
    
    def _generate_diffuse_map(self, requirements: Dict[str, Any]) -> str:
        """Generate diffuse color map."""
        # In a full implementation, this would use AI to generate textures
        # For now, we'll use a basic color or pattern
        return str(self.texture_cache_path / "default_diffuse.png")
    
    def _generate_normal_map(self, requirements: Dict[str, Any]) -> str:
        """Generate normal map for surface detail."""
        return str(self.texture_cache_path / "default_normal.png")
    
    def _generate_roughness_map(self, requirements: Dict[str, Any]) -> str:
        """Generate roughness map for surface properties."""
        return str(self.texture_cache_path / "default_roughness.png")
    
    def _generate_metallic_map(self, requirements: Dict[str, Any]) -> str:
        """Generate metallic map for material properties."""
        return str(self.texture_cache_path / "default_metallic.png")
    
    def _apply_textures_to_material(self, material: bpy.types.Material, texture_maps: Dict[str, str]) -> None:
        """Apply generated texture maps to the material."""
        nodes = material.node_tree.nodes
        principled = nodes.get("Principled BSDF")
        
        for map_type, filepath in texture_maps.items():
            if Path(filepath).exists():
                tex_image = nodes.new('ShaderNodeTexImage')
                tex_image.image = bpy.data.images.load(filepath)
                
                if map_type == "diffuse":
                    material.node_tree.links.new(tex_image.outputs[0], principled.inputs['Base Color'])
                elif map_type == "normal":
                    normal_map = nodes.new('ShaderNodeNormalMap')
                    material.node_tree.links.new(tex_image.outputs[0], normal_map.inputs[1])
                    material.node_tree.links.new(normal_map.outputs[0], principled.inputs['Normal'])
                elif map_type == "roughness":
                    material.node_tree.links.new(tex_image.outputs[0], principled.inputs['Roughness'])
                elif map_type == "metallic":
                    material.node_tree.links.new(tex_image.outputs[0], principled.inputs['Metallic'])
    
    async def initialize(self) -> None:
        """Initialize texture generation resources."""
        self.texture_cache_path.mkdir(parents=True, exist_ok=True)
        # Load material presets and texture templates
        await self._load_material_presets()
    
    async def _load_material_presets(self) -> None:
        """Load predefined material presets."""
        # Load material presets from configuration or database
        pass
    
    async def cleanup(self) -> None:
        """Cleanup texture generation resources."""
        self.texture_library.clear()
        self.material_presets.clear() 