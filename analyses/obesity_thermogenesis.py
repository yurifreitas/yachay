"""The obesity screen, put through Stage 1 — with the best control pool this library has seen.

WHOSE DATA THIS IS. The Broad / Eric and Wendy Schmidt Center obesity challenge asked which
gene perturbations promote thermogenesis in adipocytes, over a space of 4,474,413 candidate
pairs. This file measures the SINGLE-gene screen underneath that space: 128 perturbations,
25,296 cells, thirteen thermogenic signature scores per cell.

WHY IT BELONGS HERE, AND WHY IT IS NOT PROSE. The competition's own aggregate is `agg_top3_z`
— the mean of the top three of thirteen correlated z-scores per perturbation. That is a
selection operator over a set of noisy, unequally sampled observations, which is the exact
object this library was built for. Nothing about that claim needs to be taken on trust: the
scores are on disk and the calibration below is computed, not quoted.

THE FOUR-QUESTION FIT TEST (.claude/skills/sieve-new-adapter), answered before any code:

  | | |
  |---|---|
  | entity | one gene perturbation |
  | observation | one cell carrying it, with its thirteen signature z-scores |
  | aggregate | **mean of the top three signatures** — a top-k, not a mean over cells |
  | counts vary | **yes, 280-fold**: 8 cells for SRPK1, 2,242 for the control |

  FOUR YESES. Stage 1 applies, and the fourth is not a technicality — `agg_top3_z` is
  literally a top-k in the column name.

THE CONTROL POOL, AND IT IS THE BEST ONE THIS REPOSITORY HAS HAD. The skill ranks three:
designed controls in the same harness, a matched inert set, or label permutation. Every
adapter here so far has used the third or the second — `hiv_resistance` says out loud that it
used the weakest of the three. This screen carries `NC`, a non-targeting control, measured in
the same experiment on 2,242 cells. That is option one, and it means the null does not have to
be assumed: it can be RESAMPLED from cells that were actually perturbed with nothing.

WHAT THIS DOES NOT DO. It does not score gene PAIRS and it does not touch the 4.47M-pair
space, the retrieval stack, or the nomination that went to the wet lab. It asks one question
about the layer underneath all of those: how much of a top-3 ranking over unequally sampled
perturbations is the floor of the statistic rather than thermogenesis.

    python analyses/obesity_thermogenesis.py
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import pathlib
import random
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

CELLS = ROOT / "data" / "obesity" / "TF150_ThermoScores_cell.csv"
DEST = ROOT / "out" / "obesity" / "obesity_thermogenesis.json"

#: The non-targeting control, measured in the same harness. Option 1 of the three control
#: pools the adapter skill ranks, and the reason this file can calibrate rather than assume.
CONTROL = "NC"

#: The aggregate the competition scores on: mean of the top three signature z-scores. Named
#: here rather than inferred, because it is the operator Stage 1 has to be calibrated against
#: — the caller must not be able to score with one statistic and calibrate against another.
TOP_K = 3

SEED = 20260830

#: Resamples of the control per observation count. Each draws `n` control cells and applies
#: the same top-3 rule, which is what makes the null the statistic's own floor rather than a
#: distributional assumption.
DRAWS = 400


def load_cells() -> tuple[dict[str, list[list[float]]], list[str]]:
    """gene -> one row of z-scores per cell, and the signature names.

    Only the `z_` columns. The raw score columns are per-cell signature means on different
    scales; the competition's own aggregate is over the z-scored ones, and mixing the two
    would be scoring on one quantity and calibrating on another.
    """
    per_gene: dict[str, list[list[float]]] = collections.defaultdict(list)
    with CELLS.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        zcols = [c for c in (reader.fieldnames or []) if c.startswith("z_")]
        for row in reader:
            vals = []
            for c in zcols:
                try:
                    vals.append(float(row[c]))
                except (TypeError, ValueError):
                    vals.append(0.0)
            per_gene[row["gene"]].append(vals)
    return dict(per_gene), zcols


def top_k_mean(cells: list[list[float]], k: int = TOP_K) -> float:
    """The competition's aggregate: mean over cells, then mean of the top k signatures.

    THE SELECTION IS IN THE SECOND STEP. Averaging cells is a mean and behaves; taking the
    best three of thirteen correlated signatures is a top-k, and a top-k over correlated
    quantities is biased upward by an amount that grows as the cell count falls. That is the
    whole reason this file exists.
    """
    if not cells:
        return 0.0
    width = len(cells[0])
    means = [statistics.fmean(c[i] for c in cells) for i in range(width)]
    means.sort(reverse=True)
    return statistics.fmean(means[:k])


def control_null(control_cells: list[list[float]], rng: random.Random,
                 grid: list[int], draws: int) -> dict[int, dict]:
    """The floor of the statistic at each observation count, resampled from real control cells.

    NOT A PARAMETRIC NULL. These are cells from the same experiment, perturbed with a
    non-targeting guide — so the resample carries the assay's real correlation between
    signatures, its real noise, and its real batch structure. A gaussian null would carry none
    of those and would flatter every perturbation with few cells.
    """
    table: dict[int, dict] = {}
    for n in grid:
        vals = []
        for _ in range(draws):
            sample = [control_cells[rng.randrange(len(control_cells))] for _ in range(n)]
            vals.append(top_k_mean(sample))
        vals.sort()
        table[n] = {
            "mean": statistics.fmean(vals),
            "sd": statistics.pstdev(vals) or 1e-9,
            "p95": vals[int(0.95 * len(vals))],
            "p99": vals[int(0.99 * len(vals))],
        }
    return table


def null_at(table: dict[int, dict], n: int) -> dict:
    """Interpolate between fitted counts; clamp outside, and say which.

    The same choice `src/sieve/stages/null.py` makes: a null fitted nowhere near the
    observation is not a null, so the clamp is reported rather than hidden.
    """
    ks = sorted(table)
    if n <= ks[0]:
        return {**table[ks[0]], "clamped": True}
    if n >= ks[-1]:
        return {**table[ks[-1]], "clamped": True}
    for a, b in zip(ks, ks[1:]):
        if a <= n <= b:
            t = (n - a) / ((b - a) or 1)
            return {
                "mean": table[a]["mean"] + t * (table[b]["mean"] - table[a]["mean"]),
                "sd": table[a]["sd"] + t * (table[b]["sd"] - table[a]["sd"]),
                "p95": table[a]["p95"] + t * (table[b]["p95"] - table[a]["p95"]),
                "p99": table[a]["p99"] + t * (table[b]["p99"] - table[a]["p99"]),
                "clamped": False,
            }
    return {**table[ks[-1]], "clamped": True}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--draws", type=int, default=DRAWS)
    args = ap.parse_args()

    if not CELLS.exists():
        print(f"missing {CELLS}", file=sys.stderr)
        return 1

    per_gene, zcols = load_cells()
    controls = per_gene.get(CONTROL)
    if not controls:
        print(f"no {CONTROL} control cells found", file=sys.stderr)
        return 1

    counts = {g: len(c) for g, c in per_gene.items()}
    perturbations = sorted(g for g in per_gene if g != CONTROL)
    ns = sorted(counts[g] for g in perturbations)

    grid = sorted({8, 16, 24, 32, 48, 64, 96, 128, 160, 200, 260, 340, 450, 600, 900})
    rng = random.Random(SEED)
    table = control_null(controls, rng, grid, args.draws)

    rows = []
    for g in perturbations:
        n = counts[g]
        raw = top_k_mean(per_gene[g])
        null = null_at(table, n)
        rows.append({
            "gene": g,
            "cells": n,
            "raw": round(raw, 5),
            "null_mean": round(null["mean"], 5),
            "null_p95": round(null["p95"], 5),
            "excess": round(raw - null["mean"], 5),
            "z": round((raw - null["mean"]) / null["sd"], 2),
            "above_null_p95": raw > null["p95"],
            "null_clamped": null["clamped"],
        })

    by_raw = sorted(rows, key=lambda r: -r["raw"])
    by_z = sorted(rows, key=lambda r: -r["z"])
    raw_top = [r["gene"] for r in by_raw[:20]]
    cal_top = [r["gene"] for r in by_z[:20]]
    survived = [g for g in raw_top if g in cal_top]

    small = [r for r in rows if r["cells"] < 100]
    small_in_raw_top = sum(1 for r in by_raw[:20] if r["cells"] < 100)
    small_in_cal_top = sum(1 for r in by_z[:20] if r["cells"] < 100)

    payload = {
        "generated": "2026-08-30",
        "provenance": "Broad / Eric and Wendy Schmidt Center obesity challenge, TF150 "
                      "thermogenic signature scores per cell",
        "governed_by": ".claude/skills/sieve-new-adapter and "
                       "docs/adr/0007-theory-enters-by-measurement.md",
        "question": "The competition ranks perturbations by the mean of their top three "
                    "thermogenic signatures. How much of that ranking is thermogenesis, and "
                    "how much is the floor of a top-3 over thirteen correlated scores at "
                    "small cell counts?",
        "fit_test": {
            "entity": "one gene perturbation",
            "observation": "one cell carrying it, with thirteen signature z-scores",
            "aggregate": f"mean of the top {TOP_K} signatures — a top-k, not a mean",
            "counts_vary": f"yes, {max(ns) // max(1, min(ns))}-fold: {min(ns)} cells to "
                           f"{max(ns)} across perturbations",
            "verdict": "four yeses; Stage 1 applies",
        },
        "control_pool": {
            "used": f"designed non-targeting control ({CONTROL}) in the same harness",
            "rank": "option 1 of 3 — the strongest the adapter skill ranks",
            "cells": len(controls),
            "why_it_matters": "Every other adapter in this repository calibrates against "
                              "permutation or a matched set; hiv_resistance says out loud "
                              "that it used the weakest of the three. Here the null is "
                              "RESAMPLED from cells perturbed with nothing, in the same "
                              "experiment — so it carries the assay's real correlation "
                              "between signatures, its real noise and its real batch "
                              "structure, none of which a parametric null would.",
        },
        "scale": {
            "perturbations": len(perturbations),
            "cells_scored": sum(counts[g] for g in perturbations),
            "signatures": len(zcols),
            "cells_min": min(ns),
            "cells_median": int(statistics.median(ns)),
            "cells_max": max(ns),
            "control_cells": len(controls),
        },
        "null_by_count": [
            {"cells": n, "null_mean": round(v["mean"], 5), "p95": round(v["p95"], 5),
             "p99": round(v["p99"], 5)}
            for n, v in sorted(table.items())
        ],
        "reranking": {
            "raw_top20": raw_top,
            "calibrated_top20": cal_top,
            "survived_both": survived,
            "displaced": len(raw_top) - len(survived),
            "small_n_in_raw_top20": small_in_raw_top,
            "small_n_in_calibrated_top20": small_in_cal_top,
            "small_n_threshold": 100,
            "perturbations_under_threshold": len(small),
        },
        "rows": sorted(rows, key=lambda r: -r["z"]),
        "says": "A calibration of the single-gene screen, not a nomination and not a claim "
                "about pairs. It says which perturbations clear the floor their own cell "
                "count sets, and nothing about whether they would work in a person.",
        "limits": [
            "One assay, one cell model, one set of thirteen signatures. A perturbation that "
            "does something real outside those signatures is invisible to this and to the "
            "competition alike.",
            "The control is one non-targeting guide. It carries the assay's noise but not "
            "the variation between different guides against the same gene, so the null is a "
            "floor for signature noise rather than for off-target effects.",
            "Cells within a perturbation are not independent — they share a guide, a well and "
            "a batch. The resample treats them as exchangeable, which is the assumption HIV "
            "resistance broke in this repository and which is stated here rather than "
            "discovered later.",
        ],
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {DEST.relative_to(ROOT)}")
    print(f"  {len(perturbations)} perturbations, {sum(counts[g] for g in perturbations):,} "
          f"cells, {len(zcols)} signatures")
    print(f"  cells per perturbation: {min(ns)} to {max(ns)} "
          f"({max(ns) // max(1, min(ns))}-fold), control {len(controls)}")
    print(f"  of the raw top 20, {len(survived)} survive calibration — "
          f"{len(raw_top) - len(survived)} displaced")
    print(f"  perturbations with under 100 cells in the raw top 20: {small_in_raw_top}; "
          f"after calibration: {small_in_cal_top}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
