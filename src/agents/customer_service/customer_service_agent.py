"""
Customer Service Agent - وكيل خدمة العملاء
Specialized agent for support and assistance
"""

from typing import List
from src.core.base_agent import BaseAgent, AgentContext


class CustomerServiceAgent(BaseAgent):
    """
    Customer Service Domain Agent with expertise in:
    - Issue resolution
    - Product support
    - Complaint handling
    - FAQ assistance
    - Ticket routing

    Pain Points Addressed:
    - Long wait times
    - Ineffective support
    - Language barriers
    - Complex issue resolution
    """

    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4-turbo-preview", **kwargs):
        super().__init__(
            agent_name="CustomerServiceAgent",
            domain="customer_service",
            llm_provider=llm_provider,
            model_name=model_name,
            **kwargs
        )
        self.logger.info("Customer Service Agent ready")

    def _define_capabilities(self) -> List[str]:
        return [
            "issue_resolution",
            "product_support",
            "complaint_handling",
            "faq_assistance",
            "empathy_response"
        ]

    def _get_system_prompt(self, language: str = "en") -> str:
        if language == "ar":
            return """أنت وكيل خدمة عملاء ذكي ومحترف.

## مهامك:
1. حل المشاكل بكفاءة
2. تقديم الدعم الفني
3. معالجة الشكاوى باحترافية
4. الإجابة على الأسئلة الشائعة
5. التعامل بتعاطف واحترام

## المبادئ:
- استمع بعناية
- كن متعاطفاً ومحترماً
- قدم حلولاً واضحة
- تابع حتى الحل"""
        else:
            return """You are an intelligent and professional customer service agent.

## Responsibilities:
1. Efficient issue resolution
2. Technical support
3. Professional complaint handling
4. FAQ assistance
5. Empathetic interaction

## Principles:
- Listen carefully
- Be empathetic and respectful
- Provide clear solutions
- Follow up until resolution"""

    def _extract_pain_points(self, query: str, context: AgentContext) -> List[str]:
        pain_points = []
        if any(word in query.lower() for word in ['problem', 'issue', 'مشكلة']):
            pain_points.append("Issue resolution needed")
        return pain_points
