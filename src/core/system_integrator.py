from typing import Dict, Any, Optional, List
import asyncio
import logging
from pathlib import Path
from datetime import datetime

from src.core.agent_manager import AgentManager
from src.core.message_bus import MessageBus
from src.core.task_scheduler import TaskScheduler
from src.core.system_monitor import SystemMonitor
from src.core.config_manager import ConfigManager
from src.core.event_handler import EventHandler
from src.core.error_handler import ErrorHandler
from src.core.system_lifecycle import SystemLifecycleManager
from src.core.config.config_monitor import ConfigMonitor

class SystemIntegrator:
    """Coordinates and integrates all system components."""
    
    def __init__(self, config_path: str = "config"):
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.config_manager = ConfigManager(config_path)
        self.message_bus = MessageBus()
        self.event_handler = EventHandler()
        self.error_handler = ErrorHandler(self.event_handler)
        self.task_scheduler = TaskScheduler()
        self.system_monitor = SystemMonitor()
        self.agent_manager = AgentManager(self.message_bus)
        
        # Initialize lifecycle manager
        self.lifecycle_manager = SystemLifecycleManager(
            self.config_manager,
            self.agent_manager,
            self.task_scheduler,
            self.system_monitor,
            self.message_bus,
            self.event_handler
        )
        
        # Initialize config monitor
        self.config_monitor = ConfigMonitor(self.config_manager)
        
        # Register configuration callbacks
        self._register_config_callbacks()
        
        # System state
        self.is_running = False
        self.active_projects: Dict[str, Dict[str, Any]] = {}
    
    async def initialize_system(self):
        """Initialize the entire system."""
        try:
            self.logger.info("Initializing system...")
            await self.lifecycle_manager.start_system()
            
            # Register core event handlers
            self._register_event_handlers()
            
            # Initialize agents
            await self._initialize_agents()
            
            self.is_running = True
            self.logger.info("System initialization complete")
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {str(e)}")
            raise
    
    async def shutdown_system(self):
        """Shutdown the entire system."""
        try:
            self.logger.info("Shutting down system...")
            await self.lifecycle_manager.stop_system()
            self.is_running = False
            self.logger.info("System shutdown complete")
            
        except Exception as e:
            self.logger.error(f"System shutdown failed: {str(e)}")
            raise
    
    async def _initialize_agents(self):
        """Initialize all required agents."""
        # Story agents
        await self._initialize_story_agents()
        
        # Visual agents
        await self._initialize_visual_agents()
        
        # Audio agents
        await self._initialize_audio_agents()
        
        # Quality agents
        await self._initialize_quality_agents()
    
    async def _initialize_story_agents(self):
        """Initialize story-related agents."""
        from src.agents.story.plot_generator import PlotGenerator
        from src.agents.story.scene_planner import ScenePlanner
        from src.agents.story.character_developer import CharacterDeveloper
        from src.agents.story.dialogue_generator import DialogueGenerator
        
        await self.agent_manager.register_agent(PlotGenerator("plot_generator"))
        await self.agent_manager.register_agent(ScenePlanner("scene_planner"))
        await self.agent_manager.register_agent(CharacterDeveloper("character_developer"))
        await self.agent_manager.register_agent(DialogueGenerator("dialogue_generator"))
    
    async def _initialize_visual_agents(self):
        """Initialize visual-related agents."""
        from src.agents.visual.scene_interpreter import SceneInterpreter
        from src.agents.visual.prompt_engineer import PromptEngineer
        from src.agents.visual.image_generator import ImageGenerator
        from src.agents.visual.animation_controller import AnimationController
        from src.agents.visual.camera_designer import CameraDesigner
        
        await self.agent_manager.register_agent(SceneInterpreter("scene_interpreter"))
        await self.agent_manager.register_agent(PromptEngineer("prompt_engineer"))
        await self.agent_manager.register_agent(ImageGenerator("image_generator"))
        await self.agent_manager.register_agent(AnimationController("animation_controller"))
        await self.agent_manager.register_agent(CameraDesigner("camera_designer"))
    
    async def _initialize_audio_agents(self):
        """Initialize audio-related agents."""
        from src.agents.audio.music_composer import MusicComposer
        from src.agents.audio.sound_effect_generator import SoundEffectGenerator
        from src.agents.audio.voice_generator import VoiceGenerator
        from src.agents.audio.audio_mixer import AudioMixer
        
        await self.agent_manager.register_agent(MusicComposer("music_composer"))
        await self.agent_manager.register_agent(SoundEffectGenerator("sfx_generator"))
        await self.agent_manager.register_agent(VoiceGenerator("voice_generator"))
        await self.agent_manager.register_agent(AudioMixer("audio_mixer"))
    
    async def _initialize_quality_agents(self):
        """Initialize quality control agents."""
        from src.agents.quality.continuity_checker import ContinuityChecker
        from src.agents.quality.technical_validator import TechnicalValidator
        from src.agents.quality.content_moderator import ContentModerator
        from src.agents.quality.feedback_analyzer import FeedbackAnalyzer
        
        await self.agent_manager.register_agent(ContinuityChecker("continuity_checker"))
        await self.agent_manager.register_agent(TechnicalValidator("technical_validator"))
        await self.agent_manager.register_agent(ContentModerator("content_moderator"))
        await self.agent_manager.register_agent(FeedbackAnalyzer("feedback_analyzer"))
    
    def _register_event_handlers(self):
        """Register system-wide event handlers."""
        self.event_handler.register_handler(
            "system_error",
            self._handle_system_error
        )
        self.event_handler.register_handler(
            "resource_warning",
            self._handle_resource_warning
        )
        self.event_handler.register_handler(
            "agent_status_change",
            self._handle_agent_status_change
        )
    
    def _register_config_callbacks(self):
        """Register configuration change callbacks."""
        self.config_monitor.register_callback("system", self._handle_system_config_change)
        self.config_monitor.register_callback("agents", self._handle_agent_config_change)
        self.config_monitor.register_callback("pipeline", self._handle_pipeline_config_change)
        self.config_monitor.register_callback("resources", self._handle_resource_config_change)
    
    async def _handle_system_config_change(self, config: Dict[str, Any]):
        """Handle system configuration changes."""
        self.logger.info("Applying system configuration changes...")
        # Update system settings
        await self.system_monitor.update_settings(config.get("settings", {}))
        await self.task_scheduler.update_settings(config.get("performance", {}))
    
    async def _handle_agent_config_change(self, config: Dict[str, Any]):
        """Handle agent configuration changes."""
        self.logger.info("Applying agent configuration changes...")
        await self.agent_manager.update_agent_configs(config)
    
    async def _handle_pipeline_config_change(self, config: Dict[str, Any]):
        """Handle pipeline configuration changes."""
        self.logger.info("Applying pipeline configuration changes...")
        try:
            # Update pipeline configurations
            for pipeline_type, pipeline_config in config.items():
                # Update stage timeouts and settings
                await self.task_scheduler.update_pipeline_config(pipeline_type, pipeline_config)
                
                # Notify affected agents of pipeline changes
                for stage in pipeline_config.get("stages", []):
                    agent_id = stage.get("agent")
                    if agent_id:
                        await self.agent_manager.notify_pipeline_update(agent_id, {
                            "pipeline": pipeline_type,
                            "stage": stage["name"],
                            "config": stage
                        })
            
            self.logger.info("Pipeline configuration updates applied successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to apply pipeline configuration changes: {str(e)}")
            raise
    
    async def _handle_resource_config_change(self, config: Dict[str, Any]):
        """Handle resource configuration changes."""
        self.logger.info("Applying resource configuration changes...")
        try:
            # Update model configurations
            if "models" in config:
                await self._update_model_configs(config["models"])
            
            # Update storage configurations
            if "storage" in config:
                await self._update_storage_configs(config["storage"])
            
            # Update compute configurations
            if "compute" in config:
                await self._update_compute_configs(config["compute"])
            
            self.logger.info("Resource configuration updates applied successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to apply resource configuration changes: {str(e)}")
            raise
    
    async def _update_model_configs(self, model_configs: Dict[str, Any]):
        """Update model-specific configurations."""
        # Update language model settings
        if "language" in model_configs:
            await self.agent_manager.update_model_configs("language", model_configs["language"])
        
        # Update image model settings
        if "image" in model_configs:
            await self.agent_manager.update_model_configs("image", model_configs["image"])
        
        # Update audio model settings
        if "audio" in model_configs:
            await self.agent_manager.update_model_configs("audio", model_configs["audio"])
    
    async def _update_storage_configs(self, storage_configs: Dict[str, Any]):
        """Update storage-related configurations."""
        # Update project file storage settings
        if "project_files" in storage_configs:
            project_storage = storage_configs["project_files"]
            await self._ensure_storage_directory(project_storage["path"])
            await self.system_monitor.update_storage_limits(
                "project_files",
                project_storage.get("max_size")
            )
        
        # Update temporary file settings
        if "temp_files" in storage_configs:
            temp_storage = storage_configs["temp_files"]
            await self._ensure_storage_directory(temp_storage["path"])
            await self.task_scheduler.update_cleanup_interval(
                temp_storage.get("cleanup_interval", 3600)
            )
        
        # Update output file settings
        if "output_files" in storage_configs:
            output_storage = storage_configs["output_files"]
            await self._ensure_storage_directory(output_storage["path"])
            await self.system_monitor.update_retention_period(
                output_storage.get("retention_period", 30)
            )
    
    async def _update_compute_configs(self, compute_configs: Dict[str, Any]):
        """Update compute-related configurations."""
        # Update GPU settings
        if "gpu" in compute_configs:
            gpu_config = compute_configs["gpu"]
            await self.task_scheduler.update_gpu_settings({
                "allocation_strategy": gpu_config.get("allocation_strategy"),
                "memory_buffer": gpu_config.get("memory_buffer")
            })
        
        # Update CPU settings
        if "cpu" in compute_configs:
            cpu_config = compute_configs["cpu"]
            await self.task_scheduler.update_cpu_settings({
                "max_threads": cpu_config.get("max_threads"),
                "priority": cpu_config.get("priority")
            })
    
    async def _ensure_storage_directory(self, directory_path: str):
        """Ensure storage directory exists and is accessible."""
        try:
            path = Path(directory_path)
            path.mkdir(parents=True, exist_ok=True)
            
            # Verify write permissions
            test_file = path / ".test_write"
            test_file.touch()
            test_file.unlink()
            
        except Exception as e:
            self.logger.error(f"Failed to setup storage directory {directory_path}: {str(e)}")
            raise
    
    async def create_project(self, project_data: Dict[str, Any]) -> str:
        """Create a new project."""
        project_id = f"proj_{datetime.now().timestamp()}"
        
        try:
            # Initialize project resources
            self.active_projects[project_id] = {
                "data": project_data,
                "status": "initializing",
                "timestamp": datetime.now().isoformat()
            }
            
            # Create project structure
            await self._create_project_structure(project_id)
            
            # Start project pipeline
            await self._start_project_pipeline(project_id, project_data)
            
            return project_id
            
        except Exception as e:
            self.logger.error(f"Project creation failed: {str(e)}")
            raise 