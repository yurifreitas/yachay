"""The layers must not start contradicting each other more than they already do.

WHY A BASELINE AND NOT A ZERO. `tools/consistency.py` currently finds three contradictions
(docs/audit.md A14), and exactly one of them — CDKL5-deficiency disorder carrying
`ORPHA:3095`, which Orphanet calls *Atypical Rett syndrome* — is an unambiguous defect in an
**authored** layer. Fixing it means editing somebody's domain knowledge, which is the
author's call and not a test's, so it is recorded here rather than silently corrected.

Asserting zero would therefore fail on day one and be deleted by the first person it
annoyed. Asserting the baseline does the useful thing instead: **a new contradiction fails
the suite, and repairing a known one fails it too** — the second is deliberate, so that
fixing a defect forces the record of it to be updated rather than left to rot.

This is F3 from docs/audit.md, generalised. The first version of F3 asserted that two
readers of one XML file agree; that caught A11's class of defect for exactly one file. This
catches it for every claim any two layers make about the same disease.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARTEFACT = ROOT / "out" / "rare" / "consistency.json"

# The contradictions that existed when this test was written, as (disease, field) pairs.
# Each one is explained in docs/audit.md A14. Shrinking this set is progress and requires
# editing it; growing it without editing it is a regression.
KNOWN = {
    ("CDKL5-deficiency disorder", "orpha"),
    ("Cystic fibrosis", "prevalence"),
    ("Duchenne muscular dystrophy", "prevalence"),
}

requires_artefact = pytest.mark.skipif(
    not ARTEFACT.exists(),
    reason="run python tools/consistency.py (or tasks.py consistency) first",
)


def _load():
    return json.loads(ARTEFACT.read_text(encoding="utf-8"))


@requires_artefact
def test_no_new_contradictions_between_layers():
    found = {(c["disease"], c["field"]) for c in _load()["contradictions"]}
    new = found - KNOWN
    assert not new, (
        "layers have started contradicting each other in new places:\n  "
        + "\n  ".join(f"{d} — {f}" for d, f in sorted(new))
        + "\nEither fix the layer or, if the contradiction is intended and explained, "
          "add it to KNOWN here and to docs/audit.md A14."
    )


@requires_artefact
def test_known_contradictions_are_still_present_or_the_record_is_stale():
    """Fixing one of these should fail here, so the write-up cannot silently go stale."""
    found = {(c["disease"], c["field"]) for c in _load()["contradictions"]}
    gone = KNOWN - found
    assert not gone, (
        "these contradictions are recorded as known but no longer occur:\n  "
        + "\n  ".join(f"{d} — {f}" for d, f in sorted(gone))
        + "\nGood — now remove them from KNOWN and update docs/audit.md A14 and "
          "docs/references/rare-layers.md, so the documentation matches the code."
    )


@requires_artefact
def test_the_join_still_finds_the_diseases_it_is_supposed_to_compare():
    """A weak join produces silence, not a false alarm — and silence reads as agreement.

    The first version of `consistency.py` deleted punctuation instead of replacing it, so
    `CDKL5-deficiency disorder` and `CDKL5 deficiency disorder` never met and the identity
    conflict between them went unreported. This asserts the join is still doing its job: a
    healthy share of diseases must be visible in more than one layer, or the check has gone
    quiet without anyone noticing.
    """
    data = _load()
    multi = data["summary"]["diseasesInMoreThanOneLayer"]
    single = data["summary"]["diseasesInOnlyOneLayer"]
    assert multi >= 10, (
        f"only {multi} diseases are cross-referenced across layers ({single} appear in one "
        "layer only). The join has probably broken, and a broken join reports no "
        "contradictions at all."
    )
