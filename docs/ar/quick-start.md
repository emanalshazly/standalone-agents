# دليل البداية السريعة

## المتطلبات الأساسية

- Python 3.10 أو أحدث
- pip (مدير الحزم)
- مفتاح API من OpenAI أو Anthropic

## التثبيت

### 1. استنساخ المشروع

```bash
git clone https://github.com/emanalshazly/standalone-agents.git
cd standalone-agents
```

### 2. إنشاء بيئة افتراضية

```bash
python -m venv venv
source venv/bin/activate  # على Windows: venv\Scripts\activate
```

### 3. تثبيت الحزم المطلوبة

```bash
pip install -r requirements.txt
```

### 4. إعداد المتغيرات البيئية

```bash
cp .env.example .env
```

افتح ملف `.env` وأضف مفتاح API الخاص بك:

```env
OPENAI_API_KEY=your-api-key-here
```

## الاستخدام الأساسي

### مثال بسيط - الوكيل الطبي

```python
from src.agents.medical.medical_agent import MedicalAgent
from src.core.base_agent import AgentContext

# إنشاء الوكيل الطبي
agent = MedicalAgent()

# إنشاء السياق
context = AgentContext(
    user_id="user123",
    session_id="session1",
    language="ar",
    domain="medical"
)

# طرح سؤال
response = agent.query(
    "ما هي أعراض مرض السكري؟",
    context=context
)

# عرض الإجابة
print(response.content)
print(f"الثقة: {response.confidence}")
```

### استخدام الوكيل المالي

```python
from src.agents.finance.finance_agent import FinanceAgent

agent = FinanceAgent()

context = AgentContext(
    user_id="user456",
    session_id="session2",
    language="ar",
    domain="finance"
)

response = agent.query(
    "كيف أبدأ في الادخار الشهري؟",
    context=context
)

print(response.content)
```

### استخدام متعدد الوكلاء

```python
from src.core.orchestrator import AgentOrchestrator, CollaborationStrategy
from src.agents.medical.medical_agent import MedicalAgent
from src.agents.finance.finance_agent import FinanceAgent

# إنشاء المنسق
orchestrator = AgentOrchestrator()

# تسجيل الوكلاء
medical = MedicalAgent()
finance = FinanceAgent()

orchestrator.register_agent("medical", medical, domains=["medical"])
orchestrator.register_agent("finance", finance, domains=["finance"])

# استعلام تعاوني
context = AgentContext(
    user_id="user789",
    session_id="collab1",
    language="ar"
)

response = orchestrator.collaborative_query(
    user_query="كيف أخطط مالياً لتكاليف العلاج الطبي؟",
    context=context,
    required_agents=["medical", "finance"],
    strategy=CollaborationStrategy.CONSENSUS
)

print(response.primary_response)
```

## تشغيل API

### بدء الخادم

```bash
cd src/api
python main.py
```

أو باستخدام uvicorn:

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### الوصول إلى الوثائق التفاعلية

افتح المتصفح وانتقل إلى:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### أمثلة API

#### استعلام وكيل محدد

```bash
curl -X POST "http://localhost:8000/query/medical" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ما هي أعراض الإنفلونزا؟",
    "language": "ar",
    "user_id": "user123"
  }'
```

#### استعلام تعاوني

```bash
curl -X POST "http://localhost:8000/collaborative-query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "نصائح للصحة المالية",
    "language": "ar",
    "required_agents": ["medical", "finance"],
    "strategy": "consensus"
  }'
```

## إضافة المعرفة للوكلاء

### إضافة معرفة يدوياً

```python
agent = MedicalAgent()

# إضافة معلومات طبية
agent.add_knowledge(
    content="السكري من النوع الثاني يمكن إدارته من خلال النظام الغذائي والرياضة...",
    metadata={
        "topic": "diabetes",
        "language": "ar",
        "source": "medical_journal"
    },
    source="verified_source"
)
```

### استيراد من ملف

```python
agent.rag_system.import_from_file(
    file_path="knowledge/medical/diabetes.txt",
    source="medical_knowledge",
    metadata={"verified": True}
)
```

## التعلم من التغذية الراجعة

```python
# بعد الحصول على إجابة
agent.learn_from_feedback(
    query="ما هي أعراض السكري؟",
    response=response.content,
    feedback={
        "rating": 4.5,
        "text": "معلومات مفيدة جداً!",
        "corrections": None
    }
)

# الحصول على رؤى التعلم
insights = agent.learning_system.get_learning_insights()
print(f"إجمالي التفاعلات: {insights['total_interactions']}")
print(f"متوسط التقييم: {insights['feedback_stats']['average_rating']}")
```

## الخطوات التالية

1. **اقرأ الوثائق الكاملة**: راجع ملفات الوثائق لمزيد من التفاصيل
2. **جرب الأمثلة**: نفذ الأمثلة في مجلد `examples/`
3. **أنشئ وكيل مخصص**: اتبع دليل إنشاء الوكلاء
4. **ساهم في المشروع**: راجع `CONTRIBUTING.md`

## الدعم

- **الوثائق**: [docs/](../README.md)
- **المشاكل**: [GitHub Issues](https://github.com/emanalshazly/standalone-agents/issues)
- **Discord**: [انضم لمجتمعنا](https://discord.gg/standalone-agents)

---

**مبروك! 🎉 أنت الآن جاهز لاستخدام نظام الوكلاء المتخصصين**
