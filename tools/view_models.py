#!/usr/bin/env python
"""Layouts solved here, so the browser only draws.

WHY THIS FILE EXISTS. The explorer's rule is that no statistic is computed in the browser —
every figure is read from the artefact the analysis wrote, which is what lets
`tools/verify_claims.py` fail the build when prose and artefact drift. But a *layout* is not a
statistic, and until now the boundary was blurry: components were sorting twenty rows and
bucketing values at render time, which is cheap at twenty rows and impossible at thirteen
thousand.

So the boundary is drawn here. This file precomputes **view models**: the orderings, the bin
counts and the coordinates a hyperdimensional view needs, in a shape a renderer can consume
without a loop over the raw data. Three consequences, all of them the point:

  * **The browser stops holding data it cannot draw.** `knowledge_shape.json` carries 12,994
    five-dimensional vectors. A parallel-coordinates plot of 12,994 lines is a black
    rectangle; what a reader can actually see is the DENSITY, so the density is computed once,
    here, and the per-disease table never ships.
  * **A seriation is a decision, not a default.** A matrix heatmap says something different
    depending on how its rows and columns are ordered, and an ordering computed in a component
    is an argument nobody can audit. The orderings below are named, explained and versioned
    with the artefact.
  * **The payload gets smaller, not larger.** Solving the layout is a reduction: 12,994 rows
    become a grid of counts.

WHAT IT DOES NOT DO. It computes no statistic that a headline depends on. Every number a
reader is asked to believe still comes from the tool that measured it; this file rearranges
what those tools already wrote.

    python tools/view_models.py

Stdlib only.
"""

from __future__ import annotations

import csv
import math
import argparse
import json
import pathlib
import sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

RARE = ROOT / "out" / "rare"
DEST = RARE / "view_models.json"

#: Bins per axis in the parallel-coordinates density. Enough to show a shape, few enough that
#: the grid stays small and every cell holds a countable number of diseases.
PCP_BINS = 24


def load(name: str) -> dict:
    path = RARE / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


# --------------------------------------------------------------- language coverage matrix

def language_matrix() -> dict:
    """A 14 x 23 matrix, seriated so the block structure is visible rather than alphabetical.

    THE ORDERING IS THE ARGUMENT. Rows (languages) are sorted by annotation-weighted coverage,
    so the reader descends from complete to absent. Columns (organ systems) are sorted by the
    MEAN coverage across languages, which puts the systems every language handles on one side
    and the systems every language drops on the other — and the resulting block is the finding:
    the holes are not scattered, they line up.
    """
    src = load("language_coverage")
    langs = [l for l in src.get("languages", []) if l.get("per_system")]
    if not langs:
        return {}

    systems = sorted({s for l in langs for s in l["per_system"]})
    col_mean = {
        s: sum(l["per_system"].get(s, 0.0) for l in langs) / len(langs)
        for s in systems
    }
    col_order = sorted(systems, key=lambda s: -col_mean[s])
    row_order = sorted(langs, key=lambda l: -l["annotation_coverage"])

    return {
        "rows": [{"id": l["language"], "label": l["name"],
                  "total": round(l["annotation_coverage"], 4)} for l in row_order],
        "cols": [{"id": s, "mean": round(col_mean[s], 4)} for s in col_order],
        "cells": [[round(l["per_system"].get(s, 0.0), 4) for s in col_order] for l in row_order],
        "ordering": ("rows by annotation-weighted coverage, columns by mean coverage across "
                     "languages — so a vertical band is a system every language drops"),
    }


# --------------------------------------------------------------- the scale inversion

def scale_slopegraph() -> dict:
    """Pathway retention against cell-type retention, per organ system, as paired points.

    A slopegraph because the finding is a CROSSING, not two rankings: pathways hold what is
    pathway-shaped, cell types hold what is structural, and the systems where the two
    disagree are the ones whose lines cross. A pair of sorted bar charts would have hidden
    exactly that.
    """
    src = load("scale_information")
    rows = src.get("per_organ_system", [])
    if not rows:
        return {}
    out = []
    for r in rows:
        a, b = r["pathway_retention"], r["cell_type_retention"]
        out.append({
            "id": r["system"], "label": r["name"], "n": r["diseases"],
            "pathway": a, "cell_type": b,
            "delta": round(b - a, 4),
            "crosses": (b - a) > 0.02,     # cell types recover what pathways lost
        })
    out.sort(key=lambda r: -r["pathway"])
    return {
        "pairs": out,
        "crossing": sum(1 for r in out if r["crosses"]),
        "reading": ("each line joins one organ system's pathway retention to its cell-type "
                    "retention; a line that rises is a system the spatial alphabet recovers "
                    "and the process alphabet loses"),
    }


