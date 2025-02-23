from typing import Optional, Dict, Any, List
from src.agents.3d.base_3d_agent import Base3DAgent
from src.core.base_agent import Message
import bpy
import math

class LightingSystem(Base3DAgent):
    """Agent responsible for creating and managing scene lighting."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.lighting_presets: Dict[str, Any] = {}
        self.active_lights: Dict[str, Any] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "setup_lighting":
            return await self._setup_lighting(message)
        elif message.message_type == "adjust_lighting":
            return await self._adjust_lighting(message)
        elif message.message_type == "apply_lighting_preset":
            return await self._apply_preset(message)
        return None
    
    async def _setup_lighting(self, message: Message) -> Message:
        """Set up lighting for a scene."""
        scene_info = message.content.get("scene_info", {})
        lighting_requirements = message.content.get("lighting_requirements", {})
        
        lighting_data = await self._create_lighting_setup(scene_info, lighting_requirements)
        
        return Message(
            message_id=f"light_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="lighting_setup_complete",
            content={"lighting_data": lighting_data},
            context=message.context,
            metadata={"requirements": lighting_requirements}
        )
    
    async def _create_lighting_setup(self, scene_info: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create lighting setup based on scene requirements."""
        try:
            # Clear existing lights
            self._clear_existing_lights()
            
            lighting_style = requirements.get("style", "three_point")
            mood = requirements.get("mood", "neutral")
            
            if lighting_style == "three_point":
                lights = self._create_three_point_lighting(requirements)
            elif lighting_style == "natural":
                lights = self._create_natural_lighting(requirements)
            elif lighting_style == "dramatic":
                lights = self._create_dramatic_lighting(requirements)
            else:
                lights = self._create_basic_lighting(requirements)
            
            # Apply color and intensity based on mood
            self._apply_mood_settings(lights, mood)
            
            return {
                "style": lighting_style,
                "mood": mood,
                "lights": [light.name for light in lights],
                "parameters": requirements
            }
            
        except Exception as e:
            print(f"Error setting up lighting: {str(e)}")
            return {}
    
    def _create_three_point_lighting(self, requirements: Dict[str, Any]) -> List[bpy.types.Object]:
        """Create standard three-point lighting setup."""
        lights = []
        
        # Key Light
        key_light = self._create_light("KEY", "AREA", location=(4, -4, 5))
        key_light.data.energy = 1000.0
        lights.append(key_light)
        
        # Fill Light
        fill_light = self._create_light("FILL", "AREA", location=(-4, -2, 3))
        fill_light.data.energy = 400.0
        lights.append(fill_light)
        
        # Back Light
        back_light = self._create_light("BACK", "AREA", location=(0, 3, 4))
        back_light.data.energy = 600.0
        lights.append(back_light)
        
        return lights
    
    def _create_natural_lighting(self, requirements: Dict[str, Any]) -> List[bpy.types.Object]:
        """Create natural lighting setup with sun and environment."""
        lights = []
        
        # Sun
        sun = self._create_light("SUN", "SUN", location=(0, 0, 10))
        sun.rotation_euler = (math.radians(45), 0, math.radians(45))
        lights.append(sun)
        
        # Environment light
        world = bpy.context.scene.world
        if not world:
            world = bpy.data.worlds.new("World")
            bpy.context.scene.world = world
        
        world.use_nodes = True
        nodes = world.node_tree.nodes
        nodes["Background"].inputs[1].default_value = 1.0  # Strength
        
        return lights
    
    def _create_dramatic_lighting(self, requirements: Dict[str, Any]) -> List[bpy.types.Object]:
        """Create dramatic lighting setup."""
        lights = []
        
        main_light = self._create_light("MAIN", "SPOT", location=(3, -2, 4))
        main_light.data.energy = 1500.0
        main_light.data.spot_size = math.radians(30)
        lights.append(main_light)
        
        rim_light = self._create_light("RIM", "AREA", location=(-2, 3, 3))
        rim_light.data.energy = 800.0
        lights.append(rim_light)
        
        return lights
    
    def _create_basic_lighting(self, requirements: Dict[str, Any]) -> List[bpy.types.Object]:
        """Create basic lighting setup."""
        light = self._create_light("MAIN", "POINT", location=(0, 0, 5))
        light.data.energy = 1000.0
        return [light]
    
    def _create_light(self, name: str, light_type: str, location: tuple) -> bpy.types.Object:
        """Create a new light object."""
        light_data = bpy.data.lights.new(name=name, type=light_type)
        light_obj = bpy.data.objects.new(name=name, object_data=light_data)
        bpy.context.scene.collection.objects.link(light_obj)
        light_obj.location = location
        return light_obj
    
    def _apply_mood_settings(self, lights: List[bpy.types.Object], mood: str) -> None:
        """Apply mood-specific settings to lights."""
        if mood == "warm":
            color = (1.0, 0.9, 0.8, 1.0)
        elif mood == "cold":
            color = (0.8, 0.9, 1.0, 1.0)
        elif mood == "dramatic":
            color = (1.0, 0.95, 0.9, 1.0)
        else:
            color = (1.0, 1.0, 1.0, 1.0)
        
        for light in lights:
            light.data.color = color
    
    def _clear_existing_lights(self) -> None:
        """Remove all existing lights from the scene."""
        for obj in bpy.data.objects:
            if obj.type == 'LIGHT':
                bpy.data.objects.remove(obj, do_unlink=True)
    
    async def initialize(self) -> None:
        """Initialize lighting system resources."""
        # Load lighting presets
        await self._load_lighting_presets()
    
    async def _load_lighting_presets(self) -> None:
        """Load predefined lighting presets."""
        # Load lighting presets from configuration
        pass
    
    async def cleanup(self) -> None:
        """Cleanup lighting system resources."""
        self.lighting_presets.clear()
        self.active_lights.clear() 