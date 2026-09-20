"""
FastAPI Application - Egyptian Legal-Literacy Agent API

Rewritten for the single-domain pivot. Two honesty fixes versus the old
multi-agent API (src/api/main.py, pre-pivot):

1. The old API had zero authentication and `allow_origins=["*"]` with
   `allow_credentials=True` (an open door, not a hardened default). Here,
   admin endpoints that can promote content into the legal knowledge base
   (feedback approve/reject) require an API key. CORS defaults to
   localhost only and is configurable via CORS_ORIGINS.
2. There is no `/agent/{name}/learning-insights` endpoint anymore — the
   old "learning system" it exposed was pickle-logged keyword counts, not
   learning. The equivalent honest endpoint is `/feedback/review-queue`,
   a human review queue (see src/feedback/curation_pipeline.py).

Known gap, called out rather than hidden: rate limiting is not yet
implemented (no Redis/slowapi wiring). Do not deploy this publicly without
adding it — see PROJECT_OVERVIEW.md "Known gaps".
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agents.legal.legal_agent import EgyptianLegalAgent
from src.feedback.curation_pipeline import CurationPipeline

app = FastAPI(
    title="Egyptian Legal-Literacy Agent API",
    description=(
        "Citation-verified, Arabic-first legal Q&A for Egyptian individuals "
        "and small businesses. Not legal advice; not a substitute for a "
        "licensed lawyer."
    ),
    version="2.0.0",
)

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_agent: EgyptianLegalAgent | None = None
_curation: CurationPipeline | None = None


def _verify_admin_key(x_api_key: str = Header(default="")) -> None:
    expected = os.getenv("LEGAL_AGENT_ADMIN_KEY")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Admin endpoints disabled: LEGAL_AGENT_ADMIN_KEY is not configured.",
        )
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


@app.on_event("startup")
async def startup_event() -> None:
    global _agent, _curation
    _agent = EgyptianLegalAgent()
    _curation = CurationPipeline()


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    answer: str
    language: str
    handoff_required: bool
    lawyer_review_pending: bool
    citations: list[str]
    timestamp: str


class SubmitCorrectionRequest(BaseModel):
    query: str
    draft_answer: str
    user_correction: str
    language: str = "ar"


class ApproveCorrectionRequest(BaseModel):
    reviewer: str
    law_name_ar: str
    law_name_en: str
    article_number: str
    source_urls: list[str]


class RejectCorrectionRequest(BaseModel):
    reviewer: str
    notes: str = ""


@app.get("/")
async def root():
    return {
        "name": "Egyptian Legal-Literacy Agent",
        "version": "2.0.0",
        "scope": "Egyptian labor/contract literacy for individuals & small businesses",
        "not_in_scope": ["criminal_law", "litigation_strategy", "court_filings", "tax_law"],
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized yet")

    result = _agent.query(request.query)
    return QueryResponse(
        answer=result.answer,
        language=result.language,
        handoff_required=result.handoff_required,
        lawyer_review_pending=result.lawyer_review_pending,
        citations=result.citations,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/feedback/submit")
async def submit_feedback(request: SubmitCorrectionRequest):
    """Anyone can propose a correction. Nothing happens with it until a
    named human reviewer approves it via /feedback/{id}/approve."""
    if _curation is None:
        raise HTTPException(status_code=503, detail="Curation pipeline not initialized yet")

    review_id = _curation.submit_correction(
        query=request.query,
        draft_answer=request.draft_answer,
        user_correction=request.user_correction,
        language=request.language,
    )
    return {"status": "queued_for_review", "review_id": review_id}


@app.get("/feedback/review-queue", dependencies=[Depends(_verify_admin_key)])
async def review_queue():
    """Admin-only: list pending human-review items. Requires X-API-Key."""
    if _curation is None:
        raise HTTPException(status_code=503, detail="Curation pipeline not initialized yet")
    return {"pending": [item.__dict__ for item in _curation.list_pending()]}


@app.post("/feedback/{review_id}/approve", dependencies=[Depends(_verify_admin_key)])
async def approve_feedback(review_id: int, request: ApproveCorrectionRequest):
    """Admin-only: a named human approves a correction, which is then
    embedded into the retrieval index as verified_by_lawyer=True."""
    if _curation is None or _agent is None:
        raise HTTPException(status_code=503, detail="Service not initialized yet")

    _curation.approve(
        review_id=review_id,
        reviewer=request.reviewer,
        law_name_ar=request.law_name_ar,
        law_name_en=request.law_name_en,
        article_number=request.article_number,
        source_urls=request.source_urls,
        legal_index=_agent.legal_index,
    )
    return {"status": "approved", "review_id": review_id, "reviewer": request.reviewer}


@app.post("/feedback/{review_id}/reject", dependencies=[Depends(_verify_admin_key)])
async def reject_feedback(review_id: int, request: RejectCorrectionRequest):
    if _curation is None:
        raise HTTPException(status_code=503, detail="Curation pipeline not initialized yet")

    _curation.reject(review_id=review_id, reviewer=request.reviewer, notes=request.notes)
    return {"status": "rejected", "review_id": review_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
