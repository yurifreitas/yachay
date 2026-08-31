#!/usr/bin/env python
"""Where three clustering algorithms disagree, gene by gene — matched, not eyeballed.

WHAT THIS IS FOR. `community_stability.py` measured that Louvain and Leiden agree at ARI 0.870
and that either agrees with label propagation at **0.29**. That number says the objective
function decides most of the partition. It does not say *which* genes move, *where* they go, or
whether the disagreement is one big split or three thousand small ones — and those are
different findings with different consequences for anyone using the communities.

## The problem that makes this hard, and the algorithm that solves it

Community labels are arbitrary. Louvain's community 7 and Leiden's community 42 may be the same
group of genes; nothing in either output says so. Comparing partitions therefore needs the
communities MATCHED first, and matching them greedily — take the best overlap, remove it,
repeat — is the obvious approach and is wrong: an early greedy choice can force every later one
into a worse pairing.

This is an **assignment problem**, and it has an exact solution. `scipy.optimize.
linear_sum_assignment` (Jonker–Volgenant) finds the matching that maximises total overlap in
polynomial time, over the full cost matrix of every community in A against every community in
B. Optimal, not heuristic, and it costs three lines.

## The form: parallel sets, drawn as ribbons

Three vertical axes, one per algorithm, each divided into its communities. A ribbon carries the
genes that go from a community on the left to a community on the right, and its thickness is
how many. It is the alluvial diagram of Sankey's family, and it is the form for this question
because the question is *flow between categorisations* — which is precisely what a bar chart
of ARI values cannot show.

**What it will look like, and why that is the point.** Louvain to Leiden should be mostly
straight ribbons. Leiden to label propagation should be a braid. The reader sees the 0.29 as a
picture instead of taking it on faith.

## What is left out

Communities below `MIN_SHOW` genes. The graph has 216 of them and most are two or three genes;
drawing all of them makes a page of hairlines. They are counted in the payload as `other`, so
the ribbon widths still sum to the number of genes.

    python tools/partition_flow.py

Requires networkx, python-igraph, leidenalg, scipy, numpy — all declared.
"""

from __future__ import annotations

import collections
import importlib.util
import json
import pathlib
import sys

import numpy as np
from scipy.optimize import linear_sum_assignment

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "web" / "public" / "data" / "gene_network.json"
IDENTITY = ROOT / "out" / "rare" / "community_identity.json"
DEST = ROOT / "out" / "rare" / "partition_flow.json"

SEED = 20260830          # the same seed community_stability.py reports its partitions at

#: Communities smaller than this are pooled into one "other" band per algorithm. 216
#: communities of which most hold two genes would be 216 hairlines and no picture.
MIN_SHOW = 20


