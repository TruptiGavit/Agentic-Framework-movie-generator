from typing import Dict, Any
from redis import Redis
from pydantic import BaseModel

class ProjectState(BaseModel):
    """Manages the state of an ongoing movie generation project."""
    
    project_id: str
    scenes: Dict[str, Any] = {}
    characters: Dict[str, Any] = {}
    assets: Dict[str, Any] = {}
    context_history: list = []
    generation_queue: list = []

class StateManager:
    """Manages state persistence and retrieval."""
    
    def __init__(self, redis_url: str):
        self.redis_client = Redis.from_url(redis_url)
    
    async def save_state(self, state: ProjectState) -> None:
        """Save project state to Redis."""
        await self.redis_client.set(
            f"project:{state.project_id}",
            state.json()
        )
    
    async def load_state(self, project_id: str) -> ProjectState:
        """Load project state from Redis."""
        state_data = await self.redis_client.get(f"project:{project_id}")
        return ProjectState.parse_raw(state_data) 