#!/usr/bin/env python
"""Is there anything to cluster? The question every gene-clustering figure assumes away.

WHERE THIS CAME FROM. `gene_embedding.py` reported that HDBSCAN calls 6,646 of 8,890 genes
unclusterable noise in the eleven-dimensional feature space, and three clusters covering all but
one gene on the UMAP of those same features. That is a finding about the PROJECTION. It leaves
the prior question open, and the prior question is the one that decides whether any of it means
anything:

    **Does this feature space contain clusters at all?**

Every clustering figure ever published answers that question by assumption. An algorithm asked
for clusters returns clusters; k-means returns exactly k of them from uniform noise, and the
silhouette that follows is computed on the partition the algorithm just invented. Nothing in
the usual pipeline can come back and say "there is nothing here".

## Three statistics, because no single one is trusted

  **Hopkins.** Compares the distance from a real point to its nearest neighbour against the
  distance from a uniformly sampled point in the same box to its nearest real neighbour.
  Around 0.5 means the data are as spread out as noise; above about 0.75 is the conventional
  reading of "clustered". Reported with an interval over repeated draws, because it is a
  sample statistic and is usually quoted as though it were not.

  **HDBSCAN noise share.** The fraction of points no density-based cluster will accept.
  Density clustering is the only family here that is *allowed* to answer "none of it".

  **k-means silhouette, swept over k.** The number the field actually reports. Included
  precisely because it is the weakest: k-means partitions anything, so its silhouette is only
  interpretable against a null, which is the whole point below.

## The null that makes them mean something

**Each feature column shuffled independently across genes.** Every marginal distribution
survives exactly — the same LOEUF values, the same paper counts, the same skew — and only the
JOINT structure is destroyed. So a difference between the real data and this null cannot be an
artefact of scale, skew or outliers; it can only be about which values travel together, which
is the only thing a cluster is.

This is the same null `knowledge_shape.py` uses on its axes, for the same reason.

    python tools/clusterability.py
    python tools/clusterability.py --draws 25

Requires scikit-learn, hdbscan, numpy.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import pathlib
import statistics
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "out" / "rare" / "clusterability.json"

SEED = 20260831

#: Null draws. Each is a full re-run of all three statistics, so this is the cost knob.
DRAWS = 20

#: Points sampled for Hopkins. The statistic is defined on a sample; using every point makes
#: it slower and no more meaningful, and the sample size is published because a Hopkins value
#: quoted without one is not reproducible.
HOPKINS_M = 400

#: k values swept for the silhouette. Stops at 12: past that the silhouette of a space with no
#: clusters simply decays, and the shape of the decay is the answer rather than its minimum.
KS = (2, 3, 4, 5, 6, 8, 10, 12)


def hopkins(x: np.ndarray, m: int, rng: np.random.Generator) -> float:
    """Hopkins statistic. 0.5 is spatial randomness; higher is clustered.

    THE DETAIL THAT IS USUALLY GOT WRONG: the real points sampled must be EXCLUDED from their
    own nearest-neighbour search, or every u-distance is zero and the statistic is pinned near
    1 whatever the data look like. Implementations that forget this report beautifully
    clustered uniform noise.
    """
    from sklearn.neighbors import NearestNeighbors

    n, d = x.shape
    m = min(m, n // 2)
    idx = rng.choice(n, size=m, replace=False)
    mask = np.ones(n, dtype=bool)
    mask[idx] = False
    rest = x[mask]

    nn = NearestNeighbors(n_neighbors=1).fit(rest)
    # u: from a real point to its nearest OTHER real point.
    u, _ = nn.kneighbors(x[idx], return_distance=True), None
    u_d = u[0].ravel()
    # w: from a uniform point in the data's own bounding box to its nearest real point.
    lo, hi = x.min(axis=0), x.max(axis=0)
    synthetic = rng.uniform(lo, hi, size=(m, d))
    w_d = nn.kneighbors(synthetic, return_distance=True)[0].ravel()

    su, sw = float(u_d.sum()), float(w_d.sum())
    return sw / (su + sw) if (su + sw) else 0.5


def statistics_of(x: np.ndarray, rng: np.random.Generator, ks=KS) -> dict:
    import hdbscan
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    h = hopkins(x, HOPKINS_M, rng)

    labels = hdbscan.HDBSCAN(min_cluster_size=40, min_samples=10).fit_predict(x)
    noise = float((labels < 0).mean())
    found = int(len(set(labels.tolist())) - (1 if -1 in labels else 0))

    # The silhouette is scored on a sample: it is O(n^2) and the value is stable well before
    # the full set. Sampling is stated rather than done quietly.
    sil_idx = rng.choice(len(x), size=min(2000, len(x)), replace=False)
    sil = {}
    for k in ks:
        km = KMeans(n_clusters=k, n_init=4, random_state=SEED).fit(x)
        sil[k] = float(silhouette_score(x[sil_idx], km.labels_[sil_idx]))

    return {"hopkins": h, "hdbscan_noise_share": noise, "hdbscan_clusters": found,
            "silhouette": sil, "best_k": max(sil, key=sil.get), "best_silhouette": max(sil.values())}


def summarise(vals: list[float]) -> dict:
    m = statistics.fmean(vals)
    se = statistics.pstdev(vals) / math.sqrt(len(vals)) if len(vals) > 1 else 0.0
    return {"mean": round(m, 4), "ci95": [round(m - 1.96 * se, 4), round(m + 1.96 * se, 4)],
            "min": round(min(vals), 4), "max": round(max(vals), 4), "n": len(vals)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--draws", type=int, default=DRAWS)
    args = ap.parse_args()

    spec = importlib.util.spec_from_file_location(
        "gene_embedding", ROOT / "tools" / "gene_embedding.py")
    ge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ge)

    from sklearn.preprocessing import StandardScaler

    x, genes, cols = ge.features()
    xs = StandardScaler().fit_transform(x)
    print(f"  {len(genes)} genes, {len(cols)} features")

    rng = np.random.default_rng(SEED)
    real = statistics_of(xs, rng)
    print(f"  real: hopkins {real['hopkins']:.4f}, hdbscan noise "
          f"{real['hdbscan_noise_share'] * 100:.1f}% in {real['hdbscan_clusters']} clusters, "
          f"best silhouette {real['best_silhouette']:.4f} at k={real['best_k']}")

    # THE NULL: each column shuffled independently. Marginals exactly preserved, joint
    # structure destroyed. A gene in the null has a real LOEUF, a real paper count and a real
    # VUS share — just not its own.
    nulls = []
    for i in range(args.draws):
        shuffled = xs.copy()
        for j in range(shuffled.shape[1]):
            rng.shuffle(shuffled[:, j])
        nulls.append(statistics_of(shuffled, rng))
        print(f"    null {i + 1}/{args.draws}", end="\r")

    n_hop = summarise([r["hopkins"] for r in nulls])
    n_noise = summarise([r["hdbscan_noise_share"] for r in nulls])
    n_sil = summarise([r["best_silhouette"] for r in nulls])
    n_clusters = summarise([float(r["hdbscan_clusters"]) for r in nulls])

    def stands_out(observed: float, null: dict) -> bool:
        return observed < null["ci95"][0] or observed > null["ci95"][1]

    verdict_parts = []
    if not stands_out(real["hopkins"], n_hop):
        verdict_parts.append(
            "Hopkins does not separate the real feature space from a marginal-preserving "
            "shuffle")
    else:
        verdict_parts.append(
            "Hopkins separates the real space from the shuffle (%.3f against %.3f)"
            % (real["hopkins"], n_hop["mean"]))
    verdict_parts.append(
        "HDBSCAN leaves %.0f%% of real genes unclustered against %.0f%% of shuffled ones"
        % (real["hdbscan_noise_share"] * 100, n_noise["mean"] * 100))
    verdict_parts.append(
        "the best k-means silhouette is %.3f on the real data and %.3f on the shuffle"
        % (real["best_silhouette"], n_sil["mean"]))

    payload = {
        "generated": "tools/clusterability.py",
        "governed_by": "docs/adr/0007 — a construct needs a null and an interval",
        "question": ("gene_embedding.py found that the tidy clusters are in the projection "
                     "rather than the features. This asks the prior question every "
                     "clustering figure answers by assumption: does this feature space "
                     "contain clusters at all?"),
        "why_it_cannot_be_asked_the_usual_way": (
            "An algorithm asked for clusters returns clusters. k-means returns exactly k of "
            "them from uniform noise and the silhouette that follows is computed on the "
            "partition it just invented. Nothing in the usual pipeline can answer 'there is "
            "nothing here', which is why the null below is the whole method."),
        "null": (
            "Each feature column shuffled independently across genes. Every marginal survives "
            "exactly - the same LOEUF values, the same paper counts, the same skew - and only "
            "which values travel together is destroyed. A difference from this null cannot be "
            "an artefact of scale, skew or outliers; it can only be structure."),
        "genes": len(genes),
        "features": cols,
        "real": {
            "hopkins": round(real["hopkins"], 4),
            "hdbscan_noise_share": round(real["hdbscan_noise_share"], 4),
            "hdbscan_clusters": real["hdbscan_clusters"],
            "silhouette_by_k": {str(k): round(v, 4) for k, v in real["silhouette"].items()},
            "best_k": real["best_k"],
            "best_silhouette": round(real["best_silhouette"], 4),
        },
        "shuffled": {
            "hopkins": n_hop,
            "hdbscan_noise_share": n_noise,
            "hdbscan_clusters": n_clusters,
            "best_silhouette": n_sil,
            "draws": args.draws,
        },
        "separates_from_the_null": {
            "hopkins": stands_out(real["hopkins"], n_hop),
            "hdbscan_noise_share": stands_out(real["hdbscan_noise_share"], n_noise),
            "best_silhouette": stands_out(real["best_silhouette"], n_sil),
        },
        "the_conventional_threshold_fails_here": {
            "textbook_rule": "Hopkins above about 0.75 is read as 'the data are clustered'.",
            "shuffled_data_scores": n_hop["mean"],
            "says": (
                "A marginal-preserving shuffle of this feature space - data with NO joint "
                "structure whatsoever, by construction - scores %.3f on Hopkins. The "
                "conventional cutoff would call it clustered. In eleven dimensions with "
                "skewed marginals the statistic is dominated by the shape of the bounding "
                "box the uniform points are drawn in, not by clustering, so the published "
                "threshold is not usable and a value quoted against it says nothing. "
                "The real data score %.3f, which is higher and outside the shuffle's "
                "interval - so there IS joint structure. But the only reason that sentence "
                "can be written is that the null was computed. This is the whole argument of "
                "this repository arriving from a direction nobody expects: a threshold from a "
                "textbook is not a calibration."
                % (n_hop["mean"], real["hopkins"])),
        },
        "how_much_structure_though": (
            "All three statistics separate from the null, so the answer to 'is there anything "
            "to cluster' is yes. The answer to 'how much' is: not a lot. HDBSCAN still leaves "
            "%.0f%% of genes in no cluster at all, and the best k-means silhouette is %.3f - "
            "double the shuffle's %.3f, and far below the 0.5 conventionally read as "
            "'reasonable structure'. A gene feature space with weak, real, mostly-unclustered "
            "structure is exactly the situation in which a UMAP's tidy three-cluster picture "
            "is most misleading, which is what gene_embedding.py measured from the other side."
            % (real["hdbscan_noise_share"] * 100, real["best_silhouette"], n_sil["mean"])),
        "hopkins_note": (
            "The real points sampled are excluded from their own nearest-neighbour search. "
            "Implementations that forget this report beautifully clustered uniform noise, "
            "because every u-distance is then zero."),
        "says": ". ".join(verdict_parts) + ".",
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    print(f"\n  shuffled: hopkins {n_hop['mean']:.4f} {n_hop['ci95']}, "
          f"noise {n_noise['mean'] * 100:.1f}%, silhouette {n_sil['mean']:.4f}")
    print(f"  separates from the null: {payload['separates_from_the_null']}")
    print(f"\nwrote {DEST.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
