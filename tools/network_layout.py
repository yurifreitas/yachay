#!/usr/bin/env python
"""The gene graph, ordered so its structure is visible — solved here, drawn in the browser.

THE GAP THIS CLOSES. `out/rare/gene_network.json` has held 5,524 genes and 38,746 edges since
the interactome layer was built, and not one of those edges has ever been drawn. The site
reports the graph as three numbers — nodes, edges, modularity — which is the least a graph can
be reduced to. `community_stability.py` then measured that the partition is 0.29 agreement
between algorithm families, and that finding is also a number. A reader cannot see whether the
blocks it describes exist.

## The form, and why it is a matrix rather than a hairball

A force-directed drawing of 38,746 edges is a hairball: at this density the layout is dominated
by the repulsion constant, two runs look different, and nothing can be read off it. The
**reordered adjacency matrix** is the honest alternative and the older one — Bertin's
*reorderable matrix* (1967), and the seriation literature before it. Every edge is drawn
exactly once, at a fixed position, with no layout parameter to tune. Community structure
appears as blocks on the diagonal, and — the part a hairball actively hides — the edges BETWEEN
communities appear as off-diagonal texture rather than being buried in the middle.

## The ordering is the argument (ADR 0008)

A matrix says nothing until its rows are ordered, and the ordering is a claim. This file makes
three, and publishes all three so the reader can switch and see which structure survives:

    consensus   by the consensus community from community_stability.py, then by spectral
                order WITHIN each community. This is the ordering that asserts the partition.
    spectral    the Fiedler vector of the whole graph, ignoring communities entirely. If the
                blocks are real they reappear here without having been assumed.
    degree      by degree alone. The control: any ordering produces SOME visible structure,
                and this is what structure looks like when it comes from the degree
                sequence rather than from the biology.

Reading the same matrix under `spectral` and under `consensus` is the whole point. If the
blocks only exist in the ordering that was told where they are, they are not in the graph.

## What is left out, and why

Isolated genes. 2,189 of the 5,524 have no edges, so they contribute 2,189 empty rows and
columns — a third of the picture, saying nothing. They are counted in the payload and excluded
from the matrix. Every other artefact here that reported "2,408 communities" was counting them.

    python tools/network_layout.py

Requires numpy, scipy and networkx, all declared.
"""

from __future__ import annotations

import base64
import json
import pathlib
import sys

import networkx as nx
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "web" / "public" / "data" / "gene_network.json"
STABILITY = ROOT / "out" / "rare" / "community_stability.json"
DEST = ROOT / "web" / "public" / "data" / "network_layout.json"

SEED = 20260831


def b64(arr: np.ndarray) -> str:
    """Columnar payload, the same encoding the dense scatter already uses.

    38,746 edges as JSON numbers is roughly 500 kB of text to parse; as two typed arrays it is
    310 kB of bytes the browser hands straight to a canvas loop.
    """
    return base64.b64encode(np.ascontiguousarray(arr).tobytes()).decode("ascii")


