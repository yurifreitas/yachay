"""Running a stage twice must produce the same bytes.

TRANSFERRED FROM `F:\\CODE\\adia`, which submits to a platform that re-executes 10 % of the
data and compares with a tolerance of **1e-8**. Its architecture note states the constraint
as a hard one — *"infer() deve ser 100 % determinístico — sem np.random, sem dropout, sem
MCMC, sem wall-clock"* — and that framing is stronger than anything here.

WHY THIS REPOSITORY NEEDED IT AND DID NOT HAVE IT. `docs/methodology.md` lists **Stage 9,
Repro**, whose stated purpose is preventing *"an artifact nobody, including you, can
regenerate"*. Twenty-eight pipeline stages, several seeded, and **nothing checked that a
rerun produces the same output.** A seed in the source is an intention; this is the
observation.

The stakes are concrete. `tools/intervals.py` and `tools/patient_frequencies.py` publish
bootstrap intervals from a seeded generator, and those intervals are now quoted in four
documents and guarded by `test_claims_match_artefacts.py`. If the resampling were
non-deterministic, that guard would fail intermittently and the published interval would be
one draw among many rather than a reproducible number.

WHAT IS AND IS NOT TESTED. Only stages that are cheap and read fixed inputs. The ones that
query a network (`dossier.py`) or measure wall-clock (`interactome_sparse.py`, which times
SpMV) are excluded **by name and with the reason**, because a determinism test that silently
skips the hard cases is worse than none.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import runpy
import shutil
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Stage tool -> the artefact it writes. Chosen for being fast and input-stable; the whole
# point is that this runs in a normal test suite rather than in a nightly job.
DETERMINISTIC = [
    ("tools/intervals.py", "out/rare/intervals.json"),
    ("tools/consistency.py", "out/rare/consistency.json"),
    ("tools/lexicon_check.py", "out/rare/lexicon_check.json"),
    ("tools/ancestry_geography.py", "out/rare/ancestry_geography.json"),
    # Added because the guard below found it unaccounted for on its first run. It resamples
    # the null to build the figure series, and BOTH the manuscript and the explorer read
    # those series — so a non-deterministic figure would let the paper and the dashboard
    # disagree with the analysis they claim to render.
    ("tools/figure_data.py", "out/figures/depmap.json"),
    # Also found by the guard, on the day it was written. It seriates 3,335 genes three ways
    # and a spectral ordering is a sign-ambiguous eigenvector: ARPACK can return -v as
    # happily as v, which reverses the ordering and every row of the matrix drawn from it.
    # If that ever becomes non-deterministic the figure flips between reloads and the caption
    # keeps claiming the same structure, so this is the exact tool the check exists for.
    ("tools/network_layout.py", "web/public/data/network_layout.json"),
    # The guard found this one too, on the day it was written. It draws 400 annotation-matched
    # null sets per community and the result decides what every block on the matrix is CALLED,
    # so a name that moved between runs would be the most quotable thing on the page and the
    # least reliable.
    ("tools/community_identity.py", "out/rare/community_identity.json"),
    # Runs three partitioners and an assignment solve. `linear_sum_assignment` is exact, but
    # an assignment problem can have several optima of equal cost and which one comes back is
    # an implementation detail — so the pairing that decides which ribbons count as agreement
    # is exactly the kind of thing that drifts silently.
    ("tools/partition_flow.py", "out/rare/partition_flow.json"),
]

# Excluded, by name and with the reason. A determinism suite that quietly omits the awkward
# cases certifies nothing.
NOT_TESTED = {
    "tools/dossier.py": "queries ClinicalTrials.gov; the cache makes it reproducible but "
                        "the first run is not, and a test must not depend on which it is",
    "tools/interactome_sparse.py": "times SpMV in wall-clock, which is non-deterministic by "
                                   "design — the timing is the measurement",
    "tools/interactome_string.py": "same, and it runs Louvain over 237k edges: too slow for "
                                   "a unit suite",
    "tools/clinvar_evidence.py": "reads 442 MB; correct but far too slow here",
    "tools/patient_frequencies.py": "4,000-resample bootstrap over 10,377 packets; covered "
                                    "indirectly, because intervals.py reads its output",
    "tools/ecosystem.py": "imports whatever is installed and greps the tree — it measures "
                          "the machine, so it is *supposed* to change",
    "tools/pipeline_state.py": "reports freshness, which any other stage running changes",
    "tools/twin_propagation.py": "seeded and deterministic by construction, but it reads an "
                                 "83 MB gzip and runs 200 degree-matched propagations per "
                                 "disease over a 16,201-node graph. Minutes, not seconds — "
                                 "excluded for runtime, not because it is unverified. This "
                                 "guard caught it the day it was written, which is the "
                                 "behaviour that justifies the guard.",
    "tools/gene_embedding.py": "four UMAP fits over 8,890 genes plus HDBSCAN on both the "
                               "embedding and the raw features - minutes, not seconds. Its "
                               "determinism is not assumed either: the artefact reports "
                               "neighbour agreement BETWEEN seeds as a published measurement, "
                               "so a run that stopped being reproducible would change the "
                               "number the panel is about rather than hiding.",
    "tools/community_stability.py": "runs three clustering algorithms twelve times each, a "
                                    "seven-point resolution sweep and twelve degree-preserving "
                                    "rewirings over a 5,524-node graph — 161 seconds, far too "
                                    "slow for a unit suite. Its determinism is covered "
                                    "directly instead by test_community_stability.py, which "
                                    "runs the same partitioners on a small synthetic graph and "
                                    "checks that a seed fixes the answer. Excluded for "
                                    "runtime, not for lack of a test.",
}


def digest(path: pathlib.Path) -> str:
    """Hash the artefact's CONTENT, ignoring the `generated` timestamp some tools write.

    A tool that stamps the date is not non-deterministic in any way that matters, and
    failing it for that would teach people to delete the test. Everything else must match
    byte for byte.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = {k: v for k, v in data.items() if k not in ("generated", "timestamp")}
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@pytest.mark.parametrize("tool,artefact", DETERMINISTIC, ids=[t for t, _ in DETERMINISTIC])
def test_rerunning_a_stage_reproduces_it_exactly(tool, artefact, tmp_path):
    tool_path = ROOT / tool
    art_path = ROOT / artefact
    if not tool_path.exists():
        pytest.skip(f"{tool} not present")
    if not art_path.exists():
        pytest.skip(f"{artefact} not generated; run the pipeline first")

    before = digest(art_path)
    backup = tmp_path / art_path.name
    shutil.copy2(art_path, backup)

    argv = sys.argv[:]
    cwd = pathlib.Path.cwd()
    try:
        sys.argv = [str(tool_path)]
        import os
        os.chdir(ROOT)
        runpy.run_path(str(tool_path), run_name="__main__")
    except SystemExit as e:
        if e.code not in (0, None):
            pytest.fail(f"{tool} exited {e.code}")
    finally:
        sys.argv = argv
        os.chdir(cwd)

    after = digest(art_path)
    if after != before:
        shutil.copy2(backup, art_path)          # leave the tree as it was found
    assert after == before, (
        f"{tool} produced different output on a rerun with identical inputs.\n"
        f"Stage 9 (Repro) exists to prevent exactly this: an artefact nobody, including "
        f"you, can regenerate. Look for an unseeded RNG, a set iteration order, or a "
        f"wall-clock read."
    )


