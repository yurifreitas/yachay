#!/usr/bin/env python
"""Does asymmetry carry information the symmetric projection loses?

WHOSE QUESTION THIS IS. Not this repository's. It is Yuri Freitas' own hypothesis, recovered
from his notes on what he calls symbiotic mathematics, and it is implemented here in the form
he stated it — with the falsifier he wrote before any number existed:

    ENUNCIADO   A relation r_ij need not equal r_ji. A may attract B while B repels A, and the
                claim is that this NON-RECIPROCITY generates organisation, not merely that
                interaction does. The operator is the comparison of a system against its own
                symmetric projection:

                    Δ_sym = Q(R) − Q((R + Rᵀ)/2)

    FALSIFIER   The strong form dies if E[S_NR] ≤ 0 with a 95% interval containing zero over a
                wide sample of diseases; more strictly, if |S_NR| < 0.01 in at least 80% of
                diseases evaluated and no benefit survives permutation controls.

That falsifier is why this file exists rather than an essay. A hypothesis with a stated number
that would kill it is a scientific hypothesis; the same idea without one is a pretty analogy,
and his own notes say so about the parts that lack it.

## The asymmetry, and where it comes from

No new data. The gene–disease catalogue already gives a naturally asymmetric affinity:

    w(i → j) = |D_i ∩ D_j| / |D_i|

the share of gene i's diseases that gene j also causes. It is asymmetric exactly when the two
genes have different disease counts — a gene implicated in one disease is entirely accounted
for by a hub that shares it, while the hub is barely touched in return. That is the shape of
relation his hypothesis is about, and it is not an artefact: it is conditional probability,
and conditional probability is not symmetric.

The symmetric projection W_s = (W + Wᵀ)/2 is the control. It holds the same pairs and the same
total affinity mass and destroys only the direction.

## The task both are judged on

Recovery of held-out disease genes. For each disease with enough genes, half are given as
seeds and the other half hidden; a random walk with restart from the seeds ranks every other
gene, and the ranking is scored on whether it puts the hidden half near the top. AUPRC rather
than AUROC, because the positives are a handful of genes among thousands and AUROC is
generous in exactly that regime.

    S_NR = AUPRC(W) − AUPRC(W_s)

per disease, then the mean with a bootstrap interval over diseases — the quantity his
falsifier is written against.

    python tools/nonreciprocal.py
    python tools/nonreciprocal.py --draws 200

Requires numpy, scipy, scikit-learn.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import pathlib
import statistics
import sys

import numpy as np
from scipy.sparse import csr_matrix

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "rare" / "nonreciprocal.json"

SEED = 20260831

#: A disease needs this many annotated genes to be scored: half become seeds and half targets,
#: and below six the split is one or two genes and the AUPRC is a coin toss.
MIN_GENES = 6

#: Restart probability, matching tools/twin_propagation.py so the two are comparable.
ALPHA = 0.7

#: Power-iteration steps. The operator is a contraction at rate ALPHA; sixty steps put the
#: residual far below anything the ranking can resolve.
ITERS = 60

#: Bootstrap resamples over diseases, for the interval the falsifier is written against.
DRAWS = 300


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


def build(genes: list[str], diseases_of: dict[str, set[str]],
          skip: str | None = None) -> csr_matrix:
    """The asymmetric affinity w(i -> j) = |D_i ∩ D_j| / |D_i|.

    Built through the disease index rather than over gene pairs: 5,524 genes is 15 million
    ordered pairs, of which almost none share a disease, and iterating diseases touches only
    the pairs that exist.
    """
    idx = {g: i for i, g in enumerate(genes)}
    by_disease: dict[str, list[int]] = collections.defaultdict(list)
    for g in genes:
        for d in diseases_of[g]:
            # ⚠️ LEAVE-ONE-DISEASE-OUT. The affinity IS disease co-membership, so when disease
            #  D is the one being predicted, its own genes are joined to each other by an edge
            #  that exists because of D. Leaving it in lets both arms read the answer key -
            #  and while it inflates both equally, the comparison between them is then made in
            #  a regime where every score is near its ceiling and differences compress.
            #  tools/relational_primacy.py hit the same leak and returned ΔAUPRC = +0.925.
            if d != skip:
                by_disease[d].append(idx[g])

    shared: dict[tuple[int, int], int] = collections.Counter()
    for members in by_disease.values():
        # A disease naming hundreds of genes is a review article, not a mechanism, and it
        # would contribute a dense block that swamps everything else.
        if len(members) > 60:
            continue
        for a in members:
            for b in members:
                if a != b:
                    shared[(a, b)] += 1

    n = len(genes)
    own = np.array([len(diseases_of[g]) for g in genes], dtype=float)
    rows, cols, vals = [], [], []
    for (a, b), k in shared.items():
        rows.append(a)
        cols.append(b)
        vals.append(k / own[a])          # asymmetric: divided by the SOURCE's own count
    return csr_matrix((vals, (rows, cols)), shape=(n, n))


def propagate(w: csr_matrix, seeds: list[int], n: int) -> np.ndarray:
    """Random walk with restart. `w` is used as given, so direction is respected."""
    p0 = np.zeros(n)
    if not seeds:
        return p0
    p0[seeds] = 1.0 / len(seeds)
    # ⚠️ THE DIRECTION HERE WAS WRONG IN THE FIRST RUN, and it mattered only for the arm the
    # whole experiment is about. `w[i, j]` is the affinity FROM i TO j. Mass must therefore
    # move to j in proportion to w[i, j], which means the transition operator is the ROW-
    # normalised matrix TRANSPOSED. The first version column-normalised and applied `w @ p`,
    # which moves mass to j in proportion to w[j, i] — along the reverse edge.
    #
    # For the symmetric projection W_s the two are identical, so the control arm was correct
    # and the asymmetric arm was propagating backwards. A falsification of a hypothesis about
    # direction, produced by running the direction backwards, would have been worthless.
    rowsum = np.asarray(w.sum(axis=1)).ravel()
    rowsum[rowsum == 0] = 1.0
    t = w.multiply((1.0 / rowsum)[:, None]).T.tocsr()
    p = p0.copy()
    for _ in range(ITERS):
        p = ALPHA * (t @ p) + (1 - ALPHA) * p0
    return p


def auprc(scores: np.ndarray, positives: set[int], exclude: set[int]) -> float:
    from sklearn.metrics import average_precision_score

    mask = np.ones(len(scores), dtype=bool)
    mask[list(exclude)] = False
    y = np.zeros(len(scores))
    y[list(positives)] = 1.0
    if y[mask].sum() == 0:
        return float("nan")
    return float(average_precision_score(y[mask], scores[mask]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--draws", type=int, default=DRAWS)
    args = ap.parse_args()

    diseases_of = gene_disease()
    genes = sorted(diseases_of)
    n = len(genes)
    idx = {g: i for i, g in enumerate(genes)}
    print(f"  {n} genes with a disease annotation")

    w = build(genes, diseases_of)
    wt = w.T.tocsr()
    ws = (w + wt) * 0.5

    # The asymmetry of the operator itself, as his formulation defines it.
    diff = (w - wt)
    a_r = float(np.sqrt((diff.multiply(diff)).sum()) / (np.sqrt((w.multiply(w)).sum()) + 1e-12))
    print(f"  asymmetry ||W - W^T||_F / ||W||_F = {a_r:.4f}")

    by_disease: dict[str, list[str]] = collections.defaultdict(list)
    for g, ds in diseases_of.items():
        for d in ds:
            by_disease[d].append(g)

    rng = np.random.default_rng(SEED)
    rows = []
    for disease, members in sorted(by_disease.items()):
        members = sorted(set(members))
        if len(members) < MIN_GENES or len(members) > 60:
            continue
        ids = [idx[g] for g in members]
        rng.shuffle(ids)
        half = len(ids) // 2
        seeds, hidden = ids[:half], set(ids[half:])

        # Rebuilt per disease so the affinity never contains the disease being predicted.
        w_d = build(genes, diseases_of, skip=disease)
        ws_d = (w_d + w_d.T.tocsr()) * 0.5
        s_asym = propagate(w_d, seeds, n)
        s_sym = propagate(ws_d, seeds, n)
        exclude = set(seeds)
        a = auprc(s_asym, hidden, exclude)
        b = auprc(s_sym, hidden, exclude)
        if math.isnan(a) or math.isnan(b):
            continue
        rows.append({"disease": disease, "genes": len(members), "seeds": len(seeds),
                     "auprc_asymmetric": round(a, 5), "auprc_symmetric": round(b, 5),
                     "s_nr": round(a - b, 5)})

    if not rows:
        print("no disease met the size criteria", file=sys.stderr)
        return 1

    # ---- the permutation control his strict falsifier requires --------------------------
    #
    #  "no benefit survives permutation controls" is a clause in the falsifier, so the benefit
    #  above is not a result until this runs. The control has to destroy DIRECTION and nothing
    #  else, or it would be testing something the hypothesis never claimed.
    #
    #  Decompose W = S + A, with S = (W + Wᵀ)/2 symmetric and A = (W − Wᵀ)/2 antisymmetric.
    #  S is what the control arm already uses. The null flips the SIGN of each antisymmetric
    #  pair at random: the magnitude of the asymmetry survives exactly, gene by gene and pair
    #  by pair, and only which of the two directions is the strong one is randomised. If the
    #  gain comes from having a direction at all rather than from having THIS direction, the
    #  null reproduces it and the hypothesis has not been supported.
    print("  permutation control: randomising the direction of the asymmetry ...")
    sym = (w + wt) * 0.5
    anti = (w - wt) * 0.5
    coo = anti.tocoo()
    upper = coo.row < coo.col
    keys = list(zip(coo.row[upper].tolist(), coo.col[upper].tolist()))
    flip_rng = np.random.default_rng(SEED + 99)
    signs = flip_rng.choice([-1.0, 1.0], size=len(keys))
    sign_of = {k: v for k, v in zip(keys, signs)}

    rr, cc, vv = [], [], []
    for r_, c_, v_ in zip(coo.row.tolist(), coo.col.tolist(), coo.data.tolist()):
        key = (r_, c_) if r_ < c_ else (c_, r_)
        sgn = sign_of.get(key, 1.0)
        rr.append(r_)
        cc.append(c_)
        vv.append(v_ * sgn)
    anti_flipped = csr_matrix((vv, (rr, cc)), shape=w.shape)
    w_null = (sym + anti_flipped).tocsr()

    null_rows = []
    for r in rows:
        members = sorted(set(by_disease[r["disease"]]))
        ids = [idx[g] for g in members]
        rng_d = np.random.default_rng(SEED + hash(r["disease"]) % 10_000)
        rng_d.shuffle(ids)
        half = len(ids) // 2
        seeds, hidden = ids[:half], set(ids[half:])
        w_d = build(genes, diseases_of, skip=r["disease"])
        wt_d = w_d.T.tocsr()
        sym_d = (w_d + wt_d) * 0.5
        anti_d = (w_d - wt_d) * 0.5
        co = anti_d.tocoo()
        rr2, cc2, vv2 = [], [], []
        for r_, c_, v_ in zip(co.row.tolist(), co.col.tolist(), co.data.tolist()):
            key = (r_, c_) if r_ < c_ else (c_, r_)
            rr2.append(r_)
            cc2.append(c_)
            vv2.append(v_ * sign_of.get(key, 1.0))
        w_null_d = (sym_d + csr_matrix((vv2, (rr2, cc2)), shape=w.shape)).tocsr()
        a = auprc(propagate(w_null_d, seeds, n), hidden, set(seeds))
        b = auprc(propagate(sym_d, seeds, n), hidden, set(seeds))
        if not (math.isnan(a) or math.isnan(b)):
            null_rows.append(a - b)

    null_mean = float(np.mean(null_rows)) if null_rows else float("nan")

    s_nr = np.array([r["s_nr"] for r in rows])
    boot = [float(np.mean(rng.choice(s_nr, size=len(s_nr), replace=True)))
            for _ in range(args.draws)]
    mean = float(s_nr.mean())
    lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
    small = float((np.abs(s_nr) < 0.01).mean())
    wins = float((s_nr > 0).mean())

    # HIS FALSIFIER, EVALUATED AS WRITTEN — not paraphrased, and not softened after seeing the
    # numbers. Both clauses are checked and both are reported.
    killed_weak = (mean <= 0) or (lo <= 0 <= hi)
    # The strict form has two clauses joined by AND: mostly-negligible AND no survival against
    # permutation. Both must hold for it to trigger, and both are evaluated.
    survives_permutation = bool(mean > null_mean) if not math.isnan(null_mean) else False
    killed_strict = (small >= 0.8) and not survives_permutation

    payload = {
        "generated": "tools/nonreciprocal.py",
        "whose_hypothesis": (
            "Yuri Freitas, from his own notes on symbiotic mathematics. This file implements "
            "the formulation and the falsifier as he stated them, before any number existed."),
        "enunciado": (
            "A relation r_ij need not equal r_ji: A may attract B while B repels A. The claim "
            "is that NON-RECIPROCITY generates organisation, not merely that interaction "
            "does. The operator is the system against its own symmetric projection, "
            "Δ_sym = Q(R) − Q((R + Rᵀ)/2)."),
        "precedent": (
            "Ivlev et al., 'Statistical Mechanics where Newton's Third Law is Broken', "
            "Phys. Rev. X 5 011035 (2015), DOI 10.1103/PhysRevX.5.011035; Schmickl, Stefanec "
            "& Crailsheim, Sci. Rep. 6 37969 (2016), DOI 10.1038/srep37969. That asymmetry "
            "produces emergent behaviour is NOT new. What may be his is using the difference "
            "between a system and its own symmetric projection as a quantitative operator for "
            "discovering organisation."),
        "leave_one_disease_out": (
            "The affinity IS disease co-membership, so the disease being predicted is removed "
            "from the affinity before its own genes are predicted. Both arms were inflated "
            "equally without it, but every score sat near its ceiling and the difference "
            "between them compressed."),
        "asymmetry_source": (
            "w(i -> j) = |D_i ∩ D_j| / |D_i|, the share of gene i's diseases that gene j also "
            "causes. Asymmetric exactly when two genes have different disease counts, and not "
            "as an artefact: it is a conditional probability, and those are not symmetric."),
        "task": (
            "Recovery of held-out disease genes. Half a disease's genes seed a random walk "
            "with restart; the other half are hidden and the ranking is scored on where it "
            "puts them. AUPRC rather than AUROC because the positives are a handful among "
            "thousands, which is the regime where AUROC flatters."),
        "genes": n,
        "diseases_scored": len(rows),
        "asymmetry_of_the_operator": round(a_r, 4),
        "s_nr": {
            "mean": round(mean, 5),
            "ci95": [round(lo, 5), round(hi, 5)],
            "median": round(float(np.median(s_nr)), 5),
            "share_positive": round(wins, 4),
            "share_below_0.01_in_absolute_value": round(small, 4),
            "bootstrap_draws": args.draws,
        },
        "permutation_control": {
            "method": ("W = S + A with S symmetric and A antisymmetric. The sign of each "
                       "antisymmetric pair is flipped at random, so the MAGNITUDE of the "
                       "asymmetry survives exactly and only its direction is randomised. It "
                       "tests whether the gain comes from having THIS direction or merely "
                       "from having one."),
            "s_nr_under_randomised_direction": (round(null_mean, 5)
                                                if not math.isnan(null_mean) else None),
            "real_exceeds_null": survives_permutation,
        },
        "falsifier_as_he_wrote_it": {
            "weak_form": ("dies if E[S_NR] <= 0 with a 95% interval containing zero over a "
                          "wide sample of diseases"),
            "weak_form_triggered": bool(killed_weak),
            "strict_form": ("dies if |S_NR| < 0.01 in at least 80% of diseases evaluated and "
                            "no benefit survives permutation controls"),
            "strict_form_triggered": bool(killed_strict),
        },
        "per_disease": sorted(rows, key=lambda r: -r["s_nr"])[:40],
        "per_disease_worst": sorted(rows, key=lambda r: r["s_nr"])[:10],
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    print(f"  {len(rows)} diseases scored")
    print(f"  S_NR mean {mean:+.5f}  95% [{lo:+.5f}, {hi:+.5f}]")
    print(f"    positive in {wins * 100:.1f}% of diseases; "
          f"|S_NR| < 0.01 in {small * 100:.1f}%")
    print(f"  randomised direction gives S_NR {null_mean:+.5f} "
          f"(real {mean:+.5f}) -> {'survives' if survives_permutation else 'DOES NOT survive'}")
    print(f"  falsifier: weak form {'TRIGGERED' if killed_weak else 'not triggered'}, "
          f"strict form {'TRIGGERED' if killed_strict else 'not triggered'}")
    print(f"\nwrote {DEST.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
