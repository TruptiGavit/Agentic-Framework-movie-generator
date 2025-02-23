from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from PIL import Image
import numpy as np
import cv2
from pathlib import Path
import json
from datetime import datetime
import aiofiles

class QualityAssurance(BaseVisualAgent):
    """Agent responsible for verifying and validating render outputs."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.qa_config = {
            "output_dir": Path("outputs/quality_assurance"),
            "report_dir": Path("reports/qa"),
            "quality_checks": {
                "image": {
                    "resolution": {
                        "min_width": 1280,
                        "min_height": 720,
                        "aspect_ratios": ["16:9", "4:3", "1:1"]
                    },
                    "color": {
                        "bit_depth": 8,
                        "color_space": "RGB",
                        "gamma": 2.2
                    },
                    "artifacts": {
                        "noise_threshold": 0.1,
                        "compression_threshold": 0.8,
                        "blur_threshold": 0.5
                    }
                },
                "video": {
                    "framerate": {
                        "min_fps": 24,
                        "max_fps": 60,
                        "frame_consistency": True
                    },
                    "encoding": {
                        "codec_whitelist": ["h264", "prores", "vp9"],
                        "bitrate_threshold": {
                            "1080p": 8000000,  # 8 Mbps
                            "4K": 20000000     # 20 Mbps
                        }
                    },
                    "audio": {
                        "sample_rate": 48000,
                        "channels": [2, 6],
                        "formats": ["aac", "wav"]
                    }
                }
            }
        }
        self.active_checks: Dict[str, Dict[str, Any]] = {}
        self.quality_reports: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "check_quality":
            return await self._check_quality(message)
        elif message.message_type == "validate_output":
            return await self._validate_output(message)
        elif message.message_type == "get_qa_report":
            return await self._get_qa_report(message)
        return None
    
    async def _check_quality(self, message: Message) -> Message:
        """Check quality of rendered content."""
        content = message.content.get("content", {})
        check_type = message.content.get("check_type", "full")
        check_id = message.content.get("check_id", "")
        
        try:
            check_result = await self._process_quality_check(
                content, check_type, check_id
            )
            
            return Message(
                message_id=f"qa_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="quality_checked",
                content={"check_result": check_result},
                context=message.context,
                metadata={"check_id": check_id}
            )
        except Exception as e:
            return Message(
                message_id=f"qa_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="quality_check_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_quality_check(self, content: Dict[str, Any],
                                   check_type: str,
                                   check_id: str) -> Dict[str, Any]:
        """Process quality check for content."""
        content_type = self._determine_content_type(content)
        checks = self.qa_config["quality_checks"][content_type]
        
        # Perform quality checks
        check_results = {}
        if content_type == "image":
            check_results = await self._check_image_quality(content, checks)
        elif content_type == "video":
            check_results = await self._check_video_quality(content, checks)
        
        # Create quality report
        report = self._create_quality_report(check_results, content, check_type)
        
        # Store check results
        self.active_checks[check_id] = {
            "content_type": content_type,
            "check_type": check_type,
            "results": check_results,
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "check_id": check_id,
            "results": check_results,
            "report": report,
            "passed": self._determine_overall_quality(check_results)
        }
    
    async def _check_image_quality(self, content: Dict[str, Any],
                                 checks: Dict[str, Any]) -> Dict[str, Any]:
        """Check image quality metrics."""
        image_path = Path(content.get("path", ""))
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        image = Image.open(image_path)
        results = {
            "resolution": self._check_resolution(image, checks["resolution"]),
            "color": self._check_color_quality(image, checks["color"]),
            "artifacts": self._check_image_artifacts(image, checks["artifacts"])
        }
        
        return results
    
    async def _check_video_quality(self, content: Dict[str, Any],
                                 checks: Dict[str, Any]) -> Dict[str, Any]:
        """Check video quality metrics."""
        video_path = content.get("path")
        cap = cv2.VideoCapture(video_path)
        
        results = {
            "framerate": self._check_framerate(cap, checks["framerate"]),
            "encoding": self._check_video_encoding(video_path, checks["encoding"]),
            "audio": await self._check_audio_quality(video_path, checks["audio"])
        }
        
        cap.release()
        return results
    
    def _check_resolution(self, image: Image.Image,
                         resolution_checks: Dict[str, Any]) -> Dict[str, Any]:
        """Check image resolution requirements."""
        width, height = image.size
        aspect_ratio = width / height
        
        return {
            "width": width >= resolution_checks["min_width"],
            "height": height >= resolution_checks["min_height"],
            "aspect_ratio": self._validate_aspect_ratio(
                aspect_ratio,
                resolution_checks["aspect_ratios"]
            ),
            "actual": {
                "width": width,
                "height": height,
                "aspect_ratio": f"{width}:{height}"
            }
        }
    
    def _check_color_quality(self, image: Image.Image,
                           color_checks: Dict[str, Any]) -> Dict[str, Any]:
        """Check image color quality."""
        return {
            "bit_depth": image.mode in ["RGB", "RGBA"],
            "color_space": image.mode == color_checks["color_space"],
            "gamma": self._check_gamma(image, color_checks["gamma"]),
            "actual": {
                "mode": image.mode,
                "bands": len(image.getbands())
            }
        }
    
    def _create_quality_report(self, check_results: Dict[str, Any],
                             content: Dict[str, Any],
                             check_type: str) -> Dict[str, Any]:
        """Create detailed quality report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "content_info": {
                "type": content.get("type"),
                "path": content.get("path"),
                "metadata": content.get("metadata", {})
            },
            "check_type": check_type,
            "results": check_results,
            "summary": {
                "passed": self._determine_overall_quality(check_results),
                "warnings": self._collect_quality_warnings(check_results),
                "failures": self._collect_quality_failures(check_results)
            }
        }
        
        return report
    
    def _determine_overall_quality(self, results: Dict[str, Any]) -> bool:
        """Determine if content passes overall quality requirements."""
        # Implement quality determination logic based on results
        critical_failures = self._collect_quality_failures(results)
        return len(critical_failures) == 0
    
    async def initialize(self) -> None:
        """Initialize quality assurance resources."""
        self.qa_config["output_dir"].mkdir(parents=True, exist_ok=True)
        self.qa_config["report_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup quality assurance resources."""
        # Save final reports
        await self._save_qa_reports()
        
        # Clear active checks and reports
        self.active_checks.clear()
        self.quality_reports.clear() 