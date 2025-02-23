from typing import Dict, Any, List, Optional
import yaml
from pathlib import Path
import logging
from dataclasses import dataclass

@dataclass
class ProjectTemplate:
    """Project template definition."""
    name: str
    description: str
    category: str
    config: Dict[str, Any]
    requirements: Dict[str, Any]

class ProjectTemplateManager:
    """Manages project templates and their instantiation."""
    
    def __init__(self, templates_dir: str = "templates"):
        self.logger = logging.getLogger("movie_generator.templates")
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Load built-in templates
        self.templates: Dict[str, ProjectTemplate] = {}
        self._load_builtin_templates()
        self._load_custom_templates()
    
    def _load_builtin_templates(self):
        """Load built-in project templates."""
        builtin_templates = {
            "short_animation": {
                "name": "Short Animation",
                "description": "A short animated film (1-5 minutes)",
                "category": "animation",
                "config": {
                    "story": {
                        "plot_complexity": "medium",
                        "character_count": 2,
                        "scene_count": 5
                    },
                    "visual": {
                        "style": "animated",
                        "resolution": "1920x1080",
                        "framerate": 30
                    },
                    "audio": {
                        "music": True,
                        "sound_effects": True,
                        "voice_acting": True
                    }
                },
                "requirements": {
                    "duration": 300,
                    "target_audience": "general",
                    "resources": {
                        "gpu_memory": "4GB",
                        "storage": "10GB"
                    }
                }
            },
            # Add more built-in templates...
        }
        
        for template_id, data in builtin_templates.items():
            self.templates[template_id] = ProjectTemplate(**data)
    
    def _load_custom_templates(self):
        """Load custom templates from templates directory."""
        for template_file in self.templates_dir.glob("*.yaml"):
            try:
                with open(template_file, 'r') as f:
                    template_data = yaml.safe_load(f)
                    template_id = template_file.stem
                    self.templates[template_id] = ProjectTemplate(**template_data)
            except Exception as e:
                self.logger.error(f"Error loading template {template_file}: {str(e)}")
    
    async def create_project_from_template(self, 
                                         template_id: str, 
                                         customizations: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new project configuration from a template."""
        if template_id not in self.templates:
            raise ValueError(f"Template not found: {template_id}")
        
        template = self.templates[template_id]
        project_config = template.config.copy()
        
        # Apply customizations
        if customizations:
            project_config = self._apply_customizations(project_config, customizations)
        
        # Validate requirements
        self._validate_requirements(template.requirements)
        
        return project_config
    
    def _apply_customizations(self, 
                            base_config: Dict[str, Any], 
                            customizations: Dict[str, Any]) -> Dict[str, Any]:
        """Apply customizations to base configuration."""
        result = base_config.copy()
        
        for key, value in customizations.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._apply_customizations(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _validate_requirements(self, requirements: Dict[str, Any]):
        """Validate system meets template requirements."""
        # Check duration
        if "duration" in requirements:
            # Validation logic...
            pass
        
        # Check resources
        if "resources" in requirements:
            resources = requirements["resources"]
            if "gpu_memory" in resources:
                # GPU memory validation...
                pass
            if "storage" in resources:
                # Storage validation...
                pass 