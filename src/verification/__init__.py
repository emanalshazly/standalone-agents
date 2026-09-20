"""Citation verification — the safety-critical piece of this pivot.

See src/verification/citation_verifier.py for why this exists: even
specialized legal RAG tools hallucinate citations 17-34% of the time
(Stanford/Yale study), and Egyptian/US courts have sanctioned lawyers
six figures for AI-fabricated citations in 2026. Retrieval quality alone
does not prevent this — the model can still misstate what a retrieved
source says. This module checks the DRAFT against the SOURCE, per claim.
"""

from src.verification.citation_verifier import (
    ClaimVerdict,
    VerificationResult,
    verify_draft,
)

__all__ = ["ClaimVerdict", "VerificationResult", "verify_draft"]
