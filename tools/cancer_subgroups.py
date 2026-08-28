#!/usr/bin/env python
"""Selective dependency by cancer subgroup — the ten stages on this repository's home ground.

WHY THIS IS OVERDUE. DepMap is the reference application of this library and the source of
every calibration result it publishes, and until now it has been scored **as one pool**:
17,916 genes ranked across 1,178 cell lines with no regard for what cancer those lines are.
That answers "what is broadly essential", which is close to the least interesting question
the data can be asked, and it is the one whose top is 60 % pan-essential genes.

The interesting question is **subgroup-selective**: which gene does *this* cancer depend on
that other cancers do not. `Model.csv` carries three nested levels of subgroup and none of
them had been read:

    OncotreeLineage          35 distinct   Lung, Lymphoid, Skin, CNS/Brain, ...
    OncotreePrimaryDisease   96 distinct   Non-Small Cell Lung Cancer, Melanoma, ...
    OncotreeSubtype         254 distinct   Lung Adenocarcinoma, Glioblastoma, ...

## The stages, applied rather than described

This is the first analysis in the repository to run several stages of the library on one
question, and each one changes the answer:

  **Stage 3, Confound.** A gene every cell line needs is not a selective dependency; it is
  toxicity. Pan-essentials are excluded using DepMap's own control set, before ranking —
  not flagged afterwards, because a ranking whose top is 60 % pan-essential has already
  wasted the reader's attention.

  **Stage 2, Power.** A subgroup of 8 lines and one of 260 are not two estimates of
  differing precision. `sieve.stages.power` reports, per subgroup, the smallest effect its
  size could detect, and a subgroup that cannot detect a large one is reported as
  **underpowered rather than as having no hits** — those are different statements and
  conflating them is how a small cancer type acquires a reputation for being boring.

  **Multiplicity.** 17,916 genes x N subgroups is a selection operator. Benjamini-Hochberg
  within each subgroup, because the question "which genes matter for THIS cancer" is asked
  once per subgroup.

## What the effect is, and what it is not

For each gene and subgroup: the difference in mean Chronos dependency between the lines of
that subgroup and all others, standardised by the pooled spread — Cohen's d, tested with
Welch's t. **Not** a calibrated z: Stage 1 calibrates a max-order statistic against a null of
the right shape, and a difference in means is not an order statistic. `docs/lineage.md` §9
records this distinction being got wrong once already, when the NF2 subgroup contrast was run
through a two-null z-difference and the positive control failed. This uses the plain
difference, which is what that finding concluded was correct for a subgroup contrast.

    python tools/cancer_subgroups.py                     # lineages
    python tools/cancer_subgroups.py --level subtype     # the 254 finer groups

Needs numpy, pandas and scipy — all dependencies.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import sieve as sv  # noqa: E402
from sieve.adapters import depmap as dm  # noqa: E402

OUT = ROOT / "out"
DATA = ROOT / "data" / "depmap"

#: A subgroup smaller than this cannot support a contrast at all. Registered in
#: manifests/thresholds.yaml.
MIN_LINES = 8
#: The effect a reader would act on, used for the Stage 2 annotation.
EFFECT_OF_INTEREST = 0.8
#: THE SIGN. `load_matrix` returns a SIGN-FLIPPED matrix — its own docstring says "dependency
#: is negative in DepMap; sieve wants larger-is-better" — and the dataclass exposes `.flipped`
#: to say so. The first two runs of this file ignored that field and ranked the *anti*-
#: dependency: they returned SOX10 for Skin at a mean of +1.261 and read it as "not a hit",
#: when +1.261 in a flipped matrix IS the melanoma lineage dependency, the most canonical
#: positive control in the whole dataset. The orientation is now read from `.flipped` rather
#: than assumed, so the assertion below fails loudly if the adapter ever changes convention.
#:
#: STAGE 0, AND THE FIRST VERSION OF THIS FILE DID NOT HAVE IT.
#: A large negative d says the subgroup is more depleted THAN THE REST — which is also
#: satisfied when the rest gains a growth advantage and the subgroup is merely neutral. The
#: first run returned NCKAP1 for Lymphoid at |d| = 1.86 with means of 0.078 in-group against
#: 0.512 elsewhere: on the correct orientation the REST are the dependent ones and the
#: subgroup is merely neutral. Ranking that is optimising a metric whose maximum is reachable
#: without the thing being measured, which is precisely what Stage 0 names.
#: So a hit must ALSO be an actual dependency, at DepMap's own 0.5 cut.
DEPENDENCY_FLOOR = 0.5
#: THE LOOSE PRE-GATE. The artefact carries every gene clearing this, not only the genes
#: clearing the registered gates, so the interface can move the thresholds and show the
#: shortlist change. That is not a convenience: a reader who can only see the answer at one
#: threshold cannot tell a robust finding from one balanced on the cut, and this library's
#: whole argument is that the cut is where the mistakes live. `hits` remains the
#: pre-registered answer; `candidates` is the material a reader may re-gate.
CAND_Q = 0.25
CAND_D = 0.3
CAND_MAX = 40
#: Positive controls, checked on every run rather than admired in a docstring. Each is a
#: textbook lineage dependency; if the run stops recovering them the orientation or the
#: gates have drifted and the artefact says so in `positiveControls`.
CONTROLS = {"Skin": ["SOX10", "MITF"], "CNS/Brain": ["SOX2"],
            "Peripheral Nervous System": ["MYCN", "PHOX2B"],
            "Lymphoid": ["IRF4", "POU2AF1"], "Bowel": ["CTNNB1", "TCF7L2"]}
LEVELS = {
    "lineage": "OncotreeLineage",
    "disease": "OncotreePrimaryDisease",
    "subtype": "OncotreeSubtype",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", choices=sorted(LEVELS), default="lineage")
    ap.add_argument("--top", type=int, default=15, help="hits kept per subgroup")
    args = ap.parse_args()
    column = LEVELS[args.level]

    print("loading the dependency matrix ...")
    depmap = dm.load_matrix(str(DATA))
    values = depmap.values if hasattr(depmap, "values") else depmap
    genes = list(depmap.genes)
    lines = list(depmap.lines)
    X = np.asarray(values, dtype=np.float32)
    if not getattr(depmap, "flipped", False):
        raise SystemExit(
            "the adapter returned an unflipped matrix; every comparison below assumes "
            "larger-is-more-dependent and would silently rank the anti-dependency")
    print("  %s lines x %s genes (sign-flipped: larger = more dependent)"
          % (f"{len(lines):,}", f"{len(genes):,}"))

    # ---- Stage 3, before anything is ranked ---------------------------------------------
    pan = set(dm.load_gene_set(str(DATA), "AchillesCommonEssentialControls.csv"))
    keep = np.array([g not in pan for g in genes])
    print("  Stage 3: dropping %s pan-essential genes before ranking, not after"
          % f"{(~keep).sum():,}")
    X = X[:, keep]
    genes = [g for g, k in zip(genes, keep) if k]

    # ---- the subgroups -------------------------------------------------------------------
    models = pd.read_csv(DATA / "Model.csv", low_memory=False)
    label = dict(zip(models["ModelID"].astype(str), models[column].astype(str)))
    groups: dict[str, list[int]] = {}
    for i, line in enumerate(lines):
        g = label.get(str(line))
        if g and g not in ("nan", "Non-Cancerous"):
            groups.setdefault(g, []).append(i)
    groups = {g: idx for g, idx in groups.items() if len(idx) >= MIN_LINES}
    print("  %d subgroups at level %r with >= %d screened lines"
          % (len(groups), args.level, MIN_LINES))

    finite = np.isfinite(X)
    results = []
    for name, idx in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        mask = np.zeros(len(lines), dtype=bool)
        mask[idx] = True

        a, b = X[mask], X[~mask]
        fa, fb = finite[mask], finite[~mask]
        na, nb = fa.sum(axis=0), fb.sum(axis=0)
        ok = (na >= MIN_LINES) & (nb >= MIN_LINES)

        ma = np.where(ok, np.nansum(np.where(fa, a, 0), axis=0) / np.maximum(na, 1), np.nan)
        mb = np.where(ok, np.nansum(np.where(fb, b, 0), axis=0) / np.maximum(nb, 1), np.nan)
        va = np.nanvar(np.where(fa, a, np.nan), axis=0)
        vb = np.nanvar(np.where(fb, b, np.nan), axis=0)
        pooled = np.sqrt((va + vb) / 2)
        pooled[pooled == 0] = np.nan
        d = (ma - mb) / pooled          # flipped matrix: POSITIVE d = subgroup depends more

        t, p = stats.ttest_ind(np.where(fa, a, np.nan), np.where(fb, b, np.nan),
                               axis=0, equal_var=False, nan_policy="omit")
        p = np.asarray(p, dtype=float)
        valid = ok & np.isfinite(p) & np.isfinite(d)
        if not valid.any():
            continue

        q = np.full_like(p, np.nan)
        q[valid] = multipletests(p[valid], alpha=0.05, method="fdr_bh")[1]

        # Stage 2: what could a subgroup this size have detected at all?
        try:
            floor = sv.min_detectable_effect(2 * len(idx)).at()
        except sv.PowerError:
            floor = None
        powered = floor is not None and floor <= EFFECT_OF_INTEREST

        # More dependent than the rest = the selective vulnerability.
        # Scan the WHOLE ordering, not a prefix of it. The first version scanned the top 60
        # by d and only then applied the Stage 0 dependency gate, which is truncate-then-
        # filter: the genes with the most extreme d are largely the artefact the gate exists
        # to remove, so the gate emptied the window and the real lineage dependencies - which
        # carry a moderate d with a genuine one - never entered it. The same mistake as the
        # dossier's [:24] (audit A12), in a different file.
        order = np.argsort(np.where(valid, d, -np.inf))[::-1]
        hits = []
        for j in order:
            # Stage 0: selective AND actually dependent. Both, or it is not a target.
            if not valid[j] or q[j] > 0.05 or d[j] < 0.5:
                continue
            if not (ma[j] >= DEPENDENCY_FLOOR):
                continue
            hits.append({
                "gene": genes[j],
                "d": round(float(d[j]), 3),
                "meanInGroup": round(float(ma[j]), 3),
                "meanElsewhere": round(float(mb[j]), 3),
                "q": float(q[j]),
                "linesInGroup": int(na[j]),
            })
            if len(hits) >= args.top:
                break

        candidates = []
        for j in order:
            if not valid[j] or q[j] > CAND_Q or d[j] < CAND_D:
                continue
            candidates.append({
                "gene": genes[j],
                "d": round(float(d[j]), 3),
                "meanInGroup": round(float(ma[j]), 3),
                "meanElsewhere": round(float(mb[j]), 3),
                "q": float(q[j]),
                "linesInGroup": int(na[j]),
            })
            if len(candidates) >= CAND_MAX:
                break

        # THE CAP MUST NOT TRUNCATE THE REGISTERED ANSWER. Candidates are collected in
        # descending effect under the LOOSE gate, and most of what the loose gate admits
        # fails only the Stage 0 floor — so for Skin, 26 floor-failures with high effect
        # filled the window and pushed the 15th registered hit outside it. The interface
        # then re-gated the truncated pool and drew 14 rows beside a sentence saying 15.
        # Truncate-then-filter for the third time in this file's history (audit A12, A29).
        #
        # So the pool is the UNION: every registered hit is present by construction, and the
        # assertion below fails the run rather than shipping a pool that cannot reproduce it.
        seen_c = {c["gene"] for c in candidates}
        for h in hits:
            if h["gene"] not in seen_c:
                candidates.append(dict(h))
        candidates.sort(key=lambda c: -c["d"])
        missing = {h["gene"] for h in hits} - {c["gene"] for c in candidates}
        assert not missing, "candidate pool cannot reproduce the registered hits: %s" % missing

        results.append({
            "subgroup": name,
            "candidates": candidates,
            "lines": len(idx),
            "detectableFloor": floor,
            "powered": powered,
            "hits": hits,
            "hitCount": len(hits),
            "positiveControls": [
                {"gene": g, "rank": next((k for k, h in enumerate(hits) if h["gene"] == g),
                                         None)}
                for g in CONTROLS.get(name, [])],
            "says": (
                "underpowered: %d lines can detect no effect smaller than %s SD, so an "
                "empty list here means the screen could not see it, not that nothing is "
                "there" % (len(idx), floor) if not powered else
                "%d selective dependencies at q < 0.05, d > 0.5 and a mean dependency "
                "of at least %.1f" % (len(hits), DEPENDENCY_FLOOR)
            ),
        })
        print("    %-42s %4d lines  floor %-6s %s"
              % (name[:42], len(idx), floor,
                 ", ".join(h["gene"] for h in hits[:5]) or "(none)"))

    powered_n = sum(1 for r in results if r["powered"])
    payload = {
        "generated": "tools/cancer_subgroups.py",
        "level": args.level,
        "column": column,
        "premise": (
            "DepMap is this library's reference application and had only ever been scored "
            "as one pool, which answers 'what is broadly essential' - the question whose "
            "top is 60% pan-essential. Model.csv carries three nested levels of subgroup "
            "and none had been read."
        ),
        "method": {
            "effect": "Cohen's d of mean Chronos dependency, subgroup against all others",
            "test": "Welch t, Benjamini-Hochberg within each subgroup",
            "stage3": "pan-essential genes dropped BEFORE ranking, using DepMap's control set",
            "orientation": (
                "load_matrix returns a SIGN-FLIPPED matrix (larger = more dependent) and "
                "exposes .flipped to say so. The first two runs of this file ignored that "
                "field and ranked the anti-dependency, returning SOX10 for Skin at a mean "
                "of 1.261 and reading it as 'not a hit' - when that is the single most "
                "canonical lineage dependency in the dataset. The orientation is now read "
                "from .flipped and the run aborts if it changes."),
            "stage0": (
                "A hit must be selective AND an actual dependency: mean dependency in the "
                "subgroup at or above %.1f. Without this the ranking is also satisfied by "
                "the REST being the dependent ones while the subgroup is merely neutral."
                % DEPENDENCY_FLOOR),
            "positiveControls": (
                "Textbook lineage dependencies checked on every run, reported with their "
                "rank or null: %s" % ", ".join(
                    "%s->%s" % (k, "/".join(v)) for k, v in sorted(CONTROLS.items()))),
            "stage2": ("sieve.stages.power reports the smallest effect each subgroup could "
                       "detect; an underpowered subgroup with no hits is reported as "
                       "underpowered, never as negative"),
            "notStage1": (
                "This is a difference in means, not a max-order statistic, so it is NOT "
                "null-calibrated. docs/lineage.md §9 records that distinction being got "
                "wrong once, when the NF2 subgroup contrast ran through a two-null "
                "z-difference and the positive control failed."
            ),
            "minLines": MIN_LINES,
            "effectOfInterest": EFFECT_OF_INTEREST,
        },
        "gates": {
            "registered": {"q": 0.05, "d": 0.5, "dependencyFloor": DEPENDENCY_FLOOR},
            "candidatePreGate": {"q": CAND_Q, "d": CAND_D, "cap": CAND_MAX},
            "says": (
                "`hits` is the shortlist at the REGISTERED gates (manifests/thresholds.yaml, "
                "ADR 0006). `candidates` is every gene clearing a deliberately loose "
                "pre-gate, so a reader can move the thresholds and watch the shortlist "
                "change. Moving them is target contact - the reader has seen the data - and "
                "the interface says so rather than presenting a re-gated list as if it were "
                "the registered one."),
        },
        "scale": {
            "lines": len(lines),
            "genesAfterStage3": len(genes),
            "panEssentialDropped": int((~keep).sum()),
            "subgroups": len(results),
            "powered": powered_n,
            "underpowered": len(results) - powered_n,
        },
        "results": results,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"cancer_subgroups_{args.level}.json"
    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print()
    print("  %d subgroups: %d powered for a %.1f SD effect, %d not"
          % (len(results), powered_n, EFFECT_OF_INTEREST, len(results) - powered_n))
    print("wrote %s" % dest.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
