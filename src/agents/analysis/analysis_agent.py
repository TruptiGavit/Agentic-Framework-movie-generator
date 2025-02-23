from typing import Dict, Any, Optional, List
from src.core.base_agent import BaseAgent, Message
from datetime import datetime
import logging
import json
from pathlib import Path
import asyncio

class AnalysisAgent(BaseAgent):
    """Agent responsible for analyzing project requirements and determining creative direction."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        
        # Analysis configuration
        self.analysis_config = {
            "video_types": [
                "animation", "documentary", "promotional",
                "educational", "narrative", "experimental"
            ],
            "style_categories": {
                "visual": ["realistic", "stylized", "abstract", "minimalist"],
                "tone": ["serious", "light", "dramatic", "humorous"],
                "pacing": ["fast", "moderate", "slow", "dynamic"]
            },
            "content_categories": {
                "audience": ["general", "children", "adult", "professional"],
                "purpose": ["entertain", "inform", "persuade", "educate"],
                "complexity": ["simple", "moderate", "complex"]
            }
        }
        
        # Active analyses
        self.active_analyses: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        if message.message_type == "analyze_requirements":
            return await self._analyze_requirements(message)
        elif message.message_type == "determine_style":
            return await self._determine_style(message)
        elif message.message_type == "create_brief":
            return await self._create_creative_brief(message)
        return None
    
    async def _analyze_requirements(self, message: Message) -> Message:
        """Analyze project requirements and determine video type."""
        project_data = message.content.get("project_data", {})
        project_id = message.context.get("project_id")
        
        try:
            # Perform requirements analysis
            analysis_result = await self._process_requirements(project_data)
            
            # Store analysis results
            self.active_analyses[project_id] = {
                "requirements": analysis_result,
                "timestamp": datetime.now().isoformat()
            }
            
            return Message(
                message_id=f"req_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="requirements_analyzed",
                content={"analysis": analysis_result},
                context={"project_id": project_id}
            )
            
        except Exception as e:
            self.logger.error(f"Requirements analysis failed: {str(e)}")
            raise
    
    async def _process_requirements(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and analyze project requirements."""
        return {
            "video_type": self._determine_video_type(project_data),
            "content_analysis": self._analyze_content_requirements(project_data),
            "technical_requirements": self._analyze_technical_requirements(project_data),
            "constraints": self._identify_constraints(project_data)
        }
    
    def _determine_video_type(self, project_data: Dict[str, Any]) -> str:
        """Determine the type of video to be generated."""
        description = project_data.get("description", "").lower()
        requirements = project_data.get("requirements", {})
        
        # Analyze keywords and requirements to determine type
        type_scores = {vtype: 0 for vtype in self.analysis_config["video_types"]}
        
        # Add scoring logic based on keywords and requirements
        if "animate" in description or "cartoon" in description:
            type_scores["animation"] += 2
        if "teach" in description or "learn" in description:
            type_scores["educational"] += 2
        if "story" in description or "narrative" in description:
            type_scores["narrative"] += 2
        
        # Get type with highest score
        return max(type_scores.items(), key=lambda x: x[1])[0]
    
    async def _determine_style(self, message: Message) -> Message:
        """Determine visual style and creative direction."""
        project_id = message.context.get("project_id")
        previous_analysis = self.active_analyses.get(project_id, {}).get("requirements", {})
        
        try:
            # Determine style based on previous analysis
            style_result = self._analyze_style_requirements(previous_analysis)
            
            # Update analysis record
            if project_id in self.active_analyses:
                self.active_analyses[project_id]["style"] = style_result
            
            return Message(
                message_id=f"style_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="style_determined",
                content={"style": style_result},
                context={"project_id": project_id}
            )
            
        except Exception as e:
            self.logger.error(f"Style determination failed: {str(e)}")
            raise
    
    def _analyze_style_requirements(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and determine style requirements."""
        video_type = analysis.get("video_type", "")
        content_analysis = analysis.get("content_analysis", {})
        
        style_result = {
            "visual_style": self._determine_visual_style(video_type, content_analysis),
            "tone": self._determine_tone(content_analysis),
            "pacing": self._determine_pacing(content_analysis)
        }
        
        return style_result
    
    async def _create_creative_brief(self, message: Message) -> Message:
        """Create comprehensive creative brief."""
        project_id = message.context.get("project_id")
        analysis_data = self.active_analyses.get(project_id, {})
        
        try:
            # Generate creative brief
            brief = self._generate_creative_brief(analysis_data)
            
            # Update analysis record
            if project_id in self.active_analyses:
                self.active_analyses[project_id]["creative_brief"] = brief
            
            return Message(
                message_id=f"brief_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="brief_created",
                content={"creative_brief": brief},
                context={"project_id": project_id}
            )
            
        except Exception as e:
            self.logger.error(f"Creative brief creation failed: {str(e)}")
            raise
    
    def _generate_creative_brief(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive creative brief."""
        requirements = analysis_data.get("requirements", {})
        style = analysis_data.get("style", {})
        
        return {
            "project_overview": {
                "video_type": requirements.get("video_type"),
                "target_audience": requirements.get("content_analysis", {}).get("audience"),
                "key_objectives": self._extract_objectives(requirements)
            },
            "creative_direction": {
                "visual_style": style.get("visual_style"),
                "tone": style.get("tone"),
                "pacing": style.get("pacing")
            },
            "technical_specifications": requirements.get("technical_requirements", {}),
            "constraints": requirements.get("constraints", {}),
            "recommendations": self._generate_recommendations(analysis_data)
        }
    
    def _extract_objectives(self, requirements: Dict[str, Any]) -> List[str]:
        """Extract key objectives from requirements."""
        content_analysis = requirements.get("content_analysis", {})
        purpose = content_analysis.get("purpose", "")
        
        objectives = []
        if purpose == "inform":
            objectives.append("Clearly communicate key information")
        elif purpose == "persuade":
            objectives.append("Drive audience engagement and action")
        elif purpose == "educate":
            objectives.append("Facilitate learning and understanding")
        elif purpose == "entertain":
            objectives.append("Create engaging and enjoyable content")
        
        return objectives 