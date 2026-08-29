#!/usr/bin/env python
"""The shape of the occupied space, and the shape of the hole.

WHY THIS FILE. `tools/knowledge_shape.py` asked whether what is known about a disease is
concentrated on one axis. It answered no, and the answer was mostly arithmetic. This asks the
harder and stranger question, and it is the one the project's own thesis keeps pointing at:

    Of all the ways a disease COULD be known — every combination of genetics, phenotype,
    cellular, natural history and population depth — how many actually occur? And of the
    combinations that do not occur, which ones are ABSENT rather than merely rare?

Every atlas in this field renders what exists and lets the rest disappear. Here the void is
the object. Three things are measured about it:

  **The occupied shape.** Cut each of the five axes into `BINS_PER_AXIS` bands and the space
  has `BINS_PER_AXIS ** 5` cells. Count how many hold at least one disease. The fraction that
  do is the *filling* of the space, and against an independence null it says whether the
  emptiness is structural or a consequence of the marginals.

  **The frontier.** An occupied cell with at least one empty neighbour sits on the edge of
  what is known. Cells whose neighbours are all occupied are interior. The ratio of the two is
  a shape statistic: a compact blob has few frontier cells for its volume, a thin filament is
  nearly all frontier.

  **The anti-forms.** The interesting empty cells are not the ones nobody expected. They are
  the cells where the five marginals, taken independently, predict a substantial number of
  diseases and the observed count is ZERO. Those are combinations of knowledge that the
  catalogue's own distributions say should be common, and are not there at all. Each one is a
  statement of the form: *no rare disease is known this way.*

## The neighbour rule, and why it is stated

Two cells are neighbours when they differ by exactly one band on exactly one axis — the 5-D
generalisation of edge adjacency, ten neighbours per interior cell. Diagonal adjacency is
excluded: two cells that differ on three axes are not "next to" each other in any sense a
reader would accept, and admitting them would make almost everything a frontier.

## What this cannot say

That an absent combination is impossible. A cell can be empty because the biology forbids it,
because nobody has looked, or because the axis is a proxy that cannot express it — and this
measurement cannot tell those apart. It can only say the combination is missing and how
surprising that is. **The distinction is exactly the atlas's own taxonomy of gaps, and this
file locates the cells without classifying them.**

    python tools/knowledge_void.py

Stdlib only.
"""

from __future__ import annotations

import argparse
import collections
import itertools
import json
import math
import pathlib
import random
import sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

RARE = ROOT / "out" / "rare"
DEST = RARE / "knowledge_void.json"

#: Bands per axis. Five axes at 4 bands is 1,024 cells against 12,994 diseases — about
#: thirteen per cell if they spread evenly, which is enough that an empty cell means
#: something. Registered as BINS_PER_AXIS. Finer bands would make emptiness trivial.
BINS_PER_AXIS = 4

#: An empty cell is an ANTI-FORM when independence predicts at least this many diseases in
#: it. Below that, absence is unremarkable. Registered as ANTIFORM_EXPECTED.
ANTIFORM_EXPECTED = 5.0

#: Draws behind the independence null for the filling statistic.
VOID_PERMUTATIONS = 200

SEED = 20260829


def load_vectors() -> tuple[list[str], list[tuple[float, ...]]]:
    path = RARE / "knowledge_shape.json"
    if not path.exists():
        return [], []
    src = json.loads(path.read_text(encoding="utf-8"))
    axes = list((src.get("axes") or {}).keys())
    rows = src.get("diseases") or []
    if not axes or not rows:
        return axes, []
    return axes, [tuple(r["vector"][a] for a in axes) for r in rows]


def band(v: float) -> int:
    return min(BINS_PER_AXIS - 1, max(0, int(v * BINS_PER_AXIS)))


def occupancy(vectors) -> collections.Counter:
    cells: collections.Counter = collections.Counter()
    for vec in vectors:
        cells[tuple(band(v) for v in vec)] += 1
    return cells


def neighbours(cell: tuple[int, ...]):
    """Differ by one band on exactly one axis. Diagonals excluded, deliberately."""
    for i, b in enumerate(cell):
        for step in (-1, 1):
            nb = b + step
            if 0 <= nb < BINS_PER_AXIS:
                yield cell[:i] + (nb,) + cell[i + 1:]


