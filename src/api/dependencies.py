from typing import Optional
from src.core.system_integrator import SystemIntegrator

# Global system instance
_system: Optional[SystemIntegrator] = None

async def get_system() -> SystemIntegrator:
    """Get or create system instance."""
    global _system
    if _system is None:
        _system = SystemIntegrator()
    return _system 