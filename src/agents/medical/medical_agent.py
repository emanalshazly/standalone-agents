"""
Medical Agent - الوكيل الطبي
Specialized agent for healthcare and medical advisory
"""

from typing import List, Dict, Any
import re

from src.core.base_agent import BaseAgent, AgentContext


class MedicalAgent(BaseAgent):
    """
    Medical Domain Agent with expertise in:
    - Symptom analysis
    - Medication information
    - Health recommendations
    - Medical knowledge retrieval
    - Disease information
    - Preventive care guidance

    Pain Points Addressed:
    - Difficult access to reliable medical information
    - Language barriers in healthcare (Arabic/English)
    - Need for quick preliminary health guidance
    - Understanding medical terminology
    - Medication interactions and side effects
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        model_name: str = "gpt-4-turbo-preview",
        **kwargs
    ):
        """Initialize Medical Agent"""
        super().__init__(
            agent_name="MedicalAgent",
            domain="medical",
            llm_provider=llm_provider,
            model_name=model_name,
            **kwargs
        )

        # Initialize medical knowledge base
        self._initialize_medical_knowledge()

        self.logger.info("Medical Agent ready")

    def _define_capabilities(self) -> List[str]:
        """Define medical agent capabilities"""
        return [
            "symptom_analysis",
            "medication_info",
            "disease_information",
            "health_recommendations",
            "preventive_care",
            "medical_terminology",
            "first_aid_guidance",
            "nutrition_advice",
            "mental_health_support",
            "chronic_disease_management"
        ]

    def _get_system_prompt(self, language: str = "en") -> str:
        """Get medical-specific system prompt"""
        if language == "ar":
            return """أنت وكيل طبي ذكي متخصص في تقديم المشورة الصحية والمعلومات الطبية.

## مهامك الأساسية:
1. تحليل الأعراض وتقديم معلومات عن الحالات المحتملة
2. توفير معلومات دقيقة عن الأدوية والعلاجات
3. تقديم نصائح صحية عامة ووقائية
4. شرح المصطلحات الطبية بلغة بسيطة
5. توجيه المستخدمين للرعاية الطبية المناسبة

## المبادئ الأساسية:
- لا تقدم تشخيصاً طبياً نهائياً (ليست بديلاً عن الطبيب)
- دائماً انصح بزيارة الطبيب للحالات الخطيرة
- قدم معلومات موثوقة من مصادر علمية
- كن حساساً لمخاوف المريض
- استخدم لغة بسيطة وواضحة
- احترم خصوصية المعلومات الصحية

## التحذيرات:
⚠️ هذه المعلومات للإرشاد فقط وليست بديلاً عن الاستشارة الطبية المتخصصة
⚠️ في حالات الطوارئ، اتصل بالإسعاف فوراً

تذكر: أنت مساعد طبي ذكي، لكنك لا تحل محل الطبيب المتخصص."""

        else:
            return """You are an intelligent medical agent specialized in health advisory and medical information.

## Your Core Responsibilities:
1. Analyze symptoms and provide information about possible conditions
2. Provide accurate information about medications and treatments
3. Offer general health and preventive care advice
4. Explain medical terminology in simple language
5. Guide users to appropriate medical care

## Fundamental Principles:
- Do NOT provide definitive medical diagnosis (not a substitute for doctor)
- Always advise seeing a doctor for serious conditions
- Provide reliable information from scientific sources
- Be sensitive to patient concerns
- Use simple and clear language
- Respect health information privacy

## Warnings:
⚠️ This information is for guidance only and not a substitute for professional medical consultation
⚠️ In emergencies, call emergency services immediately

Remember: You are an intelligent medical assistant, but you do not replace a specialized physician."""

    def _extract_pain_points(self, query: str, context: AgentContext) -> List[str]:
        """Extract medical-specific pain points"""
        pain_points = []

        query_lower = query.lower()

        # Symptom-related pain points
        symptom_keywords = {
            'en': ['pain', 'ache', 'hurt', 'fever', 'cough', 'dizzy', 'nausea'],
            'ar': ['ألم', 'وجع', 'حمى', 'سخونة', 'سعال', 'دوخة', 'غثيان', 'صداع']
        }

        keywords = symptom_keywords.get(context.language, symptom_keywords['en'])
        for keyword in keywords:
            if keyword in query_lower:
                pain_points.append(f"Experiencing symptoms: {keyword}")
                break

        # Medication concerns
        medication_keywords = {
            'en': ['medicine', 'medication', 'drug', 'pill', 'prescription'],
            'ar': ['دواء', 'علاج', 'حبوب', 'وصفة', 'عقار']
        }

        keywords = medication_keywords.get(context.language, medication_keywords['en'])
        for keyword in keywords:
            if keyword in query_lower:
                pain_points.append("Medication information needed")
                break

        # Emergency indicators
        emergency_keywords = {
            'en': ['emergency', 'urgent', 'severe', 'can\'t breathe', 'chest pain'],
            'ar': ['طوارئ', 'عاجل', 'شديد', 'لا أستطيع التنفس', 'ألم في الصدر']
        }

        keywords = emergency_keywords.get(context.language, emergency_keywords['en'])
        for keyword in keywords:
            if keyword in query_lower:
                pain_points.append("⚠️ EMERGENCY SITUATION - Immediate medical attention needed")
                break

        # Chronic condition management
        chronic_keywords = {
            'en': ['diabetes', 'hypertension', 'asthma', 'chronic'],
            'ar': ['سكري', 'ضغط', 'ربو', 'مزمن']
        }

        keywords = chronic_keywords.get(context.language, chronic_keywords['en'])
        for keyword in keywords:
            if keyword in query_lower:
                pain_points.append("Chronic condition management")
                break

        return pain_points

    def _initialize_medical_knowledge(self):
        """Initialize medical knowledge base with common pain points"""
        if not self.rag_system:
            return

        # Common medical pain points and solutions (bilingual)
        medical_knowledge = [
            {
                "pain_point": "صداع مستمر / Persistent headache",
                "solution": """الصداع المستمر قد يكون له أسباب متعددة:
