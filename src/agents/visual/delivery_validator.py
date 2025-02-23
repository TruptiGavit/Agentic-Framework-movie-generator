from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from pathlib import Path
import json
import ffmpeg
from datetime import datetime
import aiofiles
import xml.etree.ElementTree as ET

class DeliveryValidator(BaseVisualAgent):
    """Agent responsible for validating delivery packages against specifications."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.validator_config = {
            "output_dir": Path("outputs/validator"),
            "report_dir": Path("reports/validation"),
            "validation_specs": {
                "dcp": {
                    "video": {
                        "formats": ["jpeg2000"],
                        "resolutions": [(2048, 858), (2048, 1080), (4096, 1716)],
                        "framerates": [24, 48],
                        "color_space": "xyz"
                    },
                    "audio": {
                        "formats": ["wav"],
                        "sample_rates": [48000, 96000],
                        "bit_depths": [24],
                        "channel_layouts": ["5.1", "7.1"]
                    },
                    "metadata": {
                        "required_files": ["cpl.xml", "pkl.xml", "assetmap.xml"],
                        "schema_versions": ["1.0", "1.1"]
                    }
                },
                "broadcast": {
                    "video": {
                        "formats": ["xdcam_hd422", "dnxhd"],
                        "resolutions": [(1920, 1080)],
                        "framerates": [25, 29.97, 30],
                        "color_space": "rec709"
                    },
                    "audio": {
                        "formats": ["pcm"],
                        "sample_rates": [48000],
                        "bit_depths": [24],
                        "channel_layouts": ["stereo", "5.1"]
                    },
                    "metadata": {
                        "required_files": ["as11_core.xml", "technical_metadata.xml"],
                        "schema_versions": ["1.1"]
                    }
                },
                "streaming": {
                    "video": {
                        "formats": ["h264", "h265"],
                        "resolutions": [
                            (1920, 1080),
                            (1280, 720),
                            (854, 480)
                        ],
                        "framerates": [24, 25, 30, 60],
                        "bitrate_ranges": {
                            "1080p": (4000000, 8000000),
                            "720p": (2000000, 4000000),
                            "480p": (1000000, 2000000)
                        }
                    },
                    "audio": {
                        "formats": ["aac"],
                        "sample_rates": [44100, 48000],
                        "bitrate_ranges": {
                            "stereo": (128000, 320000),
                            "surround": (384000, 640000)
                        }
                    }
                }
            }
        }
        self.active_validations: Dict[str, Dict[str, Any]] = {}
        self.validation_history: List[Dict[str, Any]] = []
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "validate_package":
            return await self._validate_package(message)
        elif message.message_type == "check_compliance":
            return await self._check_compliance(message)
        elif message.message_type == "get_validation_report":
            return await self._get_validation_report(message)
        return None
    
    async def _validate_package(self, message: Message) -> Message:
        """Validate a delivery package."""
        package_path = message.content.get("package_path", "")
        delivery_type = message.content.get("delivery_type", "")
        validation_id = message.content.get("validation_id", "")
        
        try:
            validation_result = await self._process_validation(
                package_path, delivery_type, validation_id
            )
            
            return Message(
                message_id=f"val_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="package_validated",
                content={"validation_result": validation_result},
                context=message.context,
                metadata={"validation_id": validation_id}
            )
        except Exception as e:
            return Message(
                message_id=f"val_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="validation_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_validation(self, package_path: str,
                                delivery_type: str,
                                validation_id: str) -> Dict[str, Any]:
        """Process package validation."""
        package_dir = Path(package_path)
        specs = self.validator_config["validation_specs"][delivery_type]
        
        # Validate package structure
        structure_results = await self._validate_package_structure(
            package_dir, delivery_type
        )
        
        # Validate media files
        media_results = await self._validate_media_files(
            package_dir, specs
        )
        
        # Validate metadata
        metadata_results = await self._validate_metadata(
            package_dir, specs.get("metadata", {})
        )
        
        # Create validation report
        validation_report = self._create_validation_report(
            structure_results,
            media_results,
            metadata_results,
            delivery_type
        )
        
        # Store validation details
        self.active_validations[validation_id] = {
            "package_path": package_path,
            "delivery_type": delivery_type,
            "report": validation_report,
            "validated_at": datetime.now().isoformat()
        }
        
        return validation_report
    
    async def _validate_package_structure(self, package_dir: Path,
                                        delivery_type: str) -> Dict[str, Any]:
        """Validate package directory structure."""
        results = {
            "status": "pass",
            "issues": [],
            "details": {}
        }
        
        try:
            # Check required files exist
            required_files = self.validator_config["validation_specs"][delivery_type]["metadata"]["required_files"]
            for file in required_files:
                file_path = package_dir / file
                if not file_path.exists():
                    results["issues"].append(f"Missing required file: {file}")
                    results["status"] = "fail"
                else:
                    results["details"][file] = {
                        "exists": True,
                        "size": file_path.stat().st_size
                    }
        except Exception as e:
            results["status"] = "error"
            results["issues"].append(f"Structure validation error: {str(e)}")
        
        return results
    
    async def _validate_media_files(self, package_dir: Path,
                                  specs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate media files against specifications."""
        results = {
            "video": await self._validate_video_files(package_dir, specs.get("video", {})),
            "audio": await self._validate_audio_files(package_dir, specs.get("audio", {}))
        }
        
        # Determine overall status
        results["status"] = "pass"
        if results["video"]["status"] != "pass" or results["audio"]["status"] != "pass":
            results["status"] = "fail"
        
        return results
    
    async def _validate_metadata(self, package_dir: Path,
                               metadata_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate package metadata."""
        results = {
            "status": "pass",
            "issues": [],
            "validations": {}
        }
        
        for metadata_file in metadata_specs.get("required_files", []):
            file_path = package_dir / metadata_file
            if file_path.exists():
                # Validate XML schema if applicable
                if file_path.suffix == ".xml":
                    schema_result = await self._validate_xml_schema(
                        file_path,
                        metadata_specs.get("schema_versions", [])
                    )
                    results["validations"][metadata_file] = schema_result
                    if not schema_result["valid"]:
                        results["status"] = "fail"
                        results["issues"].extend(schema_result["errors"])
        
        return results
    
    def _create_validation_report(self, structure_results: Dict[str, Any],
                                media_results: Dict[str, Any],
                                metadata_results: Dict[str, Any],
                                delivery_type: str) -> Dict[str, Any]:
        """Create comprehensive validation report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "delivery_type": delivery_type,
            "overall_status": self._determine_overall_status(
                structure_results,
                media_results,
                metadata_results
            ),
            "results": {
                "structure": structure_results,
                "media": media_results,
                "metadata": metadata_results
            },
            "specifications": self.validator_config["validation_specs"][delivery_type]
        }
    
    async def initialize(self) -> None:
        """Initialize delivery validator resources."""
        self.validator_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.validator_config["report_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup delivery validator resources."""
        # Archive validation history
        for validation_id, validation in self.active_validations.items():
            self.validation_history.append({
                "validation_id": validation_id,
                "archived_at": datetime.now().isoformat(),
                **validation
            })
        
        # Clear active validations
        self.active_validations.clear() 