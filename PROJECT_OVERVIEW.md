# Project Overview — Why This Pivot, and the Research Behind It

This document is the record of the analysis that turned a six-domain
generalist agent demo into a single-domain Egyptian legal-literacy agent.
It exists so the reasoning isn't lost — the next person touching this repo
(including a future version of whoever is reading this) should be able to
tell *why* the scope is this narrow, not just that it is.

## 1. What was here before, and what an actual code audit found

The original repo had six "domain agents" (medical, legal, finance,
education, e-commerce, customer service), each inheriting from a shared
`BaseAgent`, backed by a custom RAG system and a custom "continuous
learning system." A line-by-line audit of that code found the "advanced AI"
framing didn't match the implementation:

- `confidence` in the old `base_agent.py` was `0.5 + min(0.1*len(sources), 0.3) + (0.1 if len(response) > 100 else 0)` — an arithmetic function of source *count* and response *length*, unrelated to whether the content was correct.
- RAG "re-ranking" was `relevance*0.7 + recency*0.2 + source_boost*0.1` — fixed weights, no cross-encoder.
- The "continuous learning system" logged interactions to a `pickle` file and counted keyword occurrences into JSON. It never updated a model, never used embedding similarity, and had no feedback loop that changed future behavior in any measurable way.
- The orchestrator's "multi-agent collaboration strategies" (parallel/sequential/hierarchical/consensus) resolved, in the routing case that actually mattered, to a plain `dict` lookup.
- The legal agent had exactly one hardcoded knowledge entry. Three trivial unit tests existed in the whole repo. The API had no authentication and wide-open CORS.

None of this made the old code *useless* — it was a reasonable scaffold —
but none of it justified words like "revolutionary continuous learning" or
"advanced RAG," and continuing to build on six shallow domains would have
meant competing with mature, free, open-source frameworks (LangGraph,
CrewAI, AutoGen, LlamaIndex, Haystack) using a weaker, custom version of
what they already do.

## 2. Why one vertical, not six

The AI companies that reached real valuations by 2026 did it by owning one
regulated domain deeply, not by being broad:

