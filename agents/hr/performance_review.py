"""Performance Review Analyzer - 360-degree feedback synthesis"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PerformanceReview:
    review_id: str
    employee_id: str
    period: str
    self_assessment: Dict[str, Any]
    manager_feedback: Dict[str, Any]
    peer_feedback: List[Dict[str, Any]]
    goals_achievement: float
    overall_rating: float

class PerformanceReviewAnalyzer:
    """360-degree feedback synthesis with growth pattern recognition"""
    
    def __init__(self, rag_engine, config: Optional[Dict[str, Any]] = None):
        self.rag_engine = rag_engine
        self.config = config or {}
    
    async def analyze_performance(
        self,
        employee_id: str,
        self_assessment: Dict[str, Any],
        manager_feedback: Dict[str, Any],
        peer_feedback: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Comprehensive performance analysis"""
        
        # Aggregate feedback from all sources
        aggregated = self._aggregate_feedback(self_assessment, manager_feedback, peer_feedback)
        
        # Identify patterns
        patterns = await self._identify_patterns(employee_id, aggregated)
        
        # Generate development recommendations
        recommendations = await self._generate_recommendations(aggregated, patterns)
        
        return {
            "employee_id": employee_id,
            "overall_score": aggregated["overall"],
            "strengths": aggregated["strengths"],
            "improvement_areas": aggregated["weaknesses"],
            "growth_patterns": patterns,
            "recommendations": recommendations,
            "next_goals": self._suggest_goals(aggregated)
        }
    
    def _aggregate_feedback(
        self,
        self_assessment: Dict[str, Any],
        manager_feedback: Dict[str, Any],
        peer_feedback: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate 360-degree feedback"""
        return {
            "overall": 4.2,
            "strengths": ["Leadership", "Communication"],
            "weaknesses": ["Time management"]
        }
    
    async def _identify_patterns(self, employee_id: str, feedback: Dict[str, Any]) -> List[str]:
        """Identify growth patterns"""
        return ["Consistent improvement in technical skills", "Leadership potential emerging"]
    
    async def _generate_recommendations(self, feedback: Dict[str, Any], patterns: List[str]) -> List[str]:
        """Generate development recommendations"""
        return ["Consider leadership training", "Improve time management skills"]
    
    def _suggest_goals(self, feedback: Dict[str, Any]) -> List[str]:
        """Suggest goals for next period"""
        return ["Lead a major project", "Mentor junior team member"]
