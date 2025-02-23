from typing import Optional
from src.core.base_agent import BaseAgent, Message
from src.core.state_manager import StateManager, ProjectState

class ControllerAgent(BaseAgent):
    """Main orchestrator agent that coordinates the movie generation process."""
    
    def __init__(self, agent_id: str, state_manager: StateManager):
        super().__init__(agent_id)
        self.state_manager = state_manager
        self.current_project: Optional[ProjectState] = None
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages and coordinate with other agents."""
        if message.message_type == "start_project":
            return await self._handle_start_project(message)
        elif message.message_type == "update_state":
            return await self._handle_state_update(message)
        # Add more message handlers
        
        return None
    
    async def _handle_start_project(self, message: Message) -> Message:
        """Handle new project creation request."""
        project_id = message.content["project_id"]
        self.current_project = ProjectState(project_id=project_id)
        await self.state_manager.save_state(self.current_project)
        
        return Message(
            message_id="response_1",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="project_started",
            content={"project_id": project_id},
            context={},
            metadata={}
        )
    
    async def _handle_state_update(self, message: Message) -> None:
        """Handle project state updates."""
        if self.current_project:
            # Update project state based on message content
            await self.state_manager.save_state(self.current_project)
    
    async def initialize(self) -> None:
        """Initialize controller agent."""
        # Add initialization logic
        pass
    
    async def cleanup(self) -> None:
        """Cleanup controller agent resources."""
        # Add cleanup logic
        pass 