| Company | Domain | 2026 valuation / traction |
|---|---|---|
| [Harvey](https://sacra.com/c/harvey/) | Legal | $11B (Mar 2026 round), $350M ARR, 1,500+ customers, 50% of Am Law 100 |
| [Abridge](https://www.softx.ca/resources/healthcare-ai-compliance-guide-2026) | Healthcare (ambient clinical) | $5.3B+, 150+ health systems, $100M+ ARR |
| Hippocratic AI | Healthcare | $3.5B after $404M raised |

Generic multi-agent frameworks, by contrast, are a crowded, mature, mostly
free lane: LangGraph, CrewAI, and AutoGen (now folded into Microsoft's
Agent Framework) all have large ecosystems and no obvious opening for a
new, smaller, custom framework to win on breadth.

**Decision: pick one vertical and go deep.** Legal was chosen (see below)
over medical (higher compliance/liability ceiling — FDA-adjacent
considerations, higher stakes) and finance (crowded with incumbent banks
and fintechs already running AI in MENA).

## 3. Why Egypt, not Saudi Arabia or the UAE

Market research (Sept 2026) found the Arabic legal-AI space is not empty —
it's just unevenly distributed:

- **Saudi Arabia**: already has multiple funded players — Adel (500K
  downloads, 70K Saudi legal documents, SAR 149–199/month), Clauze.AI
  (enterprise), Shwra, Laika, Malakah, and HAQQ (raised $3M, the largest
  disclosed MENA-native legal-AI round as of early 2026).
- **UAE**: Lexzur (practice management + Arabic contract tooling), Qanooni
  ($2M pre-seed), Clara (company formation automation).
- **Egypt**: comparatively undeveloped — the only entrants found were
  Elmetr (a lawyer marketplace, not an AI research/drafting tool) and
  Waseya (a narrow inheritance/will tool). No Egyptian competitor doing
  AI-assisted contract/rights explanation for consumers or SMEs was found.

**Decision: target Egypt**, and target **individuals and small businesses**
who need to understand a contract or know their rights in plain language —
not the BigLaw case-research segment Harvey, Clauze.AI, and Adel already
serve. This is a genuinely different buyer and a genuinely different
product shape (a "know your rights" explainer, not a research copilot).

## 4. The hallucination problem, and why it drove the architecture

This is the risk that most directly shaped the technical rebuild:

- Stanford/Yale research found even **specialized legal RAG tools**
  hallucinate citations **17–34% of the time** — retrieval grounding alone
  does not solve this, because a model can retrieve the right source and
  still misstate what it says.
- In 2026, U.S. courts issued six-figure sanctions against lawyers who
  filed AI-fabricated citations — a $110,000 combined fine in one Oregon
  case, $15,000+ punitive damages plus full appellate fees in a Sixth
  Circuit case, plus bar referrals in every state where the sanctioned
  lawyers were licensed.
- A public tracker (Damien Charlotin's database) recorded roughly 1,490
  court decisions worldwide where a party relied on AI-hallucinated legal
  material, as of mid-2026.

**This is why `src/verification/citation_verifier.py` exists as a hard
gate, not a nice-to-have**: every factual sentence in a draft answer must
cite a specific retrieved chunk by number, and an LLM-as-judge checks each
cited (claim, source) pair for entailment. Claims that fail, or have no
citation at all, cause the graph to retry the draft (bounded, ≤2 attempts)
or fall back to an explicit "cannot answer confidently, consult a lawyer"
handoff — never a silently-emitted unverified claim.

Even so, this pipeline has not eliminated the risk, only architected
against the parts of it that are architecturally addressable. The seed
knowledge base itself was compiled by an AI research agent from secondary
sources, not the primary Official Gazette text, and is explicitly marked
`verified_by_lawyer: false` pending human review — see
[`docs/eval/citation_audit.md`](docs/eval/citation_audit.md). One entry
(the notice-period rule) has a documented conflict in the article number
across the secondary sources consulted; this is left visible in the data
and in the generated citation label rather than resolved by guessing.

## 5. What "rebuilding on proven tools" means concretely

| Layer | Old | New |
|---|---|---|
| Orchestration | `src/core/orchestrator.py`, dict-lookup "routing" | `src/graph/legal_graph.py`, a LangGraph `StateGraph` with real conditional edges and bounded retries |
| Retrieval | `src/core/rag_system.py`, ChromaDB + heuristic rerank | `src/rag/legal_index.py`, LlamaIndex + `BAAI/bge-reranker-v2-m3` (real multilingual cross-encoder) |
| Verification | `_calculate_confidence()` heuristic | `src/verification/citation_verifier.py`, per-claim LLM-as-judge entailment check against retrieved source text |
| Feedback | `src/core/learning_system.py`, pickle + keyword counts | `src/feedback/curation_pipeline.py`, SQLite human-review queue; only human-approved content is ever marked `verified_by_lawyer=True` |
| Evaluation | none | `tests/eval/golden_qa.jsonl` + `tests/eval/run_eval.py` (retrieval-recall checks with no API key required, plus RAGAS faithfulness scoring when one is available) |

## 6. What's still a gap (stated plainly, not buried)

- No rate limiting on the public API.
- No Langfuse tracing wired in yet (it's in `requirements.txt` but not yet
  called from the graph nodes) — tracing every node's cost/latency/verdict
  is the natural next step once this runs against real traffic.
- The knowledge base covers seven labor-law topics. It does not cover
  rental/lease or consumer contracts yet, despite those being in the
  declared in-scope topic list in `config/config.example.yaml` — scope was
  declared ahead of content on purpose (see `docs/eval/citation_audit.md`
  gate: content should not outrun verification).
- No lawyer has reviewed the seed knowledge base yet. This is the single
  most important open item before any real user sees this agent's answers.
