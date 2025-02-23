from typing import Dict, Optional, Type, Any
from src.core.base_agent import BaseAgent
from src.core.message_bus import MessageBus
import asyncio
import logging

class AgentManager:
    """Manages agent lifecycle and coordination."""
    
    def __init__(self, message_bus: MessageBus):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_bus = message_bus
        self.logger = logging.getLogger(__name__)
    
    async def register_agent(self, agent: BaseAgent):
        """Register a new agent."""
        if agent.agent_id in self.agents:
            raise ValueError(f"Agent with ID {agent.agent_id} already exists")
        
        self.agents[agent.agent_id] = agent
        await agent.initialize()
        
        # Register agent's message handlers
        for message_type, handler in agent.get_message_handlers().items():
            self.message_bus.register_route(MessageRoute(
                source="*",
                destination=agent.agent_id,
                message_type=message_type,
                handler=handler
            ))
    
    async def unregister_agent(self, agent_id: str):
        """Unregister an agent."""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            await agent.cleanup()
            del self.agents[agent_id]
    
    async def start_all_agents(self):
        """Start all registered agents."""
        for agent in self.agents.values():
            try:
                await agent.initialize()
            except Exception as e:
                self.logger.error(f"Error starting agent {agent.agent_id}: {str(e)}")
    
    async def stop_all_agents(self):
        """Stop all registered agents."""
        for agent in self.agents.values():
            try:
                await agent.cleanup()
            except Exception as e:
                self.logger.error(f"Error stopping agent {agent.agent_id}: {str(e)}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    async def send_message_to_agent(self, agent_id: str, message: Any):
        """Send a message to a specific agent."""
        if agent_id in self.agents:
            await self.message_bus.publish(message)
        else:
            raise ValueError(f"Agent {agent_id} not found") 