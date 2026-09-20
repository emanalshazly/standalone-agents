# 🏛️ Egyptian Legal Agent — الوكيل القانوني المصري

<div dir="rtl">

## نظرة عامة

نظام قانوني عربي بمسارين منفصلين عمداً (راجع [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md#6-two-track-architecture-literacy-agent-vs-case-assistant)):

1. **وكيل التوعية القانونية** (`EgyptianLegalAgent`) — إجابة على أسئلة الأفراد
   والشركات الصغيرة حول **عقود العمل وحقوق العمال** بلغة بسيطة، مع **تحقق إلزامي
   من كل استشهاد قانوني** قبل عرض الإجابة، اعتماداً على قاعدة معرفية محلية فقط.
2. **وكيل المساعدة القضائية** (`CaseAssistantAgent`) — أداة **مسودات فقط** لبحث
   وتقييم أدلة وصياغة مستندات نزاع عمالي/مدني محدد، بحلقة بحث تكرارية (محلي + بحث
   حي على الإنترنت)، ومراجعة أدلة، وصياغة — كل ناتج منها مُعلَّم صراحة كمسودة
   أولية لمراجعة محامٍ مرخّص، وليست جاهزة للتقديم لأي جهة.

</div>

## Why this project pivoted

This repository used to contain six shallow generalist "domain agents"
(medical, legal, finance, education, e-commerce, customer service). It has
been rebuilt around a single, deep, real vertical instead. Two things drove
that:

1. **Market pattern.** The vertical-AI companies that actually won —
   [Harvey](https://sacra.com/c/harvey/) (legal, $11B valuation, $350M ARR),
   [Abridge](https://www.softx.ca/resources/healthcare-ai-compliance-guide-2026)
   (healthcare, $5.3B+) — did it by going deep in **one** regulated domain
   with real compliance infrastructure, not by being a broad generalist
   framework. Generic multi-agent frameworks (LangGraph, CrewAI, AutoGen)
   are mature and free; a hand-rolled competitor to them has no edge.
2. **An honest audit of this repo's own code** found that its "advanced AI"
   features were arithmetic dressed up as intelligence: `confidence` was
   `0.5 + 0.1*len(sources)`, "re-ranking" was a fixed weighted sum, and
   "continuous learning" was pickling interaction logs and counting
   keywords. None of it was wrong to build as a learning exercise, but none
   of it should be marketed as what it isn't.

So: one domain (Egyptian labor/contract literacy), one market (Egypt, where
legal AI is far less crowded than Saudi Arabia's — see
[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for the competitive research),
and a real architecture: **LangGraph** for orchestration, **LlamaIndex** +
a real cross-encoder reranker for retrieval, and a **citation verifier**
that can refuse to answer rather than emit an ungrounded claim.

## ⚠️ Scope and known limitations — read before using this for anything real

- **Not legal advice, from either track.** The literacy agent explains
  publicly available legal information in plain language. The case
  assistant drafts preliminary paperwork. Neither is a lawyer, neither
  represents you, and the case assistant **never files or submits
  anything** — see
  [PROJECT_OVERVIEW.md §6](PROJECT_OVERVIEW.md#6-two-track-architecture-literacy-agent-vs-case-assistant).
- **Explicitly out of scope for both tracks**: criminal law, litigation
  strategy, court filings, tax law. Queries about these are routed to
  human handoff, not answered or drafted.
- **The case-assistant track has not been reviewed by a lawyer at all.**
  It is an internal prototype — see
  [`docs/eval/case_drafting_audit.md`](docs/eval/case_drafting_audit.md).
  Do not point real users at `/case/draft` yet.
- **The seed knowledge base is NOT yet lawyer-verified.** Every entry in
  `src/knowledge/legal_eg/labor_law_2025_seed.json` was compiled by an AI
  research agent from secondary sources (law-firm client alerts about
  Egypt's Labor Law No. 14 of 2025), not from the primary Official Gazette
  text, and is explicitly flagged `verified_by_lawyer: false`. One entry
  (notice period) has a **known conflict** in the article number cited
  across secondary sources. See
  [`docs/eval/citation_audit.md`](docs/eval/citation_audit.md) — this is
  the non-negotiable manual sign-off step before real deployment.
- **Legal RAG hallucinates.** Even specialized legal RAG tools hallucinate
  citations 17–34% of the time (Stanford/Yale research), and 2026 saw
  six-figure U.S. court sanctions against lawyers who filed AI-fabricated
  citations. The citation-verification gate in this project exists
  specifically because retrieval alone does not solve this.
- **No rate limiting yet** on the API. Admin endpoints (feedback approval)
  require `LEGAL_AGENT_ADMIN_KEY`; the `/query` endpoint does not yet have
  abuse protection — do not expose it publicly without adding some.

## 🏗️ Architecture

```
User query
    │
    ▼
┌─────────────────┐   out of scope    ┌──────────┐
│ classify_intent  │──────────────────▶│ handoff  │──▶ END
└─────────────────┘                    └──────────┘
    │ in scope                              ▲
    ▼                                       │ no sources /
┌─────────────────┐   no chunks found       │ retries exhausted
│    retrieve      │────────────────────────┤
│ (LlamaIndex +    │                        │
│  cross-encoder)  │                        │
└─────────────────┘                        │
    │                                       │
    ▼                                       │
┌─────────────────┐                        │
│  draft_answer    │◀──── retry (≤2) ───┐   │
│  (cites [n])     │                    │   │
└─────────────────┘                    │   │
    │                                   │   │
    ▼                                   │   │
┌─────────────────┐  unsupported claim  │   │
│ verify_citations │────────────────────┘   │
│ (LLM-as-judge    │                        │
│  per claim)      │────────────────────────┘
└─────────────────┘  all supported
    │
    ▼
┌─────────────────┐
│ add_disclaimer   │──▶ END
└─────────────────┘
```

| Old (deleted)                     | New                                          | Why |
|---|---|---|
| `src/core/orchestrator.py` (dict lookup) | `src/graph/legal_graph.py` (LangGraph `StateGraph`) | Real branching/retry logic, not a lookup table |
| `src/core/rag_system.py` (heuristic rerank) | `src/rag/legal_index.py` (LlamaIndex + `BAAI/bge-reranker-v2-m3`) | Real cross-encoder, mandatory citation metadata |
| `src/core/learning_system.py` (pickle + keyword counts) | `src/feedback/curation_pipeline.py` (SQLite human review queue) | Honestly scoped — no "learning" claim |
| `_calculate_confidence()` heuristic | `src/verification/citation_verifier.py` (per-claim entailment check) | Checks the draft against the actual source, not against source *count* |

### Track 2 (case assistant) components — new, not a replacement of anything

| Component | Role |
|---|---|
| `src/tools/web_search.py` | Pluggable search provider (Tavily via `httpx`, or `NullSearchProvider` with no key) — every result tagged `trust_tier="web_unverified"` |
| `src/subagents/research_subagent.py` | ReAct-style loop: retrieve → judge sufficiency → refine query → retrieve again (bounded) |
| `src/subagents/evidence_review_subagent.py` | Gap analysis between the user's case facts and the research results — never predicts an outcome |
| `src/subagents/drafting_subagent.py` | Assembles the draft, reuses `citation_verifier`, enforces the DRAFT-ONLY header in code |
| `src/graph/case_drafting_graph.py` | Wires the three sub-agents into a `StateGraph`, separate from `legal_graph.py` on purpose — see [PROJECT_OVERVIEW.md §6](PROJECT_OVERVIEW.md#6-two-track-architecture-literacy-agent-vs-case-assistant) |

## 📦 Installation

```bash
git clone https://github.com/emanalshazly/standalone-agents.git
cd standalone-agents
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY or ANTHROPIC_API_KEY
```

## 🚀 Usage

### Track 1: legal literacy

```python
from src.agents.legal.legal_agent import EgyptianLegalAgent

agent = EgyptianLegalAgent()
answer = agent.query("هل يجوز لصاحب العمل تجديد فترة الاختبار؟")

print(answer.answer)
print("handoff_required:", answer.handoff_required)
print("lawyer_review_pending:", answer.lawyer_review_pending)  # currently always True — see Scope section above
print("citations:", answer.citations)
```

### Track 2: case assistant (research + evidence review + drafting)

⚠️ Prototype — not lawyer-reviewed. See Scope section above.

```python
from src.agents.case_assistant.drafting_agent import CaseAssistantAgent

case_agent = CaseAssistantAgent()  # optionally: legal_index=agent.legal_index to share the vector store
result = case_agent.prepare_draft(
    case_facts="صاحب العمل أنهى عقدي بدون إخطار مسبق بعد سنتين من العمل",
)

print(result.draft_text)          # always starts with a DRAFT-ONLY header
print(result.handoff_required)    # True if out of scope or research/drafting couldn't be verified
print(result.evidence_gaps)       # what's missing to strengthen the case
print(result.web_sources_consulted)  # unverified web sources, if TAVILY_API_KEY is set
```

Without `TAVILY_API_KEY` set, the research loop runs on the local knowledge
base only (`NullSearchProvider` — degrades gracefully, does not fabricate
web results).

### Run the API

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
# docs at http://localhost:8000/docs
```

```bash
curl -X POST "http://localhost:8000/case/draft" \
  -H "Content-Type: application/json" \
  -d '{
    "case_facts": "صاحب العمل أنهى عقدي بدون إخطار مسبق",
    "acknowledge_draft_only": true
  }'
```

## 🧪 Testing

```bash
# Pure-logic unit tests (no API key, no network needed)
pytest tests/ --ignore=tests/eval

# Retrieval-only eval (downloads the embedding model; still no LLM/API key)
python tests/eval/run_eval.py --mode retrieval

# Full eval incl. RAGAS faithfulness scoring (needs OPENAI_API_KEY)
python tests/eval/run_eval.py --mode full
```

A passing eval run is **necessary but not sufficient**. See
[`docs/eval/citation_audit.md`](docs/eval/citation_audit.md) for the manual
lawyer sign-off gate.

## 🤝 Feedback / correction workflow

```
POST /feedback/submit                     -> anyone can propose a correction
GET  /feedback/review-queue   (admin)     -> list pending corrections
POST /feedback/{id}/approve   (admin)     -> named human approves, embeds
                                              as verified_by_lawyer=true
POST /feedback/{id}/reject    (admin)     -> named human rejects
```

Admin routes require the `X-API-Key` header matching `LEGAL_AGENT_ADMIN_KEY`.

## 📄 License

MIT License — see [LICENSE](LICENSE).

## Further reading

- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) — the competitive research and
  strategic reasoning behind this pivot (Harvey/Abridge/Hippocratic AI
  benchmarks, Egypt vs. Saudi/UAE legal-AI market analysis, legal-AI
  hallucination sanctions).
- [docs/eval/citation_audit.md](docs/eval/citation_audit.md) — the manual
  verification log every seed knowledge-base entry needs before production
  use.
