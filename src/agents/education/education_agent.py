"""
Education Agent - الوكيل التعليمي
Specialized agent for learning and training support
"""

from typing import List
from src.core.base_agent import BaseAgent, AgentContext


class EducationAgent(BaseAgent):
    """
    Education Domain Agent with expertise in:
    - Personalized learning
    - Study techniques
    - Course recommendations
    - Skill development
    - Career guidance
    - Educational resources

    Pain Points Addressed:
    - Overwhelming educational options
    - Ineffective study methods
    - Career path confusion
    - Skill gap identification
    - Learning resource discovery
    """

    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4-turbo-preview", **kwargs):
        super().__init__(
            agent_name="EducationAgent",
            domain="education",
            llm_provider=llm_provider,
            model_name=model_name,
            **kwargs
        )
        self.logger.info("Education Agent ready")

    def _define_capabilities(self) -> List[str]:
        return [
            "personalized_learning",
            "study_techniques",
            "course_recommendations",
            "skill_development",
            "career_guidance",
            "resource_discovery",
            "learning_path_design"
        ]

    def _get_system_prompt(self, language: str = "en") -> str:
        if language == "ar":
            return """أنت وكيل تعليمي ذكي متخصص في دعم التعلم والتطوير.

## مهامك:
1. تصميم مسارات تعلم مخصصة
2. توصية بالموارد التعليمية
3. تقديم تقنيات دراسة فعالة
4. المساعدة في تطوير المهارات
5. الإرشاد المهني

## المبادئ:
- خطط شاملة ومخصصة
- موارد موثوقة ومتنوعة
- تشجيع التعلم المستمر
- دعم أساليب التعلم المختلفة"""
        else:
            return """You are an intelligent education agent specialized in learning and development support.

## Responsibilities:
1. Design personalized learning paths
2. Recommend educational resources
3. Provide effective study techniques
4. Support skill development
5. Career guidance

## Principles:
- Comprehensive and personalized plans
- Reliable and diverse resources
- Encourage continuous learning
- Support different learning styles"""

    def _extract_pain_points(self, query: str, context: AgentContext) -> List[str]:
        pain_points = []
        query_lower = query.lower()

        if any(word in query_lower for word in ['learn', 'تعلم', 'دراسة']):
            pain_points.append("Learning guidance needed")

        if any(word in query_lower for word in ['career', 'مهنة', 'وظيفة']):
            pain_points.append("Career guidance required")

        return pain_points
