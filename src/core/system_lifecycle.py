from typing import Dict, Any, List, Optional
import asyncio
import logging
from enum import Enum
from datetime import datetime

from src.core.agent_manager import AgentManager
from src.core.task_scheduler import TaskScheduler
from src.core.system_monitor import SystemMonitor
from src.core.message_bus import MessageBus
from src.core.config_manager import ConfigManager
from src.core.event_handler import EventHandler, Event, EventPriority

class SystemState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

class SystemLifecycleManager:
    """Manages system startup and shutdown sequences."""
    
    def __init__(self,
                 config_manager: ConfigManager,
                 agent_manager: AgentManager,
                 task_scheduler: TaskScheduler,
                 system_monitor: SystemMonitor,
                 message_bus: MessageBus,
                 event_handler: EventHandler):
        self.config_manager = config_manager
        self.agent_manager = agent_manager
        self.task_scheduler = task_scheduler
        self.system_monitor = system_monitor
        self.message_bus = message_bus
        self.event_handler = event_handler
        
        self.state = SystemState.STOPPED
        self.logger = logging.getLogger(__name__)
        
        # Component status tracking
        self.component_status: Dict[str, bool] = {
            "config": False,
            "message_bus": False,
            "event_handler": False,
            "task_scheduler": False,
            "system_monitor": False,
            "agents": False
        }
        
        # Startup/shutdown hooks
        self.startup_hooks: List[callable] = []
        self.shutdown_hooks: List[callable] = []
    
    async def start_system(self):
        """Start the system in the correct sequence."""
        try:
            self.state = SystemState.STARTING
            await self._emit_lifecycle_event("system_starting")
            
            # Initialize configuration
            await self._start_component("config", self.config_manager.initialize)
            
            # Start message bus
            await self._start_component("message_bus", self.message_bus.start)
            
            # Start event handler
            await self._start_component("event_handler", self.event_handler.start)
            
            # Start task scheduler
            await self._start_component("task_scheduler", self.task_scheduler.start)
            
            # Start system monitor
            await self._start_component("system_monitor", self.system_monitor.start)
            
            # Start all agents
            await self._start_component("agents", self.agent_manager.start_all_agents)
            
            # Run startup hooks
            await self._run_hooks(self.startup_hooks)
            
            self.state = SystemState.RUNNING
            await self._emit_lifecycle_event("system_started")
            
            self.logger.info("System started successfully")
            
        except Exception as e:
            self.state = SystemState.ERROR
            self.logger.error(f"System startup failed: {str(e)}")
            await self._emit_lifecycle_event("system_startup_failed", {"error": str(e)})
            raise
    
    async def stop_system(self):
        """Stop the system in the correct sequence."""
        try:
            self.state = SystemState.STOPPING
            await self._emit_lifecycle_event("system_stopping")
            
            # Run shutdown hooks
            await self._run_hooks(self.shutdown_hooks)
            
            # Stop agents first
            await self._stop_component("agents", self.agent_manager.stop_all_agents)
            
            # Stop system monitor
            await self._stop_component("system_monitor", self.system_monitor.stop)
            
            # Stop task scheduler
            await self._stop_component("task_scheduler", self.task_scheduler.stop)
            
            # Stop event handler
            await self._stop_component("event_handler", self.event_handler.stop)
            
            # Stop message bus last
            await self._stop_component("message_bus", self.message_bus.stop)
            
            self.state = SystemState.STOPPED
            await self._emit_lifecycle_event("system_stopped")
            
            self.logger.info("System stopped successfully")
            
        except Exception as e:
            self.state = SystemState.ERROR
            self.logger.error(f"System shutdown failed: {str(e)}")
            await self._emit_lifecycle_event("system_shutdown_failed", {"error": str(e)})
            raise
    
    async def _start_component(self, name: str, start_func: callable):
        """Start a system component."""
        try:
            self.logger.info(f"Starting {name}")
            await start_func()
            self.component_status[name] = True
            await self._emit_lifecycle_event(f"{name}_started")
        except Exception as e:
            self.logger.error(f"Failed to start {name}: {str(e)}")
            raise
    
    async def _stop_component(self, name: str, stop_func: callable):
        """Stop a system component."""
        try:
            self.logger.info(f"Stopping {name}")
            await stop_func()
            self.component_status[name] = False
            await self._emit_lifecycle_event(f"{name}_stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop {name}: {str(e)}")
            raise
    
    async def _emit_lifecycle_event(self, event_type: str, data: Dict[str, Any] = None):
        """Emit a lifecycle event."""
        if self.event_handler:
            event = Event(
                event_type=f"lifecycle_{event_type}",
                source="system_lifecycle",
                data=data or {},
                priority=EventPriority.HIGH
            )
            await self.event_handler.emit_event(event)
    
    async def _run_hooks(self, hooks: List[callable]):
        """Run lifecycle hooks."""
        for hook in hooks:
            try:
                await hook()
            except Exception as e:
                self.logger.error(f"Hook execution failed: {str(e)}")
    
    def add_startup_hook(self, hook: callable):
        """Add a startup hook."""
        self.startup_hooks.append(hook)
    
    def add_shutdown_hook(self, hook: callable):
        """Add a shutdown hook."""
        self.shutdown_hooks.append(hook)
    
    def get_system_state(self) -> SystemState:
        """Get current system state."""
        return self.state
    
    def get_component_status(self) -> Dict[str, bool]:
        """Get status of all components."""
        return self.component_status.copy() 