def main() -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    rng = random.Random(SEED)

    axes, vectors = load_vectors()
    if not vectors:
        print("  knowledge_shape.json has no per-disease vectors — run tools/knowledge_shape.py")
        return 1

    total_cells = BINS_PER_AXIS ** len(axes)
    cells = occupancy(vectors)
    filled = len(cells)
    print(f"  {len(vectors)} diseases, {len(axes)} axes, {total_cells} cells")
    print(f"  {filled} cells occupied ({100 * filled / total_cells:.1f} %)")

    # --- is the emptiness structural? ---------------------------------------------------
    # Shuffle each axis independently across diseases: the marginals survive, the
    # co-occurrence does not. If the real space is EMPTIER than that, the axes are entangled
    # and the void has structure. If it is fuller, the axes are more independent than they
    # look, which would be its own finding.
    columns = [[vec[i] for vec in vectors] for i in range(len(axes))]
    null_filled = []
    for _ in range(VOID_PERMUTATIONS):
        shuffled = []
        for col in columns:
            c = col[:]
            rng.shuffle(c)
            shuffled.append(c)
        seen = set()
        for j in range(len(vectors)):
            seen.add(tuple(band(shuffled[i][j]) for i in range(len(axes))))
        null_filled.append(len(seen))
    null_mean = sum(null_filled) / len(null_filled)
    null_sd = (sum((x - null_mean) ** 2 for x in null_filled) / max(len(null_filled) - 1, 1)) ** 0.5
    z = (filled - null_mean) / null_sd if null_sd else None

    # --- an interval on every headline ---------------------------------------------------
    # docs/references/standards.md 4 (GUM) asks for an uncertainty on any published number,
    # and the first version of this file shipped three headlines with none. The unit that
    # could have been sampled differently is the DISEASE, so the resample is over diseases
    # and the three counts are recomputed on each draw. A count of occupied cells is biased
    # downward by resampling with replacement — a draw holds ~63% of the distinct diseases —
    # so the interval is reported as the point plus the bootstrap's own spread rather than
    # as raw percentiles, the same correction scale_information needed for the same reason.
    # Its own generator. Sharing `rng` with the permutation null couples an added statistic
    # to an existing published one — it moved knowledge_shape's z from -19.0 to -20.37 in
    # exactly that way, and verify_claims caught it. Every statistic gets its own stream.
    boot_rng = random.Random(SEED + 1)

    def resample_counts(draws: int = 120):
        occ, front, anti = [], [], []
        for _ in range(draws):
            sample = [vectors[boot_rng.randrange(len(vectors))] for _ in range(len(vectors))]
            c = occupancy(sample)
            occ.append(len(c))
            front.append(sum(1 for x in c if any(nb not in c for nb in neighbours(x))))
            marg = []
            for i in range(len(axes)):
                cnt = collections.Counter(band(v[i]) for v in sample)
                marg.append([cnt.get(b, 0) / len(sample) for b in range(BINS_PER_AXIS)])
            n_anti = 0
            for cell in itertools.product(range(BINS_PER_AXIS), repeat=len(axes)):
                if cell in c:
                    continue
                p_ = 1.0
                for i, b in enumerate(cell):
                    p_ *= marg[i][b]
                if p_ * len(sample) >= ANTIFORM_EXPECTED:
                    n_anti += 1
            anti.append(n_anti)
        return occ, front, anti

    def spread(vals: list[float]) -> float:
        m = sum(vals) / len(vals)
        return (sum((x - m) ** 2 for x in vals) / max(len(vals) - 1, 1)) ** 0.5

    boot_occ, boot_front, boot_anti = resample_counts()

    # --- the shape of what is occupied ---------------------------------------------------
    frontier = [c for c in cells if any(nb not in cells for nb in neighbours(c))]
    interior = filled - len(frontier)

    # --- the anti-forms ------------------------------------------------------------------
    # Independence expectation per cell, from the observed marginals of each axis.
    marginals = []
    for i in range(len(axes)):
        counts = collections.Counter(band(vec[i]) for vec in vectors)
        marginals.append([counts.get(b, 0) / len(vectors) for b in range(BINS_PER_AXIS)])

    antiforms = []
    for cell in itertools.product(range(BINS_PER_AXIS), repeat=len(axes)):
        if cell in cells:
            continue
        p = 1.0
        for i, b in enumerate(cell):
            p *= marginals[i][b]
        expected = p * len(vectors)
        if expected >= ANTIFORM_EXPECTED:
            antiforms.append({
                "cell": list(cell),
                "expected": round(expected, 2),
                "reads_as": {axes[i]: ["lowest", "low", "high", "highest"][b]
                             for i, b in enumerate(cell)},
            })
    antiforms.sort(key=lambda a: -a["expected"])

    # The densest occupied cells, for contrast: what the catalogue actually looks like.
    densest = [{"cell": list(c), "diseases": n,
                "reads_as": {axes[i]: ["lowest", "low", "high", "highest"][b]
                             for i, b in enumerate(c)}}
               for c, n in cells.most_common(8)]

    # --- the projection a reader can actually look at -------------------------------------
    # Five axes cannot be drawn. Ten pairwise faces can, and each face is a 4x4 grid whose
    # cells carry two counts: how many diseases sit above it, and how many of the 5-D
    # ANTI-FORM cells lie in the fibre over it. A face where the diseases hug the diagonal
    # and the anti-forms fill the corners is the entanglement, drawn.
    antiform_set = {tuple(a["cell"]) for a in antiforms}
    faces = []
    for i, j in itertools.combinations(range(len(axes)), 2):
        grid = [[{"n": 0, "anti": 0} for _ in range(BINS_PER_AXIS)]
                for _ in range(BINS_PER_AXIS)]
        for cell, n in cells.items():
            grid[cell[i]][cell[j]]["n"] += n
        for cell in antiform_set:
            grid[cell[i]][cell[j]]["anti"] += 1
        faces.append({"x": axes[i], "y": axes[j], "grid": grid})

    payload = {
        "generated": date.today().isoformat(),
        "provenance": "derived from out/rare/knowledge_shape.json per-disease vectors",
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md",
        "question": ("Of all the ways a rare disease could be known, how many occur — and "
                     "which absent combinations does the catalogue's own distribution say "
                     "should have been common?"),
        "lattice": {
            "axes": axes, "bins_per_axis": BINS_PER_AXIS, "cells": total_cells,
            "diseases": len(vectors),
            "neighbour_rule": ("differ by one band on exactly one axis; diagonals excluded "
                               "because two cells differing on three axes are not adjacent "
                               "in any sense a reader would accept"),
        },
        "occupied": {
            "cells": filled,
            "share": round(filled / total_cells, 4),
            "null_mean": round(null_mean, 1),
            "null_sd": round(null_sd, 2),
            "z_vs_null": round(z, 2) if z is not None else None,
            "se": round(spread(boot_occ), 1),
            "ci95": [round(filled - 1.96 * spread(boot_occ), 1),
                     round(filled + 1.96 * spread(boot_occ), 1)],
            "interval": ("point +- 1.96 SE from a 120-draw bootstrap over diseases; the "
                         "bootstrap gives the DISPERSION only, because a count of distinct "
                         "occupied cells is biased downward when a draw holds only ~63% of "
                         "the distinct diseases"),
            "reading": ("the null shuffles each axis independently, so the marginals survive "
                        "and the entanglement does not. Fewer cells than the null means the "
                        "void has structure the marginals do not explain"),
        },
        "shape": {
            "frontier_cells": len(frontier),
            "interior_cells": interior,
            "frontier_share": round(len(frontier) / filled, 4) if filled else None,
            "frontier_se": round(spread(boot_front), 1),
            "frontier_ci95": [round(len(frontier) - 1.96 * spread(boot_front), 1),
                              round(len(frontier) + 1.96 * spread(boot_front), 1)],
            "reading": ("an occupied cell with at least one empty neighbour is on the edge of "
                        "what is known. A compact region has few frontier cells for its "
                        "volume; a filament is nearly all frontier"),
        },
        "antiforms": {
            "threshold_expected": ANTIFORM_EXPECTED,
            "count": len(antiforms),
            "count_se": round(spread(boot_anti), 1),
            "count_ci95": [round(len(antiforms) - 1.96 * spread(boot_anti), 1),
                           round(len(antiforms) + 1.96 * spread(boot_anti), 1)],
            "diseases_expected_in_them": round(sum(a["expected"] for a in antiforms), 1),
            "cells": antiforms[:40],
            "reading": ("empty cells where the five marginals, taken independently, predict "
                        f"at least {ANTIFORM_EXPECTED:.0f} diseases. Each one is a way of "
                        "knowing a disease that the catalogue's own distributions say should "
                        "be common, and that nothing occupies"),
        },
        "densest": densest,
        "faces": {
            "reading": ("ten pairwise faces of the five-dimensional lattice. Each 4x4 cell "
                        "carries the diseases sitting above it and the number of anti-form "
                        "cells in the fibre over it — so the occupied shape and the "
                        "structured void appear in the same figure"),
            "bins": BINS_PER_AXIS,
            "items": faces,
        },
        "says": ("Locates absent combinations; it does NOT classify why they are absent. A "
                 "cell can be empty because the biology forbids it, because nobody looked, or "
                 "because a proxy axis cannot express it, and this measurement cannot tell "
                 "those apart. That distinction is the atlas's own gap taxonomy and it is not "
                 "computed here."),
        "limits": [
            "Bands are quartiles of a RANK, so an axis with many ties spreads unevenly and a "
            "cell can be empty for a reason that is entirely about the ranking.",
            "Independence is a weak expectation. The axes are known to be entangled — the "
            "same measurement reports it above — so 'expected under independence' overstates "
            "how surprising some absences are.",
            f"{BINS_PER_AXIS} bands per axis is a choice: finer bands make emptiness trivial "
            "and coarser bands make it invisible.",
        ],
    }
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"  null fills {null_mean:.0f} cells (z = {z:.1f})" if z is not None else "")
    print(f"  frontier {len(frontier)} of {filled} occupied "
          f"({100 * len(frontier) / filled:.0f} %), interior {interior}")
    print(f"  {len(antiforms)} anti-forms — empty cells where independence expects "
          f">= {ANTIFORM_EXPECTED:.0f} diseases, {sum(a['expected'] for a in antiforms):.0f} in total")
    for a in antiforms[:5]:
        reads = ", ".join(f"{k} {v}" for k, v in a["reads_as"].items())
        print(f"    expected {a['expected']:6.1f}  {reads}")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
