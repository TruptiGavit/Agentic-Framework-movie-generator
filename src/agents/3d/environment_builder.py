from typing import Optional, Dict, Any, List
from src.agents.3d.base_3d_agent import Base3DAgent
from src.core.base_agent import Message
import bpy
import math
from pathlib import Path

class EnvironmentBuilder(Base3DAgent):
    """Agent responsible for creating and managing scene environments."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.environment_presets: Dict[str, Any] = {}
        self.asset_library_path = Path("assets/environments")
        self.hdri_path = Path("assets/hdri")
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "create_environment":
            return await self._create_environment(message)
        elif message.message_type == "modify_environment":
            return await self._modify_environment(message)
        elif message.message_type == "add_environment_element":
            return await self._add_environment_element(message)
        return None
    
    async def _create_environment(self, message: Message) -> Message:
        """Create a new environment based on requirements."""
        env_type = message.content.get("environment_type", "interior")
        env_requirements = message.content.get("requirements", {})
        
        environment_data = await self._generate_environment(env_type, env_requirements)
        
        return Message(
            message_id=f"env_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="environment_created",
            content={"environment_data": environment_data},
            context=message.context,
            metadata={"env_type": env_type}
        )
    
    async def _generate_environment(self, env_type: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate environment based on type and requirements."""
        try:
            # Clear existing environment
            self._clear_environment()
            
            if env_type == "interior":
                env_data = self._create_interior_environment(requirements)
            elif env_type == "exterior":
                env_data = self._create_exterior_environment(requirements)
            elif env_type == "abstract":
                env_data = self._create_abstract_environment(requirements)
            else:
                env_data = self._create_basic_environment(requirements)
            
            # Set up world lighting
            self._setup_world_lighting(requirements)
            
            return env_data
            
        except Exception as e:
            print(f"Error generating environment: {str(e)}")
            return {}
    
    def _create_interior_environment(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create an interior environment."""
        room_size = requirements.get("room_size", (5.0, 5.0, 3.0))
        
        # Create floor
        bpy.ops.mesh.primitive_plane_add(size=1.0)
        floor = bpy.context.active_object
        floor.scale = (room_size[0], room_size[1], 1.0)
        floor.name = "Floor"
        
        # Create walls
        walls = self._create_walls(room_size)
        
        # Add architectural elements
        elements = self._add_architectural_elements(requirements)
        
        return {
            "type": "interior",
            "room_size": room_size,
            "objects": {
                "floor": floor.name,
                "walls": [wall.name for wall in walls],
                "elements": elements
            }
        }
    
    def _create_exterior_environment(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create an exterior environment."""
        terrain_size = requirements.get("terrain_size", (20.0, 20.0))
        
        # Create terrain
        terrain = self._create_terrain(terrain_size, requirements)
        
        # Add landscape elements
        landscape = self._add_landscape_elements(requirements)
        
        # Add atmospheric effects
        atmosphere = self._setup_atmosphere(requirements)
        
        return {
            "type": "exterior",
            "terrain_size": terrain_size,
            "objects": {
                "terrain": terrain.name,
                "landscape_elements": landscape,
                "atmosphere": atmosphere
            }
        }
    
    def _create_walls(self, room_size: tuple) -> List[bpy.types.Object]:
        """Create walls for interior environment."""
        walls = []
        
        # Create four walls
        for i in range(4):
            bpy.ops.mesh.primitive_plane_add(size=1.0)
            wall = bpy.context.active_object
            
            # Rotate and position walls
            if i < 2:
                wall.rotation_euler = (math.pi/2, 0, 0)
                wall.location.x = room_size[0]/2 * (-1 if i == 0 else 1)
                wall.scale = (1.0, room_size[2], room_size[1])
            else:
                wall.rotation_euler = (math.pi/2, 0, math.pi/2)
                wall.location.y = room_size[1]/2 * (-1 if i == 2 else 1)
                wall.scale = (1.0, room_size[2], room_size[0])
            
            wall.name = f"Wall_{i+1}"
            walls.append(wall)
        
        return walls
    
    def _create_terrain(self, size: tuple, requirements: Dict[str, Any]) -> bpy.types.Object:
        """Create terrain with displacement."""
        bpy.ops.mesh.primitive_grid_add(size=1.0, x_subdivisions=64, y_subdivisions=64)
        terrain = bpy.context.active_object
        terrain.scale = (size[0], size[1], 1.0)
        
        # Add displacement modifier
        displace = terrain.modifiers.new(name="Terrain", type='DISPLACE')
        # Setup displacement texture
        # This would be expanded in a full implementation
        
        return terrain
    
    def _add_landscape_elements(self, requirements: Dict[str, Any]) -> List[str]:
        """Add landscape elements like trees, rocks, etc."""
        elements = []
        
        if requirements.get("add_vegetation", True):
            elements.extend(self._add_vegetation(requirements))
        
        if requirements.get("add_rocks", True):
            elements.extend(self._add_rocks(requirements))
        
        return elements
    
    def _setup_atmosphere(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Setup atmospheric effects."""
        world = bpy.context.scene.world
        if not world:
            world = bpy.data.worlds.new("World")
            bpy.context.scene.world = world
        
        # Setup sky, clouds, etc.
        # This would be expanded in a full implementation
        
        return {"world": world.name}
    
    def _setup_world_lighting(self, requirements: Dict[str, Any]) -> None:
        """Setup world lighting and HDRI environment."""
        world = bpy.context.scene.world
        world.use_nodes = True
        nodes = world.node_tree.nodes
        
        # Setup environment texture if HDRI is specified
        hdri_path = requirements.get("hdri_path")
        if hdri_path and (self.hdri_path / hdri_path).exists():
            env_tex = nodes.new('ShaderNodeTexEnvironment')
            env_tex.image = bpy.data.images.load(str(self.hdri_path / hdri_path))
            world.node_tree.links.new(env_tex.outputs[0], nodes["Background"].inputs[0])
    
    def _clear_environment(self) -> None:
        """Clear existing environment objects."""
        for obj in bpy.data.objects:
            if obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'VOLUME'}:
                bpy.data.objects.remove(obj, do_unlink=True)
    
    async def initialize(self) -> None:
        """Initialize environment builder resources."""
        self.asset_library_path.mkdir(parents=True, exist_ok=True)
        self.hdri_path.mkdir(parents=True, exist_ok=True)
        await self._load_environment_presets()
    
    async def _load_environment_presets(self) -> None:
        """Load predefined environment presets."""
        # Load presets from configuration or database
        pass
    
    async def cleanup(self) -> None:
        """Cleanup environment builder resources."""
        self.environment_presets.clear() 