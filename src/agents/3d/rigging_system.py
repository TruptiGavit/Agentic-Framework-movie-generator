from typing import Optional, Dict, Any, List
from src.agents.3d.base_3d_agent import Base3DAgent
from src.core.base_agent import Message
import bpy

class RiggingSystem(Base3DAgent):
    """Agent responsible for creating and managing character rigs."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.rig_templates: Dict[str, Any] = {}
        self.active_rigs: Dict[str, Any] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "create_rig":
            return await self._create_rig(message)
        elif message.message_type == "setup_animation":
            return await self._setup_animation(message)
        elif message.message_type == "apply_pose":
            return await self._apply_pose(message)
        return None
    
    async def _create_rig(self, message: Message) -> Message:
        """Create a rig for a character model."""
        model_data = message.content.get("model_data", {})
        rig_type = message.content.get("rig_type", "humanoid")
        
        rig_data = await self._generate_rig(model_data, rig_type)
        
        return Message(
            message_id=f"rig_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="rig_created",
            content={"rig_data": rig_data},
            context=message.context,
            metadata={"rig_type": rig_type}
        )
    
    async def _generate_rig(self, model_data: Dict[str, Any], rig_type: str) -> Dict[str, Any]:
        """Generate a rig based on the model and type."""
        try:
            # Select the model
            model_name = model_data.get("model_name", "")
            model = bpy.data.objects.get(model_name)
            
            if not model:
                raise ValueError(f"Model {model_name} not found")
            
            # Create armature
            bpy.ops.object.armature_add()
            armature = bpy.context.active_object
            armature.name = f"{model_name}_armature"
            
            if rig_type == "humanoid":
                bones = self._create_humanoid_rig(armature, model_data)
            else:
                bones = self._create_basic_rig(armature, model_data)
            
            # Parent model to armature
            model.parent = armature
            model.modifiers.new(name="Armature", type='ARMATURE')
            model.modifiers["Armature"].object = armature
            
            return {
                "rig_name": armature.name,
                "bone_count": len(bones),
                "model_name": model_name,
                "rig_type": rig_type
            }
            
        except Exception as e:
            print(f"Error generating rig: {str(e)}")
            return {}
    
    def _create_humanoid_rig(self, armature: bpy.types.Object, model_data: Dict[str, Any]) -> List[str]:
        """Create a humanoid character rig."""
        bones = []
        
        # Enter edit mode to add bones
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Add basic bone structure
        bone_names = ["spine", "neck", "head", "shoulder.L", "shoulder.R", 
                     "upper_arm.L", "upper_arm.R", "forearm.L", "forearm.R",
                     "hand.L", "hand.R", "thigh.L", "thigh.R", 
                     "shin.L", "shin.R", "foot.L", "foot.R"]
        
        for name in bone_names:
            bone = armature.data.edit_bones.new(name)
            bones.append(bone.name)
        
        # Set up bone hierarchy and positions
        # This would be more detailed in a full implementation
        
        bpy.ops.object.mode_set(mode='OBJECT')
        return bones
    
    def _create_basic_rig(self, armature: bpy.types.Object, model_data: Dict[str, Any]) -> List[str]:
        """Create a basic rig structure."""
        bones = []
        
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Add a simple bone chain
        bone = armature.data.edit_bones.new("root")
        bones.append(bone.name)
        
        bpy.ops.object.mode_set(mode='OBJECT')
        return bones
    
    async def _setup_animation(self, message: Message) -> Message:
        """Set up animation controls for a rig."""
        rig_data = message.content.get("rig_data", {})
        animation_type = message.content.get("animation_type", "")
        
        # Setup animation controls and constraints
        # This would be implemented based on the animation requirements
        
        return Message(
            message_id=f"anim_setup_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="animation_setup_complete",
            content={"status": "success"},
            context=message.context,
            metadata={"animation_type": animation_type}
        )
    
    async def initialize(self) -> None:
        """Initialize rigging system resources."""
        # Load rig templates and setup Blender environment
        pass
    
    async def cleanup(self) -> None:
        """Cleanup rigging system resources."""
        self.active_rigs.clear()
        self.rig_templates.clear() 