def load_stability():
    """Reuse the partitioners rather than writing a second copy of them.

    Two files that each build their own Leiden call are two files that will disagree about
    what the partition is the first time one of them changes a parameter. `community_stability`
    already owns `run_algorithms`, and it is imported here for exactly that reason.
    """
    spec = importlib.util.spec_from_file_location(
        "community_stability", ROOT / "tools" / "community_stability.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def matched_flow(a: np.ndarray, b: np.ndarray) -> dict:
    """Flows between two partitions, with their communities optimally matched first.

    The matching does not change any flow — every gene goes where it goes. It changes which
    community is drawn opposite which, and that is what turns a braid nobody can read into a
    picture where the disagreement is the part that crosses.
    """
    la, lb = sorted(set(a.tolist())), sorted(set(b.tolist()))
    ia = {c: i for i, c in enumerate(la)}
    ib = {c: i for i, c in enumerate(lb)}

    overlap = np.zeros((len(la), len(lb)), dtype=np.int64)
    for x, y in zip(a.tolist(), b.tolist()):
        overlap[ia[x], ib[y]] += 1

    # Maximise total overlap: the assignment routine minimises, so the cost is the negation.
    # Rectangular is fine - it pairs min(rows, cols) of them and leaves the rest unmatched,
    # which is the honest outcome when one algorithm finds more communities than the other.
    rows, cols = linear_sum_assignment(-overlap)
    pairing = {int(la[r]): int(lb[c]) for r, c in zip(rows, cols)}
    matched_genes = int(sum(overlap[r, c] for r, c in zip(rows, cols)))

    return {
        "pairs": pairing,
        "genes_in_matched_pairs": matched_genes,
        "share_matched": round(matched_genes / len(a), 4),
        "overlap": overlap,
        "labels": (la, lb),
    }


def band_of(labels: np.ndarray, keep: set) -> np.ndarray:
    """Community id, or -1 for the pooled `other` band."""
    return np.array([c if c in keep else -1 for c in labels.tolist()], dtype=np.int64)


def main() -> int:
    if not SRC.exists():
        print(f"missing {SRC}", file=sys.stderr)
        return 1

    cs = load_stability()
    g, names = cs.load_graph()
    keep = sorted(v for v in g.nodes() if g.degree(v) > 0)
    sub = g.subgraph(keep)
    n = sub.number_of_nodes()
    print(f"  {n} genes with at least one edge")

    parts = cs.run_algorithms(sub, seed=SEED)
    order = ["louvain", "leiden", "label_prop"]
    gene_names = [names[v] for v in sorted(sub.nodes())]

    # Which communities get their own band, per algorithm.
    bands = {}
    for name in order:
        sizes = collections.Counter(parts[name].tolist())
        big = {c for c, k in sizes.items() if k >= MIN_SHOW}
        bands[name] = {
            "kept": sorted(big),
            "labels": band_of(parts[name], big),
            "communities": len(sizes),
            "drawn": len(big),
            "in_other": int(sum(k for c, k in sizes.items() if c not in big)),
        }
        print(f"    {name:12s} {len(sizes):4d} communities, {len(big):3d} at "
              f"{MIN_SHOW}+ genes, {bands[name]['in_other']} pooled")

    # Identity, so a band can be labelled with what it IS rather than with a number. Only the
    # consensus partition has been characterised, so this is a best-effort join by majority
    # gene overlap - and it is reported as such rather than presented as the band's identity.
    identity = {}
    if IDENTITY.exists():
        ident = json.loads(IDENTITY.read_text(encoding="utf-8"))
        by_gene = {}
        for c in ident.get("communities", []):
            head = (c.get("headline") or {}).get("name")
            if head:
                for gname in c.get("examples", []):
                    by_gene[gname] = head
        for name in order:
            lbl = bands[name]["labels"]
            per = collections.defaultdict(collections.Counter)
            for i, c in enumerate(lbl.tolist()):
                hit = by_gene.get(gene_names[i])
                if hit:
                    per[c][hit] += 1
            identity[name] = {str(c): v.most_common(1)[0][0] for c, v in per.items() if v}

    flows, matches = [], {}
    for left, right in zip(order, order[1:]):
        m = matched_flow(bands[left]["labels"], bands[right]["labels"])
        matches[f"{left}->{right}"] = {
            "pairs": m["pairs"],
            "genes_in_matched_pairs": m["genes_in_matched_pairs"],
            "share_matched": m["share_matched"],
        }
        la, lb = m["labels"]
        ov = m["overlap"]
        for i, ca in enumerate(la):
            for j, cb in enumerate(lb):
                if ov[i, j] > 0:
                    flows.append({
                        "from": f"{left}:{ca}", "to": f"{right}:{cb}",
                        "genes": int(ov[i, j]),
                        # A ribbon is "kept" when it runs between two communities the
                        # assignment paired. Everything else is a gene the two algorithms put
                        # in different places, which is the whole subject of the figure.
                        "matched": bool(m["pairs"].get(int(ca)) == int(cb)),
                    })
        print(f"    {left} -> {right}: {m['share_matched'] * 100:.1f}% of genes stay in "
              f"matched communities")

    # ---- band order, so the ribbons can be read ------------------------------------------
    #
    #  A PARALLEL-SETS DIAGRAM IS UNREADABLE UNTIL THE BANDS ARE ORDERED, and the ordering is
    #  a layout problem with a standard answer: the barycentre heuristic from Sugiyama's
    #  layered graph drawing. Each band is placed at the weighted mean position of the bands
    #  it connects to on the axis before it, the axes are swept forward and back, and
    #  crossings fall out. It is a heuristic - minimising crossings exactly is NP-hard - so
    #  the number of crossings BEFORE and AFTER is reported rather than claimed to be optimal.
    #
    #  Solved here and not in the browser, per ADR 0008: a layout recomputed on every render
    #  is a layout that can differ between two readers looking at the same figure.
    axis_order = {name: list(range(len(bands[name]["kept"]) + 1)) for name in order}
    ids = {name: bands[name]["kept"] + [-1] for name in order}

    flow_by_pair = collections.defaultdict(int)
    for f in flows:
        la, ca = f["from"].split(":")
        lb, cb = f["to"].split(":")
        flow_by_pair[(la, int(ca), lb, int(cb))] += f["genes"]

    def crossings(left: str, right: str) -> int:
        """Pairs of ribbons that cross, counted directly. 115 ribbons is small enough."""
        pos_l = {c: i for i, c in enumerate(
            [ids[left][k] for k in axis_order[left]])}
        pos_r = {c: i for i, c in enumerate(
            [ids[right][k] for k in axis_order[right]])}
        es = [(pos_l[ca], pos_r[cb]) for (la, ca, lb, cb) in flow_by_pair
              if la == left and lb == right and ca in pos_l and cb in pos_r]
        return sum(1 for i, a in enumerate(es) for b in es[i + 1:]
                   if (a[0] - b[0]) * (a[1] - b[1]) < 0)

    before = sum(crossings(a, b) for a, b in zip(order, order[1:]))

    for sweep in range(6):
        pairs = list(zip(order, order[1:]))
        for left, right in (pairs if sweep % 2 == 0 else list(reversed(pairs))):
            fixed, moving = (left, right) if sweep % 2 == 0 else (right, left)
            pos_fixed = {c: i for i, c in enumerate(
                [ids[fixed][k] for k in axis_order[fixed]])}
            bary = {}
            for k, c in enumerate(ids[moving]):
                num = den = 0.0
                for (la, ca, lb, cb), w in flow_by_pair.items():
                    other = None
                    if la == moving and lb == fixed and ca == c:
                        other = cb
                    elif lb == moving and la == fixed and cb == c:
                        other = ca
                    if other is not None and other in pos_fixed:
                        num += w * pos_fixed[other]
                        den += w
                # A band with no flow to the fixed axis keeps its place rather than being
                # swept to the top by a default of zero.
                bary[k] = num / den if den else k
            axis_order[moving] = sorted(axis_order[moving], key=lambda k: (bary[k], k))

    after = sum(crossings(a, b) for a, b in zip(order, order[1:]))
    print(f"  ribbon crossings {before} -> {after} after {6} barycentre sweeps")

    payload = {
        "generated": "tools/partition_flow.py",
        "band_order": {
            "order": {name: [int(ids[name][k]) for k in axis_order[name]] for name in order},
            "crossings_before": before,
            "crossings_after": after,
            "method": ("barycentre sweeps (Sugiyama), six passes alternating direction. "
                       "Minimising crossings exactly is NP-hard, so both counts are published "
                       "rather than the result being called optimal."),
        },
        "governed_by": "docs/adr/0008 — the layout is solved here, the browser draws it",
        "question": ("community_stability.py measured that two algorithm families agree at "
                     "ARI 0.29. Which genes actually move, and where do they go?"),
        "method": (
            "Community labels are arbitrary, so the communities are MATCHED before anything "
            "is compared - scipy.optimize.linear_sum_assignment (Jonker-Volgenant) on the "
            "full overlap matrix, which is the exact solution to the assignment problem. "
            "Greedy best-overlap matching is the obvious alternative and it is wrong: one "
            "early choice can force every later pairing into a worse one. The matching moves "
            "no gene; it decides which community is drawn opposite which, which is what turns "
            "an unreadable braid into a picture where the crossings ARE the disagreement."),
        "form": ("parallel sets / alluvial. Three axes, one per algorithm, each divided into "
                 "its communities; a ribbon's thickness is how many genes take that path. The "
                 "form is chosen because the question is flow between categorisations, and no "
                 "bar chart of ARI values can show it."),
        "genes": n,
        "min_community_drawn": MIN_SHOW,
        "axes": [{"algorithm": name,
                  "communities": bands[name]["communities"],
                  "drawn": bands[name]["drawn"],
                  "pooled_into_other": bands[name]["in_other"],
                  "bands": [{"id": int(c),
                             "genes": int((bands[name]["labels"] == c).sum()),
                             "name": identity.get(name, {}).get(str(c))}
                            for c in bands[name]["kept"]]
                  + [{"id": -1,
                      "genes": bands[name]["in_other"],
                      "name": f"{bands[name]['communities'] - bands[name]['drawn']} "
                              f"communities under {MIN_SHOW} genes"}],
                  } for name in order],
        "flows": sorted(flows, key=lambda f: -f["genes"]),
        "matching": matches,
        "says": (
            "Louvain and Leiden keep %.0f%% of genes in matched communities; Leiden and label "
            "propagation keep %.0f%%. The ARI already said the two families disagree - this "
            "says the disagreement is not a handful of border cases but a wholesale "
            "re-partition, and it names the genes."
            % (matches["louvain->leiden"]["share_matched"] * 100,
               matches["leiden->label_prop"]["share_matched"] * 100)),
        "identity_is_best_effort": (
            "Band names are joined from community_identity.json by majority overlap with the "
            "CONSENSUS partition's characterised communities. Only that partition was "
            "characterised, so a name here says 'this band is mostly the group that was named "
            "X', not 'this band was tested and found to be X'."),
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"\n  {len(flows)} ribbons")
    print(f"wrote {DEST.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
