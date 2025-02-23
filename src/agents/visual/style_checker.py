from typing import Optional, Dict, Any, List
from src.agents.visual.base_visual_agent import BaseVisualAgent
from src.core.base_agent import Message
from pathlib import Path
import json
from datetime import datetime

class StyleChecker(BaseVisualAgent):
    """Agent responsible for maintaining visual style consistency."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.style_config = {
            "output_dir": Path("outputs/style_checker"),
            "style_elements": {
                "visual_style": {
                    "color_scheme": ["primary", "secondary", "accent"],
                    "lighting": ["key", "fill", "ambient"],
                    "texture": ["surface", "material", "pattern"]
                },
                "composition": {
                    "framing": ["rule_of_thirds", "golden_ratio", "symmetry"],
                    "depth": ["foreground", "midground", "background"],
                    "perspective": ["angle", "distance", "distortion"]
                },
                "consistency": {
                    "character": ["appearance", "scale", "detail"],
                    "environment": ["architecture", "nature", "props"],
                    "lighting": ["direction", "intensity", "color"]
                }
            }
        }
        self.active_styles: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "check_style":
            return await self._check_style(message)
        elif message.message_type == "update_style_guide":
            return await self._update_style_guide(message)
        return None
    
    async def _check_style(self, message: Message) -> Message:
        """Check style consistency of content."""
        content = message.content.get("content", {})
        style_id = message.content.get("style_id", "")
        
        try:
            style_check = await self._process_style_check(
                content, style_id
            )
            
            return Message(
                message_id=f"style_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="style_checked",
                content={"style_check": style_check},
                context=message.context,
                metadata={"style_id": style_id}
            )
        except Exception as e:
            return Message(
                message_id=f"style_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="style_check_failed",
                content={"error": str(e)},
                context=message.context
            )
    
    async def _process_style_check(self, content: Dict[str, Any],
                                 style_id: str) -> Dict[str, Any]:
        """Process style consistency check."""
        # Get reference style
        reference_style = self.active_styles.get(style_id, {}).get("style_guide", {})
        
        # Check each style element
        style_results = {}
        for category, elements in self.style_config["style_elements"].items():
            style_results[category] = self._check_style_category(
                content, reference_style, category, elements
            )
        
        # Generate overall assessment
        assessment = self._generate_style_assessment(style_results)
        
        # Create style check report
        check_report = {
            "style_id": style_id,
            "results": style_results,
            "assessment": assessment,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        
        return check_report
    
    def _check_style_category(self, content: Dict[str, Any],
                            reference: Dict[str, Any],
                            category: str,
                            elements: Dict[str, List[str]]) -> Dict[str, Any]:
        """Check style consistency for a category."""
        results = {
            "matches": [],
            "discrepancies": [],
            "score": 0.0
        }
        
        for element_type, attributes in elements.items():
            element_check = self._check_element_consistency(
                content, reference, category, element_type, attributes
            )
            
            if element_check["consistent"]:
                results["matches"].append(element_type)
            else:
                results["discrepancies"].append({
                    "element": element_type,
                    "details": element_check["details"]
                })
            
            results["score"] += element_check["score"]
        
        # Normalize score
        results["score"] /= len(elements)
        
        return results
    
    def _check_element_consistency(self, content: Dict[str, Any],
                                 reference: Dict[str, Any],
                                 category: str,
                                 element_type: str,
                                 attributes: List[str]) -> Dict[str, Any]:
        """Check consistency of specific style element."""
        result = {
            "consistent": True,
            "details": [],
            "score": 1.0
        }
        
        content_element = content.get(category, {}).get(element_type, {})
        reference_element = reference.get(category, {}).get(element_type, {})
        
        for attr in attributes:
            if attr in content_element and attr in reference_element:
                if content_element[attr] != reference_element[attr]:
                    result["consistent"] = False
                    result["score"] -= 1.0 / len(attributes)
                    result["details"].append({
                        "attribute": attr,
                        "expected": reference_element[attr],
                        "found": content_element[attr]
                    })
        
        return result
    
    def _generate_style_assessment(self, style_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall style assessment."""
        total_score = 0.0
        issues = []
        
        for category, results in style_results.items():
            total_score += results["score"]
            if results["discrepancies"]:
                issues.extend([
                    f"{category}.{d['element']}: {d['details']}"
                    for d in results["discrepancies"]
                ])
        
        return {
            "overall_score": total_score / len(style_results),
            "issues": issues,
            "status": "consistent" if total_score / len(style_results) >= 0.8 else "inconsistent"
        }
    
    async def initialize(self) -> None:
        """Initialize style checker resources."""
        self.style_config["output_dir"].mkdir(parents=True, exist_ok=True)
    
    async def cleanup(self) -> None:
        """Cleanup style checker resources."""
        self.active_styles.clear() 