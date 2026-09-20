#!/usr/bin/env python3
"""
mark_reviewed.py - أداة سطر أوامر لتأكيد مُدخل seed كمُراجَع من محامٍ

For the "confirmed correct as written" case ONLY, per
docs/eval/citation_audit.md's runbook. If the content needs a CORRECTION
rather than a confirmation, use the existing feedback flow instead
(POST /feedback/submit -> POST /feedback/{id}/approve) — do not use this
script to sneak in different text under a "confirmed" label.

Usage:
    python scripts/mark_reviewed.py <entry_id> "<reviewer name>" <source_url> [<source_url> ...]

Example:
    python scripts/mark_reviewed.py probation_period "Eman Alshazly, Egyptian Bar #12345" \\
        "https://manshurat.org/node/12345"

This is intentionally a thin one-shot script, not an interactive tool: the
legal judgment call belongs to the human reviewer looking at the actual
Official Gazette text side-by-side with the seed JSON file (see
docs/eval/citation_audit.md) — this script only records that a decision
was made and by whom, then flips the underlying knowledge chunk to
verified_by_lawyer=True via EgyptianLegalIndex.mark_entry_verified().
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.legal_index import EgyptianLegalIndex


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 1

    entry_id = sys.argv[1]
    reviewer = sys.argv[2]
    source_urls = sys.argv[3:]

    print(f"Marking entry_id={entry_id!r} as verified_by_lawyer=True, reviewer={reviewer!r}")
    print(f"Sources recorded: {source_urls}")
    confirm = input("Type 'yes' to confirm this was actually reviewed against the "
                     "primary Official Gazette text (not a secondary source): ")
    if confirm.strip().lower() != "yes":
        print("Aborted — nothing changed.")
        return 1

    legal_index = EgyptianLegalIndex()
    updated_count = legal_index.mark_entry_verified(
        entry_id=entry_id, reviewer=reviewer, source_urls=source_urls
    )

    if updated_count == 0:
        print(f"No chunks found for entry_id={entry_id!r} — check the id and try again.")
        return 1

    print(f"Done: {updated_count} chunk(s) for entry_id={entry_id!r} now verified_by_lawyer=True.")
    print("Remember to also update the row in docs/eval/citation_audit.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
