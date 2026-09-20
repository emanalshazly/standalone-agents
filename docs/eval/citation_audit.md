# سجل مراجعة الاستشهادات القانونية / Citation Audit Log

**غير قابل للتفاوض قبل أي استخدام إنتاجي حقيقي.** كل صف في هذا الجدول يمثل مُدخلاً واحداً
في `src/knowledge/legal_eg/labor_law_2025_seed.json`، ويجب أن يراجعه محامٍ مصري مرخّص
مقارنةً بنص الجريدة الرسمية الأصلي — وليس مقارنةً بمصادر ثانوية (تحليلات مكاتب محاماة)
كما جُمعت أول مرة بواسطة وكيل بحث آلي.

**Non-negotiable before any real production use.** Each row below is one entry in
`src/knowledge/legal_eg/labor_law_2025_seed.json`, and must be reviewed by a licensed
Egyptian lawyer against the primary Official Gazette text — not against the secondary
sources (law-firm client alerts) an AI research agent originally used to compile it.

## كيفية الاستخدام / How to use this log

1. لكل `entry_id`، افتح نص الجريدة الرسمية الأصلي (لا تعتمد على مواقع مكاتب المحاماة).
2. تحقق من رقم المادة والنص الفعلي.
3. سجّل الحالة: `✅ مطابق` / `⚠️ يحتاج تصحيح` / `❌ خاطئ`.
4. إذا كان يحتاج تصحيحاً، أرسله عبر `/feedback/submit` ثم اعتمده عبر `/feedback/{id}/approve`
   (انظر `src/feedback/curation_pipeline.py`) — لا تُعدّل ملف JSON يدوياً دون تسجيل من
   راجعه ومتى.

| entry_id | الحالة الحالية | رقم المادة المذكور | تاريخ المراجعة | المحامي المراجع | القرار | ملاحظات |
|---|---|---|---|---|---|---|
| probation_period | seed (غير مُراجَع) | 104 (مصدر واحد فقط) | — | — | — | — |
| working_hours | seed (غير مُراجَع) | 117 (مصدر واحد فقط) | — | — | — | — |
| overtime_cap | seed (غير مُراجَع) | 121 (مصدر واحد فقط) | — | — | — | — |
| notice_period_indefinite | seed (غير مُراجَع) | **متضارب: 156 أو 123** | — | — | — | أولوية عالية — تعارض موثّق بين المصادر الثانوية |
| severance_pay_indefinite | seed (غير مُراجَع) | 165 (مصدر واحد فقط) | — | — | — | — |
| fixed_term_early_termination | seed (غير مُراجَع) | غير مؤكد | — | — | — | لم يُعثر على رقم مادة في البحث |
| annual_leave_tiers | seed (غير مُراجَع) | غير مؤكد | — | — | — | لم يُعثر على رقم مادة في البحث |

## قاعدة الإصدار / Release gate

لا تُشغَّل هذه القاعدة المعرفية لمستخدمين حقيقيين حتى تكون جميع الصفوف أعلاه
`✅ مطابق`، أو حتى تُستبدل المُدخلات غير المؤكدة بمُدخلات معتمدة عبر
`/feedback/{id}/approve` (والتي تُعلَّم تلقائياً `verified_by_lawyer=true`).

This knowledge base must not be served to real users until every row above is
`✅ matches`, or the unconfirmed entries have been replaced with lawyer-approved
ones via `/feedback/{id}/approve` (which are automatically tagged `verified_by_lawyer=true`).
