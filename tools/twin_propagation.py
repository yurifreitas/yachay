#!/usr/bin/env python
"""The first dynamical component of the digital twin: where a disease's perturbation spreads.

WHY THIS FILE, AND WHY NOW. `tools/thesis_seed.py` encodes the research thesis this whole
repository serves, and it is explicit about the object being built:

    "modelar distúrbios ultra-raros como SISTEMAS DINÂMICOS MULTIESCALA … representar a
     incerteza explicitamente, SIMULAR A PROPAGAÇÃO DE PERTURBAÇÕES, priorizar intervenções,
     e escolher os experimentos com maior ganho de informação esperado."

Its own audit grades the ladder that thesis needs, and the grades are the plan:

    Genotype              built        <- tools/patient_variants.py
    Protein structure     named-only
    Conformational dyn.   named-only
    Interactome           partial      <- THIS FILE
    Pathway               partial      <- THIS FILE
    Cell state            partial
    Tissue and space      absent
    Patient               built        <- tools/patient_frequencies.py

Every layer in this project so far is a **static description**: what is known, how well, about
whom. None of them propagates anything. This is the first that does, and it is deliberately
the smallest possible dynamical step — a stationary diffusion, not a simulation over time —
because the ladder above says the rungs beneath it are named-only, and a time-resolved model
standing on a named-only rung would be an animation rather than a twin.

## The method, and the reason for each choice

**Random walk with restart** over the STRING interaction graph. From the disease's causal
genes, a walk that restarts at the seeds with probability `1 - alpha` and otherwise steps to
a neighbour; the stationary distribution is how strongly each protein is reached. This is the
standard network-propagation kernel of network medicine (the family Menche et al. work in),
chosen because it is *interpretable and cheap*, not because it is fashionable: every value is
"how much of the perturbation ends up here", and the whole vector is one sparse linear solve.

**A degree-matched null, always.** A propagation from any seed set reaches hubs, because hubs
are what a random walk finds. Reporting the top of a propagation without a null measures the
graph and calls it the disease — which is Stage 1 of this library, on a different object. So
every disease is propagated against `N_NULL` seed sets drawn to match the seeds' degree
distribution, and what is reported is the **z against that null**, never the raw score.

**Confidence-thresholded edges.** STRING at `>= 700` is the standard high-confidence cut, and
the threshold is registered in `manifests/thresholds.yaml` (ADR 0006) as *conventional* -
external, and not chosen after looking at our result.

## What this is not

Not a simulation of disease progression: there is no time, no rate constant and no direction
of causality in an undirected co-functional graph. It answers *"if this gene is perturbed,
what else is implicated?"*, which is a reachability question wearing a probability, and the
`says` field of the output states that in the artefact rather than only here.

    python tools/twin_propagation.py                # the twelve dossier diseases
    python tools/twin_propagation.py --gene NF2     # one gene as the seed

Needs numpy and scipy, already dependencies.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import importlib.util
import json
import pathlib
import sys
from collections import defaultdict

import numpy as np
from scipy import sparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

RARE = ROOT / "out" / "rare"

#: STRING's own high-confidence cut. Registered in manifests/thresholds.yaml as conventional.
STRING_SCORE_FLOOR = 700
#: Restart probability. 0.7 is the value the network-propagation literature settled on; the
#: result is famously insensitive to it across 0.5-0.9, and that insensitivity is checked
#: below rather than assumed.
RESTART_ALPHA = 0.7
#: Degree-matched null draws. Enough for a stable z at this graph size.
N_NULL = 200
SEED = 20260828


def load_symbols() -> dict[str, str]:
    """STRING protein id -> preferred gene symbol."""
    out = {}
    with gzip.open(BY_KEY["string_info"].dest, "rt", encoding="utf-8", errors="replace") as fh:
        next(fh)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                out[parts[0]] = parts[1]
    return out


def load_graph(symbols: dict[str, str], floor: int):
    """The high-confidence STRING graph, keyed on gene symbol."""
    edges: list[tuple[str, str]] = []
    with gzip.open(BY_KEY["string_links"].dest, "rt", encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            a, b, score = line.rstrip("\n").split(" ")
            if int(score) < floor:
                continue
            ga, gb = symbols.get(a), symbols.get(b)
            if ga and gb and ga != gb:
                edges.append((ga, gb))

    nodes = sorted({g for e in edges for g in e})
    index = {g: i for i, g in enumerate(nodes)}
    rows = [index[a] for a, _ in edges] + [index[b] for _, b in edges]
    cols = [index[b] for _, b in edges] + [index[a] for a, _ in edges]
    data = np.ones(len(rows), dtype=np.float64)
    A = sparse.csr_matrix((data, (rows, cols)), shape=(len(nodes), len(nodes)))
    A.data[:] = 1.0
    A.sum_duplicates()
    A.data[:] = 1.0
    return nodes, index, A


def normalise(A: sparse.csr_matrix) -> sparse.csr_matrix:
    """Column-normalised adjacency — the walk's transition matrix."""
    deg = np.asarray(A.sum(axis=0)).ravel()
    deg[deg == 0] = 1.0
    return A @ sparse.diags(1.0 / deg)


