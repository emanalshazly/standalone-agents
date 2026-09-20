# دليل البداية السريعة

<div dir="rtl">

## المتطلبات الأساسية

- Python 3.10 أو أحدث
- مفتاح API من OpenAI أو Anthropic
- اتصال بالإنترنت (لتحميل نموذج التضمين متعدد اللغات ونموذج إعادة الترتيب عند أول تشغيل)

## التثبيت

```bash
git clone https://github.com/emanalshazly/standalone-agents.git
cd standalone-agents
python -m venv venv
source venv/bin/activate  # على Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

افتح `.env` وأضف مفتاح API الخاص بك:

```env
OPENAI_API_KEY=your-api-key-here
```

## الاستخدام الأساسي

هذا المشروع أصبح وكيلاً واحداً متخصصاً (وليس ستة وكلاء عامّين كما كان سابقاً) —
راجع [PROJECT_OVERVIEW.md](../../PROJECT_OVERVIEW.md) لفهم سبب هذا التحول.

```python
from src.agents.legal.legal_agent import EgyptianLegalAgent

agent = EgyptianLegalAgent()

answer = agent.query("هل يجوز لصاحب العمل تجديد فترة الاختبار؟")

print(answer.answer)
print("يحتاج تحويل لمحامٍ:", answer.handoff_required)
print("المصادر لم تُراجَع من محامٍ بعد:", answer.lawyer_review_pending)
print("الاستشهادات:", answer.citations)
```

⚠️ لاحظ أن `lawyer_review_pending` سيكون `True` دائماً حالياً — قاعدة المعرفة
الحالية مُجمَّعة من مصادر ثانوية ولم يراجعها محامٍ مصري مرخّص بعد. راجع
[docs/eval/citation_audit.md](../eval/citation_audit.md).

### أسئلة خارج النطاق تُحوَّل تلقائياً لمحامٍ بشري

```python
answer = agent.query("أنا متهم في قضية جنائية، كيف أدافع عن نفسي؟")
print(answer.handoff_required)  # True — القانون الجنائي خارج نطاق هذا الوكيل عمداً
```

## تشغيل الـ API

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

الوثائق التفاعلية على: http://localhost:8000/docs

### مثال استعلام عبر curl

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "كم عدد أيام الإجازة السنوية المستحقة لي في السنة الثانية؟"}'
```

### اقتراح تصحيح لمعلومة قانونية

```bash
curl -X POST "http://localhost:8000/feedback/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "...",
    "draft_answer": "...",
    "user_correction": "النص الصحيح مع رقم المادة والمصدر الرسمي"
  }'
```

لن يُستخدم هذا التصحيح في أي إجابة مستقبلية حتى يعتمده مراجع بشري مُسمّى عبر
`/feedback/{id}/approve` (يتطلب `X-API-Key`).

## الاختبارات

```bash
# اختبارات منطقية لا تحتاج مفتاح API ولا اتصال إنترنت
pytest tests/ --ignore=tests/eval

# تقييم الاسترجاع فقط (يحتاج تحميل نموذج التضمين، لا يحتاج مفتاح API)
python tests/eval/run_eval.py --mode retrieval

# تقييم كامل شامل RAGAS (يحتاج OPENAI_API_KEY)
python tests/eval/run_eval.py --mode full
```

## الخطوات التالية

1. اقرأ [PROJECT_OVERVIEW.md](../../PROJECT_OVERVIEW.md) لفهم السياق التنافسي والقرارات الاستراتيجية
2. راجع [docs/eval/citation_audit.md](../eval/citation_audit.md) قبل أي استخدام حقيقي
3. جرّب [examples/basic_usage.py](../../examples/basic_usage.py)

</div>
