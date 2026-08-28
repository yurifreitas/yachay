"""The prose must not drift from the artefacts that produced it.

This is **F1** of `docs/audit.md`, proposed in the first sweep and built in the thirteenth.
It exists because the same failure has now happened twice and both times a person caught it:

  * **A1** — `CITATION.cff` advertised a `-4.09` anomaly that had been fixed, in the header
    block a citing author copies.
  * **A11** — three documents read `770` ultra-rare diseases while the artefact said
    `4,586`, because one regeneration was not propagated.

A person reading carefully is not a control. This is.

WHAT IT DOES NOT COVER, said plainly so nobody mistakes a green suite for a guarantee: it
checks the numbers in `tools/verify_claims.py`'s registry, and nothing else. A figure nobody
registered can still drift. Registering a claim is part of publishing it.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_claims", ROOT / "tools" / "verify_claims.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V = _verifier()

# A claim whose artefact is not on disk cannot be checked, and skipping is correct: a fresh
# clone has no `out/`. What must never happen is a claim being skipped because the artefact
# is missing when it should be there, so the skip reason names the tool that writes it.
CLAIMS = [c for c in V.CLAIMS]


@pytest.mark.parametrize("claim", CLAIMS, ids=[c[0] for c in CLAIMS])
def test_every_document_still_quotes_what_the_artefact_says(claim):
    name, artefact, path, formatter, docs = claim
    p = ROOT / artefact
    if not p.exists():
        pytest.skip(f"{artefact} not generated; run the pipeline")

    data = json.loads(p.read_text(encoding="utf-8"))
    value, err = V.dig(data, path)
    assert not err, (
        f"{name}: {artefact} no longer has {'.'.join(path)}. A renamed key is drift too — "
        f"the prose still quotes a number the artefact stopped producing."
    )

    acceptable = formatter(value)
    for doc in docs:
        d = ROOT / doc
        assert d.exists(), f"{name} cites {doc}, which does not exist"
        text = d.read_text(encoding="utf-8")
        assert any(w in text for w in acceptable), (
            f"{name}: {artefact} says {acceptable[0]!r} and {doc} contains no rendering "
            f"of it.\nEither regenerate the document or, if the number legitimately "
            f"changed, update the prose and say so in place — the way "
            f"rare-disease-scale.md §2 records the 770 -> 4,586 correction rather than "
            f"silently restating it."
        )


def test_the_registry_covers_the_layers_that_carry_headline_numbers():
    """A guard on the guard: the registry must not quietly stop covering a layer.

    The failure this prevents is subtle — deleting a row makes the suite greener, and a
    checker that can be silenced by deleting its input is not a control either.
    """
    covered = {c[1] for c in V.CLAIMS}
    must_cover = {
        "out/rare/atlas.json",
        "out/rare/evidence_atlas.json",
        "out/rare/ancestry_geography.json",
        "out/rare/patient_frequencies.json",
        "out/rare/patient_variants.json",
        "out/rare/clinvar_evidence.json",
        "out/rare/genotype_phenotype.json",
        "out/rare/consistency.json",
    }
    missing = must_cover - covered
    assert not missing, (
        "these artefacts carry headline numbers and no claim registers them: "
        + ", ".join(sorted(missing))
    )


def test_every_registered_document_exists():
    for name, _artefact, _path, _fmt, docs in V.CLAIMS:
        for doc in docs:
            assert (ROOT / doc).exists(), f"{name} cites a document that does not exist: {doc}"
