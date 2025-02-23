from typing import Dict, Any, List, Optional
import yaml
from pathlib import Path
import logging
from .config_validator import ConfigValidator

class SystemConfig:
    """System-wide configuration management."""
    
    def __init__(self, config_dir: str = "config"):
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.validator = ConfigValidator()
        
        # Load and validate configurations
        self.system_config = self._load_and_validate_config("system")
        self.agent_config = self._load_and_validate_config("agents")
        self.pipeline_config = self._load_and_validate_config("pipeline")
        self.resource_config = self._load_and_validate_config("resources")
    
    def _load_and_validate_config(self, config_name: str) -> Dict[str, Any]:
        """Load and validate configuration from YAML file."""
        config = self._load_config(config_name)
        
        # Validate configuration
        errors = self.validator.validate_config(config_name, config)
        if errors:
            for error in errors:
                self.logger.error(f"Configuration error in {config_name}: {error}")
            raise ValueError(f"Invalid configuration in {config_name}")
        
        return config
    
    def _load_config(self, config_name: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = self.config_dir / f"{config_name}.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def get_system_settings(self) -> Dict[str, Any]:
        """Get system-wide settings."""
        return self.system_config.get("settings", {})
    
    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """Get configuration for specific agent type."""
        return self.agent_config.get(agent_type, {})
    
    def get_pipeline_config(self, pipeline_name: str) -> Dict[str, Any]:
        """Get configuration for specific pipeline."""
        return self.pipeline_config.get(pipeline_name, {})
    
    def get_resource_config(self, resource_type: str) -> Dict[str, Any]:
        """Get configuration for specific resource type."""
        return self.resource_config.get(resource_type, {}) 