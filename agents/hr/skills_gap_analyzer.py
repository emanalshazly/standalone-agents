"""Skills Gap Analyzer - Future-skills forecasting"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SkillsGapReport:
    report_id: str
    team_id: str
    current_skills: Dict[str, float]
    required_skills: Dict[str, float]
    gaps: List[Dict[str, Any]]
    training_recommendations: List[str]
    priority_areas: List[str]

class SkillsGapAnalyzer:
    """Future-skills forecasting with learning path recommendations"""
    
    def __init__(self, rag_engine, config: Optional[Dict[str, Any]] = None):
        self.rag_engine = rag_engine
        self.config = config or {}
    
    async def analyze_team_skills(
        self,
        team_id: str,
        team_members: List[Dict[str, Any]],
        business_goals: List[str]
    ) -> SkillsGapReport:
        """Analyze team skills and identify gaps"""
        
        # Aggregate current skills
        current_skills = self._aggregate_team_skills(team_members)
        
        # Predict required skills based on business goals
        required_skills = await self._predict_required_skills(business_goals)
        
        # Identify gaps
        gaps = self._calculate_gaps(current_skills, required_skills)
        
        # Generate training recommendations
        recommendations = await self._recommend_training(gaps)
        
        # Prioritize
        priorities = self._prioritize_gaps(gaps)
        
        report = SkillsGapReport(
            report_id=f"gap_analysis_{team_id}",
            team_id=team_id,
            current_skills=current_skills,
            required_skills=required_skills,
            gaps=gaps,
            training_recommendations=recommendations,
            priority_areas=priorities
        )
        
        return report
    
    def _aggregate_team_skills(self, team_members: List[Dict[str, Any]]) -> Dict[str, float]:
        """Aggregate skills across team"""
        return {"Python": 0.8, "Machine Learning": 0.6, "Cloud": 0.5}
    
    async def _predict_required_skills(self, business_goals: List[str]) -> Dict[str, float]:
        """Predict future skill requirements"""
        query = f"Required skills for: {', '.join(business_goals)}"
        # Would use RAG to predict based on industry trends
        return {"Python": 0.9, "Machine Learning": 0.9, "Cloud": 0.85, "DevOps": 0.7}
    
    def _calculate_gaps(self, current: Dict[str, float], required: Dict[str, float]) -> List[Dict[str, Any]]:
        """Calculate skill gaps"""
        gaps = []
        for skill, req_level in required.items():
            curr_level = current.get(skill, 0)
            if curr_level < req_level:
                gaps.append({
                    "skill": skill,
                    "current": curr_level,
                    "required": req_level,
                    "gap": req_level - curr_level
                })
        return sorted(gaps, key=lambda x: x["gap"], reverse=True)
    
    async def _recommend_training(self, gaps: List[Dict[str, Any]]) -> List[str]:
        """Recommend training programs"""
        return [f"Training course for {gap['skill']}" for gap in gaps[:3]]
    
    def _prioritize_gaps(self, gaps: List[Dict[str, Any]]) -> List[str]:
        """Prioritize skill gaps"""
        return [gap["skill"] for gap in gaps[:5]]
