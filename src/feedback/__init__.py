"""Human-reviewed feedback curation — replaces src/core/learning_system.py.

The old "continuous learning system" logged interactions to a pickle file
and counted keyword patterns into JSON, then called that "learning". It
never updated any model or retrieval behavior in a way that would justify
the name. This module is honestly scoped: it is a review queue. A human
(a partner lawyer, or the operator) approves or rejects each submitted
correction; only approved corrections are ever added to the retrieval
index (via EgyptianLegalIndex.add_verified_chunk), and they are added
with verified_by_lawyer=True and a named reviewer — never silently.
"""

from src.feedback.curation_pipeline import CurationPipeline

__all__ = ["CurationPipeline"]
