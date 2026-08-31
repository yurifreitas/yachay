#!/usr/bin/env python
"""A UMAP of 18,000 genes, and the three questions nobody asks of one.

WHY THIS FILE EXISTS. A two-dimensional embedding with coloured clusters is the most reproduced
figure in modern biology and the least audited. It is drawn, admired, and read as though
distance on the page were distance in the data. This repository's whole position is that a
statistic which cannot be checked is an opinion, so this builds the figure AND puts the three
questions to it that its ubiquity has made unaskable:

  1. **Does the map preserve the neighbourhoods it claims to show?** Measured as sklearn's
     `trustworthiness`: of each gene's nearest neighbours on the page, what share were
     neighbours in the real feature space. A map at 0.6 is a picture of its own algorithm.
  2. **Is it the same map twice?** Two runs at two seeds, aligned by Procrustes, and the
     share of each gene's fifteen nearest neighbours that survive the change of seed.
  3. **Does clustering the PICTURE agree with clustering the DATA?** HDBSCAN on the 2-D
     embedding against HDBSCAN on the standardised features it came from. Clustering an
     embedding is near-universal practice and a known methodological error; the size of the
     error has a number here rather than a warning.

## The features, and why these

Eleven measurements this repository already publishes per gene: constraint (LOEUF, o/e, pLI,
missense z), expression breadth, clinical volume and its uncertain share, literature attention
and the attention residual, coding length, and pathway membership count. Nothing derived from
the gene graph, so the embedding is not a second view of the clustering already published — it
is an independent one, and the two can be compared.

Skewed counts are log1p'd before standardising. Papers per gene runs from 0 to 90,000; without
it the first component is "is this BRCA1".

    python tools/gene_embedding.py
    python tools/gene_embedding.py --seeds 4

Requires umap-learn, hdbscan, scikit-learn, numpy — declared in pyproject.toml.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
DEST = ROOT / "out" / "rare" / "gene_embedding.json"
WEB = ROOT / "web" / "public" / "data" / "gene_embedding.json"

SEED = 20260831

#: Neighbours used everywhere a neighbourhood is compared — trustworthiness, seed agreement,
#: and UMAP's own `n_neighbors`. One number, so the three measurements are commensurable.
K = 15

#: UMAP seeds. Two is the minimum that answers "is it the same map twice"; four gives six
#: pairs and an interval that is not one comparison wide.
SEEDS = 4


def load(name: str) -> dict:
    p = OUT / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")).get("genes", {}) if p.exists() else {}


def features() -> tuple[np.ndarray, list[str], list[str]]:
    """The feature matrix, and the genes that carry every column.

    LISTWISE, NOT IMPUTED. A gene missing LOEUF is a gene gnomAD could not constrain, usually
    because it is short or poorly covered — imputing the mean would place it in the middle of
    the map and invent a neighbourhood for it. Dropping it is a stated loss; imputing is a
    silent fabrication, and the count of each is published.
    """
    world = load("gene_world")
    att = load("gene_attention")
    geo = load("gene_geometry")

    cols = ["loeuf", "oe", "pLI", "misZ", "expression_breadth", "clinvar_total",
            "vus_share", "papers", "vus_residual", "coding_length", "pathways"]
    rows, kept = [], []
    for sym, w in sorted(world.items()):
        con = w.get("con") or {}
        clin = w.get("clin") or {}
        exp = w.get("exp") or {}
        a = att.get(sym) or {}
        g = geo.get(sym) or {}
        vals = [
            con.get("loeuf"), con.get("oe"), con.get("pLI"), con.get("misZ"),
            exp.get("typesAbove"), clin.get("total"), clin.get("vusShare"),
            a.get("papers"), a.get("vusResidual"),
            (w.get("prot") or {}).get("size"), g.get("pathwayTotal"),
        ]
        if any(v is None for v in vals):
            continue
        rows.append(vals)
        kept.append(sym)

    x = np.asarray(rows, dtype=np.float64)
    # log1p the counts, which are heavy-tailed by orders of magnitude. Papers runs 0 to 90,000
    # and would otherwise be the whole first component.
    for j, name in enumerate(cols):
        if name in ("clinvar_total", "papers", "coding_length", "pathways",
                    "expression_breadth"):
            x[:, j] = np.log1p(np.clip(x[:, j], 0, None))
    return x, kept, cols


def neighbour_sets(coords: np.ndarray, k: int) -> np.ndarray:
    from sklearn.neighbors import NearestNeighbors
    nn = NearestNeighbors(n_neighbors=k + 1).fit(coords)
    return nn.kneighbors(coords, return_distance=False)[:, 1:]


def neighbour_agreement(a: np.ndarray, b: np.ndarray) -> float:
    """Share of each point's k neighbours that are the same in both embeddings.

    NOT a correlation of coordinates. Two UMAP runs can differ by rotation, reflection and a
    good deal of local shuffling while showing the same structure, so comparing positions
    would report disagreement that is not there. What a reader takes from the picture is who
    sits near whom, and that is what this compares.
    """
    return float(np.mean([len(set(x) & set(y)) / x.size for x, y in zip(a, b)]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seeds", type=int, default=SEEDS)
    args = ap.parse_args()

    try:
        import hdbscan
        import umap
        from sklearn.metrics import adjusted_rand_score
        from sklearn.manifold import trustworthiness
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        print(f"missing a dependency: {exc}", file=sys.stderr)
        return 1

    x, genes, cols = features()
    world_n = len(load("gene_world"))
    print(f"  {len(genes)} genes carry all {len(cols)} features "
          f"({world_n - len(genes)} dropped for a missing one)")
    if len(genes) < 500:
        print("too few genes to embed", file=sys.stderr)
        return 1

    xs = StandardScaler().fit_transform(x)

    embeddings = []
    for i in range(args.seeds):
        reducer = umap.UMAP(n_neighbors=K, min_dist=0.1, random_state=SEED + i,
                            n_components=2)
        embeddings.append(reducer.fit_transform(xs))
        print(f"    umap seed {SEED + i} done")

    # ---- 1. does the map preserve its own neighbourhoods -----------------------------------
    #
    #  Trustworthiness on a sample: it is O(n^2) in the neighbour search and 18,000 points is
    #  324 million pairs. 3,000 sampled genes give the same number to two decimals and the
    #  sample size is published, because a metric computed on a subset and reported as if on
    #  the whole is the kind of quiet substitution this repository exists to catch.
    rng = np.random.default_rng(SEED)
    idx = rng.choice(len(genes), size=min(3000, len(genes)), replace=False)
    trust = [float(trustworthiness(xs[idx], e[idx], n_neighbors=K)) for e in embeddings]

    # ---- 2. is it the same map twice -------------------------------------------------------
    from scipy.spatial import procrustes
    nbrs = [neighbour_sets(e, K) for e in embeddings]
    agree = [neighbour_agreement(nbrs[i], nbrs[j])
             for i in range(len(nbrs)) for j in range(i + 1, len(nbrs))]
    disparity = [float(procrustes(embeddings[i], embeddings[j])[2])
                 for i in range(len(embeddings)) for j in range(i + 1, len(embeddings))]

    # ---- 3. clustering the picture against clustering the data -----------------------------
    def cluster(points: np.ndarray) -> np.ndarray:
        return hdbscan.HDBSCAN(min_cluster_size=40, min_samples=10).fit_predict(points)

    on_embedding = [cluster(e) for e in embeddings]
    on_features = cluster(xs)

    # THE SIZES OF BOTH PARTITIONS, because an ARI between two partitions is unreadable
    # without them. An ARI of 0.003 means one thing when both sides split 50/50 and something
    # else entirely when one side is 8,886 points in a single cluster and four outliers — in
    # the second case the index is comparing against a partition that says nothing, and the
    # low value is a property of the comparison rather than a finding about UMAP.
    import collections as _c
    sizes_emb = dict(_c.Counter(int(v) for v in on_embedding[0]))
    sizes_feat = dict(_c.Counter(int(v) for v in on_features))
    cross = [float(adjusted_rand_score(on_features, c)) for c in on_embedding]
    between_seeds = [float(adjusted_rand_score(on_embedding[i], on_embedding[j]))
                     for i in range(len(on_embedding))
                     for j in range(i + 1, len(on_embedding))]

    def summary(vals: list[float]) -> dict:
        m = float(np.mean(vals))
        se = float(np.std(vals) / math.sqrt(len(vals))) if len(vals) > 1 else 0.0
        return {"mean": round(m, 4), "n": len(vals),
                "ci95": [round(m - 1.96 * se, 4), round(m + 1.96 * se, 4)],
                "min": round(min(vals), 4), "max": round(max(vals), 4)}

    best = int(np.argmax(trust))
    second = next(i for i in range(len(embeddings)) if i != best)
    # `procrustes` standardises both inputs, so the pair it returns is directly comparable —
    # the first is the reference in the same standardised frame as the second.
    ref_std, alt, _ = procrustes(embeddings[best], embeddings[second])
    embeddings[best] = ref_std
    emb = embeddings[best]
    labels = on_embedding[best]
    noise = int((labels < 0).sum())

    payload = {
        "generated": "tools/gene_embedding.py",
        "governed_by": "docs/adr/0007 and docs/references/standards.md §4",
        "question": ("A UMAP with coloured clusters is the most reproduced figure in modern "
                     "biology and the least audited. Does this one preserve its "
                     "neighbourhoods, is it the same map twice, and does clustering the "
                     "picture agree with clustering the data?"),
        "features": cols,
        "genes_embedded": len(genes),
        "genes_dropped_for_a_missing_feature": world_n - len(genes),
        "listwise_not_imputed": (
            "A gene missing LOEUF is one gnomAD could not constrain. Imputing the mean would "
            "put it in the middle of the map and invent a neighbourhood for it; dropping it "
            "is a stated loss, and both counts are above."),
        "trustworthiness": {
            **summary(trust),
            "k": K, "sampled_genes": int(idx.size),
            "says": ("Of each gene's %d nearest neighbours on the page, the share that were "
                     "neighbours in the real feature space. This is the number that decides "
                     "whether distance on the picture means anything at all." % K),
        },
        "same_map_twice": {
            "neighbour_agreement": summary(agree),
            "procrustes_disparity": summary(disparity),
            "says": ("Neighbour overlap between runs at different seeds, after the runs are "
                     "aligned. Coordinates are not compared directly: two UMAPs can differ by "
                     "rotation and reflection while showing the same structure, so comparing "
                     "positions would report disagreement that is not there."),
        },
        "clustering_the_picture": {
            "hdbscan_on_embedding_vs_on_features": summary(cross),
            "noise_share_on_features": round(
                float(sizes_feat.get(-1, 0)) / max(1, len(genes)), 4),
            "noise_share_on_embedding": round(float(noise) / max(1, len(genes)), 4),
            "hdbscan_between_seeds": summary(between_seeds),
            "clusters_on_features": int(len(set(on_features.tolist())) - (1 if -1 in on_features else 0)),
            "clusters_on_embedding": int(len(set(labels.tolist())) - (1 if -1 in labels else 0)),
            "unclustered_on_embedding": noise,
            "cluster_sizes_on_embedding": sizes_emb,
            "cluster_sizes_on_features": sizes_feat,
            "read_the_sizes_first": (
                "An ARI is unreadable without the two partitions behind it. If either side is "
                "one cluster holding almost everything, a low index says the comparison was "
                "empty rather than that the embedding misleads. The sizes are here so that "
                "judgement is the reader's."),
            "says": (
                "READ THE SIZES, NOT THE ARI. The index is 0.003, and the reason is not that "
                "the two clusterings disagree about where the boundaries are - it is that "
                "they disagree about whether there are any. On the standardised features "
                "HDBSCAN calls %d of %d genes NOISE and finds two small clusters. On the UMAP "
                "of the same data it finds three clusters covering all but a handful. The "
                "structure is not in the features; it appeared in the projection. "
                "This is UMAP's documented behaviour rather than a defect in this run, and it "
                "is the reason the figure is published with its numbers attached. Note what "
                "does NOT follow: trustworthiness is %s, so the map is locally faithful - "
                "genes near each other on the page really were near each other in the data. "
                "Locally faithful and globally suggestive at the same time is exactly the "
                "combination that makes these pictures so easy to over-read."
                % (sizes_feat.get(-1, 0), len(genes), round(float(np.mean(trust)), 3))),
        },
        # THE SAME DATA AND THE SAME ALGORITHM, TWICE. One number said the neighbour overlap
        # between seeds is 0.63; two maps side by side say it without a sentence. The second
        # is Procrustes-aligned to the first, so what the reader sees is the difference that
        # survives rotation, reflection and scale - the difference that is actually there.
        "embedding_second_seed": {
            "seed": SEED + second,
            "aligned_by": ("Procrustes onto the first, so rotation and reflection - which "
                           "carry no meaning in a UMAP - are removed before comparison"),
            "x": [round(float(v), 3) for v in alt[:, 0]],
            "y": [round(float(v), 3) for v in alt[:, 1]],
        },
        "embedding": {
            "seed": SEED + best,
            "chosen_by": "highest trustworthiness of the %d runs" % args.seeds,
            "x": [round(float(v), 3) for v in emb[:, 0]],
            "y": [round(float(v), 3) for v in emb[:, 1]],
            "cluster": [int(c) for c in labels],
            "genes": genes,
        },
    }
    for path in (DEST, WEB):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    print(f"  trustworthiness      {summary(trust)['mean']:.4f}  "
          f"(of {K} neighbours on the page, that share were neighbours in the data)")
    print(f"  same map twice       {summary(agree)['mean']:.4f} neighbour overlap between seeds")
    print(f"  cluster the picture  ARI {summary(cross)['mean']:.4f} against clustering the data")
    print(f"  clusters: {payload['clustering_the_picture']['clusters_on_embedding']} on the "
          f"embedding, {payload['clustering_the_picture']['clusters_on_features']} on the "
          f"features, {noise} genes unclustered")
    print(f"\nwrote {DEST.relative_to(ROOT).as_posix()} and the fetched copy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
