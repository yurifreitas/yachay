"""The candidate pool must be able to reproduce the registered shortlist.

WHY THIS TEST EXISTS. The cancer section lets a reader move the three gates and re-filters a
wider `candidates` set in the browser. That makes the definition of a hit exist in two
places — Python and TypeScript — which is a drift risk accepted knowingly (see
`web/src/lib/cancerModel.ts`). This is the guard on the half that can be checked here.

It was written because the invariant had already been broken once, silently. Candidates were
collected in descending effect under a deliberately loose gate, and most of what that gate
admits fails only the Stage 0 dependency floor — so for Skin, 26 high-effect floor-failures
filled the 40-slot window and pushed the 15th registered hit outside it. The interface then
re-gated the truncated pool and drew **14 rows beside a sentence saying 15**. Nothing errored.

The failure mode is the one this repository keeps rediscovering: truncating before filtering
(audit A12, A29). The repair is a union, and this test is what stops it regressing into a cap
again.
"""

from __future__ import annotations

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "out"

SUBGROUP_FILES = [f"cancer_subgroups_{lv}.json" for lv in ("lineage", "disease", "subtype")]


def _load(name: str) -> dict:
    path = OUT / name
    if not path.exists():
        pytest.skip(f"{name} not present — run tools/cancer_subgroups.py")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", SUBGROUP_FILES)
def test_every_registered_hit_is_in_the_candidate_pool(name: str) -> None:
    data = _load(name)
    broken = []
    for row in data["results"]:
        pool = {c["gene"] for c in row.get("candidates", [])}
        missing = {h["gene"] for h in row["hits"]} - pool
        if missing:
            broken.append(f"{row['subgroup']}: {sorted(missing)}")
    assert not broken, (
        "candidate pool cannot reproduce the registered shortlist, so the interface will "
        "draw fewer rows than the analysis reported at the analysis's own thresholds:\n  "
        + "\n  ".join(broken))


@pytest.mark.parametrize("name", SUBGROUP_FILES)
def test_regating_at_the_registered_values_reproduces_the_hits(name: str) -> None:
    """The predicate, re-applied. This is the Python half of what the browser does.

    Compared as a SET and not as a list: the interface has no `--top` cap, so at the
    registered gates it may legitimately show more rows than `hits`, which Python truncates.
    What it must never do is show a gene `hits` does not contain, or miss one it does.
    """
    data = _load(name)
    reg = data["gates"]["registered"]
    for row in data["results"]:
        pool = row.get("candidates")
        if pool is None:
            continue
        regated = {c["gene"] for c in pool
                   if c["q"] <= reg["q"] and c["d"] >= reg["d"]
                   and c["meanInGroup"] >= reg["dependencyFloor"]}
        frozen = {h["gene"] for h in row["hits"]}
        assert frozen <= regated, (
            f"{row['subgroup']}: re-gating at the registered values drops "
            f"{sorted(frozen - regated)}, which the analysis published as hits")


def test_genotype_pool_reproduces_its_hits() -> None:
    data = _load("cancer_genotype.json")
    broken = []
    for row in data["results"]:
        pool = {c["gene"] for c in row.get("candidates", [])}
        missing = {h["gene"] for h in row["hits"]} - pool
        if missing:
            broken.append(f"{row['driver']}: {sorted(missing)}")
    assert not broken, "genotype candidate pool is missing registered hits:\n  " + \
        "\n  ".join(broken)


@pytest.mark.parametrize("name", SUBGROUP_FILES + ["cancer_genotype.json"])
def test_the_registered_gates_are_published_with_the_artefact(name: str) -> None:
    """The interface must not hardcode the thresholds it re-applies.

    If it did, moving a value in `manifests/thresholds.yaml` would leave the dashboard
    silently re-gating at the old one and calling the result registered.
    """
    data = _load(name)
    reg = data.get("gates", {}).get("registered")
    assert reg, f"{name} does not publish its registered gates"
    for key in ("q", "d", "dependencyFloor"):
        assert isinstance(reg.get(key), (int, float)), f"{name}: gates.registered.{key}"
