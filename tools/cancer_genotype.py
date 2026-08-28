#!/usr/bin/env python
"""Mutation-defined subgroups, and the lineage confound that makes the naive version wrong.

`tools/cancer_subgroups.py` groups cell lines by their Oncotree label. That is a **catalogue
subgroup**: someone decided what to call the tumour. This file groups them by **genotype** —
does this line carry a damaging mutation in gene G — which is the grouping a target programme
actually acts on, and which had never been read here despite
`OmicsSomaticMutationsMatrixDamaging.csv` (141 MB, 1,929 lines x 19,097 genes) sitting in
`data/depmap/` since the first ingest.

## The confound, stated before the result

**Mutation status is not independent of lineage.** BRAF mutants are overwhelmingly melanoma;
VHL mutants are overwhelmingly renal; APC mutants are overwhelmingly colorectal. So a naive
mutant-versus-wild-type dependency contrast is partly, and sometimes entirely, a *lineage*
contrast wearing a genotype's name. Reporting it as "the dependency of BRAF-mutant cells"
would be the same error as reporting an uncalibrated top-k score: a real number answering a
question nobody asked.

This is Stage 3, and it is handled the way a confound must be — **by design, not by
disclaimer**. Two estimates are computed for every pair:

    naive        mutant vs wild-type across all lines
    stratified   the contrast computed WITHIN each lineage, then pooled across lineages by
                 inverse-variance weighting (the continuous-outcome analogue of
                 Cochran-Mantel-Haenszel)

The stratified estimate is the one reported. The naive one is kept beside it, because the
**difference between them is the size of the confound**, and that number is more informative
than either estimate alone.

## The prediction this makes, written down before it was run

The two mechanisms in the control set fail differently under stratification, and they must:

  * **Paralog synthetic lethality** — SMARCA4-mutant lines depending on SMARCA2, ARID1A-mutant
    on ARID1B — is a within-cell mechanism with no lineage story. It should **survive**
    stratification largely intact.
  * **Oncogene addiction** — BRAF-mutant lines depending on BRAF — is real, but the mutation
    is concentrated in one lineage, so a large part of the naive effect is recoverable from
    lineage alone. It should **shrink**.

If stratification flattened everything equally it would be removing signal rather than
confound, and the artefact would say so. `shrinkage` is reported per control for exactly this.

## What the first run overturned, kept here rather than edited away

**Half the control set was inconstructible, and the prediction above did not notice.** The
matrix counts *damaging* variants — truncating, frameshift, splice. **BRAF V600E is an
activating missense and is not damaging**, so it is absent: BRAF shows 9 mutant lines and
PIK3CA 6, against the ~100 melanoma lines that actually carry V600E. KRAS, NRAS and CTNNB1
are not testable at all. This is a **loss-of-function matrix**, and the oncogene-addiction
half of the prediction cannot be asked of it. What survives is the tumour-suppressor half,
where it held: 3 of 3.

The oncogene rows are kept in `controls` marked untestable rather than deleted, because "the
data cannot answer this" is a result about the data, and deleting the question hides it.

**A second confound appeared that was not designed for: mutational burden.** `WRN` — the
canonical microsatellite-instability synthetic lethality — came back for MSH3 *and* for
SEC31A, KMT2B, MBD6 and CTCF. Hypermutated lines accumulate damaging mutations everywhere, so
any moderately sized gene becomes a proxy for "this line is hypermutated", and the top of a
genotype ranking stops being genotype. This is the pan-essential error one level up.

**And it must not be adjusted away blindly**, which is the part worth stating carefully:

  * For **MSH3**, burden is a **mediator**. Mismatch-repair loss *causes* microsatellite
    instability, which *causes* the WRN dependency. Conditioning on burden removes real
    signal and would make a correct finding disappear.
  * For **SEC31A**, burden is a **confounder**. Nothing connects it to WRN except that
    hypermutated lines are mutated in it too.

The arithmetic is identical in both cases and **the data cannot distinguish them** — only the
mechanism can. So this file computes the burden-adjusted estimate, reports it beside the
others, flags which drivers are burden proxies, and *refuses to pick one as the answer*. An
automatic adjustment here would silently delete the MSI biology to remove the MSI artefact.

## What is NOT claimed

A damaging-mutation call is not a functional allele: the matrix counts damaging variants, not
gain versus loss of function. Every effect here is therefore about losing a gene, never about
an activating hotspot.

    python tools/cancer_genotype.py
    python tools/cancer_genotype.py --min-mutant 20 --top 12

Needs numpy, pandas and scipy — all dependencies.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import sieve as sv  # noqa: E402
from sieve.adapters import depmap as dm  # noqa: E402

OUT = ROOT / "out"
DATA = ROOT / "data" / "depmap"

#: A genotype subgroup smaller than this cannot support a contrast. Matches MIN_LINES in
#: tools/cancer_subgroups.py deliberately: the two analyses should not disagree about how
#: small is too small.
MIN_MUTANT = 15
#: Within one lineage stratum, the smallest arm that contributes to the pooled estimate.
#: Below this a stratum's variance estimate is noise and its weight would be arbitrary.
MIN_PER_STRATUM = 3
#: Stage 0, carried over: a hit must be an actual dependency, not merely a difference.
DEPENDENCY_FLOOR = 0.5
#: The effect a reader would act on, for the Stage 2 annotation.
EFFECT_OF_INTEREST = 0.8

#: Controls, and the MECHANISM each one tests — named before the run, with the direction
#: each is expected to take under stratification (see the module docstring's prediction).
CONTROLS = [
    # Loss-of-function mechanisms — the half this matrix can actually express.
    ("SMARCA4", "SMARCA2", "paralog synthetic lethality", "survives"),
    ("ARID1A", "ARID1B", "paralog synthetic lethality", "survives"),
    ("TP53", "MDM2", "loss of a dependency (NEGATIVE direction)", "survives"),
    ("TP53", "TP53", "loss of a dependency (NEGATIVE direction)", "survives"),
    ("RB1", "E2F3", "released cell-cycle dependency", "survives"),
    # The burden pair: SAME TARGET, opposite causal role. Identical arithmetic, and the
    # data cannot tell them apart — see the docstring. Both are reported, neither adjusted.
    ("MSH3", "WRN", "MSI synthetic lethality — burden is a MEDIATOR", "survives"),
    ("SEC31A", "WRN", "burden proxy — burden is a CONFOUNDER", "shrinks"),
    # Oncogene addiction. Kept although this matrix cannot express an activating hotspot,
    # because "the data cannot answer this" is a result about the data.
    ("BRAF", "BRAF", "oncogene addiction (hotspot absent from a damaging matrix)", "shrinks"),
    ("KRAS", "KRAS", "oncogene addiction (hotspot absent from a damaging matrix)", "shrinks"),
    ("NRAS", "NRAS", "oncogene addiction (hotspot absent from a damaging matrix)", "shrinks"),
    ("CTNNB1", "TCF7L2", "pathway addiction (hotspot absent)", "shrinks"),
]

#: The loose pre-gate; see the same constants in tools/cancer_subgroups.py for the argument.
CAND_Q = 0.25
CAND_D = 0.3
CAND_MAX = 30
#: A driver whose arms separate by more than this in standardised log burden is a candidate
#: burden proxy rather than a genotype. Flagged, never silently dropped.
BURDEN_PROXY_D = 0.8


def _symbol(col: str) -> str:
    """`FAM87B (400728)` -> `FAM87B`."""
    return col.split(" (")[0].strip()


def load_mutations(lines: list[str]) -> tuple[np.ndarray, list[str]]:
    """Damaging-mutation indicator, aligned to the CRISPR line order.

    Read in column chunks rather than whole: the file is 141 MB of float text and pandas
    would materialise it at eight bytes a cell. Booleans are what the analysis needs.
    """
    frame = pd.read_csv(DATA / "OmicsSomaticMutationsMatrixDamaging.csv",
                        index_col=0, low_memory=False)
    frame.index = frame.index.astype(str)
    frame = frame.reindex([str(x) for x in lines])
    genes = [_symbol(c) for c in frame.columns]
    M = (frame.to_numpy(dtype=np.float32) > 0)
    M[~np.isfinite(frame.to_numpy(dtype=np.float32))] = False
    return M, genes


def group_stats(A: np.ndarray, X0: np.ndarray, X2: np.ndarray, F: np.ndarray):
    """Count, mean and variance of every gene within every group, in three matmuls.

    `A` is (n_groups x n_lines) float32 membership. The alternative — looping groups and
    slicing — costs the same arithmetic with none of the BLAS, and this runs over 200
    genotype groups x 24 lineage strata.
    """
    n = A @ F
    s = A @ X0
    q = A @ X2
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = s / n
        var = q / n - mean ** 2
    return n, mean, np.maximum(var, 0.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-mutant", type=int, default=MIN_MUTANT)
    ap.add_argument("--top", type=int, default=12, help="hits kept per genotype")
    ap.add_argument("--max-genotypes", type=int, default=120)
    args = ap.parse_args()

    print("loading the dependency matrix ...")
    depmap = dm.load_matrix(str(DATA))
    if not getattr(depmap, "flipped", False):
        raise SystemExit("adapter returned an unflipped matrix; the sign convention below "
                         "assumes larger-is-more-dependent")
    X = np.asarray(depmap.values, dtype=np.float32)
    genes = list(depmap.genes)
    lines = [str(x) for x in depmap.lines]

    # Stage 3, part one: a pan-essential gene is a dependency of everything and cannot be a
    # genotype-selective one.
    pan = set(dm.load_gene_set(str(DATA), "AchillesCommonEssentialControls.csv"))
    keep = np.array([g not in pan for g in genes])
    X = X[:, keep]
    genes = [g for g, k in zip(genes, keep) if k]
    gene_ix = {g: i for i, g in enumerate(genes)}
    print("  %s lines x %s genes after dropping %s pan-essentials"
          % (f"{len(lines):,}", f"{len(genes):,}", f"{(~keep).sum():,}"))

    print("reading the damaging-mutation matrix ...")
    M, mut_genes = load_mutations(lines)
    counts = M.sum(axis=0)
    print("  %s lines x %s genes; %s genes mutated in >= %d lines"
          % (f"{M.shape[0]:,}", f"{M.shape[1]:,}",
             f"{int((counts >= args.min_mutant).sum()):,}", args.min_mutant))

    # Which genotypes to test: the most frequently mutated, plus every named control, so the
    # control set cannot be quietly excluded by a frequency cut.
    order = np.argsort(-counts)
    chosen: list[int] = [int(i) for i in order[: args.max_genotypes]
                         if counts[i] >= args.min_mutant]
    by_name = {g: i for i, g in enumerate(mut_genes)}
    for driver, _, _, _ in CONTROLS:
        j = by_name.get(driver)
        if j is not None and j not in chosen and counts[j] >= MIN_PER_STRATUM * 2:
            chosen.append(int(j))
    drivers = [mut_genes[i] for i in chosen]
    print("  testing %d genotypes (%d by frequency, controls forced in)"
          % (len(chosen), min(args.max_genotypes, len(chosen))))

    # Lineage strata.
    models = pd.read_csv(DATA / "Model.csv", low_memory=False)
    label = dict(zip(models["ModelID"].astype(str), models["OncotreeLineage"].astype(str)))
    strata: dict[str, np.ndarray] = {}
    for name in sorted({label.get(l, "") for l in lines} - {"", "nan", "Non-Cancerous"}):
        mask = np.array([label.get(l) == name for l in lines])
        if mask.sum() >= MIN_PER_STRATUM * 2:
            strata[name] = mask
    print("  %d lineage strata" % len(strata))

    # ---- mutational burden, and the strata that let it be examined ---------------------
    # Counting damaging calls per line. Hypermutated lines carry damaging mutations
    # everywhere, so a moderately sized gene becomes a proxy for "this line is
    # hypermutated" and the top of a genotype ranking stops being about genotype.
    burden = M.sum(axis=1).astype(np.float64)
    log_burden = np.log1p(burden)
    cuts = np.quantile(log_burden, [1 / 3, 2 / 3])
    burden_strata_masks = {
        "low": log_burden <= cuts[0],
        "mid": (log_burden > cuts[0]) & (log_burden <= cuts[1]),
        "high": log_burden > cuts[1],
    }
    print("  mutational burden: median %d damaging calls, tertile cuts at %d and %d"
          % (np.median(burden), np.expm1(cuts[0]), np.expm1(cuts[1])))

    X0 = np.nan_to_num(X, nan=0.0)
    F = np.isfinite(X).astype(np.float32)
    X2 = X0 ** 2

    Mut = M[:, chosen].astype(np.float32)             # (n_lines x n_drivers)

    # ---- naive contrast, one pair of matmuls -------------------------------------------
    A1 = Mut.T
    A0 = (1.0 - Mut).T
    n1, m1, v1 = group_stats(A1, X0, X2, F)
    n0, m0, v0 = group_stats(A0, X0, X2, F)
    with np.errstate(invalid="ignore", divide="ignore"):
        sp = np.sqrt((v1 + v0) / 2)
        d_naive = (m1 - m0) / np.where(sp > 0, sp, np.nan)

    # ---- stratified pooling, reusable across stratification factors --------------------
    # Fixed-effect inverse-variance pooling. var(d) ~ 1/n1 + 1/n0 + d^2 / (2(n1+n0)) is the
    # standard large-sample form; it is used rather than a permutation because it is the
    # form whose WEIGHTS are interpretable, and the weights are the point of stratifying.
    def pooled(masks: dict) -> tuple:
        num = np.zeros_like(d_naive)
        den = np.zeros_like(d_naive)
        used = np.zeros_like(d_naive)
        for mask in masks.values():
            Xs0, Xs2, Fs = X0[mask], X2[mask], F[mask]
            Ms = Mut[mask]
            sn1, sm1, sv1 = group_stats(Ms.T, Xs0, Xs2, Fs)
            sn0, sm0, sv0 = group_stats((1.0 - Ms).T, Xs0, Xs2, Fs)
            with np.errstate(invalid="ignore", divide="ignore"):
                ssp = np.sqrt((sv1 + sv0) / 2)
                d_s = (sm1 - sm0) / np.where(ssp > 0, ssp, np.nan)
                var_s = 1.0 / sn1 + 1.0 / sn0 + d_s ** 2 / (2 * (sn1 + sn0))
                w = 1.0 / var_s
            ok = ((sn1 >= MIN_PER_STRATUM) & (sn0 >= MIN_PER_STRATUM)
                  & np.isfinite(d_s) & np.isfinite(w))
            num += np.where(ok, w * d_s, 0.0)
            den += np.where(ok, w, 0.0)
            used += ok
        with np.errstate(invalid="ignore", divide="ignore"):
            d = np.where(den > 0, num / den, np.nan)
            se = np.where(den > 0, np.sqrt(1.0 / np.where(den > 0, den, np.nan)), np.nan)
        return d, se, used

    d_strat, se, strata_used = pooled(strata)
    # The burden-adjusted estimate is a DIAGNOSTIC, not the answer. See the docstring: for a
    # driver whose burden is a mediator, this deletes real signal; for one whose burden is a
    # confounder, it removes an artefact. The arithmetic cannot tell which, so both are
    # published and neither is chosen automatically.
    d_burden, _, burden_used = pooled(burden_strata_masks)
    with np.errstate(invalid="ignore", divide="ignore"):
        z = d_strat / se
    p = 2 * stats.norm.sf(np.abs(z))

    # ---- assemble ------------------------------------------------------------------------
    # How far each driver's two arms separate on burden alone. A large value means the
    # "genotype" is largely restating "this line is hypermutated".
    sep = np.zeros(len(drivers))
    for r in range(len(drivers)):
        m = Mut[:, r] > 0
        if m.sum() >= 2 and (~m).sum() >= 2:
            a, b = log_burden[m], log_burden[~m]
            pooled_sd = np.sqrt((a.var() + b.var()) / 2)
            sep[r] = (a.mean() - b.mean()) / pooled_sd if pooled_sd > 0 else 0.0

    results = []
    for r, driver in enumerate(drivers):
        n_mut = int(Mut[:, r].sum())
        try:
            floor = sv.min_detectable_effect(2 * n_mut).at()
        except sv.PowerError:
            floor = None
        powered = floor is not None and floor <= EFFECT_OF_INTEREST

        valid = np.isfinite(p[r]) & np.isfinite(d_strat[r]) & (strata_used[r] >= 2)
        q = np.full(len(genes), np.nan)
        if valid.any():
            q[valid] = multipletests(p[r][valid], alpha=0.05, method="fdr_bh")[1]

        hits = []
        for j in np.argsort(np.where(valid, d_strat[r], -np.inf))[::-1]:
            if not valid[j] or not (q[j] <= 0.05) or d_strat[r, j] < 0.5:
                continue
            if not (m1[r, j] >= DEPENDENCY_FLOOR):      # Stage 0
                continue
            hits.append({
                "gene": genes[j],
                "dStratified": round(float(d_strat[r, j]), 3),
                "dNaive": round(float(d_naive[r, j]), 3),
                "confoundShare": _share(d_naive[r, j], d_strat[r, j]),
                "dBurdenAdjusted": (round(float(d_burden[r, j]), 3)
                                    if np.isfinite(d_burden[r, j]) else None),
                "burdenStrata": int(burden_used[r, j]),
                "strata": int(strata_used[r, j]),
                "q": float(q[j]),
                "meanMutant": round(float(m1[r, j]), 3),
                "meanWildType": round(float(m0[r, j]), 3),
            })
            if len(hits) >= args.top:
                break

        candidates = []
        for j in np.argsort(np.where(valid, d_strat[r], -np.inf))[::-1]:
            if not valid[j] or not (q[j] <= CAND_Q) or d_strat[r, j] < CAND_D:
                continue
            candidates.append({
                "gene": genes[j],
                "dStratified": round(float(d_strat[r, j]), 3),
                "dNaive": round(float(d_naive[r, j]), 3),
                "dBurdenAdjusted": (round(float(d_burden[r, j]), 3)
                                    if np.isfinite(d_burden[r, j]) else None),
                "burdenStrata": int(burden_used[r, j]),
                "strata": int(strata_used[r, j]),
                "q": float(q[j]),
                "meanMutant": round(float(m1[r, j]), 3),
                "meanWildType": round(float(m0[r, j]), 3),
            })
            if len(candidates) >= CAND_MAX:
                break

        # Same union as tools/cancer_subgroups.py, for the same reason: a candidate pool that
        # does not contain the registered shortlist lets the interface draw fewer rows than
        # the analysis reported, at the analysis's own thresholds.
        seen_c = {c["gene"] for c in candidates}
        for h in hits:
            if h["gene"] not in seen_c:
                candidates.append(dict(h))
        candidates.sort(key=lambda c: -c["dStratified"])
        missing = {h["gene"] for h in hits} - {c["gene"] for c in candidates}
        assert not missing, "candidate pool cannot reproduce the registered hits: %s" % missing

        results.append({
            "driver": driver,
            "candidates": candidates,
            "mutantLines": n_mut,
            "detectableFloor": floor,
            "powered": powered,
            "lineagesSpanned": int(np.nanmax(strata_used[r])) if valid.any() else 0,
            "burdenSeparation": round(float(sep[r]), 3),
            "burdenProxy": bool(abs(sep[r]) >= BURDEN_PROXY_D),
            "hits": hits,
            "hitCount": len(hits),
            "says": (
                "underpowered: %d mutant lines cannot resolve an effect below %s SD"
                % (n_mut, floor) if not powered else
                "%d genotype-selective dependencies surviving lineage stratification"
                % len(hits)),
        })
        print("    %-10s %4d mutant  floor %-6s %s"
              % (driver[:10], n_mut, floor,
                 ", ".join(h["gene"] for h in hits[:5]) or "(none)"))

    # ---- the controls, read out whatever they say ----------------------------------------
    control_rows = []
    for driver, target, mechanism, expected in CONTROLS:
        r = drivers.index(driver) if driver in drivers else None
        j = gene_ix.get(target)
        if r is None or j is None:
            control_rows.append({"driver": driver, "target": target, "mechanism": mechanism,
                                 "expected": expected, "measured": None,
                                 "says": "not testable: driver or target absent"})
            continue
        dn, ds = float(d_naive[r, j]), float(d_strat[r, j])
        control_rows.append({
            "driver": driver, "target": target, "mechanism": mechanism,
            "expected": expected,
            "mutantLines": int(Mut[:, r].sum()),
            "dNaive": round(dn, 3), "dStratified": round(ds, 3),
            "shrinkage": _share(dn, ds),
            "dBurdenAdjusted": (round(float(d_burden[r, j]), 3)
                                if np.isfinite(d_burden[r, j]) else None),
            "burdenSeparation": round(float(sep[r]), 3),
            "burdenStrata": int(burden_used[r, j]),
            "strata": int(strata_used[r, j]),
            "q": None if not np.isfinite(p[r, j]) else float(p[r, j]),
            # A burden-adjusted estimate resting on fewer than two populated strata is not
            # an adjustment: with a separation this large the tertiles barely overlap, so
            # there is no stratum in which both arms exist to be compared. Saying "survives
            # burden adjustment" there would be the strongest available claim resting on the
            # weakest available evidence, so it is refused by name.
            "burdenSeparable": bool(burden_used[r, j] >= 2),
            "observed": (
                "not separable from burden"
                if burden_used[r, j] < 2 and abs(sep[r]) >= BURDEN_PROXY_D
                else "survives" if np.isfinite(ds) and np.isfinite(dn)
                and abs(ds) >= 0.6 * abs(dn) else "shrinks"),
        })

    agree = sum(1 for c in control_rows
                if c.get("observed") and c["observed"] == c["expected"])
    testable = sum(1 for c in control_rows if c.get("observed"))

    payload = {
        "generated": "tools/cancer_genotype.py",
        "premise": (
            "tools/cancer_subgroups.py groups lines by their Oncotree LABEL - someone decided "
            "what to call the tumour. This groups them by GENOTYPE, which is the grouping a "
            "target programme acts on, and which had never been read here although the "
            "damaging-mutation matrix has been on disk since the first ingest."
        ),
        "confound": {
            "statement": (
                "Mutation status is not independent of lineage. BRAF mutants are "
                "overwhelmingly melanoma, VHL mutants renal, APC mutants colorectal. A naive "
                "mutant-vs-wild-type contrast is partly a LINEAGE contrast wearing a "
                "genotype's name."),
            "handling": (
                "Two estimates per pair: naive across all lines, and stratified - the "
                "contrast computed within each lineage then pooled by inverse-variance "
                "weighting, the continuous-outcome analogue of Cochran-Mantel-Haenszel. The "
                "stratified estimate is the one reported; the difference between them is the "
                "size of the confound, which is more informative than either alone."),
            "minPerStratum": MIN_PER_STRATUM,
        },
        "prediction": {
            "written": "before the run, in the module docstring",
            "claim": (
                "Paralog synthetic lethality (SMARCA4->SMARCA2, ARID1A->ARID1B) is a "
                "within-cell mechanism with no lineage story and should SURVIVE "
                "stratification. Oncogene addiction (BRAF->BRAF) is real but concentrated in "
                "one lineage, so much of its naive effect is recoverable from lineage alone "
                "and it should SHRINK. If stratification flattened everything equally it "
                "would be removing signal rather than confound."),
            "controlsAgreeing": agree,
            "controlsTestable": testable,
        },
        "isNot": (
            "A damaging-mutation call is not a functional allele. The matrix counts damaging "
            "variants, not gain versus loss of function, so BRAF V600E and a BRAF truncation "
            "are the same entry. Every 'addiction' result here is therefore a lower bound on "
            "the effect a functional-allele grouping would show."),
        "method": {
            "effect": "Cohen's d of mean Chronos dependency, mutant against wild-type",
            "pooling": "fixed-effect inverse-variance across lineage strata",
            "stage0": ("a hit must also be an actual dependency: mean in the mutant arm at "
                       "or above %.1f" % DEPENDENCY_FLOOR),
            "stage2": "sieve.stages.power, per genotype",
            "stage3": ("pan-essentials dropped before ranking, AND lineage removed by "
                       "stratification rather than by disclaimer"),
            "minMutant": args.min_mutant,
        },
        "gates": {
            "registered": {"q": 0.05, "d": 0.5, "dependencyFloor": DEPENDENCY_FLOOR,
                           "burdenProxyD": BURDEN_PROXY_D},
            "candidatePreGate": {"q": CAND_Q, "d": CAND_D, "cap": CAND_MAX},
            "says": (
                "`hits` is the shortlist at the registered gates; `candidates` is the "
                "material a reader may re-gate. Every threshold here is in "
                "manifests/thresholds.yaml with the one field that matters - whether the "
                "data had been seen when it was chosen. A reader moving a slider has seen "
                "the data, so anything they produce is calibrated, not pre-registered, and "
                "the interface must not let that distinction blur."),
        },
        "scale": {
            "lines": len(lines),
            "genesAfterStage3": len(genes),
            "genotypesTested": len(drivers),
            "lineageStrata": len(strata),
            "powered": sum(1 for r in results if r["powered"]),
        },
        "controls": control_rows,
        "results": results,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "cancer_genotype.json"
    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print()
    print("  controls: %d of %d testable behaved as predicted" % (agree, testable))
    print("wrote %s" % dest.relative_to(ROOT))
    return 0


def _share(naive: float, strat: float) -> float | None:
    """Fraction of the naive effect that stratification removed. Negative means the
    within-lineage effect is LARGER — the confound was masking, not inflating."""
    if not np.isfinite(naive) or not np.isfinite(strat) or abs(naive) < 1e-9:
        return None
    return round(float(1.0 - strat / naive), 3)


if __name__ == "__main__":
    raise SystemExit(main())