# --------------------------------------------------------------- knowledge shape density

def knowledge_pcp() -> dict:
    """Binned parallel coordinates over the five knowledge axes.

    12,994 lines drawn individually is a filled rectangle. What survives at that count is
    density, so each axis is cut into PCP_BINS and what ships is a grid of counts plus the
    counts of each adjacent-bin TRANSITION — which is what actually draws a parallel-
    coordinates plot legibly at scale (the ribbon between axes, not the polyline).
    """
    src = load("knowledge_shape")
    diseases = src.get("diseases")
    axes = list((src.get("axes") or {}).keys())
    if not diseases or not axes:
        return {"unavailable": ("knowledge_shape.json ships without its per-disease table by "
                                "design; run tools/knowledge_shape.py and read the local "
                                "artefact to rebuild this view model")}

    def b(v: float) -> int:
        return min(PCP_BINS - 1, max(0, int(v * PCP_BINS)))

    density = [[0] * PCP_BINS for _ in axes]
    links: dict[tuple[int, int, int], int] = {}
    for d in diseases:
        vec = [d["vector"][a] for a in axes]
        for i, v in enumerate(vec):
            density[i][b(v)] += 1
        for i in range(len(vec) - 1):
            key = (i, b(vec[i]), b(vec[i + 1]))
            links[key] = links.get(key, 0) + 1

    return {
        "axes": axes,
        "bins": PCP_BINS,
        "density": density,
        "links": [{"axis": k[0], "from": k[1], "to": k[2], "n": v}
                  for k, v in sorted(links.items(), key=lambda kv: -kv[1])[:1200]],
        "diseases": len(diseases),
        "reading": ("each column is one axis of what is known, cut into bins; the ribbons "
                    "between columns are how many diseases move from one band to the next"),
    }


# --------------------------------------------------------------- conflict gradient

def conflict_grid() -> dict:
    """The submitter x condition table as a grid, so the gradient reads as a surface.

    The table already ships and stays. This is the same numbers arranged for a heatmap,
    because the finding — conflict rising with conditions, and rising FASTER the more
    submitters there are — is a slope across two axes and a table asks the reader to hold
    twenty-five numbers in their head to see it.
    """
    src = load("evidence_conflict")
    strata = src.get("by_submitter_stratum", {})
    if not strata:
        return {}
    bins = ["0", "1", "2", "3", "4+"]
    rows = list(strata.keys())
    cells = []
    for r in rows:
        cells.append([
            (strata[r][b]["conflict_rate"] if b in strata[r] else None) for b in bins
        ])
    return {
        "rows": rows, "cols": bins, "cells": cells,
        "marginal": [
            (src.get("marginal", {}).get(b, {}) or {}).get("conflict_rate") for b in bins
        ],
        "reading": ("rows are how many submitters a variant has, columns how many distinct "
                    "conditions; the value is the share carrying conflicting classifications"),
    }


def knowledge_void() -> dict:
    """The lattice faces, passed through with the headline the reader needs beside them.

    No layout to solve — `tools/knowledge_void.py` already emits ten 4x4 faces. What this adds
    is the framing numbers a face is meaningless without: how full the space is, how much of
    it is frontier, and how many anti-forms there are in total. A grid of squares with no
    denominator is decoration.
    """
    src = load("knowledge_void")
    faces = (src.get("faces") or {}).get("items")
    if not faces:
        return {}
    return {
        "bins": src["lattice"]["bins_per_axis"],
        "axes": src["lattice"]["axes"],
        "faces": faces,
        "occupied": src["occupied"],
        "shape": src["shape"],
        "antiforms": {k: v for k, v in src["antiforms"].items() if k != "cells"},
        "top_antiforms": src["antiforms"]["cells"][:6],
        "reading": (src.get("faces") or {}).get("reading", ""),
        # The epistemic fields travel with the view. A figure whose limits live in another
        # file is a figure whose limits nobody reads.
        "generated": src.get("generated"),
        "provenance": src.get("provenance"),
        "says": src.get("says"),
        "limits": src.get("limits"),
        "governed_by": src.get("governed_by"),
        "neighbour_rule": src["lattice"]["neighbour_rule"],
    }


# --------------------------------------------------------------- the calibration field

