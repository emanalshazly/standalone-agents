"""
E-commerce Agent - وكيل التجارة الإلكترونية
Specialized agent for shopping and product advisory
"""

from typing import List
from src.core.base_agent import BaseAgent, AgentContext


class EcommerceAgent(BaseAgent):
    """
    E-commerce Domain Agent with expertise in:
    - Product recommendations
    - Price comparison
    - Shopping assistance
    - Product reviews analysis
    - Deal finding

    Pain Points Addressed:
    - Product overwhelm
    - Price uncertainty
    - Review confusion
    - Purchase decision difficulty
    """

    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4-turbo-preview", **kwargs):
        super().__init__(
            agent_name="EcommerceAgent",
            domain="ecommerce",
            llm_provider=llm_provider,
            model_name=model_name,
            **kwargs
        )
        self.logger.info("E-commerce Agent ready")

    def _define_capabilities(self) -> List[str]:
        return [
            "product_recommendations",
            "price_comparison",
            "review_analysis",
            "deal_finding",
            "shopping_assistance"
        ]

    def _get_system_prompt(self, language: str = "en") -> str:
        if language == "ar":
            return """أنت وكيل تجارة إلكترونية ذكي متخصص في مساعدة المتسوقين.

## مهامك:
1. توصيات المنتجات المخصصة
2. مقارنة الأسعار
3. تحليل المراجعات
4. إيجاد أفضل العروض
5. مساعدة في اتخاذ قرار الشراء"""
        else:
            return """You are an intelligent e-commerce agent specialized in shopping assistance.

## Responsibilities:
1. Personalized product recommendations
2. Price comparison
3. Review analysis
4. Deal finding
5. Purchase decision support"""

    def _extract_pain_points(self, query: str, context: AgentContext) -> List[str]:
        pain_points = []
        if any(word in query.lower() for word in ['buy', 'purchase', 'شراء']):
            pain_points.append("Purchase decision support needed")
        return pain_points
