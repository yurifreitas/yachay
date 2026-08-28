"""Apply sieve to DepMap: which genes are SELECTIVE dependencies?

The scale test. Everything the method claims is re-run here on ~18,000 genes across
~1,100 cell lines, where the answers can be checked against biology that is already
known — which is the point. A method validated only on the screen that produced it has
not been validated.

The question: a useful target kills SOME cell lines and spares the rest. A gene that
kills everything is a toxic liability. So we score each gene by how strong its
dependency is in the contexts where it matters (a top-k mean over its most dependent
lines) — which is exactly the kind of max-order statistic that cannot be ranked raw.

Emits: out/DEPMAP_FINDINGS.md and out/depmap_genes.csv

Run:  python analyses/depmap_selective_dependency.py
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import sieve as sv
from sieve.adapters import depmap as dm

DATA = os.environ.get("SIEVE_DATA", "data/depmap")
OUT = "out"
K = 20                      # "the contexts where it matters": top 20 most dependent lines
N_DRAWS = 2000

os.makedirs(OUT, exist_ok=True)
notes: list[str] = []


def log(msg: str = "") -> None:
    print(msg, flush=True)
    notes.append(msg)


# ---------------------------------------------------------------------------
log("loading DepMap gene-effect matrix (chunked, float32)...")
mat = dm.load_matrix(DATA)
log("matrix: %d cell lines x %d genes  (%.0f MB in memory)"
    % (mat.shape[0], mat.shape[1], mat.values.nbytes / 1e6))
log("sign flipped: dependency is now POSITIVE (sieve assumes larger is better)")
log()

nonessential = dm.load_gene_set(DATA, dm.NONESSENTIAL)
common_ess = dm.load_gene_set(DATA, dm.COMMON_ESSENTIAL)
log("control gene sets: %d nonessential, %d common-essential"
    % (len(nonessential), len(common_ess)))

stat = sv.top_k_mean(K)
genes = dm.score_genes(mat, stat, min_lines=K)
sv.entity_scores().validate(genes)
log("scored %d genes with at least %d screened lines" % (len(genes), K))
log()

# ===========================================================================
log("=" * 74)
log("STAGE 0 - the objective and its degeneracies")
log("=" * 74)
top_raw = genes.nlargest(10, "score")
log("top 10 by RAW top-%d mean dependency:" % K)
log("   %-12s %9s %8s   %s" % ("gene", "score", "lines", "known pan-essential?"))
for _, r in top_raw.iterrows():
    log("   %-12s %9.4f %8d   %s"
        % (r.entity, r.score, r.n, "YES" if r.entity in set(common_ess) else "-"))
ess = set(common_ess)
frac_ess = np.mean([g in ess for g in top_raw.entity])
log()
log("-> %.0f%% of the raw top 10 are known PAN-ESSENTIAL genes: the metric's maximum is"
    % (100 * frac_ess))
log("   dominated by genes that kill every cell line. This is the KIF11 lesson at scale:")
log("   the strongest signal in a viability screen is toxicity, not selectivity.")
log()

# ===========================================================================
log("=" * 74)
log("STAGE 1 - null calibration")
log("=" * 74)
control, control_blocks = mat.control_pool(nonessential, with_blocks=True)
log("control pool: %s individual (cell line, gene) values from %d nonessential genes"
    % (format(control.shape[0], ","), len(nonessential)))
log("(these genes are KNOWN to do nothing when knocked out - a real null, not a")
log(" parametric one, so it inherits the screen's own correlation structure)")
log("")
log("blocks=gene: each null draw is one GENE's values, not a mixture of 726 genes.")
log("Pooling rows across genes was a real defect - it discarded the between-gene")
log("variance, put these same control genes at z = -4.09 (sd 3.28) instead of ~0, and")
log("made the null climb 1.93x too steeply with n. See docs/adr/0004-block-nulls.md.")

# reduce="raw": a gene's score is top-k applied directly to its per-line values.
null = sv.fit_null(control, stat, observed_counts=genes["n"].to_numpy(),
                   reduce="raw", n_draws=N_DRAWS, blocks=control_blocks)
log()
log(null.summary())
log()
log("   %8s %11s %9s %9s" % ("lines", "null mean", "null sd", "p99"))
for _, r in null.to_frame().iterrows():
    log("   %8d %11.4f %9.4f %9.4f" % (r["n"], r["null_mean"], r["null_sd"], r["p99"]))
log()

genes = sv.calibrate(genes, null, score="score", count="n")


def spearman(a, b):
    ra = pd.Series(np.asarray(a, float)).rank()
    rb = pd.Series(np.asarray(b, float)).rank()
    return float(np.corrcoef(ra, rb)[0, 1])


before = spearman(genes["score"], np.log1p(genes["n"]))
after = spearman(genes["z"], np.log1p(genes["n"]))
log("correlation of the score with log(lines screened): %+.4f raw -> %+.4f calibrated"
    % (before, after))
log()

# ===========================================================================
log("=" * 74)
log("STAGE 3 - the confound: pan-essentiality")
log("=" * 74)
genes["is_common_essential"] = genes["entity"].isin(ess)
genes["is_nonessential_control"] = genes["entity"].isin(set(nonessential))

# Selectivity: strong where it matters, quiet elsewhere. Measured directly from the
# matrix rather than assumed - the median line is the "spared" case.
vals = mat.values
finite = np.isfinite(vals)
med = np.full(vals.shape[1], np.nan)
for j in range(vals.shape[1]):
    col = vals[finite[:, j], j]
    if col.size:
        med[j] = np.median(col)
median_by_gene = pd.Series(med, index=mat.genes.astype(str))
genes["median_dependency"] = genes["entity"].map(median_by_gene)
genes["selectivity"] = genes["score"] - genes["median_dependency"]

log("mean calibrated z by class:")
for label, mask in (("common-essential", genes.is_common_essential),
                    ("nonessential control", genes.is_nonessential_control),
                    ("everything else", ~genes.is_common_essential & ~genes.is_nonessential_control)):
    sub = genes[mask]
    if len(sub):
        log("   %-22s n=%5d   z=%+8.2f   selectivity=%+.3f"
            % (label, len(sub), sub["z"].mean(), sub["selectivity"].mean()))
log()
log("-> the nonessential controls must sit near zero with unit spread: genes known to")
log("   do nothing must score like nothing. That check FAILED before the block fix")
log("   (-4.09, sd 3.28) and is the reason the fix exists.")
log()

# ===========================================================================
log("=" * 74)
log("STAGE 7 - the shortlist: selective dependencies")
log("=" * 74)
cand = genes[~genes.is_common_essential & (genes["z"] > 0)].copy()
cand["shortlist_score"] = cand["z"] * cand["selectivity"].clip(lower=0)
short = cand.nlargest(20, "shortlist_score")

log("top 20 SELECTIVE dependencies (calibrated, pan-essentials excluded):")
log("   %-12s %8s %8s %9s %9s" % ("gene", "z", "raw", "median", "selectivity"))
for _, r in short.iterrows():
    log("   %-12s %8.1f %8.3f %9.3f %9.3f"
        % (r.entity, r.z, r.score, r.median_dependency, r.selectivity))
log()

# Ranks are computed HERE, over every gene, and shipped as columns. The explorer only
# ever receives a subset of the rows, so a rank it computed itself would be a rank
# within that subset -- which is not the rank anything in this repository claims.
genes["rank_raw"] = genes["score"].rank(ascending=False, method="min").astype(int)
genes["rank_cal"] = genes["z"].rank(ascending=False, method="min").astype(int)
genes.sort_values("z", ascending=False).to_csv(os.path.join(OUT, "depmap_genes.csv"), index=False)
null.to_frame().to_csv(os.path.join(OUT, "depmap_null.csv"), index=False)

# The manifest is how this run appears in the explorer. An adapter that does not write
# one simply does not show up, rather than rendering half a page.
import json

with open(os.path.join(OUT, "depmap.manifest.json"), "w", encoding="utf-8") as fh:
    json.dump({
        "id": "depmap",
        "title": "DepMap CRISPR — selective dependency",
        "subtitle": ("%d cell lines x %d genes. Score = mean of the top %d most-dependent "
                     "lines per gene, a max-order statistic." % (mat.shape[0], mat.shape[1], K)),
        "statistic": "top%d_mean" % K,
        "reduce": "raw",
        "entities": "depmap_genes.csv",
        "null": "depmap_null.csv",
        "headline": {
            "genes_scored": int(len(genes)),
            "cell_lines": int(mat.shape[0]),
            "control_genes": int(len(nonessential)),
            "pan_essential_in_raw_top10": float(frac_ess),
            "count_spearman_raw": round(before, 4),
            "count_spearman_calibrated": round(after, 4),
            "nonessential_mean_z": round(float(genes[genes.is_nonessential_control]["z"].mean()), 3),
            "nonessential_sd_z": round(float(genes[genes.is_nonessential_control]["z"].std()), 3),
            "null_blocks": "gene",
            "common_essential_mean_z": round(float(genes[genes.is_common_essential]["z"].mean()), 3),
        },
    }, fh, indent=2)

# ===========================================================================
lines = [
    "# DepMap — sieve at scale",
    "",
    "Generated by `analyses/depmap_selective_dependency.py`.",
    "",
    "## Setup",
    "",
    "- matrix: **%d cell lines x %d genes**" % (mat.shape[0], mat.shape[1]),
    "- score: mean of the top %d most-dependent lines per gene (a max-order statistic)" % K,
    "- control pool: %d nonessential genes — knockouts KNOWN to do nothing" % len(nonessential),
    "- confound set: %d known pan-essential genes" % len(common_ess),
    "",
    "## Result",
    "",
    "- %.0f%% of the raw top 10 are known pan-essential genes." % (100 * frac_ess),
    "- Correlation with log(lines screened): **%+.4f raw -> %+.4f calibrated**." % (before, after),
    "- Nonessential controls calibrate to a mean z of "
    "**%+.2f**." % genes[genes.is_nonessential_control]["z"].mean(),
    "",
    "## Log",
    "",
    "```",
]
lines += notes + ["```", ""]
with open(os.path.join(OUT, "DEPMAP_FINDINGS.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("\nwrote out/DEPMAP_FINDINGS.md and out/depmap_genes.csv")
