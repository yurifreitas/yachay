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

import argparse
import json
import math
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


def main() -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    models = {
        "language_matrix": language_matrix(),
        "scale_slopegraph": scale_slopegraph(),
        "knowledge_pcp": knowledge_pcp(),
        "conflict_grid": conflict_grid(),
        "knowledge_void": knowledge_void(),
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
