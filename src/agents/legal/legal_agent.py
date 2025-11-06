"""
Legal Agent - الوكيل القانوني
Specialized agent for legal consultation and documentation
"""

from typing import List, Dict, Any
from src.core.base_agent import BaseAgent, AgentContext


class LegalAgent(BaseAgent):
    """
    Legal Domain Agent with expertise in:
    - Contract review and analysis
    - Legal consultation
    - Rights and obligations
    - Labor law guidance
    - Business law support
    - Legal document drafting

    Pain Points Addressed:
    - High cost of legal consultation
    - Complexity of legal language
    - Understanding rights and responsibilities
    - Contract comprehension
    - Access to legal information in Arabic
    """

    def __init__(self, llm_provider: str = "openai", model_name: str = "gpt-4-turbo-preview", **kwargs):
        super().__init__(
            agent_name="LegalAgent",
            domain="legal",
            llm_provider=llm_provider,
            model_name=model_name,
            **kwargs
        )
        self._initialize_legal_knowledge()
        self.logger.info("Legal Agent ready")

    def _define_capabilities(self) -> List[str]:
        return [
            "contract_review",
            "legal_consultation",
            "rights_information",
            "labor_law",
            "business_law",
            "document_drafting",
            "legal_terminology",
            "dispute_resolution",
            "compliance_guidance"
        ]

    def _get_system_prompt(self, language: str = "en") -> str:
        if language == "ar":
            return """أنت وكيل قانوني ذكي متخصص في تقديم المشورة القانونية والمعلومات.

## مهامك:
1. مراجعة وتحليل العقود
2. تقديم استشارات قانونية عامة
3. شرح الحقوق والواجبات
4. توفير معلومات عن قانون العمل
5. المساعدة في صياغة الوثائق القانونية

## المبادئ:
- لا تقدم مشورة قانونية ملزمة (ليست بديلاً عن المحامي)
- قدم معلومات دقيقة ومحدثة
- اشرح المصطلحات القانونية بوضوح
- انصح باستشارة محامٍ للحالات المعقدة

⚠️ هذه معلومات عامة وليست مشورة قانونية ملزمة"""
        else:
            return """You are an intelligent legal agent specialized in legal consultation and information.

## Responsibilities:
1. Contract review and analysis
2. General legal consultation
3. Explaining rights and obligations
4. Labor law information
5. Legal document drafting assistance

## Principles:
- Do NOT provide binding legal advice (not a substitute for lawyer)
- Provide accurate and updated information
- Explain legal terms clearly
- Advise consulting a lawyer for complex cases

⚠️ This is general information, not binding legal advice"""

    def _extract_pain_points(self, query: str, context: AgentContext) -> List[str]:
        pain_points = []
        query_lower = query.lower()

        if any(word in query_lower for word in ['contract', 'عقد']):
            pain_points.append("Contract understanding needed")

        if any(word in query_lower for word in ['rights', 'حقوق', 'حق']):
            pain_points.append("Rights clarification required")

        if any(word in query_lower for word in ['employment', 'عمل', 'وظيفة']):
            pain_points.append("Labor law guidance needed")

        return pain_points

    def _initialize_legal_knowledge(self):
        if not self.rag_system:
            return

        legal_knowledge = [
            {
                "pain_point": "عقد العمل / Employment contract",
                "solution": """عقد العمل - حقوقك وواجباتك:

العناصر الأساسية:
1. المسمى الوظيفي ووصف العمل
2. الراتب والبدلات
3. ساعات العمل والإجازات
4. فترة التجربة
5. شروط الإنهاء

حقوقك:
- راتب في الوقت المحدد
- بيئة عمل آمنة
- إجازة سنوية مدفوعة
- إجازة مرضية
- نهاية خدمة

⚠️ اقرأ العقد بعناية قبل التوقيع"""
            }
        ]

        for item in legal_knowledge:
            self.rag_system.add_pain_point_knowledge(
                pain_point=item["pain_point"],
                solution=item["solution"],
                metadata={"domain": "legal", "priority": "high"}
            )