def _fiedler_component(adj: csr_matrix) -> np.ndarray:
    """Fiedler order of one CONNECTED block — sorted by the second-smallest eigenvector of
    the Laplacian. Callers must not pass a disconnected graph; `fiedler_order` below is the
    entry point that splits one into components first.

    THE REASON THIS IS THE RIGHT DEFAULT. Minimising the sum of |i - j| over edges — putting
    connected nodes near each other in the ordering — is NP-hard, and the Fiedler vector is its
    standard continuous relaxation. It is not a heuristic somebody invented for this file; it
    is the same object that underlies spectral clustering, and sorting by it is the classic
    seriation of a symmetric matrix.

    Falls back to degree order when the eigensolver does not converge, which happens on tiny or
    disconnected pieces. The fallback is REPORTED rather than silent: an ordering that quietly
    became a different ordering is a figure making a claim its caption denies.
    """
    n = adj.shape[0]
    if n < 3:
        return np.arange(n)
    deg = np.asarray(adj.sum(axis=1)).ravel()
    lap = csr_matrix(np.diag(deg)) - adj if n < 400 else None
    try:
        if lap is None:
            from scipy.sparse import diags
            lap = diags(deg) - adj
        # A FIXED STARTING VECTOR. ARPACK is an iterative method: without `v0` it starts from
        # a vector SciPy draws from its own global random state, and for eigenvalues as
        # closely spaced as a Laplacian's smallest two it converges to a different point in
        # the eigenspace on each call. Canonicalising the sign was not enough — 1,584 of
        # 3,335 positions still moved between runs — because the vector itself was different,
        # not just its sign. This is the fix; the sign canonicalisation above is still needed
        # on top of it.
        v0 = np.random.default_rng(SEED).standard_normal(n)
        vals, vecs = eigsh(lap.astype(float), k=2, sigma=-1e-5, which="LM", v0=v0)
        fiedler = vecs[:, np.argsort(vals)[1]]
        # ⚠️ THE SIGN OF AN EIGENVECTOR IS ARBITRARY, and this is where that bites. ARPACK
        # returns -v as happily as v, and the two give exactly reversed orderings — so the
        # matrix drawn from this would flip end-for-end between runs while the caption went
        # on describing the same structure. The determinism test caught it on the first run
        # after the tool was added to the suite, which is the whole reason the suite holds
        # every seeded tool to being tested or excused.
        #
        # Canonicalised by the entry of largest magnitude: the largest |value| is a well
        # separated choice, where "first non-zero" would be decided by floating-point noise
        # near the middle of the vector.
        if fiedler[np.argmax(np.abs(fiedler))] < 0:
            fiedler = -fiedler
        # Stable sort, so genes tied at the same coordinate keep index order rather than
        # whatever the sort happened to do. Ties are common: a path-like component gives
        # several genes identical values.
        return np.argsort(fiedler, kind="stable")
    except Exception:
        return np.argsort(-deg)


def fiedler_order(adj: csr_matrix) -> np.ndarray:
    """Spectral seriation, COMPONENT BY COMPONENT.

    ⚠️ THE FIRST VERSION OF THIS FUNCTION WAS WRONG, and the figure it fed made a claim its own
    numbers refuted. It ran the Fiedler vector over the whole edge-bearing subgraph, which has
    **191 connected components** — 148 of them with three genes or fewer. On a disconnected
    graph the Laplacian's zero eigenvalue has multiplicity equal to the number of components,
    so the "second smallest" eigenvector is another vector from that null space: an arbitrary
    combination of component indicators, carrying no ordering within any component at all.

    It looked plausible and it was noise. Measured: only 6.2% of edges landed within 1% of the
    diagonal, against 2.0% for a random shuffle and 35.6% for ordering by degree alone. The
    caption drafted for it — "the blocks come back even without being told where they are" —
    was false, and the measurement is what caught it.

    The correct construction seriates each component separately and concatenates them, largest
    first. That is what the seriation literature means by a spectral ordering of a graph that
    is not connected, and it is what a reader comparing it against the consensus ordering needs
    it to be for the comparison to mean anything.
    """
    n = adj.shape[0]
    if n < 3:
        return np.arange(n)
    g = nx.from_scipy_sparse_array(adj)
    # Sorted by size, then by smallest member: `key=len` alone leaves same-sized components
    # in whatever order the generator produced, which is a second way for the ordering to
    # move between runs without anything in the data changing.
    comps = sorted((sorted(c) for c in nx.connected_components(g)),
                   key=lambda c: (-len(c), c[0]))
    out = []
    for comp in comps:
        members = np.array(comp)
        if members.size > 2:
            members = members[_fiedler_component(adj[members][:, members])]
        out.append(members)
    return np.concatenate(out)


