from typing import Dict, Any, Optional, List
from src.core.base_agent import BaseAgent, Message
from datetime import datetime
import logging
import json
from pathlib import Path

class ContentModerator(BaseAgent):
    """Agent responsible for ensuring content appropriateness and guideline compliance."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        
        # Content moderation templates
        self.moderation_templates = {
            "content_guidelines": {
                "age_ratings": ["general", "teen", "mature"],
                "sensitive_content": ["violence", "language", "themes"],
                "cultural_sensitivity": ["stereotypes", "representation", "inclusivity"]
            },
            "compliance_rules": {
                "legal": ["copyright", "trademarks", "licenses"],
                "platform": ["content_policies", "community_guidelines", "restrictions"],
                "regulatory": ["regional_requirements", "industry_standards"]
            },
            "quality_standards": {
                "professionalism": ["language_quality", "presentation", "consistency"],
                "accessibility": ["captions", "descriptions", "translations"],
                "engagement": ["appropriateness", "relevance", "value"]
            }
        }
        
        # Active moderations
        self.active_moderations: Dict[str, Dict[str, Any]] = {}
        
        # Output settings
        self.output_dir = Path("outputs/quality/moderation")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        if message.message_type == "moderate_content":
            return await self._moderate_content(message)
        elif message.message_type == "check_compliance":
            return await self._check_compliance(message)
        elif message.message_type == "get_moderation_report":
            return await self._get_moderation_report(message)
        return None
    
    async def _moderate_content(self, message: Message) -> Message:
        """Moderate content for appropriateness and compliance."""
        project_id = message.context.get("project_id")
        content_data = message.content.get("content_data", {})
        moderation_requirements = message.content.get("moderation_requirements", {})
        
        try:
            # Perform content moderation
            moderation_results = await self._perform_content_moderation(
                content_data,
                moderation_requirements
            )
            
            # Store moderation results
            if project_id not in self.active_moderations:
                self.active_moderations[project_id] = {
                    "moderations": {},
                    "timestamp": datetime.now().isoformat()
                }
            
            moderation_id = f"mod_{datetime.now().timestamp()}"
            self.active_moderations[project_id]["moderations"][moderation_id] = moderation_results
            
            # Save moderation results
            await self._save_moderation_results(moderation_results, project_id, moderation_id)
            
            return Message(
                message_id=f"mod_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="content_moderated",
                content={"moderation_results": moderation_results},
                context={"project_id": project_id, "moderation_id": moderation_id}
            )
            
        except Exception as e:
            self.logger.error(f"Content moderation failed: {str(e)}")
            raise
    
    async def _perform_content_moderation(self, content_data: Dict[str, Any],
                                        requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive content moderation."""
        moderation_results = {
            "content_review": self._review_content_guidelines(content_data, requirements),
            "compliance_check": self._check_compliance_rules(content_data, requirements),
            "quality_assessment": self._assess_quality_standards(content_data, requirements),
            "flags": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Analyze results and generate recommendations
        self._analyze_moderation_results(moderation_results, requirements)
        
        return moderation_results
    
    def _review_content_guidelines(self, content_data: Dict[str, Any],
                                 requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Review content against guidelines."""
        review_results = {}
        
        # Check age rating compliance
        review_results["age_rating"] = self._check_age_rating(
            content_data,
            requirements.get("target_rating")
        )
        
        # Check sensitive content
        review_results["sensitive_content"] = self._check_sensitive_content(
            content_data,
            self.moderation_templates["content_guidelines"]["sensitive_content"]
        )
        
        # Check cultural sensitivity
        review_results["cultural_sensitivity"] = self._check_cultural_sensitivity(
            content_data,
            self.moderation_templates["content_guidelines"]["cultural_sensitivity"]
        )
        
        return review_results
    
    def _check_compliance_rules(self, content_data: Dict[str, Any],
                              requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with legal and platform rules."""
        compliance_results = {}
        
        # Check legal compliance
        compliance_results["legal"] = self._check_legal_compliance(
            content_data,
            self.moderation_templates["compliance_rules"]["legal"]
        )
        
        # Check platform compliance
        compliance_results["platform"] = self._check_platform_compliance(
            content_data,
            self.moderation_templates["compliance_rules"]["platform"]
        )
        
        # Check regulatory compliance
        compliance_results["regulatory"] = self._check_regulatory_compliance(
            content_data,
            self.moderation_templates["compliance_rules"]["regulatory"]
        )
        
        return compliance_results
    
    def _assess_quality_standards(self, content_data: Dict[str, Any],
                                requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Assess content quality standards."""
        quality_results = {}
        
        # Check professionalism
        quality_results["professionalism"] = self._check_professionalism(
            content_data,
            self.moderation_templates["quality_standards"]["professionalism"]
        )
        
        # Check accessibility
        quality_results["accessibility"] = self._check_accessibility(
            content_data,
            self.moderation_templates["quality_standards"]["accessibility"]
        )
        
        # Check engagement
        quality_results["engagement"] = self._check_engagement(
            content_data,
            self.moderation_templates["quality_standards"]["engagement"]
        )
        
        return quality_results
    
    def _analyze_moderation_results(self, results: Dict[str, Any],
                                  requirements: Dict[str, Any]) -> None:
        """Analyze moderation results and generate recommendations."""
        # Identify flags and warnings
        for review_type, review in results.items():
            if review_type in ["content_review", "compliance_check", "quality_assessment"]:
                self._identify_content_issues(review, results["flags"], results["warnings"])
        
        # Generate recommendations
        results["recommendations"] = self._generate_content_recommendations(
            results["flags"],
            results["warnings"],
            requirements
        )
    
    async def _save_moderation_results(self, results: Dict[str, Any], project_id: str,
                                     moderation_id: str) -> None:
        """Save moderation results to file."""
        filename = f"{project_id}_{moderation_id}.json"
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(results, f)
    
    async def _check_compliance(self, message: Message) -> Message:
        """Check compliance with legal and platform rules."""
        project_id = message.context.get("project_id")
        content_data = message.content.get("content_data", {})
        
        compliance_results = self._check_compliance_rules(content_data, message.content)
        
        return Message(
            message_id=f"compliance_check_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="compliance_check_results",
            content={"compliance_results": compliance_results},
            context={"project_id": project_id}
        )
    
    async def _get_moderation_report(self, message: Message) -> Message:
        """Get moderation report for a specific project."""
        project_id = message.context.get("project_id")
        moderation_id = message.context.get("moderation_id")
        
        if project_id and moderation_id:
            filename = f"{project_id}_{moderation_id}.json"
            filepath = self.output_dir / filename
            if filepath.exists():
                with open(filepath, 'r') as f:
                    results = json.load(f)
                return Message(
                    message_id=f"moderation_report_{message.message_id}",
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type="moderation_report",
                    content={"moderation_results": results},
                    context={"project_id": project_id, "moderation_id": moderation_id}
                )
        return None 