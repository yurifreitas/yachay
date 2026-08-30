"""The HIV adapter's gates, offline.

Two things are worth a test here, and neither is the numbers. The numbers change when
Stanford publishes a new release; the GATES must not.

  1. **The positive control is named before the run.** ADR 0003 says a failed positive
     control blocks the shortlist, which only means anything if the control list cannot be
     edited to match the result. This asserts the list is a module constant, that it holds
     mutations the literature calls major, and — the part that matters — that it is NOT
     derived from the artefact.

  2. **Sign is normalised once, at the boundary.** Every stage in this library assumes larger
     is better. Fold-resistance already points that way and the loader takes a log; a future
     edit that flips it would invert the whole ranking silently.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def load_module():
    path = ROOT / "analyses" / "hiv_resistance.py"
    if not path.exists():
        pytest.skip("analyses/hiv_resistance.py not present")
    spec = importlib.util.spec_from_file_location("hiv_resistance", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_positive_controls_are_declared_in_the_module():
    """Not read from the artefact, not inferred from the data — written in the source."""
    mod = load_module()
    controls = mod.POSITIVE_CONTROLS
    assert set(controls) == {"PI", "NRTI", "NNRTI"}
    # The canonical ones, from the literature. If a future edit quietly drops these to make a
    # gate pass, this fails.
    assert "184V" in controls["NRTI"], "M184V is the canonical 3TC resistance mutation"
    assert "103N" in controls["NNRTI"], "K103N is the canonical NNRTI resistance mutation"
    assert "90M" in controls["PI"], "L90M is a canonical PI resistance mutation"


def test_the_control_list_is_not_derived_from_the_result():
    """The gate is only a gate if it cannot be fitted to the answer.

    Read as text rather than by import: the point is that no line of this file builds the
    control set from the artefact or from the scored mutations.
    """
    src = (ROOT / "analyses" / "hiv_resistance.py").read_text(encoding="utf-8")
    block = src.split("POSITIVE_CONTROLS")[1].split("}")[0]
    for forbidden in ("rows", "scored", "json.load", "top20", "read_text"):
        assert forbidden not in block, (
            f"the positive control list must be literal; found {forbidden!r} inside it")


def test_larger_is_better_is_established_once():
    """The loader is the only place that touches sign, and it takes a log of a fold-change."""
    src = (ROOT / "analyses" / "hiv_resistance.py").read_text(encoding="utf-8")
    loader = src.split("def load_panel")[1].split("def ")[0]
    assert "math.log10" in loader
    assert "-f" not in loader and "* -1" not in loader, "sign must not be flipped here"


def test_min_carriers_is_enforced_before_scoring():
    """A median over one assay is not an estimate, and the floor must be applied to the
    CARRIER count and not only to the per-drug count."""
    mod = load_module()
    assert mod.MIN_CARRIERS >= 3
    src = (ROOT / "analyses" / "hiv_resistance.py").read_text(encoding="utf-8")
    scorer = src.split("def score_mutations")[1].split("def ")[0]
    assert "len(idx) < MIN_CARRIERS" in scorer


@pytest.mark.skipif(not (ROOT / "out" / "hiv_resistance.json").exists(),
                    reason="the artefact has not been produced in this checkout")
def test_the_artefact_reports_whether_each_gate_passed():
    """A run that produced no verdict is a run nobody can act on."""
    payload = json.loads((ROOT / "out" / "hiv_resistance.json").read_text(encoding="utf-8"))
    assert payload["fit_test"]["selection_operator"] is True
    for name, panel in payload["panels"].items():
        assert "positive_control" in panel, f"{name} has no gate"
        assert isinstance(panel["positive_control"]["passes"], bool)
        assert "passengers_in_top20" in panel, (
            f"{name} must report what is in the top twenty that is NOT a known resistance "
            "mutation — that is the dependence this adapter predicts")
