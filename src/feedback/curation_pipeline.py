"""
Feedback Curation Pipeline - قائمة مراجعة التصحيحات

Honest replacement for src/core/learning_system.py's fake "continuous
learning". This is a human-in-the-loop review queue backed by SQLite:

    user/lawyer submits a correction
        -> stored as status="pending"
        -> a named human reviewer approves or rejects it
        -> only on approval does the correction get embedded into the
           retrieval index, tagged verified_by_lawyer=True

No automatic retraining, no similarity-based "pattern learning", no claim
that the agent has learned anything. The API layer must not describe this
as "learning insights" — see src/api/main.py's /feedback/* routes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from src.rag.legal_index import EgyptianLegalIndex

logger = logging.getLogger(__name__)

Base = declarative_base()


class ReviewItem(Base):
    __tablename__ = "review_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, nullable=False)
    draft_answer = Column(Text, nullable=False)
    user_correction = Column(Text, nullable=False)
    language = Column(String(8), default="ar")
    status = Column(String(16), default="pending")  # pending|approved|rejected
    reviewer = Column(String(128), nullable=True)
    review_notes = Column(Text, nullable=True)
    law_name_ar = Column(String(256), nullable=True)
    law_name_en = Column(String(256), nullable=True)
    article_number = Column(String(64), nullable=True)
    source_urls_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime, nullable=True)


@dataclass
class ReviewItemView:
    id: int
    query: str
    draft_answer: str
    user_correction: str
    status: str
    reviewer: Optional[str]
    created_at: datetime


class CurationPipeline:
    def __init__(self, db_path: str = "./src/knowledge/feedback/review_queue.db"):
        self._engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine)

    def submit_correction(
        self,
        query: str,
        draft_answer: str,
        user_correction: str,
        language: str = "ar",
    ) -> int:
        """A user or lawyer flags that a draft answer was wrong/incomplete
        and proposes a correction. Status starts at 'pending' — nothing is
        used until a named human reviews it."""
        with self._Session() as session:
            item = ReviewItem(
                query=query,
                draft_answer=draft_answer,
                user_correction=user_correction,
                language=language,
                status="pending",
            )
            session.add(item)
            session.commit()
            logger.info("Submitted correction id=%s for review", item.id)
            return item.id

    def list_pending(self) -> list[ReviewItemView]:
        with self._Session() as session:
            items = (
                session.query(ReviewItem)
                .filter(ReviewItem.status == "pending")
                .order_by(ReviewItem.created_at.asc())
                .all()
            )
            return [
                ReviewItemView(
                    id=i.id,
                    query=i.query,
                    draft_answer=i.draft_answer,
                    user_correction=i.user_correction,
                    status=i.status,
                    reviewer=i.reviewer,
                    created_at=i.created_at,
                )
                for i in items
            ]

    def approve(
        self,
        review_id: int,
        reviewer: str,
        law_name_ar: str,
        law_name_en: str,
        article_number: str,
        source_urls: list[str],
        legal_index: Optional[EgyptianLegalIndex] = None,
    ) -> None:
        """A named human approves a correction. If `legal_index` is given,
        the approved text is immediately embedded as a verified_by_lawyer=True
        chunk — this is the ONLY code path that ever sets that flag to True."""
        import json as _json

        with self._Session() as session:
            item = session.get(ReviewItem, review_id)
            if item is None:
                raise ValueError(f"No review item with id={review_id}")

            item.status = "approved"
            item.reviewer = reviewer
            item.law_name_ar = law_name_ar
            item.law_name_en = law_name_en
            item.article_number = article_number
            item.source_urls_json = _json.dumps(source_urls)
            item.reviewed_at = datetime.now(timezone.utc)
            session.commit()

            if legal_index is not None:
                legal_index.add_verified_chunk(
                    entry_id=f"feedback_{item.id}",
                    text=item.user_correction,
                    language=item.language,
                    law_name_ar=law_name_ar,
                    law_name_en=law_name_en,
                    article_number=article_number,
                    source_urls=source_urls,
                    reviewer=reviewer,
                )
            logger.info("Approved correction id=%s by reviewer=%s", review_id, reviewer)

    def reject(self, review_id: int, reviewer: str, notes: str = "") -> None:
        with self._Session() as session:
            item = session.get(ReviewItem, review_id)
            if item is None:
                raise ValueError(f"No review item with id={review_id}")
            item.status = "rejected"
            item.reviewer = reviewer
            item.review_notes = notes
            item.reviewed_at = datetime.now(timezone.utc)
            session.commit()
            logger.info("Rejected correction id=%s by reviewer=%s", review_id, reviewer)
