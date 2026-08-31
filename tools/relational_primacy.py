#!/usr/bin/env python
"""Is a gene better predicted by what it IS, or by what it is CONNECTED TO?

WHOSE QUESTION THIS IS. Yuri Freitas', and it is the most central of his recovered
formulations — the one he calls the Campo Simbiótico Não-Originário. Its ontological claim is
that entities are not fundamental: relations and constraints are, and an object is what a
stable configuration of relations looks like from outside.

    Object ∉ Fundamental
    Relations + Constraints → Stable Configurations → Observed Objects

In that cosmological form it has no falsifier, and his own notes say so explicitly. But he
also wrote down the biomedical version that does:

    ENUNCIADO   Biomedical entities should be more predictable from their RELATIONS than from
                their intrinsic attributes in isolation. P(D | N(g), paths(g)) against
                P(D | features(g)).

    FALSIFIER   Seriously weakened if ΔAUPRC ≤ 0 consistently across disease families and
                out-of-distribution splits. If intrinsic attributes explain everything and
                relations add ΔAUPRC < 0.01 with a 95% interval containing zero, there is no
                evidence to raise relational primacy to an operational principle.

## Making the comparison fair, which is the whole difficulty

The lazy version of this test is rigged. Give the relational model the disease's own seed
genes and give the intrinsic model only a gene's attributes, and the relational model wins
because it is the only one that knows which disease is being asked about. That would measure
the experimental design, not the hypothesis.

So **both arms receive the same seeds and differ only in what they do with them**:

    intrinsic    how much gene g RESEMBLES the seeds, in the eleven-dimensional attribute
                 space this repository already publishes — constraint, expression breadth,
                 clinical volume, literature attention, length, pathway count. Cosine to the
                 seed centroid. No edges are consulted.
    relational   how strongly the seeds REACH g, by random walk with restart on the
                 gene–disease co-membership graph. No attributes are consulted.

One asks "is it the same kind of thing"; the other asks "is it connected to it". That is the
comparison his statement is actually about.

## The control

A degree-preserving rewiring of the graph. If the relational arm's advantage survives on a
graph with the same degree sequence and none of the biology, the advantage is the degree
sequence and not the relations.

    python tools/relational_primacy.py

Requires numpy, scipy, scikit-learn.
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "rare" / "relational_primacy.json"

SEED = 20260831
MIN_GENES = 6
MAX_GENES = 60
ALPHA = 0.7
ITERS = 60
DRAWS = 300


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def gene_disease() -> dict[str, set[str]]:
    out: dict[str, set[str]] = collections.defaultdict(set)
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        header = next(fh, "")
        cols = header.rstrip("\n").split("\t")
        try:
            gi, di = cols.index("gene_symbol"), cols.index("disease_id")
        except ValueError:
            gi, di = 1, 0
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > max(gi, di):
                out[parts[gi]].add(parts[di])
    return dict(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--draws", type=int, default=DRAWS)
    args = ap.parse_args()

    from scipy.sparse import csr_matrix
    from sklearn.metrics import average_precision_score
    from sklearn.preprocessing import StandardScaler

    # The attribute space is the one gene_embedding.py already assembles, reused rather than
    # rebuilt: two files with two definitions of "a gene's features" is how a comparison ends
    # up measuring which file was edited last.
    ge = load("gene_embedding")
    x_all, feat_genes, cols = ge.features()
    xs = StandardScaler().fit_transform(x_all)
    fidx = {g: i for i, g in enumerate(feat_genes)}

    diseases_of = gene_disease()
    # Only genes that have BOTH an attribute vector and a disease annotation can be scored by
    # both arms. Restricting to the intersection is what keeps the arms comparable; the count
    # dropped is published rather than buried.
    genes = sorted(g for g in diseases_of if g in fidx)
    n = len(genes)
    gidx = {g: i for i, g in enumerate(genes)}
    feats = np.array([xs[fidx[g]] for g in genes])
    # Cosine works on directions, so the vectors are unit-normalised once here.
    norms = np.linalg.norm(feats, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    feats_n = feats / norms
    print(f"  {n} genes carry both an attribute vector and a disease annotation "
          f"({len(diseases_of) - n} dropped)")

    by_disease: dict[str, list[str]] = collections.defaultdict(list)
    for g in genes:
        for d in diseases_of[g]:
            by_disease[d].append(g)

    # The co-membership graph, undirected and unweighted: this arm is about whether a relation
    # EXISTS, not about its direction — that is the separate hypothesis tools/nonreciprocal.py
    # tests, and mixing the two would make neither answerable.
    rows, cols_, vals = [], [], []
    cliques: dict[str, list[int]] = {}
    for disease, members in by_disease.items():
        if len(members) > MAX_GENES:
            continue
        ids = [gidx[g] for g in members]
        cliques[disease] = ids
        for a in ids:
            for b in ids:
                if a != b:
                    rows.append(a)
                    cols_.append(b)
                    vals.append(1.0)
    w = csr_matrix((vals, (rows, cols_)), shape=(n, n))
    w.sum_duplicates()

    # ⚠️ LEAVE-ONE-DISEASE-OUT, AND WITHOUT IT THIS ENTIRE FILE WAS A LEAK.
    #
    #  The graph's edges ARE disease co-membership. So when disease D is the one being tested,
    #  every seed of D is joined to every hidden gene of D by an edge that exists BECAUSE of D.
    #  The relational arm was reading the answer key: ΔAUPRC came out at +0.925 and the
    #  relational arm won 100% of 155 diseases, which is not a finding, it is a tell.
    #
    #  The fix is to rebuild the graph without D's own contribution each time. The weights are
    #  counts of shared diseases, so D's clique is subtracted and pairs that fall to zero lose
    #  their edge. Two genes that share only the disease under test are then unconnected, which
    #  is exactly the situation the hypothesis is supposed to be predicting from.
    def graph_without(disease: str):
        ids = cliques.get(disease)
        if not ids:
            return w
        k = len(ids)
        r = np.repeat(ids, k)
        c = np.tile(ids, k)
        keep = r != c
        clique = csr_matrix((np.ones(int(keep.sum())), (r[keep], c[keep])), shape=(n, n))
        out = (w - clique).tocsr()
        out.data[out.data < 0] = 0.0        # numerical guard; counts cannot go negative
        out.eliminate_zeros()
        return out

    def propagate(mat, seeds):
        p0 = np.zeros(n)
        p0[seeds] = 1.0 / len(seeds)
        colsum = np.asarray(mat.sum(axis=0)).ravel()
        colsum[colsum == 0] = 1.0
        t = mat.multiply(1.0 / colsum)
        p = p0.copy()
        for _ in range(ITERS):
            p = ALPHA * (t @ p) + (1 - ALPHA) * p0
        return p

    # THE CONTROL: a degree-preserving rewiring. Built once, by shuffling the endpoints of the
    # edge list, so the degree sequence survives and no biology does.
    rng = np.random.default_rng(SEED)
    coo = w.tocoo()
    perm = rng.permutation(len(coo.data))
    w_null = csr_matrix((coo.data, (coo.row, coo.col[perm])), shape=w.shape)
    w_null = ((w_null + w_null.T) * 0.5).tocsr()

    rows_out = []
    for disease, members in sorted(by_disease.items()):
        members = sorted(set(members))
        if len(members) < MIN_GENES or len(members) > MAX_GENES:
            continue
        ids = [gidx[g] for g in members]
        rng.shuffle(ids)
        half = len(ids) // 2
        seeds, hidden = ids[:half], set(ids[half:])

        mask = np.ones(n, dtype=bool)
        mask[seeds] = False
        y = np.zeros(n)
        y[list(hidden)] = 1.0
        if y[mask].sum() == 0:
            continue

        # Intrinsic: cosine to the seed centroid in attribute space. No edges consulted.
        centroid = feats_n[seeds].mean(axis=0)
        cn = np.linalg.norm(centroid) or 1.0
        s_intrinsic = feats_n @ (centroid / cn)

        s_relational = propagate(graph_without(disease), seeds)
        s_null = propagate(w_null, seeds)

        a = float(average_precision_score(y[mask], s_relational[mask]))
        b = float(average_precision_score(y[mask], s_intrinsic[mask]))
        c = float(average_precision_score(y[mask], s_null[mask]))
        rows_out.append({
            "disease": disease, "genes": len(members),
            "auprc_relational": round(a, 5),
            "auprc_intrinsic": round(b, 5),
            "auprc_degree_matched_null": round(c, 5),
            "delta": round(a - b, 5),
            "delta_over_null": round(a - c, 5),
        })

    if not rows_out:
        print("no disease met the size criteria", file=sys.stderr)
        return 1

    delta = np.array([r["delta"] for r in rows_out])
    over_null = np.array([r["delta_over_null"] for r in rows_out])
    boot = [float(np.mean(rng.choice(delta, size=len(delta), replace=True)))
            for _ in range(args.draws)]
    mean = float(delta.mean())
    lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))

    killed = (mean <= 0) or (lo <= 0 <= hi) or (abs(mean) < 0.01 and lo <= 0 <= hi)

    payload = {
        "generated": "tools/relational_primacy.py",
        "whose_hypothesis": (
            "Yuri Freitas. The biomedical, falsifiable form of what he calls the Campo "
            "Simbiótico Não-Originário. Its cosmological form - that there is no fundamental "
            "origin, only configuration - has no falsifier in any public dataset, and his own "
            "notes say so."),
        "enunciado": (
            "Biomedical entities should be more predictable from their RELATIONS than from "
            "their intrinsic attributes in isolation: P(D | N(g), paths(g)) against "
            "P(D | features(g))."),
        "precedent": (
            "Ontic structural realism - Ladyman, Ross, Spurrett & Collier, 'Every Thing Must "
            "Go', OUP 2007, DOI 10.1093/acprof:oso/9780199276196.003.0003; and Rovelli, "
            "'Relational Quantum Mechanics', Int. J. Theor. Phys. 35, 1637 (1996), DOI "
            "10.1007/BF02302261. That properties are relational is not new. His addition - "
            "possibility → tension → stabilisation, and origin replaced by configuration - is "
            "metaphysics, and is not what is tested here."),
        "leave_one_disease_out": (
            "The graph's edges ARE disease co-membership, so the disease under test is removed "
            "from the graph before its own genes are predicted. Without this the seeds and the "
            "hidden genes are joined by edges that exist because of the very disease being "
            "predicted: the first run of this file returned ΔAUPRC = +0.925 with the "
            "relational arm winning 100% of 155 diseases, which is a leak rather than a "
            "result."),
        "fairness": (
            "Both arms get the SAME seed genes and differ only in what they do with them. The "
            "intrinsic arm scores how much a gene RESEMBLES the seeds in the eleven-dimensional "
            "attribute space (cosine to the seed centroid, no edges consulted); the relational "
            "arm scores how strongly the seeds REACH it (random walk with restart, no "
            "attributes consulted). Giving only one arm the disease's identity would measure "
            "the experimental design instead of the hypothesis."),
        "genes": n,
        "features": cols,
        "diseases_scored": len(rows_out),
        "delta_auprc": {
            "mean": round(mean, 5),
            "ci95": [round(lo, 5), round(hi, 5)],
            "median": round(float(np.median(delta)), 5),
            "share_relational_wins": round(float((delta > 0).mean()), 4),
            "bootstrap_draws": args.draws,
        },
        "against_a_degree_matched_null": {
            "mean": round(float(over_null.mean()), 5),
            "share_positive": round(float((over_null > 0).mean()), 4),
            "says": ("The relational arm re-run on a rewiring with the same degree sequence "
                     "and none of the biology. If its advantage survived there, the advantage "
                     "would be the degree sequence."),
        },
        "falsifier_as_he_wrote_it": {
            "statement": ("seriously weakened if ΔAUPRC <= 0 consistently, or if relations add "
                          "less than 0.01 with a 95% interval containing zero"),
            "triggered": bool(killed),
        },
        "per_disease": sorted(rows_out, key=lambda r: -r["delta"])[:40],
        "per_disease_worst": sorted(rows_out, key=lambda r: r["delta"])[:10],
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    print(f"  {len(rows_out)} diseases scored")
    print(f"  relational - intrinsic  = {mean:+.5f}  95% [{lo:+.5f}, {hi:+.5f}]  "
          f"({(delta > 0).mean() * 100:.1f}% of diseases)")
    print(f"  relational - degree null = {over_null.mean():+.5f}  "
          f"({(over_null > 0).mean() * 100:.1f}% of diseases)")
    print(f"  falsifier: {'TRIGGERED' if killed else 'not triggered'}")
    print(f"\nwrote {DEST.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