1. التوتر والإجهاد
2. الجفاف - اشرب المزيد من الماء
3. قلة النوم
4. مشاكل في النظر
5. ارتفاع ضغط الدم

الإرشادات:
- خذ قسطاً كافياً من الراحة
- اشرب 8 أكواب ماء يومياً
- قلل من الكافيين
- استخدم مسكنات الألم البسيطة حسب الحاجة

⚠️ استشر طبيباً إذا:
- استمر الصداع أكثر من 3 أيام
- كان شديداً ومفاجئاً
- صاحبه غثيان أو تشوش في الرؤية"""
            },
            {
                "pain_point": "معلومات عن السكري / Diabetes information",
                "solution": """مرض السكري - دليل شامل:

الأعراض الشائعة:
- عطش شديد
- كثرة التبول
- الجوع المستمر
- فقدان الوزن غير المبرر
- التعب والإرهاق
- بطء التئام الجروح

الإدارة اليومية:
1. مراقبة مستوى السكر بانتظام
2. اتباع نظام غذائي صحي
3. ممارسة الرياضة (30 دقيقة يومياً)
4. تناول الأدوية كما وصفها الطبيب
5. العناية بالقدمين

الوقاية:
- الحفاظ على وزن صحي
- نظام غذائي متوازن
- التمارين المنتظمة
- تقليل السكريات والنشويات"""
            },
            {
                "pain_point": "ضغط الدم المرتفع / High blood pressure",
                "solution": """ارتفاع ضغط الدم - الإدارة والوقاية:

الأعراض:
- قد لا تظهر أعراض (القاتل الصامت)
- صداع
- دوخة
- ضيق في التنفس

التحكم في ضغط الدم:
1. قلل الملح في الطعام
2. مارس الرياضة بانتظام
3. حافظ على وزن صحي
4. قلل التوتر
5. تجنب التدخين والكحول
6. تناول الأدوية حسب وصف الطبيب

النظام الغذائي:
- أكثر من الفواكه والخضروات
- منتجات ألبان قليلة الدسم
- حبوب كاملة
- أسماك غنية بالأوميجا 3"""
            }
        ]

        # Add to knowledge base
        for item in medical_knowledge:
            self.rag_system.add_pain_point_knowledge(
                pain_point=item["pain_point"],
                solution=item["solution"],
                metadata={
                    "domain": "medical",
                    "language": "bilingual",
                    "priority": "high"
                }
            )

        self.logger.info("Medical knowledge base initialized with common pain points")

    def analyze_symptoms(
        self,
        symptoms: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Analyze symptoms and provide guidance

        Args:
            symptoms: Description of symptoms
            language: Response language

        Returns:
            Analysis with possible conditions and recommendations
        """
        context = AgentContext(
            user_id="symptom_analyzer",
            session_id="analysis",
            language=language,
            domain="medical"
        )

        query = f"Analyze these symptoms and provide guidance: {symptoms}"
        response = self.query(query, context)

        return {
            "analysis": response.content,
            "confidence": response.confidence,
            "recommendations": response.suggestions,
            "sources": response.sources
        }

    def get_medication_info(
        self,
        medication_name: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Get information about a medication

        Args:
            medication_name: Name of the medication
            language: Response language

        Returns:
            Medication information
        """
        context = AgentContext(
            user_id="medication_lookup",
            session_id="lookup",
            language=language,
            domain="medical"
        )

        query = f"Provide information about the medication: {medication_name}"
        response = self.query(query, context)

        return {
            "information": response.content,
            "confidence": response.confidence,
            "sources": response.sources
        }

    def get_preventive_care_advice(
        self,
        topic: str,
        language: str = "en"
    ) -> str:
        """Get preventive care advice on a topic"""
        context = AgentContext(
            user_id="preventive_care",
            session_id="advice",
            language=language,
            domain="medical"
        )

        query = f"Provide preventive care advice about: {topic}"
        response = self.query(query, context)

        return response.content