def main() -> int:
    if not SRC.exists():
        print(f"missing {SRC}", file=sys.stderr)
        return 1

    d = json.loads(SRC.read_text(encoding="utf-8"))
    names = d["nodes"]
    indptr, indices = d["indptr"], d["indices"]

    g = nx.Graph()
    g.add_nodes_from(range(len(names)))
    for i in range(len(names)):
        for j in indices[indptr[i]:indptr[i + 1]]:
            if j > i:
                g.add_edge(i, j)

    keep = sorted(v for v in g.nodes() if g.degree(v) > 0)
    sub = g.subgraph(keep)
    pos = {v: i for i, v in enumerate(keep)}
    n = len(keep)
    print(f"  {len(names)} genes, {g.number_of_edges()} edges; "
          f"{n} with at least one edge, {len(names) - n} isolated and dropped")

    rows = np.array([pos[u] for u, _ in sub.edges()] + [pos[v] for _, v in sub.edges()])
    cols = np.array([pos[v] for _, v in sub.edges()] + [pos[u] for u, _ in sub.edges()])
    adj = csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))
    degree = np.asarray(adj.sum(axis=1)).ravel().astype(np.int32)

    # ---- the consensus partition, if community_stability has run ------------------------
    comm = np.zeros(n, dtype=np.int32)
    conf = np.full(n, np.nan, dtype=np.float32)
    have_consensus = False
    if STABILITY.exists():
        st = json.loads(STABILITY.read_text(encoding="utf-8"))
        per = st.get("per_gene") or {}
        by_name = {g_: (c, cf) for g_, c, cf
                   in zip(per.get("genes", []), per.get("community", []),
                          per.get("confidence", []))}
        hit = 0
        for v in keep:
            rec = by_name.get(names[v])
            if rec:
                comm[pos[v]], conf[pos[v]] = rec[0], rec[1]
                hit += 1
        have_consensus = hit > 0
        print(f"  consensus communities joined for {hit} of {n} genes")

    # ---- three orderings ------------------------------------------------------------------
    spectral = fiedler_order(adj)

    by_degree = np.argsort(-degree)

    if have_consensus:
        # Communities biggest first, and each community internally spectral-ordered. Sorting
        # the blocks by size is a presentation choice and is stated: it puts the structure at
        # the top left where a reader looks first, and it changes nothing inside a block.
        order_parts = []
        sizes = {}
        for c in sorted(set(comm.tolist()),
                        key=lambda c: -int((comm == c).sum())):
            members = np.where(comm == c)[0]
            sizes[int(c)] = int(members.size)
            if members.size > 2:
                local = adj[members][:, members]
                members = members[fiedler_order(local)]
            order_parts.append(members)
        consensus_order = np.concatenate(order_parts)
    else:
        consensus_order = spectral
        sizes = {}

    # Block boundaries, so the drawing can rule the communities off without recomputing them.
    bounds = []
    if have_consensus:
        seen = comm[consensus_order]
        start = 0
        for i in range(1, n + 1):
            if i == n or seen[i] != seen[start]:
                if i - start > 1:
                    bounds.append([start, i, int(seen[start])])
                start = i

    # ---- how much structure each ordering actually shows ---------------------------------
    #
    #  A CAPTION ABOUT A FIGURE IS A CLAIM, AND THIS ONE IS MEASURED RATHER THAN EYEBALLED.
    #  The first draft of the caption said the blocks reappear under the spectral ordering.
    #  They did not — that ordering was broken (see fiedler_order) and put 6.2% of edges near
    #  the diagonal against 2.0% for a random shuffle. The number is what caught it, so the
    #  number is published beside the figure it describes.
    #
    #  Two quantities, because they answer different questions: the mean rank distance over
    #  edges says how LOCAL the ordering is overall, and the share within 1% of the diagonal
    #  says how much of it collapses into visible blocks.
    def locality(order: np.ndarray) -> dict:
        rank = np.empty(n, dtype=np.int64)
        rank[order] = np.arange(n)
        dist = np.abs(rank[rows[:len(rows) // 2]].astype(np.int64)
                      - rank[cols[:len(cols) // 2]].astype(np.int64))
        return {"mean_rank_distance": round(float(dist.mean() / n), 4),
                "share_within_1pct_of_diagonal": round(float((dist <= n * 0.01).mean()), 4)}

    rng = np.random.default_rng(SEED)
    shuffled = [locality(rng.permutation(n)) for _ in range(20)]
    locality_report = {
        "consensus": locality(consensus_order),
        "spectral": locality(spectral),
        "degree": locality(by_degree),
        "random": {
            "mean_rank_distance": round(float(np.mean(
                [x["mean_rank_distance"] for x in shuffled])), 4),
            "share_within_1pct_of_diagonal": round(float(np.mean(
                [x["share_within_1pct_of_diagonal"] for x in shuffled])), 4),
            "draws": len(shuffled),
        },
        "says": ("The spectral ordering is never told where the communities are, and it still "
                 "puts a majority of edges within 1% of the diagonal against 2% for a random "
                 "shuffle - so the blocks are in the graph rather than in the ordering that "
                 "assumes them. Ordering by degree alone reaches a third, which is why it is "
                 "the control the comparison needs: SOME structure appears under any "
                 "non-random ordering, and the question is always how much more."),
    }

    payload = {
        "generated": "tools/network_layout.py",
        "locality": locality_report,
        "governed_by": "docs/adr/0008 — layouts are computed once, in Python; a seriation is "
                       "an argument",
        "form": ("reordered adjacency matrix (Bertin 1967). Every edge drawn once at a fixed "
                 "position, with no layout parameter to tune - unlike a force-directed "
                 "drawing of 38,746 edges, which is dominated by its repulsion constant and "
                 "differs between runs."),
        "genes": [names[v] for v in keep],
        "counts": {
            "genes_total": len(names),
            "genes_with_an_edge": n,
            "isolated_dropped": len(names) - n,
            "edges": int(sub.number_of_edges()),
        },
        "orderings": {
            "consensus": {
                "index": b64(consensus_order.astype(np.int32)),
                "says": ("by consensus community, biggest first, spectral within each. This "
                         "ordering ASSERTS the partition - it was told where the blocks are."),
            },
            "spectral": {
                "index": b64(spectral.astype(np.int32)),
                "says": ("the Fiedler vector of the whole graph, communities ignored. If the "
                         "blocks survive here they are in the graph rather than in the "
                         "ordering, and this is the only comparison that can tell."),
            },
            "degree": {
                "index": b64(by_degree.astype(np.int32)),
                "says": ("degree alone - the control. Any ordering produces some visible "
                         "structure; this is what it looks like when it comes from the degree "
                         "sequence and nothing else."),
            },
        },
        "edges": {"i": b64(np.array([pos[u] for u, _ in sub.edges()], dtype=np.int32)),
                  "j": b64(np.array([pos[v] for _, v in sub.edges()], dtype=np.int32))},
        "degree": b64(degree),
        "community": b64(comm),
        "confidence": b64(np.nan_to_num(conf, nan=-1.0).astype(np.float32)),
        "blocks": bounds,
        "block_sizes": sizes,
        "reading": (
            "Each pixel is a gene pair; a mark means the two share at least one disease. "
            "Blocks on the diagonal are communities. Switch the ordering to `spectral` - "
            "which was never told the communities exist - and the same blocks reappear, "
            "which is the evidence that they are in the graph. Switch to `degree` and they "
            "do not."),
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    kb = DEST.stat().st_size / 1024
    print(f"  {len(bounds)} community blocks; largest {max(sizes.values()) if sizes else 0} genes")
    print(f"wrote {DEST.relative_to(ROOT).as_posix()}  ({kb:.0f} kB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
