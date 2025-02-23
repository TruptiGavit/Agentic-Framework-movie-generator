from typing import Dict, Any, Optional, List
import yaml
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from .system_config import SystemConfig
from .config_validator import ConfigValidator

class ConfigManager:
    """Manages configuration loading, updating, and reloading."""
    
    def __init__(self, config_dir: str = "config"):
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path(config_dir)
        self.validator = ConfigValidator()
        
        # Initialize system config
        self.system_config = SystemConfig(config_dir)
        
        # Track configuration versions
        self.config_versions: Dict[str, str] = {}
        self._track_config_versions()
        
        # Configuration update lock
        self._update_lock = asyncio.Lock()
    
    def _track_config_versions(self):
        """Track configuration file versions using timestamps."""
        for config_file in self.config_dir.glob("*.yaml"):
            self.config_versions[config_file.stem] = self._get_file_version(config_file)
    
    def _get_file_version(self, file_path: Path) -> str:
        """Get file version based on modification time."""
        return str(file_path.stat().st_mtime)
    
    async def check_for_updates(self) -> List[str]:
        """Check for configuration file updates."""
        updated_configs = []
        
        for config_file in self.config_dir.glob("*.yaml"):
            current_version = self._get_file_version(config_file)
            if current_version != self.config_versions.get(config_file.stem):
                updated_configs.append(config_file.stem)
        
        return updated_configs
    
    async def reload_config(self, config_type: Optional[str] = None) -> Dict[str, Any]:
        """Reload configuration files."""
        async with self._update_lock:
            try:
                if config_type:
                    # Reload specific configuration
                    return await self._reload_specific_config(config_type)
                else:
                    # Reload all configurations
                    return await self._reload_all_configs()
                    
            except Exception as e:
                self.logger.error(f"Configuration reload failed: {str(e)}")
                raise
    
    async def _reload_specific_config(self, config_type: str) -> Dict[str, Any]:
        """Reload a specific configuration file."""
        config_path = self.config_dir / f"{config_type}.yaml"
        if not config_path.exists():
            raise ValueError(f"Configuration file not found: {config_type}")
        
        # Load and validate new configuration
        with open(config_path, 'r') as f:
            new_config = yaml.safe_load(f)
        
        errors = self.validator.validate_config(config_type, new_config)
        if errors:
            raise ValueError(f"Invalid configuration in {config_type}: {errors}")
        
        # Update configuration
        if config_type == "system":
            self.system_config.system_config = new_config
        elif config_type == "agents":
            self.system_config.agent_config = new_config
        elif config_type == "pipeline":
            self.system_config.pipeline_config = new_config
        elif config_type == "resources":
            self.system_config.resource_config = new_config
        
        # Update version tracking
        self.config_versions[config_type] = self._get_file_version(config_path)
        
        return new_config
    
    async def _reload_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Reload all configuration files."""
        updated_configs = {}
        
        for config_type in ["system", "agents", "pipeline", "resources"]:
            try:
                updated_configs[config_type] = await self._reload_specific_config(config_type)
            except Exception as e:
                self.logger.error(f"Failed to reload {config_type} configuration: {str(e)}")
                raise
        
        return updated_configs
    
    async def update_config(self, config_type: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration with new values."""
        async with self._update_lock:
            try:
                # Get current configuration
                current_config = self._get_current_config(config_type)
                
                # Apply updates
                updated_config = self._deep_update(current_config, updates)
                
                # Validate updated configuration
                errors = self.validator.validate_config(config_type, updated_config)
                if errors:
                    raise ValueError(f"Invalid configuration updates: {errors}")
                
                # Save updated configuration
                config_path = self.config_dir / f"{config_type}.yaml"
                with open(config_path, 'w') as f:
                    yaml.safe_dump(updated_config, f)
                
                # Reload configuration
                return await self._reload_specific_config(config_type)
                
            except Exception as e:
                self.logger.error(f"Configuration update failed: {str(e)}")
                raise
    
    def _get_current_config(self, config_type: str) -> Dict[str, Any]:
        """Get current configuration by type."""
        if config_type == "system":
            return self.system_config.system_config
        elif config_type == "agents":
            return self.system_config.agent_config
        elif config_type == "pipeline":
            return self.system_config.pipeline_config
        elif config_type == "resources":
            return self.system_config.resource_config
        else:
            raise ValueError(f"Unknown configuration type: {config_type}")
    
    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Deep update dictionary with new values."""
        result = base.copy()
        
        for key, value in updates.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._deep_update(result[key], value)
            else:
                result[key] = value
        
        return result 