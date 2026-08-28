#!/usr/bin/env python
"""An interval on every headline number, including the ones that might not survive one.

WHY THIS IS THE OLDEST DEBT IN THE PROJECT. `references/standards.md` §4 adopts GUM, and
states the rule in one line:

    A difference smaller than its own interval is not a difference and must not be reported
    as one.

The repository has produced **exactly one interval** in its life — the 4,000-resample paired
bootstrap that settled `lineage.md` §8b — and has since published dozens of point estimates
that carry real weight: 73.5 %, 39.7 %, 52.0 %, 8 %, and the sharpest claim of all, that a
curated frequency resting on one patient reads 0.932 where the patients say 0.436. Every one
is quoted in prose as though it were exact. `docs/audit.md` A6 has said so since the first
sweep and nothing was done about it for thirteen more.

**This file is written to be able to embarrass its author.** A bootstrap can come back wide,
and a headline whose interval spans the thing it denies has to be walked back rather than
softened. That is the point of running it and the reason it is not optional.

WHAT IS COMPUTED, AND HOW.

  proportions        Wilson score interval, which behaves at the extremes where the normal
                     approximation does not - and most of these proportions are extreme.
  differences        Paired bootstrap over the unit of resampling that matters, which is
                     never the observation: for the single-case bias it is the FEATURE-
                     DISEASE PAIR, because two features of one disease are not independent.
  rank correlations  Bootstrap over diseases, the same reason.

THE UNIT OF RESAMPLING IS THE WHOLE ARGUMENT. This library exists because a null fitted on
the wrong resampling unit produced a z of -4.09 for two months (`lineage.md` §8a, ADR 0004).
Bootstrapping observations that are clustered inside diseases would repeat that mistake in a
different file, so every resample below draws whole clusters.

    python tools/intervals.py                # 4,000 resamples, the published default
    python tools/intervals.py --resamples 20000

Needs numpy, already a dependency.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
from collections import defaultdict

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
RARE = ROOT / "out" / "rare"
OUT = ROOT / "out"

#: The same seed the rest of the project uses, so a rerun reproduces a published interval.
SEED = 20260827
RESAMPLES = 4000


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval for a proportion.

    Chosen over the normal approximation because most proportions here are extreme - 84.6 %,
    52.0 %, 8 % - and the normal interval famously misbehaves there, running past 0 or 1 and
    covering badly. Wilson is the standard fix and it is three lines.
    """
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def cluster_bootstrap(values_by_cluster: dict, stat, rng, resamples: int) -> tuple:
    """Resample whole clusters, apply `stat` to the pooled draw, return the percentiles.

    `stat` receives a flat list of the values inside the drawn clusters. Drawing clusters
    rather than values is what keeps the interval honest when observations are correlated
    inside a disease.
    """
    keys = list(values_by_cluster)
    if not keys:
        return (None, None, None)
    n = len(keys)
    draws = []
    for _ in range(resamples):
        picked = rng.integers(0, n, n)
        pooled = []
        for i in picked:
            pooled.extend(values_by_cluster[keys[i]])
        if pooled:
            draws.append(stat(pooled))
    if not draws:
        return (None, None, None)
    arr = np.asarray(draws, dtype=float)
    return (float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5)), float(arr.mean()))


