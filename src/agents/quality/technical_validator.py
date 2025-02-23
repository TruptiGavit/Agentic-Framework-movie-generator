from typing import Dict, Any, Optional, List
from src.core.base_agent import BaseAgent, Message
from datetime import datetime
import logging
import json
from pathlib import Path

class TechnicalValidator(BaseAgent):
    """Agent responsible for verifying technical requirements and specifications."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        
        # Technical validation templates
        self.validation_templates = {
            "video": {
                "specs": ["resolution", "framerate", "codec", "bitrate", "color_depth"],
                "formats": ["mp4", "mov", "avi", "webm"],
                "quality_metrics": ["compression", "artifacts", "color_accuracy"]
            },
            "audio": {
                "specs": ["sample_rate", "bit_depth", "channels", "format"],
                "formats": ["wav", "mp3", "aac", "flac"],
                "quality_metrics": ["noise_floor", "dynamic_range", "frequency_response"]
            },
            "rendering": {
                "specs": ["engine_version", "render_settings", "export_format"],
                "performance": ["memory_usage", "gpu_utilization", "render_time"],
                "optimization": ["asset_loading", "cache_usage", "thread_utilization"]
            }
        }
        
        # Active validations
        self.active_validations: Dict[str, Dict[str, Any]] = {}
        
        # Output settings
        self.output_dir = Path("outputs/quality/technical")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        if message.message_type == "validate_technical":
            return await self._validate_technical(message)
        elif message.message_type == "check_compatibility":
            return await self._check_compatibility(message)
        elif message.message_type == "get_validation_report":
            return await self._get_validation_report(message)
        return None
    
    async def _validate_technical(self, message: Message) -> Message:
        """Validate technical specifications of project assets."""
        project_id = message.context.get("project_id")
        project_data = message.content.get("project_data", {})
        requirements = message.content.get("technical_requirements", {})
        
        try:
            # Perform technical validation
            validation_results = await self._perform_technical_validation(
                project_data,
                requirements
            )
            
            # Store validation results
            if project_id not in self.active_validations:
                self.active_validations[project_id] = {
                    "validations": {},
                    "timestamp": datetime.now().isoformat()
                }
            
            validation_id = f"val_{datetime.now().timestamp()}"
            self.active_validations[project_id]["validations"][validation_id] = validation_results
            
            # Save validation results
            await self._save_validation_results(validation_results, project_id, validation_id)
            
            return Message(
                message_id=f"tech_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="technical_validated",
                content={"validation_results": validation_results},
                context={"project_id": project_id, "validation_id": validation_id}
            )
            
        except Exception as e:
            self.logger.error(f"Technical validation failed: {str(e)}")
            raise
    
    async def _perform_technical_validation(self, project_data: Dict[str, Any],
                                         requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive technical validation."""
        validation_results = {
            "video_validation": self._validate_video_specs(project_data, requirements),
            "audio_validation": self._validate_audio_specs(project_data, requirements),
            "rendering_validation": self._validate_rendering_specs(project_data, requirements),
            "compatibility_checks": self._check_format_compatibility(project_data),
            "performance_metrics": self._analyze_performance_metrics(project_data),
            "issues": [],
            "warnings": [],
            "optimizations": []
        }
        
        # Analyze results and generate recommendations
        self._analyze_validation_results(validation_results, requirements)
        
        return validation_results
    
    def _validate_video_specs(self, project_data: Dict[str, Any],
                            requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate video specifications."""
        video_validation = {}
        
        # Check basic specs
        for spec in self.validation_templates["video"]["specs"]:
            video_validation[spec] = self._validate_spec(
                spec,
                project_data.get("video", {}),
                requirements.get("video", {})
            )
        
        # Check format compatibility
        video_validation["format"] = self._validate_format(
            project_data.get("video", {}).get("format"),
            self.validation_templates["video"]["formats"]
        )
        
        # Check quality metrics
        video_validation["quality"] = self._check_video_quality(
            project_data.get("video", {}),
            self.validation_templates["video"]["quality_metrics"]
        )
        
        return video_validation
    
    def _validate_audio_specs(self, project_data: Dict[str, Any],
                            requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate audio specifications."""
        audio_validation = {}
        
        # Check basic specs
        for spec in self.validation_templates["audio"]["specs"]:
            audio_validation[spec] = self._validate_spec(
                spec,
                project_data.get("audio", {}),
                requirements.get("audio", {})
            )
        
        # Check format compatibility
        audio_validation["format"] = self._validate_format(
            project_data.get("audio", {}).get("format"),
            self.validation_templates["audio"]["formats"]
        )
        
        # Check quality metrics
        audio_validation["quality"] = self._check_audio_quality(
            project_data.get("audio", {}),
            self.validation_templates["audio"]["quality_metrics"]
        )
        
        return audio_validation
    
    def _validate_rendering_specs(self, project_data: Dict[str, Any],
                                requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate rendering specifications."""
        rendering_validation = {}
        
        # Check rendering specs
        for spec in self.validation_templates["rendering"]["specs"]:
            rendering_validation[spec] = self._validate_spec(
                spec,
                project_data.get("rendering", {}),
                requirements.get("rendering", {})
            )
        
        # Check performance metrics
        rendering_validation["performance"] = self._check_rendering_performance(
            project_data.get("rendering", {}),
            self.validation_templates["rendering"]["performance"]
        )
        
        # Check optimizations
        rendering_validation["optimization"] = self._check_rendering_optimization(
            project_data.get("rendering", {}),
            self.validation_templates["rendering"]["optimization"]
        )
        
        return rendering_validation
    
    def _validate_spec(self, spec: str, project_data: Dict[str, Any],
                     requirements: Dict[str, Any]) -> Any:
        """Validate a specific technical specification."""
        if spec in project_data:
            if spec in requirements:
                return project_data[spec]
            else:
                return "Not specified in requirements"
        else:
            return "Not available in project data"
    
    def _validate_format(self, project_format: str,
                        supported_formats: List[str]) -> str:
        """Validate format compatibility."""
        if project_format in supported_formats:
            return "Compatible"
        else:
            return f"Incompatible. Supported formats: {', '.join(supported_formats)}"
    
    def _check_video_quality(self, video_data: Dict[str, Any],
                            quality_metrics: List[str]) -> Dict[str, Any]:
        """Check video quality metrics."""
        quality_check = {}
        for metric in quality_metrics:
            if metric in video_data:
                quality_check[metric] = video_data[metric]
            else:
                quality_check[metric] = "Not available"
        return quality_check
    
    def _check_audio_quality(self, audio_data: Dict[str, Any],
                            quality_metrics: List[str]) -> Dict[str, Any]:
        """Check audio quality metrics."""
        quality_check = {}
        for metric in quality_metrics:
            if metric in audio_data:
                quality_check[metric] = audio_data[metric]
            else:
                quality_check[metric] = "Not available"
        return quality_check
    
    def _check_format_compatibility(self, project_data: Dict[str, Any]) -> str:
        """Check format compatibility."""
        compatibility = "Compatible"
        for format in project_data:
            if format not in self.validation_templates["video"]["formats"] and \
               format not in self.validation_templates["audio"]["formats"] and \
               format not in self.validation_templates["rendering"]["specs"]:
                compatibility = f"Incompatible. Unsupported format: {format}"
        return compatibility
    
    def _analyze_performance_metrics(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics."""
        performance_metrics = {}
        for metric in project_data:
            if metric in self.validation_templates["rendering"]["performance"]:
                performance_metrics[metric] = project_data[metric]
        return performance_metrics
    
    def _analyze_validation_results(self, validation_results: Dict[str, Any],
                                   requirements: Dict[str, Any]) -> None:
        """Analyze validation results and generate recommendations."""
        # Implement recommendation generation logic based on validation results and requirements
        pass
    
    async def _save_validation_results(self, validation_results: Dict[str, Any],
                                       project_id: str, validation_id: str) -> None:
        """Save validation results to file."""
        filename = f"{project_id}_{validation_id}_validation_results.json"
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(validation_results, f)
    
    async def initialize(self) -> None:
        """Initialize technical validator resources."""
        # Load technical requirements from configuration
        pass
    
    async def cleanup(self) -> None:
        """Cleanup technical validator resources."""
        pass 