# سجل مراجعة وكيل المساعدة القضائية / Case-Assistant Audit Log

**هذا السجل أشد صرامة من [`citation_audit.md`](citation_audit.md)، وليس بديلاً عنه.**
وكيل المساعدة القضائية (`CaseAssistantAgent`, `src/agents/case_assistant/`) يُنتج
مسودات مستندات فعلية قد يعتمد عليها مستخدم في نزاع حقيقي — وهي بالضبط الفئة التي
تسبّبت في عقوبات قضائية بمئات الآلاف من الدولارات على محامين قدّموا استشهادات
مُختلقة بالذكاء الاصطناعي في مستندات فعلية خلال 2026 (راجع
[`PROJECT_OVERVIEW.md`](../../PROJECT_OVERVIEW.md) القسم 4).

**This log is stricter than [`citation_audit.md`](citation_audit.md), not a
replacement for it.** The case-assistant agent produces draft documents a
user might actually rely on in a real dispute — exactly the category that
produced six-figure court sanctions against lawyers who filed
AI-fabricated citations in 2026.

## حالة الإصدار الحالية / Current release status

> 🔴 **لم يراجع أي محامٍ مرخّص هذا المسار بعد. يُعامَل كنموذج أولي داخلي فقط.**
> 🔴 **No licensed lawyer has reviewed this track yet. Treat as an internal prototype only.**

## بروتوكول المراجعة لكل مسودة / Per-draft review protocol

قبل أي استخدام حقيقي، يجب على محامٍ مصري مرخّص مراجعة **كل مسودة على حدة** (وليس
عيّنة عشوائية كما في `citation_audit.md`)، والتحقق من:

1. **كل استشهاد [n] في المسودة**: هل النص المصدر المحلي يقول فعلاً هذا؟ (نفس فحص
   `citation_verifier.py`، لكن بمراجعة بشرية وليس LLM-as-judge فقط).
2. **مصادر الويب المذكورة في قسم "ملاحظات بحثية إضافية"**: هل هي فعلاً ذات صلة
   وحديثة وموثوقة؟ هذه المصادر **لم تمر بأي تحقق آلي من صحة المحتوى** — فقط
   `trust_tier="web_unverified"` كعلامة، وليس كفحص.
3. **وقائع الحالة**: هل المسودة تطابق فقط ما ذكره المستخدم، بدون افتراض وقائع
   إضافية؟
4. **فجوات الأدلة**: هل تحليل `EvidenceReviewSubAgent` واقعي، أم فوّت نقاطاً
   جوهرية يعرفها المحامي من خبرته؟
5. **النطاق**: هل تسرّبت أي عناصر جنائية أو ضريبية لم يلتقطها `classify_case_scope`
   أو الفحص الدفاعي في `_contains_out_of_scope_keywords`؟

| رقم المراجعة | تاريخ | المحامي المراجع | القرار (اعتماد/رفض/تعديل) | ملاحظات |
|---|---|---|---|---|
| — | — | — | — | لا توجد مراجعات مسجّلة بعد |

## قاعدة الإصدار / Release gate

لا يُطلق `/case/draft` لمستخدمين حقيقيين قبل:

- [ ] مراجعة محامٍ مرخّص لعيّنة تمثيلية من كل نوع مستند مدعوم (بدءاً بـ "مذكرة شكوى" عمالية)
- [ ] توثيق نتائج المراجعة في هذا الملف لكل حالة تمت مراجعتها فعلياً مع مستخدمين
- [ ] تفعيل Langfuse tracing لتتبع كل قرار `blocked`/`handoff` (راجع "الفجوات" في PROJECT_OVERVIEW.md)
- [ ] مراجعة قائمة `_CRIMINAL_LAW_KEYWORDS` في `src/subagents/drafting_subagent.py` من محامٍ للتأكد من شمولها

This gate is not optional and is stricter than the literacy agent's
because the downside of a bad draft here is a real filing or negotiation,
not just a confusing explanation.