def load(name: str):
    p = RARE / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resamples", type=int, default=RESAMPLES)
    args = ap.parse_args()
    rng = np.random.default_rng(SEED)

    results = []
    notes = []

    def proportion(name, k, n, doc):
        lo, hi = wilson(k, n)
        results.append({
            "claim": name, "kind": "proportion", "point": round(k / n, 4) if n else None,
            "k": k, "n": n, "lo": round(lo, 4), "hi": round(hi, 4),
            "width": round(hi - lo, 4), "method": "Wilson score, 95%", "citedIn": doc,
        })

    # ---- 1. the prevalence discordance ---------------------------------------------------
    ang = load("ancestry_geography")
    if ang:
        d = ang["discordance"]
        proportion("disorders whose prevalence class disagrees across countries",
                   d["discordant"], d["comparableDisorders"],
                   "references/rare-disease-ancestry.md §1c")

    # ---- 2. the evidence share -----------------------------------------------------------
    ea = load("evidence_atlas")
    if ea:
        p = ea["profile"]
        proportion("diseases with at least one sign from a real series",
                   p["diseasesWithAQuantifiedSign"], p["diseasesWithPhenotypeAnnotations"],
                   "references/rare-disease-scale.md §4b")
        proportion("diseases with no fraction of any kind",
                   p["diseasesWithNoFractionAtAll"], p["diseasesWithPhenotypeAnnotations"],
                   "references/rare-disease-scale.md §4b")

    # ---- 3. ClinVar ----------------------------------------------------------------------
    cv = load("clinvar_evidence")
    if cv:
        n = cv["scale"]["grch38Rows"]
        proportion("ClinVar variants of uncertain significance",
                   cv["significance"]["counts"].get("uncertain significance", 0), n,
                   "references/patient-data.md §3c")
        proportion("ClinVar variants at one star or less",
                   cv["reviewStatus"]["atOneStarOrLess"], n, "audit.md A21")
        cc = cv["crossCheck"]
        found = cc["foundInClinVar"]
        not_confident = sum(cc["bySignificance"].get(k, 0) for k in
                            ("uncertain significance", "conflicting", "likely benign",
                             "benign", "not provided", "other"))
        proportion("our patient variants NOT confidently pathogenic in ClinVar",
                   not_confident, found, "audit.md A21")

    # ---- 4. the genotype-phenotype power share -------------------------------------------
    gp = load("genotype_phenotype")
    if gp:
        s = gp["scale"]
        proportion("gene-feature comparisons powered for a 50-point difference",
                   s["powered"], s["tests"], "references/patient-data.md §2f")

    # ---- 5. THE ONE THAT COULD EMBARRASS US ----------------------------------------------
    # The single-case bias: at a curated denominator of 1, the catalogue's mean is 0.932 and
    # the patients' is 0.436. Paired bootstrap over DISEASES, not over pairs: two features of
    # the same disease share patients, a curator and a publication, so treating them as
    # independent would give an interval that is too narrow in exactly the direction that
    # flatters the claim.
    # THE INTERVAL ON THE STRONGEST CLAIM IS COMPUTED WHERE THE DATA IS, NOT HERE.
    # The first version of this file bootstrapped the worst-disagreement head the artefact
    # ships (25 pairs) and returned -0.98 — which is a tautology wearing an interval, since
    # the head was SELECTED for large differences. `tools/patient_frequencies.py` now
    # computes it over the full 16,276 comparisons, clustered by disease, and this file
    # reads the result rather than reproducing it badly.
    pf = load("patient_frequencies")
    if pf:
        for bucket, v in (pf.get("singleCaseBias", {})
                            .get("byCuratedDenominator", {}) or {}).items():
            iv = v.get("interval") or {}
            ci = iv.get("meanDifference")
            if not ci:
                continue
            results.append({
                "claim": f"single-case bias, curated denominator {bucket}",
                "kind": "paired difference",
                "point": round(v["meanPatientFrequency"] - v["meanCuratedPoint"], 4),
                "lo": ci[0], "hi": ci[1], "width": round(ci[1] - ci[0], 4),
                "pairs": v["pairs"], "clusters": iv.get("diseases"),
                "method": iv.get("method"),
                "excludesZero": iv.get("excludesZero"),
                "citedIn": "references/patient-data.md §2c",
            })

    # ---- 6. the bias statistics ----------------------------------------------------------
    bias = load("bias")
    if bias:
        for f in bias.get("findings", []):
            if f.get("statistic") is None:
                continue
            notes.append(
                "%s is reported as %s with verdict %r and NO interval: it is a rank "
                "correlation over a join this file cannot reconstruct from the artefact "
                "alone. Computing it needs tools/atlas_bias.py to emit its per-disease "
                "vectors, which it does not yet do."
                % (f["name"], f["statistic"], f.get("verdict"))
            )

    payload = {
        "generated": "tools/intervals.py",
        "resamples": args.resamples,
        "seed": SEED,
        "premise": (
            "references/standards.md §4 adopts GUM: a difference smaller than its own "
            "interval is not a difference. The project had produced exactly one interval "
            "and published dozens of point estimates. docs/audit.md A6, open since the "
            "first sweep."
        ),
        "resamplingUnit": (
            "Clusters, never observations. A null fitted on the wrong resampling unit "
            "produced a z of -4.09 here for two months (lineage.md §8a); bootstrapping "
            "correlated observations would repeat that in a different file."
        ),
        "results": results,
        "notMeasured": notes,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    dest = RARE / "intervals.json"
    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("wrote %s" % dest.relative_to(ROOT))
    print()
    print("  %-62s %9s  %-19s %s" % ("claim", "point", "95% interval", "width"))
    for r in results:
        if r["lo"] is None:
            continue
        width = r.get("width")
        print("  %-62s %9.4f  [%7.4f, %7.4f] %s"
              % (r["claim"][:62], r["point"], r["lo"], r["hi"],
                 f"{width:.4f}" if width is not None else ""))
    if notes:
        print()
        print("  NOT MEASURED (%d):" % len(notes))
        for n in notes:
            print("    - %s" % n[:150])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
