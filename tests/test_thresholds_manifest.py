r"""The threshold manifest must describe the code, and must not be quietly edited.

TRANSFERRED FROM `F:\CODE\climate`, whose `manifests/feature_blocks.yaml` is frozen with a
date and a `target_contact` flag, and whose rule is unambiguous: *"Alteração motivada por
resultado observado no alvo INVALIDA o experimento."* This repository had the habit — ADR
0003 and 0004 both record thresholds fixed before the work — and no mechanism.

WHAT THESE TESTS PROTECT. Not the values: a threshold is allowed to change. What must not
happen is a value changing while the manifest still claims it was pre-registered, because
that converts an honest label into a false one — which is worse than no label, since it
carries the authority of the practice without the constraint.
"""

from __future__ import annotations

import pathlib
import re

import pytest

yaml = pytest.importorskip("yaml")

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifests" / "thresholds.yaml"


def manifest() -> dict:
    if not MANIFEST.exists():
        pytest.skip("manifests/thresholds.yaml not present")
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def test_every_declared_threshold_matches_the_source():
    """The manifest is a claim about the code. This is the claim being checked.

    A manifest that drifts from the module it describes is documentation theatre — the same
    failure `verify_claims.py` exists to catch for prose numbers.
    """
    mismatches = []
    for row in manifest()["thresholds"]:
        module = row["module"]
        path = (ROOT / "src" / (module.replace(".", "/") + ".py")
                if module.startswith("sieve.") else ROOT / module)
        if not path.exists():
            mismatches.append(f"{row['id']}: {module} does not exist")
            continue
        text = path.read_text(encoding="utf-8")
        # Two kinds of threshold literal. Numeric is the original case; a CATEGORICAL
        # threshold - `TRANSLATION_STATUS = "OFFICIAL"`, the status a translation must carry
        # to count as delivered - is still a threshold, and reporting it as "not defined"
        # would have pushed it out of the manifest rather than into it. Both are matched
        # exactly; neither branch is looser than the other.
        m = re.search(rf"^{re.escape(row['id'])}\s*=\s*([0-9.]+|\"[^\"]*\"|'[^']*')",
                      text, re.M)
        if not m:
            mismatches.append(f"{row['id']}: not defined in {module}")
            continue
        literal = m.group(1)
        if literal[0] in "\"'":
            if literal[1:-1] != str(row["value"]):
                mismatches.append(
                    f"{row['id']}: manifest says {row['value']!r}, {module} says {literal}")
        elif abs(float(literal) - float(row["value"])) > 1e-12:
            mismatches.append(
                f"{row['id']}: manifest says {row['value']}, {module} says {literal}")
    assert not mismatches, "\n  ".join(["threshold manifest disagrees with the code:"]
                                       + mismatches)


def test_a_pre_registered_threshold_declares_no_target_contact():
    """The two fields cannot contradict each other. If the data was seen, it is not
    pre-registered, whatever anyone wishes."""
    for row in manifest()["thresholds"]:
        if row["pre_registered"]:
            assert not row["target_contact"], (
                f"{row['id']} claims pre-registration and also target contact. "
                f"Pick the true one."
            )


def test_every_threshold_states_a_reason_and_its_kind():
    for row in manifest()["thresholds"]:
        assert row.get("justification") in ("mechanistic", "empirical", "conventional"), (
            f"{row['id']}: justification must be 'mechanistic' (survives a change of "
            f"dataset), 'empirical' (does not), or 'conventional' (fixed by fiat or an "
            f"external convention, chosen blind)")
        assert len(row.get("reason", "")) > 40, f"{row['id']}: needs a real reason"
        if row["justification"] == "empirical":
            assert not row["pre_registered"], (
                f"{row['id']}: a threshold read off this data cannot be pre-registered")


def test_no_seeded_or_hardcoded_gate_escapes_the_manifest():
    """The guard on the guard: a new module constant that looks like a threshold must be
    registered or the manifest slowly stops describing the project."""
    declared = {r["id"] for r in manifest()["thresholds"]}
    # Screaming-snake module constants assigned a bare number, in the stages that gate.
    unregistered = []
    for rel in ("src/sieve/stages/target.py", "src/sieve/stages/power.py"):
        p = ROOT / rel
        if not p.exists():
            continue
        for name, _val in re.findall(r"^([A-Z][A-Z0-9_]{3,})\s*=\s*([0-9.]+)\s*$",
                                     p.read_text(encoding="utf-8"), re.M):
            if name in declared or name.startswith("_"):
                continue
            unregistered.append(f"{rel}::{name}")
    assert not unregistered, (
        "these look like gates and are not in manifests/thresholds.yaml: "
        + ", ".join(unregistered) + " — register them, with target_contact stated honestly."
    )
