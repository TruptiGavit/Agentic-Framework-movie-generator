from typing import Dict, Any, Optional, List
from src.core.base_agent import BaseAgent, Message
from datetime import datetime
import logging
import json
from pathlib import Path

class FeedbackAnalyzer(BaseAgent):
    """Agent responsible for processing user feedback and generating improvements."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        
        # Feedback analysis templates
        self.analysis_templates = {
            "feedback_categories": {
                "visual": ["quality", "style", "effects", "composition"],
                "audio": ["clarity", "balance", "sync", "quality"],
                "narrative": ["pacing", "engagement", "clarity", "impact"],
                "technical": ["performance", "stability", "compatibility"]
            },
            "sentiment_levels": {
                "positive": ["excellent", "good", "satisfactory"],
                "neutral": ["adequate", "acceptable", "moderate"],
                "negative": ["poor", "unsatisfactory", "problematic"]
            },
            "priority_levels": {
                "critical": ["blocking", "severe", "major"],
                "important": ["significant", "moderate", "notable"],
                "minor": ["cosmetic", "trivial", "enhancement"]
            }
        }
        
        # Active analyses
        self.active_analyses: Dict[str, Dict[str, Any]] = {}
        
        # Output settings
        self.output_dir = Path("outputs/quality/feedback")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        if message.message_type == "analyze_feedback":
            return await self._analyze_feedback(message)
        elif message.message_type == "generate_improvements":
            return await self._generate_improvements(message)
        elif message.message_type == "get_analysis_report":
            return await self._get_analysis_report(message)
        return None
    
    async def _analyze_feedback(self, message: Message) -> Message:
        """Analyze user feedback and generate insights."""
        project_id = message.context.get("project_id")
        feedback_data = message.content.get("feedback_data", {})
        analysis_requirements = message.content.get("analysis_requirements", {})
        
        try:
            # Perform feedback analysis
            analysis_results = await self._perform_feedback_analysis(
                feedback_data,
                analysis_requirements
            )
            
            # Store analysis results
            if project_id not in self.active_analyses:
                self.active_analyses[project_id] = {
                    "analyses": {},
                    "timestamp": datetime.now().isoformat()
                }
            
            analysis_id = f"analysis_{datetime.now().timestamp()}"
            self.active_analyses[project_id]["analyses"][analysis_id] = analysis_results
            
            # Save analysis results
            await self._save_analysis_results(analysis_results, project_id, analysis_id)
            
            return Message(
                message_id=f"feedback_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="feedback_analyzed",
                content={"analysis_results": analysis_results},
                context={"project_id": project_id, "analysis_id": analysis_id}
            )
            
        except Exception as e:
            self.logger.error(f"Feedback analysis failed: {str(e)}")
            raise
    
    async def _perform_feedback_analysis(self, feedback_data: Dict[str, Any],
                                       requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive feedback analysis."""
        analysis_results = {
            "category_analysis": self._analyze_feedback_categories(feedback_data),
            "sentiment_analysis": self._analyze_sentiment(feedback_data),
            "priority_analysis": self._analyze_priorities(feedback_data),
            "trends": self._identify_trends(feedback_data),
            "key_issues": [],
            "improvement_areas": [],
            "recommendations": []
        }
        
        # Generate insights and recommendations
        self._generate_insights(analysis_results, requirements)
        
        return analysis_results
    
    def _analyze_feedback_categories(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze feedback by category."""
        category_analysis = {}
        
        for category, aspects in self.analysis_templates["feedback_categories"].items():
            category_analysis[category] = {
                "feedback_items": self._collect_category_feedback(feedback_data, category),
                "common_issues": self._identify_common_issues(feedback_data, category),
                "positive_points": self._identify_positive_points(feedback_data, category),
                "metrics": self._calculate_category_metrics(feedback_data, category)
            }
        
        return category_analysis
    
    def _analyze_sentiment(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze feedback sentiment."""
        sentiment_analysis = {
            "overall_sentiment": self._calculate_overall_sentiment(feedback_data),
            "sentiment_by_category": {},
            "sentiment_trends": self._analyze_sentiment_trends(feedback_data),
            "key_factors": self._identify_sentiment_factors(feedback_data)
        }
        
        # Analyze sentiment for each category
        for category in self.analysis_templates["feedback_categories"]:
            sentiment_analysis["sentiment_by_category"][category] = \
                self._calculate_category_sentiment(feedback_data, category)
        
        return sentiment_analysis
    
    def _analyze_priorities(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze feedback priorities."""
        priority_analysis = {
            "critical_issues": self._identify_critical_issues(feedback_data),
            "important_improvements": self._identify_important_improvements(feedback_data),
            "minor_enhancements": self._identify_minor_enhancements(feedback_data),
            "priority_distribution": self._calculate_priority_distribution(feedback_data)
        }
        
        return priority_analysis
    
    async def _generate_improvements(self, message: Message) -> Message:
        """Generate improvement suggestions based on feedback analysis."""
        project_id = message.context.get("project_id")
        analysis_id = message.content.get("analysis_id")
        
        try:
            analysis_results = self.active_analyses.get(project_id, {}).get("analyses", {}).get(analysis_id)
            if analysis_results:
                improvements = self._generate_improvement_suggestions(analysis_results)
                
                return Message(
                    message_id=f"improvements_{message.message_id}",
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type="improvements_generated",
                    content={"improvements": improvements},
                    context={"project_id": project_id, "analysis_id": analysis_id}
                )
                
        except Exception as e:
            self.logger.error(f"Improvement generation failed: {str(e)}")
            raise 