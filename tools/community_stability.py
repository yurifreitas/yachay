#!/usr/bin/env python
"""The published partition, held to the same standard as every other number here.

WHAT WAS PUBLISHED, AND WHAT WAS NEVER ASKED. `out/rare/gene_network.json` reports **2,408
communities at modularity 0.8605**, from one run of Louvain at one seed and one resolution.
Every other statistic in this repository carries a null and an interval. This one carried
neither, and three questions had never been put to it:

  1. **Is it stable?** Louvain is stochastic. A different seed gives a different partition,
     and nobody had run a second seed, let alone measured how far apart the answers land.
  2. **Is the resolution the right one?** Modularity has a resolution limit (Fortunato and
     Barthelemy 2007): at gamma = 1 it cannot resolve a community smaller than about
     sqrt(2m) edges, which on this graph is 278. Communities below that size are merged by
     the objective function, not by the biology. Nobody swept gamma.
  3. **Does the method matter?** If Louvain, Leiden, greedy modularity and label propagation
     return the same grouping, the grouping is in the graph. If they disagree, it is in the
     algorithm, and the published number is an opinion with a decimal point.

## What this measures

**Stability, as pairwise adjusted Rand index across seeds.** The ARI corrects for the
agreement two random partitions reach by chance, which matters enormously here: with 2,189
isolated genes each forming its own community, two arbitrary partitions already agree on most
pairs. Reported as a mean with a 95% interval over all seed pairs.

**Agreement between algorithms**, the same way. Leiden is included because it is the one with
a guarantee Louvain lacks — Traag, Waltman and van Eck (2019) showed Louvain can return
communities that are internally DISCONNECTED, and Leiden cannot. That defect was checked for
on this graph before the library was added and does not occur here, which is worth stating:
the reason to use Leiden is not that Louvain broke, it is that nothing had checked.

**A consensus partition with a per-gene confidence.** Over N runs, the fraction of runs in
which a gene lands with its eventual consensus partners. A gene at 1.0 is in the same group
every time; a gene at 0.4 is being assigned by the seed. That number is the interval this
artefact never had, one per gene, and it is what the site should show instead of a colour.

**A degree-preserving null**, as everywhere else here: the same pipeline on a rewired graph
that keeps every gene's degree. Modularity is not comparable across graphs, so the excess over
this null is the only comparable quantity.

    python tools/community_stability.py
    python tools/community_stability.py --seeds 20 --draws 20

Requires networkx, python-igraph, leidenalg, scikit-learn, numpy - all declared in
pyproject.toml. This is the first tool here to need a clustering library, and hand-rolling
one to preserve a stdlib streak would be the wrong kind of self-reliance, the same call
pyproject.toml already records for scipy.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import statistics
import sys
import time

import igraph as ig
import leidenalg
import networkx as nx
import numpy as np
from sklearn.metrics import adjusted_rand_score

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "web" / "public" / "data" / "gene_network.json"
DEST = ROOT / "out" / "rare" / "community_stability.json"

SEED = 20260830

#: Seeds per algorithm. Twenty pairs of twenty runs is 190 comparisons per algorithm, enough
#: for a stable interval on the mean ARI without turning the tool into a batch job.
SEEDS = 12

#: Resolutions to sweep. Centred on 1.0, the value that was published without being chosen.
RESOLUTIONS = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]

#: Degree-preserving rewirings behind the null.
NULL_DRAWS = 12


def load_graph() -> tuple[nx.Graph, list[str]]:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    nodes = d["nodes"]
    indptr, indices = d["indptr"], d["indices"]
    g = nx.Graph()
    g.add_nodes_from(range(len(nodes)))
    for i in range(len(nodes)):
        for j in indices[indptr[i]:indptr[i + 1]]:
            if j > i:
                g.add_edge(i, j)
    return g, nodes


def index_of(g: nx.Graph) -> dict:
    """Node label to position.

    THE TOOL USED TO ASSUME THESE WERE THE SAME THING, and on the graph it reads they are:
    `gene_network.json` stores a CSR structure, so its nodes are 0..n-1 by construction and
    every array could be indexed by node label directly. That assumption is invisible until
    the tool meets any other graph, and it met one the first time a test built a small
    example — an isolated node numbered 999 in a 49-node graph raised IndexError inside
    `labels_from`. Positions are computed here once and the rest of the file uses them.
    """
    return {v: i for i, v in enumerate(g.nodes())}


def labels_from(partition, n: int, index: dict | None = None) -> np.ndarray:
    """Community assignment as one label per node position, for the ARI."""
    out = np.full(n, -1, dtype=np.int64)
    for k, part in enumerate(partition):
        for v in part:
            out[index[v] if index else v] = k
    # An unassigned node would silently share the label -1 with every other unassigned node
    # and read as one enormous community. Every partitioner here covers the graph, so this is
    # a guard rather than a fix, and it fails loudly rather than quietly relabelling.
    if (out < 0).any():
        raise AssertionError("a partitioner left nodes unassigned")
    return out


def to_igraph(g: nx.Graph, index: dict) -> ig.Graph:
    return ig.Graph(n=g.number_of_nodes(),
                    edges=[(index[u], index[v]) for u, v in g.edges()])


def run_algorithms(g: nx.Graph, seed: int, resolution: float = 1.0) -> dict[str, np.ndarray]:
    """One partition per algorithm at this seed."""
    n = g.number_of_nodes()
    idx = index_of(g)
    out: dict[str, np.ndarray] = {}

    out["louvain"] = labels_from(
        nx.community.louvain_communities(g, seed=seed, resolution=resolution), n, idx)

    # Leiden, through igraph. RBConfiguration is modularity with an explicit resolution, so
    # the two are comparable at the same gamma - which is the whole point of including it.
    ige = to_igraph(g, idx)
    part = leidenalg.find_partition(
        ige, leidenalg.RBConfigurationVertexPartition,
        resolution_parameter=resolution, seed=seed, n_iterations=2)
    out["leiden"] = np.asarray(part.membership, dtype=np.int64)

    # Label propagation: near-linear, no objective function at all. It is here as the
    # DISAGREEING method - if it matched the modularity family, that would say the structure
    # is strong enough that the objective does not matter.
    out["label_prop"] = labels_from(
        nx.community.asyn_lpa_communities(g, seed=seed), n, idx)

    return out


def internally_disconnected(g: nx.Graph, labels: np.ndarray) -> dict:
    """The defect Leiden exists to prevent, counted rather than assumed.

    A community whose induced subgraph is not connected is not a community: it is two or more
    groups the objective function happened to score better together. Louvain can produce them;
    Leiden's guarantee is that it cannot.
    """
    pos = list(g.nodes())
    by = collections.defaultdict(list)
    for i, c in enumerate(labels):
        by[int(c)].append(pos[i])
    bad = pieces = members = 0
    for mem in by.values():
        if len(mem) < 2:
            continue
        sub = g.subgraph(mem)
        if not nx.is_connected(sub):
            bad += 1
            members += len(mem)
            pieces += nx.number_connected_components(sub)
    return {"communities": bad, "genes_in_them": members, "pieces_they_split_into": pieces}


def pairwise_ari(runs: list[np.ndarray]) -> dict:
    vals = [adjusted_rand_score(a, b)
            for i, a in enumerate(runs) for b in runs[i + 1:]]
    if not vals:
        return {}
    mean = statistics.fmean(vals)
    se = statistics.pstdev(vals) / (len(vals) ** 0.5) if len(vals) > 1 else 0.0
    return {
        "pairs": len(vals),
        "mean": round(mean, 4),
        "ci95": [round(mean - 1.96 * se, 4), round(mean + 1.96 * se, 4)],
        "min": round(min(vals), 4),
        "max": round(max(vals), 4),
    }


def consensus(runs: list[np.ndarray], g: nx.Graph, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """A consensus partition, and how firmly each gene belongs to its group.

    THE CO-ASSOCIATION IS BUILT ON EDGES, NOT ON ALL PAIRS. A dense 5,524 x 5,524 matrix is 30
    million entries to hold a number that can only be non-zero where the graph already has an
    edge for two nodes to be grouped through. Restricting it to the 38,746 edges is not an
    approximation of the usual construction, it is the same construction with the structural
    zeros left out.

    The consensus graph - edges weighted by how often the two ends were grouped together - is
    then partitioned once more. A gene's CONFIDENCE is the share of runs in which it sat with
    the partners the consensus finally gave it: 1.0 means the seed never mattered, 0.4 means
    the seed decided.
    """
    m = len(runs)
    idx = index_of(g)
    cg = nx.Graph()
    cg.add_nodes_from(g.nodes())
    for u, v in g.edges():
        w = sum(1 for r in runs if r[idx[u]] == r[idx[v]]) / m
        if w > 0:
            cg.add_edge(u, v, weight=w)

    final = labels_from(nx.community.louvain_communities(cg, seed=seed, weight="weight"),
                        g.number_of_nodes(), index_of(cg))

    by = collections.defaultdict(list)
    for i, c in enumerate(final):
        by[int(c)].append(i)

    conf = np.ones(g.number_of_nodes())
    for mem in by.values():
        if len(mem) < 2:
            # A singleton is not a confident assignment, it is the absence of one. Scoring it
            # 1.0 would have put 2,189 isolated genes at maximum confidence and lifted the
            # artefact's headline number by forty points.
            for v in mem:
                conf[v] = float("nan")
            continue
        arr = np.array(mem)
        for v in mem:
            same = sum(int((r[v] == r[arr]).mean()) if False else float((r[v] == r[arr]).mean())
                       for r in runs) / m
            # The gene itself is always in its own group; removing it keeps the number
            # honest for a two-member community, where it would otherwise never fall below
            # 0.5 whatever the runs did.
            conf[v] = (same * len(mem) - 1) / (len(mem) - 1)
    return final, conf


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seeds", type=int, default=SEEDS)
    ap.add_argument("--draws", type=int, default=NULL_DRAWS)
    args = ap.parse_args()

    if not SRC.exists():
        print(f"missing {SRC}", file=sys.stderr)
        return 1

    t0 = time.time()
    g, nodes = load_graph()
    n = g.number_of_nodes()
    m = g.number_of_edges()
    connected = [v for v in g.nodes() if g.degree(v) > 0]
    print(f"  graph {n} genes, {m} edges, {n - len(connected)} isolated")

    # THE RESOLUTION LIMIT, as a number rather than a citation. Modularity at gamma = 1 cannot
    # resolve a community joined to the rest by fewer than about sqrt(2m) edges.
    limit = (2 * m) ** 0.5

    seeds = [SEED + i for i in range(args.seeds)]
    by_alg: dict[str, list[np.ndarray]] = collections.defaultdict(list)
    for s in seeds:
        for name, lab in run_algorithms(g, s).items():
            by_alg[name].append(lab)
        print(f"    seed {s} done ({time.time() - t0:.0f}s)", end="\r")

    stability = {name: pairwise_ari(runs) for name, runs in by_alg.items()}
    counts = {name: [int(len(set(r.tolist()))) for r in runs] for name, runs in by_alg.items()}

    # Between algorithms, at a shared seed: the same question asked of the method rather than
    # of the randomness.
    cross = {}
    names = sorted(by_alg)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            vals = [adjusted_rand_score(x, y) for x, y in zip(by_alg[a], by_alg[b])]
            cross[f"{a} vs {b}"] = {
                "mean": round(statistics.fmean(vals), 4),
                "min": round(min(vals), 4),
                "max": round(max(vals), 4),
            }

    disconnected = {name: internally_disconnected(g, runs[0]) for name, runs in by_alg.items()}

    # The resolution sweep, on Leiden because it is the one with the connectivity guarantee.
    sweep = []
    for gamma in RESOLUTIONS:
        labs = [run_algorithms(g, SEED + i, gamma)["leiden"] for i in range(3)]
        sizes = collections.Counter(labs[0].tolist())
        big = [s for s in sizes.values() if s > 1]
        sweep.append({
            "resolution": gamma,
            "communities": len(sizes),
            "communities_above_one_gene": len(big),
            "largest": max(sizes.values()),
            "median_size_above_one": statistics.median(big) if big else 0,
            "modularity": round(float(nx.community.modularity(
                g, [{i for i, c in enumerate(labs[0]) if c == k} for k in set(labs[0].tolist())])), 4),
            "stability_ari": pairwise_ari(labs).get("mean"),
        })
        print(f"    gamma {gamma} done ({time.time() - t0:.0f}s)", end="\r")

    final, conf = consensus(by_alg["leiden"], g, SEED)
    scored = conf[~np.isnan(conf)]
    firm = float((scored >= 0.9).mean()) if scored.size else 0.0
    weak = float((scored < 0.5).mean()) if scored.size else 0.0

    # THE NULL. A degree-preserving rewiring, so the comparison is against a graph with the
    # same degree sequence and none of the biology. Modularity is not comparable across
    # graphs; the excess over this is.
    null_mod, null_stab = [], []
    for k in range(args.draws):
        rg = nx.expected_degree_graph([d for _, d in g.degree()], seed=SEED + 500 + k,
                                      selfloops=False)
        rg = nx.Graph(rg)
        ridx = index_of(rg)
        labs = [labels_from(nx.community.louvain_communities(rg, seed=SEED + j),
                            rg.number_of_nodes(), ridx)
                for j in range(3)]
        null_mod.append(float(nx.community.modularity(
            rg, [{i for i, c in enumerate(labs[0]) if c == kk} for kk in set(labs[0].tolist())])))
        null_stab.append(pairwise_ari(labs)["mean"])
        print(f"    null {k + 1}/{args.draws} ({time.time() - t0:.0f}s)", end="\r")

    real_mod = float(nx.community.modularity(
        g, [{i for i, c in enumerate(by_alg["louvain"][0]) if c == k}
            for k in set(by_alg["louvain"][0].tolist())]))

    payload = {
        "generated": "tools/community_stability.py",
        "governed_by": "docs/adr/0007 (a construct needs a null and an interval) and "
                       "docs/references/standards.md §4",
        "question": ("The site publishes 2,408 communities at modularity 0.8605 from one "
                     "Louvain run at one seed. Is that partition stable, is its resolution "
                     "chosen, and does the algorithm decide it?"),
        "libraries": {
            "why": ("This is the first tool here to take a clustering dependency. Hand-rolling "
                    "Leiden or an adjusted Rand index to preserve a stdlib streak would be the "
                    "wrong kind of self-reliance - the same call pyproject.toml already "
                    "records for scipy."),
            "networkx": nx.__version__,
            "igraph": ig.__version__,
            "leidenalg": leidenalg.version,
        },
        "graph": {"genes": n, "edges": m, "isolated": n - len(connected),
                  "connected": len(connected)},
        "what_was_published": {
            "communities": 2408,
            "modularity": 0.8605,
            "the_problem": ("2,189 of those 2,408 are single isolated genes. A count of "
                            "communities that is 91% singletons describes the ingestion, not "
                            "the biology; the connected part of this graph carries about 219."),
        },
        "resolution_limit": {
            "edges": m,
            "sqrt_2m": round(limit, 1),
            "says": ("Modularity at gamma = 1 cannot resolve a community joined to the rest "
                     "by fewer than about %d edges (Fortunato and Barthelemy 2007). Every "
                     "community below that size in the published partition was merged or "
                     "split by the objective function rather than found in the graph, and "
                     "the sweep below is what that costs." % round(limit)),
        },
        "stability_across_seeds": stability,
        "communities_per_run": {k: {"min": min(v), "max": max(v),
                                    "median": statistics.median(v)} for k, v in counts.items()},
        "agreement_between_algorithms": cross,
        "internally_disconnected": {
            "says": ("Traag, Waltman and van Eck (2019) showed Louvain can return communities "
                     "whose own subgraph is disconnected - not a community at all. Leiden "
                     "cannot. Checked here rather than assumed, and on this graph it does not "
                     "occur: the reason to use Leiden is that nothing had looked."),
            "by_algorithm": disconnected,
        },
        "resolution_sweep": sweep,
        "consensus": {
            "method": ("co-association over the %d Leiden runs, restricted to existing edges, "
                       "repartitioned; a gene's confidence is the share of runs in which it "
                       "sat with the partners the consensus gave it" % args.seeds),
            "genes_scored": int(scored.size),
            "not_scored_singletons": int(np.isnan(conf).sum()),
            "share_at_or_above_0.9": round(firm, 4),
            "share_below_0.5": round(weak, 4),
            "median_confidence": round(float(np.median(scored)), 4) if scored.size else None,
        },
        "null": {
            "method": "%d degree-preserving rewirings, Louvain on each" % args.draws,
            "modularity_real": round(real_mod, 4),
            "modularity_null_mean": round(statistics.fmean(null_mod), 4),
            "modularity_null_sd": round(statistics.pstdev(null_mod), 4),
            "stability_null_mean": round(statistics.fmean(null_stab), 4),
            "says": ("Absolute modularity is not comparable across graphs, so the excess over "
                     "a degree-matched rewiring is the only comparable quantity - and the "
                     "null's own STABILITY is the number that says whether an ARI of this "
                     "size means anything, because a rewired graph has no communities to find "
                     "and its runs still agree somewhat."),
        },
        "per_gene": {
            # The whole point of the artefact: one confidence per gene, so a page can stop
            # printing a community as a colour and start printing it as a claim with a number.
            "genes": [nodes[i] for i in range(n) if not np.isnan(conf[i])],
            "confidence": [round(float(conf[i]), 3) for i in range(n) if not np.isnan(conf[i])],
            "community": [int(final[i]) for i in range(n) if not np.isnan(conf[i])],
        },
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    print(f"\n  stability (mean pairwise ARI over {args.seeds} seeds):")
    for k, v in stability.items():
        print(f"    {k:12s} {v['mean']:.4f}  95% [{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}]  "
              f"range {v['min']:.3f}-{v['max']:.3f}")
    print("  between algorithms:")
    for k, v in cross.items():
        print(f"    {k:28s} {v['mean']:.4f}")
    print(f"  consensus: {payload['consensus']['share_at_or_above_0.9'] * 100:.1f}% of "
          f"{scored.size} scored genes at 0.9 or above, "
          f"{payload['consensus']['share_below_0.5'] * 100:.1f}% below 0.5")
    print(f"  modularity {real_mod:.4f} against a rewired null of "
          f"{statistics.fmean(null_mod):.4f}; the null's own stability is "
          f"{statistics.fmean(null_stab):.4f}")
    print(f"\nwrote {DEST.relative_to(ROOT).as_posix()}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