def test_the_exclusions_are_named_and_still_exist():
    """An exclusion list is a promise. This checks it has not become a graveyard.

    A tool that stops existing must leave the list, or the list slowly becomes a record of
    what someone once decided not to test — which reads as coverage and is not.
    """
    gone = [t for t in NOT_TESTED if not (ROOT / t).exists()]
    assert not gone, (
        "these tools are excluded from the determinism suite and no longer exist: "
        + ", ".join(gone) + ". Remove them from NOT_TESTED."
    )


def test_every_seeded_tool_is_either_tested_or_excused():
    """The real guard: a tool that sets a seed is claiming reproducibility.

    Grepping for a seed is crude and that is the point — it finds the tools that *intend* to
    be deterministic, and every one of them must be either covered above or excluded with a
    stated reason. A new seeded tool fails here until someone decides which it is.
    """
    tested = {t for t, _ in DETERMINISTIC}
    unaccounted = []
    for p in sorted((ROOT / "tools").glob("*.py")):
        rel = f"tools/{p.name}"
        if rel in tested or rel in NOT_TESTED:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if "default_rng(" in text or "seed=" in text or "random.seed" in text:
            unaccounted.append(rel)
    assert not unaccounted, (
        "these tools seed a random generator and are neither determinism-tested nor "
        "excluded with a reason: " + ", ".join(unaccounted)
    )
