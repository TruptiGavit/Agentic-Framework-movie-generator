from typing import Dict, Any, Optional, List
from src.core.base_agent import BaseAgent, Message
from datetime import datetime
import logging
import json
from pathlib import Path

class ContinuityChecker(BaseAgent):
    """Agent responsible for ensuring consistency across all elements."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        
        # Continuity check templates
        self.check_templates = {
            "visual": {
                "elements": ["characters", "settings", "props", "lighting", "colors"],
                "transitions": ["scene_changes", "time_shifts", "location_changes"],
                "styles": ["artistic_style", "camera_angles", "composition"]
            },
            "audio": {
                "elements": ["dialogue", "music", "effects", "ambient"],
                "transitions": ["audio_bridges", "fade_points", "overlaps"],
                "levels": ["volume_consistency", "mix_balance", "eq_matching"]
            },
            "narrative": {
                "elements": ["plot_points", "character_arcs", "dialogue_flow"],
                "timeline": ["chronology", "pacing", "scene_order"],
                "context": ["mood", "tone", "theme"]
            }
        }
        
        # Active checks
        self.active_checks: Dict[str, Dict[str, Any]] = {}
        
        # Output settings
        self.output_dir = Path("outputs/quality/continuity")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        if message.message_type == "check_continuity":
            return await self._check_continuity(message)
        elif message.message_type == "verify_changes":
            return await self._verify_changes(message)
        elif message.message_type == "get_report":
            return await self._get_report(message)
        return None
    
    async def _check_continuity(self, message: Message) -> Message:
        """Check continuity across project elements."""
        project_id = message.context.get("project_id")
        project_data = message.content.get("project_data", {})
        check_requirements = message.content.get("check_requirements", {})
        
        try:
            # Perform continuity check
            check_results = await self._perform_continuity_check(
                project_data,
                check_requirements
            )
            
            # Store check results
            if project_id not in self.active_checks:
                self.active_checks[project_id] = {
                    "checks": {},
                    "timestamp": datetime.now().isoformat()
                }
            
            check_id = f"check_{datetime.now().timestamp()}"
            self.active_checks[project_id]["checks"][check_id] = check_results
            
            # Save check results
            await self._save_check_results(check_results, project_id, check_id)
            
            return Message(
                message_id=f"cont_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="continuity_checked",
                content={"check_results": check_results},
                context={"project_id": project_id, "check_id": check_id}
            )
            
        except Exception as e:
            self.logger.error(f"Continuity check failed: {str(e)}")
            raise
    
    async def _perform_continuity_check(self, project_data: Dict[str, Any],
                                      requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive continuity check."""
        check_results = {
            "visual_continuity": self._check_visual_continuity(project_data),
            "audio_continuity": self._check_audio_continuity(project_data),
            "narrative_continuity": self._check_narrative_continuity(project_data),
            "issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Analyze results and generate recommendations
        self._analyze_check_results(check_results, requirements)
        
        return check_results
    
    def _check_visual_continuity(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check visual continuity across scenes."""
        visual_checks = {}
        scenes = project_data.get("scenes", [])
        
        for element in self.check_templates["visual"]["elements"]:
            visual_checks[element] = self._check_element_continuity(
                element,
                scenes,
                "visual"
            )
        
        # Check transitions
        visual_checks["transitions"] = self._check_transition_continuity(
            scenes,
            self.check_templates["visual"]["transitions"]
        )
        
        # Check style consistency
        visual_checks["style"] = self._check_style_consistency(
            scenes,
            self.check_templates["visual"]["styles"]
        )
        
        return visual_checks
    
    def _check_audio_continuity(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check audio continuity across scenes."""
        audio_checks = {}
        scenes = project_data.get("scenes", [])
        
        for element in self.check_templates["audio"]["elements"]:
            audio_checks[element] = self._check_element_continuity(
                element,
                scenes,
                "audio"
            )
        
        # Check audio transitions
        audio_checks["transitions"] = self._check_transition_continuity(
            scenes,
            self.check_templates["audio"]["transitions"]
        )
        
        # Check audio levels
        audio_checks["levels"] = self._check_audio_levels(
            scenes,
            self.check_templates["audio"]["levels"]
        )
        
        return audio_checks
    
    def _check_narrative_continuity(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check narrative continuity."""
        narrative_checks = {}
        
        # Check story elements
        for element in self.check_templates["narrative"]["elements"]:
            narrative_checks[element] = self._check_story_element_continuity(
                element,
                project_data
            )
        
        # Check timeline consistency
        narrative_checks["timeline"] = self._check_timeline_consistency(
            project_data,
            self.check_templates["narrative"]["timeline"]
        )
        
        # Check context consistency
        narrative_checks["context"] = self._check_context_consistency(
            project_data,
            self.check_templates["narrative"]["context"]
        )
        
        return narrative_checks
    
    def _analyze_check_results(self, results: Dict[str, Any],
                             requirements: Dict[str, Any]) -> None:
        """Analyze check results and generate recommendations."""
        # Identify critical issues
        for check_type, checks in results.items():
            if check_type in ["visual_continuity", "audio_continuity", "narrative_continuity"]:
                self._identify_issues(checks, results["issues"], results["warnings"])
        
        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(
            results["issues"],
            results["warnings"],
            requirements
        )
    
    async def initialize(self) -> None:
        """Initialize continuity checker resources."""
        # Load any necessary reference data
        pass
    
    async def cleanup(self) -> None:
        """Cleanup continuity checker resources."""
        self.active_checks.clear() 