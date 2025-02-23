from typing import Dict, Any, List
import jsonschema
from pathlib import Path
import logging

class ConfigValidator:
    """Validates configuration files against defined schemas."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define configuration schemas
        self.schemas = {
            "system": {
                "type": "object",
                "required": ["settings", "performance", "security", "monitoring"],
                "properties": {
                    "settings": {
                        "type": "object",
                        "required": ["log_level", "max_concurrent_projects"],
                        "properties": {
                            "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                            "debug_mode": {"type": "boolean"},
                            "max_concurrent_projects": {"type": "integer", "minimum": 1},
                            "output_directory": {"type": "string"},
                            "temp_directory": {"type": "string"}
                        }
                    },
                    "performance": {
                        "type": "object",
                        "required": ["max_memory_usage", "max_cpu_usage"],
                        "properties": {
                            "max_memory_usage": {"type": "string", "pattern": "^\\d+GB$"},
                            "max_cpu_usage": {"type": "integer", "minimum": 0, "maximum": 100},
                            "gpu_enabled": {"type": "boolean"}
                        }
                    }
                }
            },
            "agents": {
                "type": "object",
                "required": ["story", "visual", "audio", "quality"],
                "properties": {
                    "story": {
                        "type": "object",
                        "required": ["plot_generator", "scene_planner", "character_developer", "dialogue_generator"]
                    },
                    "visual": {
                        "type": "object",
                        "required": ["scene_interpreter", "image_generator", "animation_controller"]
                    },
                    "audio": {
                        "type": "object",
                        "required": ["music_composer", "voice_generator", "audio_mixer"]
                    },
                    "quality": {
                        "type": "object",
                        "required": ["continuity_checker", "content_moderator"]
                    }
                }
            }
        }
    
    def validate_config(self, config_type: str, config_data: Dict[str, Any]) -> List[str]:
        """Validate configuration data against its schema."""
        errors = []
        
        try:
            if config_type in self.schemas:
                jsonschema.validate(instance=config_data, schema=self.schemas[config_type])
            else:
                errors.append(f"No schema defined for config type: {config_type}")
                
        except jsonschema.exceptions.ValidationError as e:
            errors.append(f"Configuration validation error: {str(e)}")
        except jsonschema.exceptions.SchemaError as e:
            errors.append(f"Schema error: {str(e)}")
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
        
        return errors
    
    def validate_agent_config(self, agent_type: str, agent_config: Dict[str, Any]) -> List[str]:
        """Validate agent-specific configuration."""
        errors = []
        
        # Common required fields for all agents
        required_fields = ["model", "quality"]
        
        for field in required_fields:
            if field not in agent_config:
                errors.append(f"Missing required field '{field}' in {agent_type} configuration")
        
        # Agent-specific validation
        if agent_type == "plot_generator":
            if "max_tokens" not in agent_config:
                errors.append("Plot generator requires 'max_tokens' configuration")
        elif agent_type == "image_generator":
            if "resolution" not in agent_config:
                errors.append("Image generator requires 'resolution' configuration")
        
        return errors
    
    def validate_pipeline_config(self, pipeline_config: Dict[str, Any]) -> List[str]:
        """Validate pipeline configuration."""
        errors = []
        
        required_fields = ["stages"]
        for field in required_fields:
            if field not in pipeline_config:
                errors.append(f"Missing required field '{field}' in pipeline configuration")
        
        if "stages" in pipeline_config:
            for stage in pipeline_config["stages"]:
                if "name" not in stage or "agent" not in stage:
                    errors.append("Pipeline stage missing required fields 'name' or 'agent'")
                if "timeout" in stage and not isinstance(stage["timeout"], (int, float)):
                    errors.append(f"Invalid timeout value in stage {stage.get('name', 'unknown')}")
        
        return errors
    
    def validate_resource_config(self, resource_config: Dict[str, Any]) -> List[str]:
        """Validate resource configuration."""
        errors = []
        
        required_sections = ["models", "storage", "compute"]
        for section in required_sections:
            if section not in resource_config:
                errors.append(f"Missing required section '{section}' in resource configuration")
        
        if "storage" in resource_config:
            for storage_type, storage_config in resource_config["storage"].items():
                if "path" not in storage_config:
                    errors.append(f"Missing 'path' in storage configuration for {storage_type}")
                if "max_size" in storage_config and not isinstance(storage_config["max_size"], str):
                    errors.append(f"Invalid max_size format in storage configuration for {storage_type}")
        
        return errors 