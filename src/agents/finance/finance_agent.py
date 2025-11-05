"""
Finance Agent - الوكيل المالي
Specialized agent for financial analysis and advisory
"""

from typing import List, Dict, Any
from src.core.base_agent import BaseAgent, AgentContext


class FinanceAgent(BaseAgent):
    """
    Finance Domain Agent with expertise in:
    - Budget planning
    - Investment analysis
    - Financial literacy
    - Saving strategies
    - Debt management
    - Retirement planning

    Pain Points Addressed:
    - Lack of financial literacy
    - Difficulty in budget management
    - Investment uncertainty
    - Debt stress
    - Retirement planning confusion
    """

    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4-turbo-preview", **kwargs):
        super().__init__(
            agent_name="FinanceAgent",
            domain="finance",
            llm_provider=llm_provider,
            model_name=model_name,
            **kwargs
        )
        self._initialize_finance_knowledge()
        self.logger.info("Finance Agent ready")

    def _define_capabilities(self) -> List[str]:
        return [
            "budget_planning",
            "investment_analysis",
            "saving_strategies",
            "debt_management",
            "financial_literacy",
            "retirement_planning",
            "tax_guidance",
            "risk_assessment"
        ]

    def _get_system_prompt(self, language: str = "en") -> str:
        if language == "ar":
            return """أنت وكيل مالي ذكي متخصص في التخطيط المالي والاستشارات.

## مهامك:
1. تخطيط الميزانية الشخصية
2. تحليل الاستثمارات
3. استراتيجيات الادخار
4. إدارة الديون
5. التخطيط للتقاعد

## المبادئ:
- قدم نصائح مالية عامة
- ساعد في فهم المفاهيم المالية
- شجع على الادخار والتخطيط
- انصح باستشارة مستشار مالي للقرارات الكبيرة

⚠️ هذه إرشادات عامة وليست نصائح استثمارية ملزمة"""
        else:
            return """You are an intelligent finance agent specialized in financial planning and advisory.

## Responsibilities:
1. Personal budget planning
2. Investment analysis
3. Saving strategies
4. Debt management
5. Retirement planning

## Principles:
- Provide general financial advice
- Help understand financial concepts
- Encourage saving and planning
- Advise consulting financial advisor for major decisions

⚠️ This is general guidance, not binding investment advice"""

    def _extract_pain_points(self, query: str, context: AgentContext) -> List[str]:
        pain_points = []
        query_lower = query.lower()

        if any(word in query_lower for word in ['budget', 'ميزانية']):
            pain_points.append("Budget planning needed")

        if any(word in query_lower for word in ['debt', 'ديون', 'قرض']):
            pain_points.append("Debt management required")

        if any(word in query_lower for word in ['saving', 'save', 'ادخار']):
            pain_points.append("Saving strategy needed")

        return pain_points

    def _initialize_finance_knowledge(self):
        if not self.rag_system:
            return

        finance_knowledge = [
            {
                "pain_point": "كيفية عمل ميزانية شخصية / How to create personal budget",
                "solution": """إنشاء ميزانية شخصية - دليل خطوة بخطوة:

القاعدة 50/30/20:
- 50% للاحتياجات الأساسية (إيجار، طعام، مواصلات)
- 30% للرغبات (ترفيه، هوايات)
- 20% للادخار والاستثمار

الخطوات:
1. احسب دخلك الشهري
2. سجل جميع النفقات
3. صنف النفقات (أساسية/ثانوية)
4. حدد أهداف ادخار
5. تابع وراجع شهرياً

نصائح:
✓ استخدم تطبيقات إدارة المال
✓ ابدأ صندوق طوارئ (3-6 أشهر من النفقات)
✓ قلل الديون ذات الفائدة العالية"""
            }
        ]

        for item in finance_knowledge:
            self.rag_system.add_pain_point_knowledge(
                pain_point=item["pain_point"],
                solution=item["solution"],
                metadata={"domain": "finance", "priority": "high"}
            )
