from typing import Dict, Any, Optional
import yaml
import json
from pathlib import Path
import logging
from dataclasses import dataclass
from datetime import datetime
import asyncio
import os

@dataclass
class SystemConfig:
    """System-wide configuration settings."""
    version: str
    environment: str
    log_level: str
    paths: Dict[str, Path]
    agent_configs: Dict[str, Dict[str, Any]]
    performance_settings: Dict[str, Any]
    resource_limits: Dict[str, Any]
    api_settings: Dict[str, Any]

class ConfigManager:
    """Manages system-wide configuration and settings."""
    
    def __init__(self, config_path: str = "config"):
        self.config_dir = Path(config_path)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Main configuration files
        self.main_config_file = self.config_dir / "system_config.yaml"
        self.agent_config_file = self.config_dir / "agent_config.yaml"
        self.resource_config_file = self.config_dir / "resource_config.yaml"
        
        # Active configuration
        self.current_config: Optional[SystemConfig] = None
        self.config_watchers: Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration defaults
        self.default_config = {
            "version": "1.0.0",
            "environment": "development",
            "log_level": "INFO",
            "paths": {
                "output": "outputs",
                "cache": "cache",
                "logs": "logs",
                "data": "data"
            },
            "performance_settings": {
                "max_concurrent_tasks": 10,
                "task_timeout": 3600,
                "queue_size": 1000
            },
            "resource_limits": {
                "max_memory": "8G",
                "max_cpu_percent": 80,
                "max_gpu_memory": "6G"
            },
            "api_settings": {
                "host": "localhost",
                "port": 8000,
                "debug": False
            }
        }
    
    async def initialize(self):
        """Initialize configuration system."""
        # Load or create initial configuration
        if not self.main_config_file.exists():
            await self._create_default_config()
        
        # Load configuration
        await self.load_config()
        
        # Start configuration watchers
        await self._start_config_watchers()
    
    async def load_config(self):
        """Load configuration from files."""
        try:
            # Load main config
            with open(self.main_config_file, 'r') as f:
                main_config = yaml.safe_load(f)
            
            # Load agent config
            with open(self.agent_config_file, 'r') as f:
                agent_config = yaml.safe_load(f)
            
            # Load resource config
            with open(self.resource_config_file, 'r') as f:
                resource_config = yaml.safe_load(f)
            
            # Merge configurations
            config = {
                **main_config,
                "agent_configs": agent_config,
                "resource_limits": resource_config
            }
            
            # Convert paths to Path objects
            config["paths"] = {k: Path(v) for k, v in config["paths"].items()}
            
            # Create SystemConfig instance
            self.current_config = SystemConfig(**config)
            
            self.logger.info("Configuration loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    async def save_config(self):
        """Save current configuration to files."""
        if not self.current_config:
            return
        
        try:
            # Convert config to dict
            config_dict = {
                "version": self.current_config.version,
                "environment": self.current_config.environment,
                "log_level": self.current_config.log_level,
                "paths": {k: str(v) for k, v in self.current_config.paths.items()},
                "performance_settings": self.current_config.performance_settings,
                "api_settings": self.current_config.api_settings
            }
            
            # Save main config
            with open(self.main_config_file, 'w') as f:
                yaml.safe_dump(config_dict, f)
            
            # Save agent config
            with open(self.agent_config_file, 'w') as f:
                yaml.safe_dump(self.current_config.agent_configs, f)
            
            # Save resource config
            with open(self.resource_config_file, 'w') as f:
                yaml.safe_dump(self.current_config.resource_limits, f)
            
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            raise
    
    async def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values."""
        if not self.current_config:
            await self.load_config()
        
        try:
            # Update configuration
            for key, value in updates.items():
                if hasattr(self.current_config, key):
                    setattr(self.current_config, key, value)
            
            # Save updated configuration
            await self.save_config()
            
            self.logger.info("Configuration updated successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {str(e)}")
            raise
    
    async def _create_default_config(self):
        """Create default configuration files."""
        try:
            # Create main config
            with open(self.main_config_file, 'w') as f:
                yaml.safe_dump(self.default_config, f)
            
            # Create agent config
            with open(self.agent_config_file, 'w') as f:
                yaml.safe_dump({}, f)
            
            # Create resource config
            with open(self.resource_config_file, 'w') as f:
                yaml.safe_dump(self.default_config["resource_limits"], f)
            
            self.logger.info("Default configuration created")
            
        except Exception as e:
            self.logger.error(f"Error creating default configuration: {str(e)}")
            raise
    
    async def _start_config_watchers(self):
        """Start watching configuration files for changes."""
        for config_file in [self.main_config_file, 
                          self.agent_config_file,
                          self.resource_config_file]:
            self.config_watchers[str(config_file)] = asyncio.create_task(
                self._watch_config_file(config_file)
            )
    
    async def _watch_config_file(self, config_file: Path):
        """Watch a configuration file for changes."""
        last_modified = config_file.stat().st_mtime
        
        while True:
            try:
                current_modified = config_file.stat().st_mtime
                if current_modified > last_modified:
                    await self.load_config()
                    last_modified = current_modified
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Error watching config file: {str(e)}")
                await asyncio.sleep(5) 