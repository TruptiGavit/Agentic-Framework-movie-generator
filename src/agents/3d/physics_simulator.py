from typing import Optional, Dict, Any, List
from src.agents.3d.base_3d_agent import Base3DAgent
from src.core.base_agent import Message
import bpy

class PhysicsSimulator(Base3DAgent):
    """Agent responsible for physics simulations in the scene."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.physics_settings: Dict[str, Any] = {}
        self.active_simulations: Dict[str, Any] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "setup_physics":
            return await self._setup_physics(message)
        elif message.message_type == "run_simulation":
            return await self._run_simulation(message)
        elif message.message_type == "modify_physics":
            return await self._modify_physics(message)
        return None
    
    async def _setup_physics(self, message: Message) -> Message:
        """Set up physics properties for objects in the scene."""
        scene_objects = message.content.get("objects", [])
        physics_requirements = message.content.get("physics_requirements", {})
        
        physics_data = await self._configure_physics(scene_objects, physics_requirements)
        
        return Message(
            message_id=f"physics_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="physics_setup_complete",
            content={"physics_data": physics_data},
            context=message.context,
            metadata={"requirements": physics_requirements}
        )
    
    async def _configure_physics(self, objects: List[str], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Configure physics properties for objects."""
        try:
            scene = bpy.context.scene
            scene.use_gravity = requirements.get("use_gravity", True)
            scene.gravity = requirements.get("gravity", (0.0, 0.0, -9.81))
            
            configured_objects = []
            
            for obj_name in objects:
                obj = bpy.data.objects.get(obj_name)
                if obj:
                    physics_type = requirements.get("physics_type", "RIGID_BODY")
                    self._setup_object_physics(obj, physics_type, requirements)
                    configured_objects.append(obj_name)
            
            return {
                "configured_objects": configured_objects,
                "gravity": scene.gravity,
                "physics_settings": requirements
            }
            
        except Exception as e:
            print(f"Error configuring physics: {str(e)}")
            return {}
    
    def _setup_object_physics(self, obj: bpy.types.Object, physics_type: str, settings: Dict[str, Any]) -> None:
        """Set up physics properties for a single object."""
        if physics_type == "RIGID_BODY":
            self._setup_rigid_body(obj, settings)
        elif physics_type == "SOFT_BODY":
            self._setup_soft_body(obj, settings)
        elif physics_type == "CLOTH":
            self._setup_cloth(obj, settings)
        elif physics_type == "FLUID":
            self._setup_fluid(obj, settings)
    
    def _setup_rigid_body(self, obj: bpy.types.Object, settings: Dict[str, Any]) -> None:
        """Configure rigid body physics."""
        bpy.context.view_layer.objects.active = obj
        bpy.ops.rigidbody.object_add()
        
        rb = obj.rigid_body
        rb.type = settings.get("body_type", "ACTIVE")
        rb.mass = settings.get("mass", 1.0)
        rb.friction = settings.get("friction", 0.5)
        rb.restitution = settings.get("restitution", 0.0)
        rb.collision_shape = settings.get("collision_shape", "CONVEX_HULL")
    
    def _setup_soft_body(self, obj: bpy.types.Object, settings: Dict[str, Any]) -> None:
        """Configure soft body physics."""
        sb = obj.modifiers.new(name="Soft Body", type='SOFT_BODY')
        
        sb.settings.mass = settings.get("mass", 1.0)
        sb.settings.spring_k = settings.get("spring_stiffness", 0.5)
        sb.settings.damping = settings.get("damping", 0.5)
        sb.settings.use_goal = settings.get("use_goal", False)
    
    def _setup_cloth(self, obj: bpy.types.Object, settings: Dict[str, Any]) -> None:
        """Configure cloth physics."""
        cloth = obj.modifiers.new(name="Cloth", type='CLOTH')
        
        cloth.settings.mass = settings.get("mass", 1.0)
        cloth.settings.tension_stiffness = settings.get("tension", 15.0)
        cloth.settings.compression_stiffness = settings.get("compression", 15.0)
        cloth.settings.shear_stiffness = settings.get("shear", 5.0)
    
    def _setup_fluid(self, obj: bpy.types.Object, settings: Dict[str, Any]) -> None:
        """Configure fluid physics."""
        fluid = obj.modifiers.new(name="Fluid", type='FLUID')
        
        fluid.fluid_type = settings.get("fluid_type", "DOMAIN")
        if fluid.fluid_type == "DOMAIN":
            fluid.domain_settings.resolution_max = settings.get("resolution", 64)
            fluid.domain_settings.use_adaptive_domain = settings.get("adaptive_domain", True)
    
    async def _run_simulation(self, message: Message) -> Message:
        """Run physics simulation for specified frame range."""
        frame_range = message.content.get("frame_range", (1, 250))
        simulation_settings = message.content.get("simulation_settings", {})
        
        # Configure simulation settings
        scene = bpy.context.scene
        scene.frame_start = frame_range[0]
        scene.frame_end = frame_range[1]
        
        # Run simulation
        bpy.ops.ptcache.bake_all(bake=True)
        
        return Message(
            message_id=f"sim_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="simulation_complete",
            content={"frame_range": frame_range},
            context=message.context,
            metadata={"settings": simulation_settings}
        )
    
    async def initialize(self) -> None:
        """Initialize physics simulation resources."""
        scene = bpy.context.scene
        scene.use_gravity = True
        scene.gravity = (0.0, 0.0, -9.81)
    
    async def cleanup(self) -> None:
        """Cleanup physics simulation resources."""
        # Clear physics caches
        bpy.ops.ptcache.free_bake_all()
        self.active_simulations.clear() 