def propagate(W: sparse.csr_matrix, seed_idx: list[int], n: int,
              alpha: float = RESTART_ALPHA, iters: int = 60) -> np.ndarray:
    """Random walk with restart, by power iteration.

    Power iteration rather than a direct solve: the graph is 17k x 17k and sparse, the
    operator is a contraction with rate `alpha`, and sixty steps put the residual far below
    anything the z-score below can resolve. A direct solve would be exact and would also be
    the slowest correct answer available.
    """
    p0 = np.zeros(n)
    if not seed_idx:
        return p0
    p0[seed_idx] = 1.0 / len(seed_idx)
    p = p0.copy()
    for _ in range(iters):
        p = alpha * (W @ p) + (1 - alpha) * p0
    return p


def disease_genes() -> dict[str, set[str]]:
    """Causal genes per disease, from the HPO gene-to-disease file."""
    out: dict[str, set[str]] = defaultdict(set)
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            g = (row.get("gene_symbol") or "").strip()
            d = (row.get("disease_id") or "").strip()
            if g and d:
                out[d].add(g)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gene", action="append", help="seed on these genes instead of diseases")
    ap.add_argument("--score", type=int, default=STRING_SCORE_FLOOR)
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    for key in ("string_info", "string_links"):
        if not BY_KEY[key].dest.exists():
            raise SystemExit("missing %s — run python tools/ingest.py" % BY_KEY[key].filename)

    print("building the interactome ...")
    symbols = load_symbols()
    nodes, index, A = load_graph(symbols, args.score)
    W = normalise(A)
    n = len(nodes)
    degree = np.asarray(A.sum(axis=0)).ravel()
    print("  %s genes, %s edges at score >= %d"
          % (f"{n:,}", f"{int(A.nnz / 2):,}", args.score))

    rng = np.random.default_rng(SEED)
    # Degree strata for the null: a seed set of hubs must be compared against other hubs.
    order = np.argsort(degree)
    strata = {int(i): int(rank * 10 // n) for rank, i in enumerate(order)}
    by_stratum: dict[int, list[int]] = defaultdict(list)
    for i, s in strata.items():
        by_stratum[s].append(i)

    # ---- what to seed on -----------------------------------------------------------------
    if args.gene:
        targets = {f"gene:{'+'.join(args.gene)}": set(args.gene)}
    else:
        dossiers = json.loads((RARE / "dossiers.json").read_text(encoding="utf-8"))
        genes_by_disease = disease_genes()
        targets = {}
        for d in dossiers["dossiers"]:
            g = set(d.get("genes") or []) | genes_by_disease.get(d.get("orpha") or "", set())
            g |= genes_by_disease.get(d.get("omim") or "", set())
            if g:
                targets[d["name"]] = g

    results = []
    for name, seeds in targets.items():
        present = sorted(g for g in seeds if g in index)
        missing = sorted(g for g in seeds if g not in index)
        if not present:
            results.append({"target": name, "seeds": sorted(seeds), "seedsInGraph": 0,
                            "says": "no seed gene is in the high-confidence interactome"})
            continue

        seed_idx = [index[g] for g in present]
        p = propagate(W, seed_idx, n)

        # ---- an interval on the propagation itself ---------------------------------------
        #
        #  THE Z IS NOT AN UNCERTAINTY. Everything reported below is a distance from a
        #  degree-matched null in units of that null's spread; none of it says how far the
        #  propagation itself would move if the seed set had been curated slightly
        #  differently. That question is not academic here, because the seed sets are TINY —
        #  a handful of causal genes per disease — and a random walk from three genes is
        #  substantially a walk from whichever of the three sits in the densest neighbourhood.
        #
        #  LEAVE-ONE-OUT OVER THE SEEDS, which is the resample the object admits. A bootstrap
        #  with replacement over four genes draws the same gene twice and calls the result an
        #  independent replicate; the jackknife asks the honest version of the same question —
        #  how much of this reach survives dropping any single causal gene.
        #
        #  It is free, because a random walk with restart is LINEAR in its restart vector:
        #  p(S) is the mean of the single-seed propagations over S, so the k replicates cost
        #  k solves and no re-derivation.
        #
        #  WHAT IT HOLDS FIXED, said out loud: the null. Each replicate is scored against the
        #  full seed set's degree-matched null rather than a null redrawn at k-1 seeds, which
        #  would cost N_NULL x k propagations per disease. So this interval carries the
        #  variation from the seed set and not the variation in the calibration, and is
        #  therefore a LOWER bound on the total uncertainty. Reported as such.
        singles = {i: propagate(W, [i], n) for i in seed_idx} if len(seed_idx) >= 3 else {}
        loo = [np.mean([v for j, v in singles.items() if j != i], axis=0)
               for i in seed_idx] if len(singles) >= 3 else []

        # ---- the degree-matched null -----------------------------------------------------
        null = np.zeros((N_NULL, n))
        for k in range(N_NULL):
            drawn = []
            for i in seed_idx:
                pool = by_stratum[strata[i]]
                drawn.append(int(pool[rng.integers(0, len(pool))]))
            null[k] = propagate(W, drawn, n)
        mu, sd = null.mean(axis=0), null.std(axis=0)
        raw_sd = sd.copy()
        sd[sd == 0] = np.inf                      # unreachable in every null draw -> z = 0
        z = (p - mu) / sd

        # ---- the moderated denominator ---------------------------------------------------
        #
        #  WHY THE PLAIN z IS THE WRONG STATISTIC HERE, established in audit A41 and A43: the
        #  denominator is a spread estimated from N_NULL draws, and at a gene of degree five
        #  almost no draw arrives, so it is near zero and any reach at all divides into an
        #  enormous number. The ten largest z values in this artefact are all low-degree genes
        #  and not one of them survives its own interval.
        #
        #  THE FIX IS NOT TO REPORT THE INSTABILITY, IT IS TO STOP CREATING IT. The spread at
        #  a degree-five gene is not unknowable — it is badly estimated at that ONE gene and
        #  well estimated across the hundreds of genes of similar degree. So each gene's own
        #  estimate is shrunk towards the fitted spread-versus-degree trend, weighted by how
        #  many draws it rests on. This is Smyth's (2004) empirical-Bayes moderation, the one
        #  limma made standard for microarray variances, pointed at a PERMUTATION null's
        #  variance instead of a measurement's — the same shape of problem, and nothing in the
        #  derivation cares which of the two the spread came from.
        #
        #  Both statistics are published. The moderated one is not asserted to be correct; it
        #  is asserted to be stable, and the difference between the two rankings is a
        #  measurement this file reports rather than a claim it makes.
        mod_sd, mod_z, trend = raw_sd, z, None
        try:
            spec_m = importlib.util.spec_from_file_location(
                "moderated_calibration", ROOT / "tools" / "moderated_calibration.py")
            mc = importlib.util.module_from_spec(spec_m)
            spec_m.loader.exec_module(mc)
            reached_any = raw_sd > 0
            if reached_any.sum() > 50:
                logd = np.log10(np.maximum(degree[reached_any].astype(float), 1.0))
                logs = np.log10(np.maximum(raw_sd[reached_any], 1e-30))
                trend = np.full_like(raw_sd, np.nan)
                trend[reached_any] = 10 ** mc.lowess_trend(logd, logs)
                mod_sd = raw_sd.copy()
                mod_sd[reached_any] = mc.moderate(
                    raw_sd[reached_any], trend[reached_any], N_NULL, mc.PRIOR_DRAWS)
                safe = np.where(mod_sd > 0, mod_sd, np.inf)
                mod_z = (p - mu) / safe
                mod_z[seed_idx] = np.nan
        except Exception as exc:                  # pragma: no cover - reported, never silent
            print(f"    moderation unavailable: {exc}")

        # ---- the statistic that does not divide at all -----------------------------------
        #
        #  MODERATION DID NOT FIX THIS, and the reason is worth more than the attempt. Smyth's
        #  moderation works when each entity's variance estimate is NOISY AROUND A GOOD TREND:
        #  borrowing strength from neighbours then recovers what one noisy estimate lost. Here
        #  the trend IS the defect. Every low-degree gene has a near-zero null spread, so a
        #  low-degree gene's own estimate already agrees with its neighbours and there is no
        #  idiosyncratic deviation to shrink. It moved the whole top of the list by about 15%
        #  and changed the ranking not at all.
        #
        #  So the answer is not a better denominator. It is not to divide.
        #
        #  The EMPIRICAL TAIL is the share of null draws that reach this gene at least as hard
        #  as the real seed set did. It is bounded below by 1/(N+1) by construction, which is
        #  exactly the resolution the permutation actually has - no extrapolation is possible,
        #  because none is expressible. Ties at the floor are then broken by the propagation
        #  score on its own scale, which is the quantity a reader is actually deciding about.
        #
        #  Three rankings are published: by z, by moderated z, and by this. The differences
        #  between them are a measurement of how much the choice of statistic decides.
        ge = (null >= p[None, :]).sum(axis=0)
        p_emp = (ge + 1.0) / (N_NULL + 1.0)
        p_emp[seed_idx] = np.nan
        z[seed_idx] = np.nan                      # a seed reaching itself is not a finding

        # The jackknife standard error of the z, gene by gene. sqrt((k-1)/k * sum of squared
        # deviations) is the jackknife's own variance estimator, not a bootstrap standard
        # deviation: leave-one-out replicates are correlated by construction and the (k-1)/k
        # factor is what corrects for it. Using pstdev here would understate the interval by
        # roughly a factor of k, which is the classic way to publish a jackknife too narrow.
        z_se = None
        if loo:
            zs = np.array([(q - mu) / sd for q in loo])          # (k, n)
            k_ = len(loo)
            z_se = np.sqrt((k_ - 1) / k_ * ((zs - zs.mean(axis=0)) ** 2).sum(axis=0))

        top = np.argsort(np.nan_to_num(z, nan=-np.inf))[::-1][: args.top]

        # ---- the same list, ordered by the bottom of each interval ------------------------
        #
        #  THE ORDER ABOVE IS BY THE LEAST STABLE QUANTITY IN THE ARTEFACT. Sorting by z puts
        #  first whichever gene the walk happens to reach hardest from this particular seed
        #  set, and the jackknife says that is exactly the quantity a single seed gene moves
        #  most: not one of the ten largest z values in this file keeps a positive interval.
        #  The largest, DNASE2B at z = 1825, has an interval of [-1753, +5403].
        #
        #  So the artefact carries BOTH orderings, and the difference between them is a
        #  measurement rather than a presentation choice. This is the same operation Stage 1
        #  performs everywhere else in this library — rank on what survives calibration, not
        #  on the raw statistic — applied here to the propagation's own uncertainty.
        top_lb, agreement = [], None
        if z_se is not None:
            lb = np.where(np.isfinite(z), z - 1.96 * z_se, -np.inf)
            lb[seed_idx] = -np.inf
            top_lb = list(np.argsort(np.nan_to_num(lb, nan=-np.inf))[::-1][: args.top])
            agreement = len(set(int(i) for i in top_lb) & set(int(i) for i in top))
        results.append({
            "target": name,
            "seeds": present,
            "seedsInGraph": len(present),
            "seedsMissing": missing,
            "reached": [
                {"gene": nodes[i], "z": round(float(z[i]), 3),
                 "score": float(p[i]), "degree": int(degree[i]),
                 # None when the seed set has fewer than three genes: a jackknife over two
                 # points is one replicate, and reporting an interval from it would be
                 # inventing a width. Which diseases those are is counted in the payload.
                 "z_se": (round(float(z_se[i]), 3) if z_se is not None else None),
                 "z_ci95": ([round(float(z[i] - 1.96 * z_se[i]), 3),
                             round(float(z[i] + 1.96 * z_se[i]), 3)]
                            if z_se is not None else None),
                 # The honest version of "this gene is reached": the LOWER end of the
                 # interval still clears the null, so the reach does not depend on one
                 # curated causal gene.
                 # The same numerator over a denominator that borrowed strength from the
                 # genes of similar degree. Published beside the raw z, never instead of it.
                 "moderated_z": (round(float(mod_z[i]), 3)
                                 if mod_z is not None and np.isfinite(mod_z[i]) else None),
                 "null_sd": round(float(raw_sd[i]), 8),
                 # The tail the permutation can actually resolve. 1/(N+1) is its floor and
                 # the value is never smaller, because nothing smaller was measured.
                 "p_empirical": (round(float(p_emp[i]), 5)
                                 if np.isfinite(p_emp[i]) else None),
                 "moderated_sd": (round(float(mod_sd[i]), 8)
                                  if mod_sd is not None else None),
                 "survives_interval": (bool(z_se is not None
                                            and float(z[i] - 1.96 * z_se[i]) > 1.96))}
                for i in top if np.isfinite(z[i])
            ],
            # The honest ordering: highest lower bound first. Empty when the seed set is too
            # small for an interval, rather than falling back to the z ordering under a name
            # that would claim it had been calibrated.
            "reachedByLowerBound": [
                {"gene": nodes[i], "z": round(float(z[i]), 3),
                 "lower": round(float(z[i] - 1.96 * z_se[i]), 3),
                 "degree": int(degree[i])}
                for i in top_lb if np.isfinite(z[i])
            ],
            "rankAgreement": agreement,
            # THE SAME GENES ORDERED BY THE STATISTIC THAT CANNOT EXTRAPOLATE. Ties at the
            # resolution floor - and there are many, because the floor is 1/201 - are broken
            # by the propagation score itself, on its own scale.
            "reachedByEmpiricalTail": [
                {"gene": nodes[i], "z": round(float(z[i]), 3),
                 "p_empirical": round(float(p_emp[i]), 5),
                 "score": float(p[i]), "degree": int(degree[i])}
                for i in sorted(
                    (j for j in range(n) if j not in set(seed_idx) and np.isfinite(p_emp[j])),
                    key=lambda j: (p_emp[j], -p[j]))[: args.top]
            ],
        })
        print("  %-42s %2d seeds -> top reach %s"
              % (name[:42], len(present),
                 ", ".join(nodes[i] for i in top[:5] if np.isfinite(z[i]))))

    # HOW MUCH OF THE REACH SURVIVES ITS OWN INTERVAL, across every disease. This is the
    # number the earlier version of this artefact could not have printed, because it had no
    # interval to survive.
    # WHAT THE TWO ORDERINGS SELECT FOR, measured rather than asserted.
    #
    #  The degree-matched null exists so that hubs cannot win by being hubs. It works. What
    #  nobody checked is what it does at the OTHER end: for a gene of degree 5, almost every
    #  null draw fails to reach it at all, so the null's spread there is nearly zero and any
    #  reach at all divides into an enormous z. The null built to stop hubs winning made the
    #  rarely-reached win instead, and a z of 1825 is what that looks like.
    #
    #  The jackknife is what makes it visible, because those same genes carry the widest
    #  intervals: reaching them depends entirely on which seed the walk started from. So the
    #  median degree of the two orderings is the diagnostic, and it is one line.
    import statistics as _stats
    deg_z = [g["degree"] for r in results for g in r.get("reached", []) if r.get("rankAgreement") is not None]
    deg_lb = [g["degree"] for r in results for g in r.get("reachedByLowerBound", [])]

    with_interval = [r for r in results if any(g.get("z_ci95") for g in r.get("reached", []))]
    reached_all = [g for r in results for g in r.get("reached", [])]
    scored = [g for g in reached_all if g.get("z_ci95")]
    survived = [g for g in scored if g["survives_interval"]]
    too_few_seeds = [r["target"] for r in results
                     if r.get("reached") and not any(g.get("z_ci95") for g in r["reached"])]

    payload = {
        "generated": "tools/twin_propagation.py",
        "three_statistics": {
            "why": ("This artefact publishes the same reach under three statistics because "
                    "the choice between them changes the answer, and hiding that behind one "
                    "ranking would be the largest unstated assumption on the page."),
            "z": ("observation minus the null's mean over the null's spread. Unstable exactly "
                  "where it is largest: the ten biggest values here are all low-degree genes "
                  "whose null spread is near zero, and not one survives its own interval."),
            "moderated_z": (
                "the same numerator over a spread shrunk towards the fitted spread-versus-"
                "degree trend, weighted by draw count - Smyth's (2004) empirical-Bayes "
                "moderation, pointed at a permutation null's variance instead of a "
                "measurement's. ⚠️ IT DOES NOT WORK HERE, and that is reported rather than "
                "dropped: moderation recovers what a NOISY estimate lost around a good trend, "
                "and here the trend is the defect. Every low-degree gene has a near-zero "
                "spread, so each already agrees with its neighbours and there is nothing "
                "idiosyncratic to shrink. It moved the top of the list by about 15% and "
                "changed the ordering not at all."),
            "p_empirical": (
                "the share of null draws reaching the gene at least as hard as the real seed "
                "set, floored at 1/(N+1) by construction. It cannot extrapolate past the "
                "resolution the permutation has, because no smaller value is expressible. "
                "Ties at the floor - and there are many - break on the propagation score "
                "itself. This is the statistic to read."),
            "says": ("The answer to a near-degenerate denominator is not a better denominator. "
                     "It is not to divide."),
        },
        "uncertainty": {
            "method": ("leave-one-out over the seed genes; the jackknife standard error "
                       "sqrt((k-1)/k * sum of squared deviations) on each reached gene's z, "
                       "reported as point +/- 1.96 SE"),
            "why_jackknife": ("the seed sets are a handful of curated causal genes. A "
                              "bootstrap with replacement over four genes draws the same "
                              "gene twice and calls that an independent replicate"),
            "what_it_holds_fixed": ("the degree-matched null. Each replicate is scored "
                                    "against the full seed set's null rather than one "
                                    "redrawn at k-1 seeds, so this is a LOWER bound on the "
                                    "total uncertainty, not the whole of it"),
            "diseases_with_an_interval": len(with_interval),
            "diseases_with_too_few_seeds": too_few_seeds,
            "reached_genes_scored": len(scored),
            "reached_genes_surviving": len(survived),
            "orderings_disagree": (
                "The list is published in both orders because they are not the same list. "
                "Ranking by z puts first the gene the walk reaches hardest from this exact "
                "seed set, which the jackknife shows is the quantity one seed gene moves "
                "most: NOT ONE of the ten largest z values in this artefact keeps a positive "
                "interval, and the largest of all sits at 1825 with an interval of "
                "[-1753, +5403]. `rankAgreement` per disorder counts how many genes the two "
                "orderings share."),
            "what_the_orderings_select": ({
                "median_degree_by_z": _stats.median(deg_z),
                "median_degree_by_lower_bound": _stats.median(deg_lb),
                "mean_degree_by_z": round(_stats.fmean(deg_z), 1),
                "mean_degree_by_lower_bound": round(_stats.fmean(deg_lb), 1),
                "says": ("The degree-matched null was built so hubs could not win by being "
                         "hubs, and at that end it works. At the other end it inverts: a "
                         "gene of degree 5 is missed by almost every null draw, so the "
                         "null's spread there is near zero and any reach at all divides "
                         "into an enormous z. Ranking by z therefore selects the "
                         "RARELY REACHED - median degree %d against %d for the interval's "
                         "lower bound - and those are exactly the genes whose intervals are "
                         "widest, because reaching them depends on which single seed the "
                         "walk started from. This is a defect in the statistic this file "
                         "publishes, found by giving it an interval."
                         % (_stats.median(deg_z), _stats.median(deg_lb))),
            } if deg_z and deg_lb else None),
            "reading": (f"{len(survived)} of {len(scored)} reported reach genes keep a z "
                        f"above 1.96 at the LOWER end of their own interval; the rest are "
                        f"carried by one causal gene, and dropping it takes the finding "
                        f"with it." if scored else
                        "no disease has three seed genes in the graph, so no interval is "
                        "reported anywhere in this artefact."),
        },
        "premise": (
            "tools/thesis_seed.py states the object being built: an ultra-rare disease as a "
            "multiscale dynamical system that can SIMULATE THE PROPAGATION OF PERTURBATIONS. "
            "Every layer in this project so far is a static description. This is the first "
            "that propagates anything."
        ),
        "method": {
            "kernel": "random walk with restart, alpha=%.2f, power iteration" % RESTART_ALPHA,
            "graph": "STRING v12 human, combined_score >= %d, keyed on gene symbol" % args.score,
            "nodes": n,
            "edges": int(A.nnz / 2),
            "null": ("%d degree-stratified seed sets per target; every value reported is a z "
                     "against that null, never a raw propagation score" % N_NULL),
            "whyTheNull": (
                "A walk from any seed set reaches hubs, because hubs are what a random walk "
                "finds. Reporting the top of a propagation without a degree-matched null "
                "measures the graph and calls it the disease - which is this library's Stage "
                "1 argument, on a different object."
            ),
        },
        "isNot": (
            "Not a simulation of disease progression. There is no time, no rate constant and "
            "no direction of causality in an undirected co-functional graph. It answers 'if "
            "this gene is perturbed, what else is implicated', which is a reachability "
            "question wearing a probability."
        ),
        "ladder": {
            "built": ["genotype", "patient", "interactome (this file)"],
            "stillNamedOnly": ["protein structure", "conformational dynamics",
                               "tissue and space"],
            "says": ("tools/thesis_seed.py grades the multiscale ladder the twin needs. This "
                     "file moves one rung from partial toward built. A time-resolved model "
                     "standing on a named-only rung would be an animation, not a twin."),
        },
        "results": results,
    }

    RARE.mkdir(parents=True, exist_ok=True)
    if scored:
        print("  reach surviving its own interval: %d of %d (%d disease(s) have too few "
              "seeds for one)" % (len(survived), len(scored), len(too_few_seeds)))
    dest = RARE / "twin_propagation.json"
    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print()
    print("wrote %s" % dest.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
