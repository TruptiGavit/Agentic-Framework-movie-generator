from typing import Optional, Dict, Any
from src.core.base_agent import BaseAgent, Message

class BaseQualityAgent(BaseAgent):
    """Base class for all quality control agents."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.quality_metrics: Dict[str, Any] = {}
        self.validation_rules: Dict[str, Any] = {}
    
    async def update_validation_rules(self, rules: Dict[str, Any]) -> None:
        """Update the validation rules."""
        self.validation_rules.update(rules) 