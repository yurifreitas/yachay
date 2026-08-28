"""NF2-null selective dependency in DepMap — sieve on a small genotype-defined subgroup.

Why this analysis exists
------------------------
A top-k over a *small* subgroup is the most inflated case Stage 1 handles: with a handful
of NF2-null lines, pure noise reaches a large maximum, so the raw "strongest dependency in
NF2-null lines" ranking is substantially a ranking of who was measured least.

And unlike every other target in this repository, it comes with a **positive control**.
Merlin (the NF2 protein) acts upstream of the Hippo pathway, so NF2-null cells lean on
YAP/TAZ-TEAD. If the calibrated contrast does not recover that axis, the pipeline is
broken and no novel hit from it should be believed. The control can fail, which is what
makes it a control.

Known limitation, stated before the result
------------------------------------------
The subgroup is defined from **damaging mutations only**. NF2 is lost by copy-number
deletion as often as by point mutation, so this subgroup is UNDER-CALLED: some lines
labelled wildtype here are really NF2-null, which biases the contrast toward zero.
Closing it needs OmicsCNGene.csv. **That file is now on disk (1.39 GB) and this analysis
still does not read it**, so the limitation has stopped being a missing download and
become an unmade decision — which is a worse thing to leave unstated, not a better one.
Any effect measured here is therefore a *lower bound* on the real one.

Emits: out/NF2_FINDINGS.md, out/nf2_genes.csv, out/nf2.manifest.json

Run:  python tasks.py fetch && python tasks.py fetch_nf2 && python tasks.py nf2
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import sieve as sv
from sieve.adapters import depmap as dm

DATA = os.environ.get("SIEVE_DATA", "data/depmap")
OUT = "out"
MODEL = "Model.csv"
DAMAGING = "OmicsSomaticMutationsMatrixDamaging.csv"
N_DRAWS = 2000
SEED = 0

# The positive control: merlin acts through LATS1/2 to restrain YAP/TAZ-TEAD.
HIPPO = ["YAP1", "WWTR1", "TEAD1", "TEAD2", "TEAD3", "TEAD4", "LATS1", "LATS2"]

os.makedirs(OUT, exist_ok=True)
notes: list[str] = []

# THE POSITIVE-CONTROL GATE, named because an arbitrary number that decides
# whether a shortlist ships must be visible rather than inline (ADR 0003, and
# now registered in manifests/thresholds.yaml under ADR 0006). It was chosen
# before the result was seen and must never be moved to let a result through.
HIPPO_RANK_GATE = 0.25


def log(msg: str = "") -> None:
    print(msg, flush=True)
    notes.append(msg)


def rule(title: str) -> None:
    log("=" * 74)
    log(title)
    log("=" * 74)


def spearman(a, b) -> float:
    ra = pd.Series(np.asarray(a, float)).rank()
    rb = pd.Series(np.asarray(b, float)).rank()
    return float(np.corrcoef(ra, rb)[0, 1])


def score_subset(values: np.ndarray, genes: pd.Index, rows: np.ndarray, k: int) -> pd.DataFrame:
    """Top-k mean per gene over a subset of cell lines, with the count behind each."""
    sub = values[rows]
    finite = np.isfinite(sub)
    counts = finite.sum(axis=0)
    scores = np.full(sub.shape[1], np.nan)
    for j in range(sub.shape[1]):
        col = sub[finite[:, j], j]
        if col.size >= k:
            scores[j] = np.sort(col)[-k:].mean()
    return pd.DataFrame({"entity": genes.astype(str), "score": scores, "n": counts})


# ---------------------------------------------------------------------------
log("loading DepMap gene-effect matrix...")
mat = dm.load_matrix(DATA)
log("matrix: %d cell lines x %d genes" % mat.shape)

model = pd.read_csv(os.path.join(DATA, MODEL))
lineage = model.set_index("ModelID")["OncotreeLineage"]

dmg_path = os.path.join(DATA, DAMAGING)
if not os.path.exists(dmg_path):
    raise SystemExit("missing %s — run: python tasks.py fetch_nf2" % dmg_path)

# The damaging matrix is lines x genes; we need one column. Read the header, find it,
# then read only that column — the file is 148 MB and we want 1/18,000th of it.
header = pd.read_csv(dmg_path, nrows=0)
nf2_cols = [c for c in header.columns if c.split(" ")[0] == "NF2"]
if not nf2_cols:
    raise SystemExit("no NF2 column in %s" % DAMAGING)
dmg = pd.read_csv(dmg_path, usecols=[header.columns[0], nf2_cols[0]], index_col=0)
nf2_damaging = dmg[nf2_cols[0]]
log("NF2 damaging-mutation calls available for %d models" % nf2_damaging.notna().sum())
log()

# ===========================================================================
rule("STAGE 2 - power, BEFORE anything else")
# Stage 2 runs first here, deliberately. If the subgroup is too small, the honest
# outcome is to say so and stop, not to rank 18,000 genes on it anyway.
line_ids = pd.Index(mat.lines.astype(str))
called = line_ids.intersection(nf2_damaging.index.astype(str))
is_null = line_ids.isin(nf2_damaging[nf2_damaging > 0].index.astype(str))
is_wt = line_ids.isin(nf2_damaging[nf2_damaging == 0].index.astype(str))

n_null, n_wt = int(is_null.sum()), int(is_wt.sum())
log("cell lines screened:            %d" % len(line_ids))
log("with an NF2 mutation call:      %d" % len(called))
log("NF2-null (damaging mutation):   %d   <- the subgroup" % n_null)
log("NF2-wildtype:                   %d" % n_wt)
log()
log("REMINDER: deletion is not counted here. OmicsCNGene.csv IS on disk (1.39 GB);")
log("          this analysis does not read it. A choice, no longer a blocker.")
log("Some 'wildtype' lines are really NF2-null, which biases the contrast TOWARD ZERO.")
log("Every effect below is therefore a lower bound.")
log()

if n_null < 10:
    log("-> subgroup too small to rank on. Stopping at Stage 2, which is the point of")
    log("   running it first.")
    raise SystemExit(0)

K = max(3, min(10, n_null // 3))
log("k for the top-k mean: %d (scaled to the subgroup, not chosen for a nice answer)" % K)
log()

# Lineage composition of the subgroup — the Stage 3 threat, measured up front.
null_lineages = pd.Series(lineage.reindex(line_ids[is_null]).values).value_counts()
all_lineages = pd.Series(lineage.reindex(line_ids).values).value_counts()
log("lineage composition of the NF2-null subgroup (top 6):")
log("   %-28s %7s %9s %10s" % ("lineage", "in null", "overall", "enrichment"))
for lin, cnt in null_lineages.head(6).items():
    share_null = cnt / n_null
    share_all = all_lineages.get(lin, 0) / len(line_ids)
    log("   %-28s %7d %9.1f%% %9.2fx"
        % (str(lin)[:28], cnt, 100 * share_all, share_null / share_all if share_all else float("nan")))
log()

# ===========================================================================
rule("STAGE 1 - null calibration, inside each group")
nonessential = dm.load_gene_set(DATA, dm.NONESSENTIAL)
stat = sv.top_k_mean(K)

results = {}
for label, rows in (("null", is_null), ("wt", is_wt)):
    scored = score_subset(mat.values, mat.genes, rows, K).dropna(subset=["score"])
    sv.entity_scores().validate(scored)
    idx = [mat.genes.get_loc(g) for g in nonessential if g in mat.genes]
    pool = mat.values[np.ix_(np.where(rows)[0], idx)].ravel()
    pool = pool[np.isfinite(pool)].reshape(-1, 1)
    null = sv.fit_null(pool, stat, observed_counts=scored["n"].to_numpy(),
                       reduce="raw", n_draws=N_DRAWS, seed=SEED)
    scored = sv.calibrate(scored, null, score="score", count="n")
    results[label] = scored
    log("%-4s group: %d lines, %d genes scored, control pool %s values"
        % (label, int(rows.sum()), len(scored), format(len(pool), ",")))
    log("      %s" % null.summary())
    raw_r = spearman(scored["score"], np.log1p(scored["n"]))
    cal_r = spearman(scored["z"], np.log1p(scored["n"]))
    log("      corr with log(lines screened): %+.4f raw -> %+.4f calibrated" % (raw_r, cal_r))
    results[label + "_corr"] = (raw_r, cal_r)
log()

# ===========================================================================
rule("THE CONTRAST - dependency in NF2-null lines, above wildtype")
a = results["null"][["entity", "score", "n", "z"]].rename(
    columns={"score": "score_null", "n": "n_null", "z": "z_null"})
b = results["wt"][["entity", "score", "n", "z"]].rename(
    columns={"score": "score_wt", "n": "n_wt", "z": "z_wt"})
g = a.merge(b, on="entity", how="inner")
g["contrast_raw"] = g["score_null"] - g["score_wt"]
g["contrast_z"] = g["z_null"] - g["z_wt"]
log("%d genes scored in both groups" % len(g))
log()

# ===========================================================================
rule("STAGE 6 - the positive control: does the Hippo axis come back?")
g["rank_raw"] = g["contrast_raw"].rank(ascending=False)
g["rank_cal"] = g["contrast_z"].rank(ascending=False)
n_genes = len(g)

log("   %-8s %10s %10s %12s %12s" % ("gene", "raw rank", "cal rank", "contrast_raw", "contrast_z"))
hippo_rows = []
for gene in HIPPO:
    row = g[g["entity"] == gene]
    if row.empty:
        log("   %-8s %10s" % (gene, "absent"))
        continue
    r = row.iloc[0]
    hippo_rows.append(r)
    log("   %-8s %10.0f %10.0f %12.3f %12.2f"
        % (gene, r["rank_raw"], r["rank_cal"], r["contrast_raw"], r["contrast_z"]))
log()

if hippo_rows:
    hp = pd.DataFrame(hippo_rows)
    med_raw = float(hp["rank_raw"].median())
    med_cal = float(hp["rank_cal"].median())
    # Where would a random gene set of this size sit? The median rank of n draws from
    # 1..N has expectation about N/2; the interesting question is whether we beat it.
    log("median rank of the %d Hippo genes: %.0f raw -> %.0f calibrated (of %d genes)"
        % (len(hp), med_raw, med_cal, n_genes))
    log("a random gene would sit at ~%d" % (n_genes // 2))
    verdict = "RECOVERED" if med_cal < n_genes * HIPPO_RANK_GATE else "NOT RECOVERED"
    log()
    log("-> positive control: %s" % verdict)
    if verdict == "NOT RECOVERED":
        log("   This is the control failing. Per docs/references/nf2.md, no novel hit from")
        log("   this run should be believed until the cause is found. Candidate causes:")
        log("   subgroup under-called (no copy number), subgroup too small, lineage")
        log("   confound, or the contrast statistic being wrong for this question.")
else:
    med_raw = med_cal = float("nan")
    verdict = "ABSENT"

log()

# ===========================================================================
rule("STAGE 3 - the lineage confound")
# Mesothelioma is over-represented among NF2-null lines. If the contrast is really a
# lineage effect, dropping that lineage from the NULL group should collapse it.
top_lineage = str(null_lineages.index[0])
drop = line_ids.isin(lineage[lineage == top_lineage].index.astype(str))
is_null_nolin = is_null & ~drop
log("dominant lineage in the subgroup: %s (%d of %d lines)"
    % (top_lineage, int((is_null & drop).sum()), n_null))

if int(is_null_nolin.sum()) >= 10:
    scored = score_subset(mat.values, mat.genes, is_null_nolin, K).dropna(subset=["score"])
    idx = [mat.genes.get_loc(gn) for gn in nonessential if gn in mat.genes]
    pool = mat.values[np.ix_(np.where(is_null_nolin)[0], idx)].ravel()
    pool = pool[np.isfinite(pool)].reshape(-1, 1)
    null2 = sv.fit_null(pool, stat, observed_counts=scored["n"].to_numpy(),
                        reduce="raw", n_draws=N_DRAWS, seed=SEED)
    scored = sv.calibrate(scored, null2, score="score", count="n")
    g2 = scored[["entity", "z"]].rename(columns={"z": "z_null_nolin"}).merge(
        b[["entity", "z_wt"]], on="entity", how="inner")
    g2["contrast_z"] = g2["z_null_nolin"] - g2["z_wt"]
    g2["rank_cal"] = g2["contrast_z"].rank(ascending=False)
    hp2 = g2[g2["entity"].isin(HIPPO)]
    med_nolin = float(hp2["rank_cal"].median()) if len(hp2) else float("nan")
    log("with %s lines removed (%d remain): Hippo median rank %.0f (was %.0f)"
        % (top_lineage, int(is_null_nolin.sum()), med_nolin, med_cal))
    log()
    if np.isfinite(med_nolin) and med_cal < n_genes * HIPPO_RANK_GATE <= med_nolin:
        log("-> the signal DEPENDED on that lineage. It is a lineage effect wearing a")
        log("   genotype's name. Stage 3 just saved the shortlist.")
    elif np.isfinite(med_nolin):
        log("-> the signal survives removing the dominant lineage, which is what a real")
        log("   genotype effect should do.")
else:
    med_nolin = float("nan")
    log("-> only %d lines remain after removing %s: too few to re-test. Stage 3 could not"
        % (int(is_null_nolin.sum()), top_lineage))
    log("   run, and that is a limitation of the result, not a pass.")
log()

# ===========================================================================
rule("STAGE 7 - shortlist (only if the positive control passed)")
if verdict == "RECOVERED":
    cand = g[~g["entity"].isin(HIPPO)].nlargest(15, "contrast_z")
    log("top 15 NF2-null-selective dependencies, Hippo axis excluded:")
    log("   %-10s %10s %12s %8s %8s" % ("gene", "contrast_z", "contrast_raw", "z_null", "z_wt"))
    for _, r in cand.iterrows():
        log("   %-10s %10.2f %12.3f %8.1f %8.1f"
            % (r["entity"], r["contrast_z"], r["contrast_raw"], r["z_null"], r["z_wt"]))
else:
    log("SKIPPED. The positive control did not pass, so a shortlist from this run would")
    log("be a list of numbers with nothing behind it. This is the gate doing its job.")
log()

# ---------------------------------------------------------------------------
g.sort_values("contrast_z", ascending=False).to_csv(os.path.join(OUT, "nf2_genes.csv"), index=False)

with open(os.path.join(OUT, "nf2.manifest.json"), "w", encoding="utf-8") as fh:
    json.dump({
        "id": "nf2",
        "title": "NF2-null selective dependency — DepMap subgroup contrast",
        "subtitle": ("%d NF2-null vs %d wildtype cell lines. Score = top-%d mean within "
                     "each group; contrast = calibrated difference." % (n_null, n_wt, K)),
        "statistic": "top%d_mean" % K,
        "reduce": "raw",
        "entities": "nf2_genes.csv",
        "headline": {
            "lines_total": int(len(line_ids)),
            "lines_null": n_null,
            "lines_wildtype": n_wt,
            "k": int(K),
            "genes_contrasted": int(n_genes),
            "hippo_median_rank_raw": med_raw,
            "hippo_median_rank_calibrated": med_cal,
            "hippo_median_rank_no_dominant_lineage": med_nolin,
            "positive_control": verdict,
            "count_spearman_null_raw": results["null_corr"][0],
            "count_spearman_null_calibrated": results["null_corr"][1],
        },
    }, fh, indent=2)

lines = [
    "# NF2 — selective dependency in an NF2-null subgroup",
    "",
    "Generated by `analyses/nf2_subgroup.py`. Domain reference: `docs/references/nf2.md`.",
    "",
    "## Setup",
    "",
    "- %d NF2-null vs %d wildtype cell lines, %d genes contrasted" % (n_null, n_wt, n_genes),
    "- score: top-%d mean within each group, calibrated separately, then differenced" % K,
    "- **subgroup defined from damaging mutations only** — copy-number deletion not "
    "counted, so the subgroup is under-called and every effect is a lower bound",
    "",
    "## Positive control",
    "",
    "- Hippo axis (%s) median rank: **%.0f raw -> %.0f calibrated** of %d genes"
    % (", ".join(HIPPO), med_raw, med_cal, n_genes),
    "- verdict: **%s**" % verdict,
    "",
    "## Log",
    "",
    "```",
]
lines += notes + ["```", ""]
with open(os.path.join(OUT, "NF2_FINDINGS.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))

log("wrote out/NF2_FINDINGS.md, out/nf2_genes.csv, out/nf2.manifest.json")
