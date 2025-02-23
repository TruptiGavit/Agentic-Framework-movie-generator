from typing import Dict, Any, Optional
import click
import asyncio
import json
from datetime import datetime
from pathlib import Path
import logging

from src.core.agent_manager import AgentManager
from src.core.task_scheduler import TaskScheduler
from src.core.system_monitor import SystemMonitor
from src.core.message_bus import MessageBus

logger = logging.getLogger(__name__)

class CLIInterface:
    """Command-line interface for system control."""
    
    def __init__(self,
                 agent_manager: AgentManager,
                 task_scheduler: TaskScheduler,
                 system_monitor: SystemMonitor,
                 message_bus: MessageBus):
        self.agent_manager = agent_manager
        self.task_scheduler = task_scheduler
        self.system_monitor = system_monitor
        self.message_bus = message_bus
        self.setup_cli()
    
    def setup_cli(self):
        """Set up CLI commands."""
        
        @click.group()
        def cli():
            """AI Movie Generation System CLI"""
            pass
        
        @cli.command()
        @click.argument('scene_file', type=click.Path(exists=True))
        @click.option('--priority', default=0, help='Task priority')
        def generate(scene_file: str, priority: int):
            """Generate content from scene description file."""
            try:
                with open(scene_file, 'r') as f:
                    scene_data = json.load(f)
                
                task_id = asyncio.run(self._create_generation_task(
                    scene_data, priority
                ))
                click.echo(f"Generation task created: {task_id}")
            except Exception as e:
                click.echo(f"Error: {str(e)}", err=True)
        
        @cli.command()
        @click.argument('task_id')
        def status(task_id: str):
            """Get task status."""
            status = self.task_scheduler.get_task_status(task_id)
            if status:
                click.echo(f"Task {task_id}: {status}")
            else:
                click.echo(f"Task {task_id} not found", err=True)
        
        @cli.command()
        def metrics():
            """Show current system metrics."""
            metrics = self.system_monitor.get_current_metrics()
            if metrics:
                click.echo(json.dumps(metrics.__dict__, indent=2))
            else:
                click.echo("No metrics available", err=True)
        
        @cli.command()
        def agents():
            """List all registered agents."""
            agents = self.agent_manager.agents
            for agent_id, agent in agents.items():
                click.echo(f"{agent_id}: {agent.__class__.__name__}")
        
        @cli.command()
        @click.argument('agent_id')
        def agent_info(agent_id: str):
            """Show detailed agent information."""
            agent = self.agent_manager.get_agent(agent_id)
            if agent:
                info = {
                    "id": agent.agent_id,
                    "type": agent.__class__.__name__,
                    "status": "active" if agent in self.agent_manager.agents.values() else "inactive"
                }
                click.echo(json.dumps(info, indent=2))
            else:
                click.echo(f"Agent {agent_id} not found", err=True)
        
        @cli.command()
        @click.argument('task_id')
        def cancel(task_id: str):
            """Cancel a running task."""
            try:
                asyncio.run(self.task_scheduler.cancel_task(task_id))
                click.echo(f"Task {task_id} cancelled")
            except Exception as e:
                click.echo(f"Error: {str(e)}", err=True)
        
        @cli.command()
        def alerts():
            """Show active system alerts."""
            alerts = self.system_monitor.get_active_alerts()
            if alerts:
                click.echo(json.dumps(alerts, indent=2))
            else:
                click.echo("No active alerts")
        
        self.cli = cli
    
    async def _create_generation_task(self, scene_data: Dict[str, Any],
                                    priority: int) -> str:
        """Create a generation task."""
        task = Task(
            task_id="",
            agent_id="scene_interpreter",
            task_type="interpret_scene",
            payload={"scene_data": scene_data},
            scheduled_time=datetime.now(),
            priority=priority
        )
        return await self.task_scheduler.schedule_task(task)
    
    def run(self):
        """Run the CLI."""
        self.cli() 