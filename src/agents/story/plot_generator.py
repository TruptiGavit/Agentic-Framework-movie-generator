from typing import Dict, Any, Optional, List
from src.core.base_agent import BaseAgent, Message
from datetime import datetime
import logging
import json
from pathlib import Path

class PlotGenerator(BaseAgent):
    """Agent responsible for generating main storyline and plot points."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.logger = logging.getLogger(__name__)
        
        # Plot structure templates
        self.plot_templates = {
            "narrative": {
                "acts": ["setup", "confrontation", "resolution"],
                "points": ["inciting_incident", "rising_action", "climax", "falling_action"]
            },
            "educational": {
                "acts": ["introduction", "explanation", "demonstration", "summary"],
                "points": ["hook", "key_concepts", "examples", "practical_application"]
            },
            "promotional": {
                "acts": ["hook", "value_proposition", "call_to_action"],
                "points": ["problem", "solution", "benefits", "proof"]
            }
        }
        
        # Active plot developments
        self.active_plots: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        if message.message_type == "generate_plot":
            return await self._generate_plot(message)
        elif message.message_type == "refine_plot":
            return await self._refine_plot(message)
        elif message.message_type == "get_plot_points":
            return await self._get_plot_points(message)
        return None
    
    async def _generate_plot(self, message: Message) -> Message:
        """Generate initial plot structure based on creative brief."""
        project_id = message.context.get("project_id")
        creative_brief = message.content.get("creative_brief", {})
        
        try:
            # Generate plot structure
            plot_structure = await self._create_plot_structure(creative_brief)
            
            # Store plot development
            self.active_plots[project_id] = {
                "structure": plot_structure,
                "status": "initial",
                "timestamp": datetime.now().isoformat()
            }
            
            return Message(
                message_id=f"plot_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="plot_generated",
                content={"plot_structure": plot_structure},
                context={"project_id": project_id}
            )
            
        except Exception as e:
            self.logger.error(f"Plot generation failed: {str(e)}")
            raise
    
    async def _create_plot_structure(self, creative_brief: Dict[str, Any]) -> Dict[str, Any]:
        """Create plot structure based on creative brief."""
        video_type = creative_brief.get("project_overview", {}).get("video_type", "narrative")
        template = self.plot_templates.get(video_type, self.plot_templates["narrative"])
        
        plot_structure = {
            "type": video_type,
            "acts": self._generate_acts(template["acts"], creative_brief),
            "plot_points": self._generate_plot_points(template["points"], creative_brief),
            "themes": self._extract_themes(creative_brief),
            "narrative_elements": {
                "setting": self._determine_setting(creative_brief),
                "conflict": self._determine_conflict(creative_brief),
                "resolution": self._determine_resolution(creative_brief)
            }
        }
        
        return plot_structure
    
    def _generate_acts(self, act_template: List[str], 
                      creative_brief: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Generate act structure with descriptions."""
        acts = {}
        for act in act_template:
            acts[act] = {
                "description": self._generate_act_description(act, creative_brief),
                "objectives": self._generate_act_objectives(act, creative_brief),
                "key_elements": self._identify_act_elements(act, creative_brief)
            }
        return acts
    
    def _generate_plot_points(self, point_template: List[str],
                            creative_brief: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Generate plot points with details."""
        plot_points = {}
        for point in point_template:
            plot_points[point] = {
                "description": self._generate_point_description(point, creative_brief),
                "purpose": self._determine_point_purpose(point, creative_brief),
                "timing": self._determine_point_timing(point)
            }
        return plot_points
    
    def _extract_themes(self, creative_brief: Dict[str, Any]) -> List[str]:
        """Extract main themes from creative brief."""
        themes = []
        objectives = creative_brief.get("project_overview", {}).get("key_objectives", [])
        
        # Extract themes based on objectives and content
        if "inform" in str(objectives):
            themes.append("knowledge_sharing")
        if "persuade" in str(objectives):
            themes.append("transformation")
        if "educate" in str(objectives):
            themes.append("growth")
        
        return themes
    
    def _determine_setting(self, creative_brief: Dict[str, Any]) -> Dict[str, Any]:
        """Determine appropriate setting for the plot."""
        style = creative_brief.get("creative_direction", {})
        return {
            "style": style.get("visual_style"),
            "tone": style.get("tone"),
            "context": self._generate_setting_context(creative_brief)
        }
    
    async def _refine_plot(self, message: Message) -> Message:
        """Refine plot based on feedback or additional requirements."""
        project_id = message.context.get("project_id")
        feedback = message.content.get("feedback", {})
        
        try:
            current_plot = self.active_plots.get(project_id, {}).get("structure", {})
            refined_plot = await self._apply_refinements(current_plot, feedback)
            
            # Update plot development
            if project_id in self.active_plots:
                self.active_plots[project_id]["structure"] = refined_plot
                self.active_plots[project_id]["status"] = "refined"
            
            return Message(
                message_id=f"ref_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="plot_refined",
                content={"refined_plot": refined_plot},
                context={"project_id": project_id}
            )
            
        except Exception as e:
            self.logger.error(f"Plot refinement failed: {str(e)}")
            raise 