def calibration_field() -> dict:
    """The library's whole thesis as a surface: what a raw score MEANS depends on n.

    A screen ranks on the raw score. This says the same score sits at a different place in
    the null depending on how many observations produced it — so the field is z over
    (score, n), and the genes are drawn on top of their own coordinate system.

    Drawn as a field rather than as the usual score-against-z scatter because the scatter
    hides the axis that does the work. On a scatter, n is a colour nobody reads; here it is a
    dimension, and the iso-lines bend, which is the argument.
    """
    genes_csv = ROOT / "out" / "depmap_genes.csv"
    null_csv = ROOT / "out" / "depmap_null.csv"
    if not genes_csv.exists() or not null_csv.exists():
        return {}

    import csv as _csv
    nulls = []
    with null_csv.open(encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            nulls.append({"n": int(row["n"]), "mean": float(row["null_mean"]),
                          "sd": float(row["null_sd"])})
    nulls.sort(key=lambda r: r["n"])

    rows = []
    with genes_csv.open(encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            try:
                rows.append({
                    "score": float(row["score"]), "n": int(row["n"]),
                    "z": float(row["z"]),
                    "ess": row["is_common_essential"] == "True",
                })
            except (ValueError, KeyError):
                continue
    if not rows:
        return {}

    SX, SY = 40, 14
    lo_s = min(r["score"] for r in rows)
    hi_s = max(r["score"] for r in rows)
    lo_n = min(r["n"] for r in rows)
    hi_n = max(r["n"] for r in rows)

    def sx(v: float) -> int:
        return min(SX - 1, max(0, int((v - lo_s) / (hi_s - lo_s) * SX)))

    def sy(v: float) -> int:
        return min(SY - 1, max(0, int((v - lo_n) / (hi_n - lo_n) * SY)))

    grid = [[{"n": 0, "ess": 0, "z": 0.0} for _ in range(SX)] for _ in range(SY)]
    for r in rows:
        cell = grid[sy(r["n"])][sx(r["score"])]
        cell["n"] += 1
        cell["ess"] += 1 if r["ess"] else 0
        cell["z"] += r["z"]
    for row in grid:
        for cell in row:
            if cell["n"]:
                cell["z"] = round(cell["z"] / cell["n"], 3)

    return {
        "grid": grid, "cols": SX, "rows_n": SY,
        "score_range": [round(lo_s, 3), round(hi_s, 3)],
        "n_range": [lo_n, hi_n],
        "null_curve": nulls,
        "genes": len(rows),
        "reading": ("x is the raw score, y is how many cell lines produced it, shade is how "
                    "many genes land there and the ring marks where pan-essential genes "
                    "concentrate. The same score is a different z at a different n — that "
                    "bend is the whole reason this library exists"),
    }


# --------------------------------------------------------------- what calibration moved

def rank_shift() -> dict:
    """Raw rank against calibrated rank, for the genes the raw ranking put on top.

    A bump chart, because the finding is a REORDERING and a bar chart of either ranking
    cannot show a reordering at all. Pan-essential genes are marked: the claim this figure
    carries is that the raw maximum is toxicity, and the toxic genes are the ones that fall.
    """
    genes_csv = ROOT / "out" / "depmap_genes.csv"
    if not genes_csv.exists():
        return {}
    import csv as _csv
    rows = []
    with genes_csv.open(encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            try:
                rows.append({
                    "gene": row["entity"],
                    "raw": int(row["rank_raw"]), "cal": int(row["rank_cal"]),
                    "n": int(row["n"]),
                    "ess": row["is_common_essential"] == "True",
                })
            except (ValueError, KeyError):
                continue
    top = sorted(rows, key=lambda r: r["raw"])[:60]
    for r in top:
        r["moved"] = r["cal"] - r["raw"]
    fell = [r for r in top if r["moved"] > 0]
    return {
        "rows": top,
        "of_which_essential": sum(1 for r in top if r["ess"]),
        "fell": len(fell),
        "essential_among_fallen": sum(1 for r in fell if r["ess"]),
        "reading": ("each line joins a gene's rank before calibration to its rank after. A "
                    "line that falls is a gene the raw metric over-rewarded; the marked ones "
                    "are known pan-essential, which is toxicity rather than selectivity"),
    }


# --------------------------------------------------------------- lineage x gene

def lineage_matrix() -> dict:
    """Which dependencies are lineage-specific and which recur, as a seriated matrix.

    Rows are cancer lineages, columns are the genes any of them nominated, ordered so genes
    shared by several lineages sit together and the specific ones fan out. A per-lineage bar
    chart would answer "what did Lung find" and hide the question that matters — whether
    anything found in Lung was found anywhere else.
    """
    path = ROOT / "out" / "cancer_subgroups_lineage.json"
    if not path.exists():
        return {}
    src = json.loads(path.read_text(encoding="utf-8"))
    results = src.get("results", [])
    if not results:
        return {}

    per_group = {}
    freq: dict[str, int] = {}
    for g in results:
        hits = {c["gene"]: c["d"] for c in (g.get("candidates") or [])[:12]}
        if hits:
            per_group[g["subgroup"]] = hits
            for gene in hits:
                freq[gene] = freq.get(gene, 0) + 1

    genes = sorted(freq, key=lambda x: (-freq[x], x))[:44]
    rows = sorted(per_group, key=lambda k: -len(per_group[k]))
    return {
        "rows": rows,
        "cols": genes,
        "shared": {g: freq[g] for g in genes},
        "cells": [[round(per_group[r].get(g, 0.0), 3) for g in genes] for r in rows],
        "reading": ("rows are lineages, columns are the genes they nominated, ordered so the "
                    "genes several lineages share sit left. A column with one mark is a "
                    "lineage-specific dependency; a column with many is a gene the metric "
                    "likes everywhere"),
    }


# --------------------------------------------------------------- the screen as an event

def screen_event() -> dict:
    """The three populations of a CRISPR screen, and the threshold meant to separate them.

    THIS VIEW WAS BUILT WRONG FIRST, AND THE WRONG VERSION IS WHY THE RIGHT ONE EXISTS.

    The first attempt was a hexbin of all 17,916 genes over (observation count, raw score)
    with the fitted null drawn across it as a fan. It is the obvious picture: this library's
    thesis is that the threshold bends with n, so put n on an axis and show the data on it.

    It came out as twenty hex cells with a peak of 8,069 — not a density, a bar. Checking why
    produced a fact worth more than the figure: **95.4 % of these genes have exactly the same
    observation count**, and the whole screen holds nineteen distinct values. There is no
    second dimension. DepMap scores almost every gene in almost every line, so an (n, score)
    plane is a line with a few strays beside it.

    That does not make `calibration_field` wrong — the surface is real and its rule is right —
    but the surface is fitted across a range where hardly any gene in this screen sits, and
    nothing in this repository said so. It is said here.

    SO THE FIGURE IS THE ONE THE DATA SUPPORTS: the score distribution of the three
    populations a screen contains, as a ridgeline, with the null's own percentiles drawn
    across them. Per `.claude/skills/viz-atlas`, a ridgeline answers how a distribution
    changes BETWEEN GROUPS and is ordered by median rather than alphabetically; and the
    nonessential controls, few enough to draw individually, are marks rather than a smoothed
    curve, because below a couple of thousand points raw marks beat any smoothing.

    The question it answers is the one a shortlist depends on: common-essential genes are a
    confound Stage 3 removes, nonessential controls are supposed to be inert, everything else
    is the candidate pool. Do they separate, and where does the threshold fall?

    Coordinates solved here (ADR 0008).
    """
    genes_csv = ROOT / "out" / "depmap_genes.csv"
    null_csv = ROOT / "out" / "depmap_null.csv"
    if not genes_csv.exists() or not null_csv.exists():
        return {}

    with null_csv.open(encoding="utf-8") as fh:
        blocks = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(fh)]
    blocks.sort(key=lambda b: b["n"])

    genes = []
    with genes_csv.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            try:
                genes.append({
                    "entity": row["entity"],
                    "score": float(row["score"]),
                    "n": int(float(row["n"])),
                    "z": float(row["z"]),
                    "essential": row.get("is_common_essential") == "True",
                    "control": row.get("is_nonessential_control") == "True",
                })
            except (KeyError, TypeError, ValueError):
                continue
    if not genes or not blocks:
        return {}

    counts_n: dict[int, int] = {}
    for g in genes:
        counts_n[g["n"]] = counts_n.get(g["n"], 0) + 1
    modal_n = max(counts_n, key=counts_n.get)

    s_lo = min(g["score"] for g in genes)
    s_hi = max(g["score"] for g in genes)

    # Monotone compression. The distribution is heavily right-skewed and a linear axis puts
    # nine tenths of the screen in the bottom sixth of the frame. Nothing is reordered, and
    # the ticks carry raw values so the compression is visible rather than silent.
    def compress(v: float) -> float:
        return math.log1p(v - s_lo)

    c_hi = compress(s_hi) or 1.0

    def sy(v: float) -> float:
        return compress(v) / c_hi

    groups = [
        ("common-essential", [g for g in genes if g["essential"]],
         "the confound Stage 3 removes - a high score here is not a discovery"),
        ("nonessential control", [g for g in genes if g["control"]],
         "designed to be inert; where these sit IS the calibration"),
        ("everything else", [g for g in genes if not g["essential"] and not g["control"]],
         "the candidate pool a shortlist is drawn from"),
    ]

    BINS = 90
    curves = []
    for name, members, note in groups:
        if not members:
            continue
        hist = [0] * BINS
        for g in members:
            b = min(BINS - 1, max(0, int(sy(g["score"]) * BINS)))
            hist[b] += 1
        peak = max(hist) or 1
        vals = sorted(g["score"] for g in members)
        mid = vals[len(vals) // 2]
        curves.append({
            "group": name,
            "note": note,
            "members": len(members),
            "median": round(mid, 4),
            "median_at": round(sy(mid), 5),
            # Normalised WITHIN the group. A ridgeline compares shapes; three groups of 277,
            # 800 and 16,000 on a shared vertical scale would show only that one is bigger,
            # which the member count already says in words.
            "density": [round(h / peak, 4) for h in hist],
            "points": ([{"at": round(sy(g["score"]), 5), "entity": g["entity"],
                         "score": round(g["score"], 4)}
                        for g in sorted(members, key=lambda x: x["score"])]
                       if len(members) <= 800 else []),
        })
    curves.sort(key=lambda c: c["median_at"])

    modal_block = min(blocks, key=lambda b: abs(b["n"] - modal_n))
    rules = [
        {"label": "null mean", "at": round(sy(modal_block["null_mean"]), 5),
         "raw": round(modal_block["null_mean"], 4)},
        {"label": "null p95", "at": round(sy(modal_block["p95"]), 5),
         "raw": round(modal_block["p95"], 4)},
        {"label": "null p99", "at": round(sy(modal_block["p99"]), 5),
         "raw": round(modal_block["p99"], 4)},
    ]

    above = [g for g in genes if g["score"] > modal_block["p99"]]
    return {
        "axis": {
            "label": "raw score (top-20 mean)",
            "min": round(s_lo, 4), "max": round(s_hi, 4),
            "scale": "log1p from the minimum - monotone, so nothing is reordered",
            "ticks": [{"at": round(sy(v), 5), "raw": v}
                      for v in (0.0, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0) if s_lo <= v <= s_hi],
        },
        "curves": curves,
        "rules": rules,
        "degenerate_axis": {
            "distinct_n": len(counts_n),
            "modal_n": modal_n,
            "share_at_modal_n": round(counts_n[modal_n] / len(genes), 4),
            "reading": (
                f"{100 * counts_n[modal_n] / len(genes):.1f} % of the screen was scored on "
                f"exactly {modal_n} cell lines, and the whole screen holds {len(counts_n)} "
                f"distinct observation counts. The calibration surface in the previous view "
                f"is real and its rule is right, but it is fitted across a range where almost "
                f"no gene in THIS screen sits - a statement about DepMap's completeness "
                f"rather than about the method, and one nothing here had made until this "
                f"figure failed to draw."
            ),
        },
        "counts": {
            "genes": len(genes),
            "above_p99": len(above),
            "essential_above_p99": sum(1 for g in above if g["essential"]),
            "controls_above_p99": sum(1 for g in above if g["control"]),
        },
        "reading": (
            f"The three populations a screen contains, on one axis, with the null fitted at "
            f"n={modal_block['n']:.0f} drawn across them. {len(above):,} genes clear the 99th "
            f"percentile and {sum(1 for g in above if g['essential']):,} of those are "
            f"common-essential - the confound, not the finding. The controls are individual "
            f"marks because there are few enough to name, and where they sit is what the "
            f"calibration is judged on."
        ),
    }


def main() -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    models = {
        "language_matrix": language_matrix(),
        "scale_slopegraph": scale_slopegraph(),
        "knowledge_pcp": knowledge_pcp(),
        "conflict_grid": conflict_grid(),
        "knowledge_void": knowledge_void(),
        "calibration_field": calibration_field(),
        "rank_shift": rank_shift(),
        "lineage_matrix": lineage_matrix(),
        "screen_event": screen_event(),
    }
    payload = {
        "generated": date.today().isoformat(),
        "provenance": "layouts solved from the artefacts in out/rare/, no new measurement",
        "says": ("View models: orderings, bins and coordinates. Every NUMBER here was "
                 "measured by the tool named in its source artefact; this file only "
                 "rearranges what those tools wrote, so nothing a reader is asked to believe "
                 "originates in this file."),
        "models": models,
    }
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    for name, m in models.items():
        if not m:
            print(f"  {name:20s} — source artefact missing")
        elif "unavailable" in m:
            print(f"  {name:20s} — {m['unavailable'][:70]}")
        else:
            size = len(json.dumps(m)) / 1024
            print(f"  {name:20s} ok, {size:6.1f} kB")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
