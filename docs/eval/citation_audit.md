# سجل مراجعة الاستشهادات القانونية / Citation Audit Log

**غير قابل للتفاوض قبل أي استخدام إنتاجي حقيقي.** كل صف في هذا الجدول يمثل مُدخلاً واحداً
في أحد ملفات `src/knowledge/legal_eg/*_seed.json`، ويجب أن يراجعه محامٍ مصري مرخّص
مقارنةً بنص الجريدة الرسمية الأصلي — وليس مقارنةً بمصادر ثانوية (تحليلات مكاتب محاماة)
كما جُمعت أول مرة بواسطة وكيل بحث آلي.

**Non-negotiable before any real production use.** Each row below is one entry in a
`src/knowledge/legal_eg/*_seed.json` file, and must be reviewed by a licensed
Egyptian lawyer against the primary Official Gazette text — not against the secondary
sources (law-firm client alerts) an AI research agent originally used to compile it.

## Runbook — خطوات المراجعة الفعلية / How a review session actually works

هذا القسم يحوّل الوصف النظري أدناه إلى خطوات تنفيذية فعلية. **إيجاد والتعاقد مع محامٍ
مصري مرخّص فعلي هو مسؤوليتك أنتِ — لا يوجد كود يعوّض عن ذلك.** دور الأدوات هنا هو
تسهيل تسجيل قرار المحامي فقط، وليس اتخاذه.

1. لكل `entry_id` في كل ملف `*_seed.json`، افتح نص الجريدة الرسمية الأصلي (لا تعتمد
   على مواقع مكاتب المحاماة كمصدر نهائي، حتى لو كانت هي المصدر الذي استُخدم لتجميع
   المُدخل أول مرة).
2. قارن رقم المادة والنص الفعلي مع ملخص `summary_ar`/`summary_en` في ملف الـ seed.
3. سجّل القرار في الجدول المناسب أدناه: `✅ مطابق` / `⚠️ يحتاج تصحيح` / `❌ خاطئ`،
   مع تاريخ المراجعة واسم المحامي.
4. **إذا كان "✅ مطابق" (صحيح كما هو مكتوب)**: شغّلي
   `python scripts/mark_reviewed.py <entry_id> "<اسم المحامي>" <رابط المصدر الرسمي>`
   — هذا يُعلِّم المُدخل `verified_by_lawyer=true` في فهرس الاسترجاع مباشرة، بدون
   المرور بمسار "اقتراح تصحيح" (الذي لا يناسب حالة "لا يوجد تصحيح، فقط تأكيد").
5. **إذا كان "⚠️ يحتاج تصحيح" أو "❌ خاطئ"**: استخدمي `/feedback/submit` ثم
   `/feedback/{id}/approve` (انظر `src/feedback/curation_pipeline.py`) — هذا المسار
   مخصص لاقتراح نص جديد أو مُصحَّح، ويُعلِّم النتيجة `verified_by_lawyer=true` تلقائياً
   عند الاعتماد.
6. لا تُعدّلي ملفات JSON الأصلية يدوياً لتغيير `verified_by_lawyer` — هذا الحقل يجب أن
   يُضبط فقط عبر الأدوات في الخطوتين 4 و5 حتى يبقى سجل "من راجع ومتى" دقيقاً.

## قانون العمل / Labor Law (`labor_law_2025_seed.json`)

| entry_id | الحالة الحالية | رقم المادة المذكور | تاريخ المراجعة | المحامي المراجع | القرار | ملاحظات |
|---|---|---|---|---|---|---|
| probation_period | seed (غير مُراجَع) | 104 (مصدر واحد فقط) | — | — | — | — |
| working_hours | seed (غير مُراجَع) | 117 (مصدر واحد فقط) | — | — | — | — |
| overtime_cap | seed (غير مُراجَع) | 121 (مصدر واحد فقط) | — | — | — | — |
| notice_period_indefinite | seed (غير مُراجَع) | **متضارب: 156 أو 123** | — | — | — | أولوية عالية — تعارض موثّق بين المصادر الثانوية |
| severance_pay_indefinite | seed (غير مُراجَع) | 165 (مصدر واحد فقط) | — | — | — | — |
| fixed_term_early_termination | seed (غير مُراجَع) | غير مؤكد | — | — | — | لم يُعثر على رقم مادة في البحث |
| annual_leave_tiers | seed (غير مُراجَع) | غير مؤكد | — | — | — | لم يُعثر على رقم مادة في البحث |

## قانون الإيجار / Rental Law (`rental_law_2025_seed.json`)

| entry_id | الحالة الحالية | رقم المادة المذكور | تاريخ المراجعة | المحامي المراجع | القرار | ملاحظات |
|---|---|---|---|---|---|---|
| residential_lease_duration | seed (غير مُراجَع) | 2 (مصدر واحد فقط) | — | — | — | — |
| nonresidential_lease_duration | seed (غير مُراجَع) | 2 (مصدر واحد فقط) | — | — | — | — |
| vacate_on_term_end | seed (غير مُراجَع) | "2 مكرر" (مصدر واحد فقط) | — | — | — | تسمية المادة غير رسمية في المصدر |
| eviction_via_summary_judge | seed (غير مُراجَع) | غير مؤكد | — | — | — | لم يُعثر على رقم مادة في البحث |
| old_rent_annual_increase | seed (غير مُراجَع) | غير مؤكد | — | — | — | لم يُعثر على رقم مادة في البحث؛ يسري من سبتمبر 2026 |
| civil_code_general_reference | seed (غير مُراجَع) | غير مؤكد | — | — | — | إحالة عامة، ليست مادة محددة |

## قانون حماية المستهلك / Consumer Protection Law (`consumer_protection_2018_seed.json`)

| entry_id | الحالة الحالية | رقم المادة المذكور | تاريخ المراجعة | المحامي المراجع | القرار | ملاحظات |
|---|---|---|---|---|---|---|
| precontract_disclosure_ecommerce | seed (غير مُراجَع) | 36 (مصدر واحد فقط) | — | — | — | — |
| return_exchange_14_days | seed (غير مُراجَع) | غير مؤكد | — | — | — | لم يُعثر على رقم مادة في البحث |
| return_exchange_30_days_defective | seed (غير مُراجَع) | غير مؤكد | — | — | — | لم يُعثر على رقم مادة في البحث |
| distance_contract_withdrawal | seed (غير مُراجَع) | غير مؤكد | — | — | — | لم يُعثر على رقم مادة في البحث |
| durable_goods_warranty | seed (غير مُراجَع) | غير مؤكد | — | — | — | لم يُعثر على رقم مادة في البحث |
| return_exceptions | seed (غير مُراجَع) | غير مؤكد | — | — | — | لم يُعثر على رقم مادة في البحث |

## قاعدة الإصدار / Release gate

لا تُشغَّل هذه القاعدة المعرفية لمستخدمين حقيقيين حتى تكون جميع الصفوف أعلاه
`✅ مطابق` (عبر `scripts/mark_reviewed.py`)، أو حتى تُستبدل المُدخلات غير المؤكدة
بمُدخلات معتمدة عبر `/feedback/{id}/approve` (والتي تُعلَّم تلقائياً
`verified_by_lawyer=true`).

This knowledge base must not be served to real users until every row above is
`✅ matches` (via `scripts/mark_reviewed.py`), or the unconfirmed entries have been
replaced with lawyer-approved ones via `/feedback/{id}/approve` (which are
automatically tagged `verified_by_lawyer=true`).
