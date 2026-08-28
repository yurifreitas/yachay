#!/usr/bin/env python
"""Generate figure data from the analysis outputs — one contract, two renderers.

The visualisation layer is deliberately NOT a chart library sitting on the analysis.
It is a *data contract*: analyses emit `out/*.csv` + a manifest, this script reduces
them to small tidy series in `out/figures/`, and both renderers consume the same series —
the React explorer under `web/`, and pgfplots in `paper/`. A figure can therefore never
disagree with the manuscript, because they read the same file.

Why this exists at all: the -4.09 defect lived in the repository for weeks. It was
present in every table it ever printed and nobody saw it. It is unmissable in the plot
this script generates first. See `docs/references/visualization.md`.

    python tools/figure_data.py            # writes out/figures/*.json
    python tools/figure_data.py --check    # exit 1 if stale
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "out"
DEST = OUT / "figures"

import sieve as sv                                          # noqa: E402
from sieve.adapters import depmap as dm                     # noqa: E402

DATA = str(ROOT / "data" / "depmap")
K = 20
N_DRAWS = 2000


def hist(values: np.ndarray, lo: float, hi: float, bins: int = 60) -> list[dict]:
    """A binned density, small enough to inline into a page."""
    values = values[np.isfinite(values)]
    # No clipping: piling out-of-range values into the edge bin draws a spike that is
    # not in the data. Values outside [lo, hi] are dropped by `range` and reported.
    counts, edges = np.histogram(values, bins=bins, range=(lo, hi))
    total = counts.sum() or 1
    width = edges[1] - edges[0]
    return [
        {"x": round(float(edges[i] + width / 2), 4),
         "density": round(float(counts[i] / total / width), 5)}
        for i in range(len(counts))
    ]


def null_grid_points(counts: np.ndarray, k: int = 7) -> list[int]:
    """A readable subset of the fitted grid: a ridgeline with 14 ridges is a smear."""
    idx = np.unique(np.round(np.linspace(0, len(counts) - 1, k)).astype(int))
    return [int(counts[i]) for i in idx]


def draw_null(control: np.ndarray, stat, n_at: int, n_draws: int,
              blocks: np.ndarray | None) -> np.ndarray:
    """Resample the statistic at one observation count, the same way fit_null does.

    Duplicated deliberately rather than exposed from the library: fit_null returns
    moments, and this needs the draws themselves. If a third caller ever wants them,
    that is the moment to add a `return_draws` option rather than now.
    """
    rng = np.random.default_rng(0)
    if blocks is None:
        idx = rng.integers(0, len(control), size=(n_draws, n_at))
    else:
        _, inv = np.unique(blocks, return_inverse=True)
        pools = [np.flatnonzero(inv == b) for b in range(int(inv.max()) + 1)]
        pools = [p for p in pools if len(p)]
        chosen = rng.integers(0, len(pools), size=n_draws)
        idx = np.empty((n_draws, n_at), dtype=np.intp)
        for r, b in enumerate(chosen):
            pool = pools[b]
            idx[r] = pool[rng.integers(0, len(pool), size=n_at)]
    return np.asarray(stat(control[idx][:, :, 0]), dtype=float)


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    figures: dict[str, dict] = {}

    mat = dm.load_matrix(DATA)
    non = dm.load_gene_set(DATA, dm.NONESSENTIAL)
    ess = set(dm.load_gene_set(DATA, dm.COMMON_ESSENTIAL))
    stat = sv.top_k_mean(K)
    genes = dm.score_genes(mat, stat, min_lines=K)
    control, blocks = mat.control_pool(non, with_blocks=True)

    import warnings
    warnings.simplefilter("ignore", UserWarning)

    fits = {}
    for name, kw in (("pooled", {}), ("blocked", {"blocks": blocks})):
        null = sv.fit_null(control, stat, observed_counts=genes["n"].to_numpy(),
                           reduce="raw", n_draws=N_DRAWS, seed=0, **kw)
        fits[name] = (null, sv.calibrate(genes, null, score="score", count="n"))

    is_ctl = genes["entity"].isin(set(non)).to_numpy()
    is_ess = genes["entity"].isin(ess).to_numpy()

    # --- FIGURE 1: the control-calibration check --------------------------------------
    # Genes known to do nothing must land on N(0,1). This is the plot that makes the
    # defect visible in one glance, and the reason this whole layer exists.
    x = np.linspace(-9, 5, 141)
    figures["control_calibration"] = {
        "title": "Do the controls read zero?",
        "question": "Genes known to do nothing must calibrate to a standard normal. "
                    "Anything else means the null is wrong.",
        "reference": [{"x": round(float(v), 3),
                       "density": round(float(np.exp(-v * v / 2) / np.sqrt(2 * np.pi)), 5)}
                      for v in x],
        "panels": [
            {
                "id": name,
                "label": {"pooled": "rows pooled across genes (the defect)",
                          "blocked": "blocks = gene (the fix)"}[name],
                "mean": round(float(df.loc[is_ctl, "z"].mean()), 3),
                "sd": round(float(df.loc[is_ctl, "z"].std()), 3),
                "bins": hist(df.loc[is_ctl, "z"].to_numpy(), -9, 5),
            }
            for name, (_, df) in fits.items()
        ],
    }

    # --- FIGURE 1b: the control Q-Q ------------------------------------------------------
    # A density overlay shows that the controls are displaced. A Q-Q plot shows WHERE and
    # HOW: location as an offset from the diagonal, scale as a slope, and tail misfit as
    # curvature at the ends -- which a density curve compresses into invisibility exactly
    # where the shortlist is drawn from. Wilk & Gnanadesikan (1968).
    probs = np.concatenate([
        np.linspace(0.0005, 0.02, 40),      # dense in the tails, which is where a
        np.linspace(0.02, 0.98, 160),       # screening decision actually lives
        np.linspace(0.98, 0.9995, 40),
    ])
    from math import erf, sqrt

    def ppf(p: float) -> float:
        """Inverse normal CDF by bisection on erf -- no scipy dependency in this repo."""
        lo, hi = -9.0, 9.0
        for _ in range(80):
            mid = (lo + hi) / 2
            if 0.5 * (1 + erf(mid / sqrt(2))) < p:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    theo = [round(ppf(float(p)), 4) for p in probs]
    figures["control_qq"] = {
        "title": "Where exactly do the controls depart from normal?",
        "question": "On a Q-Q plot a correct null is the diagonal. An offset is bias, a "
                    "slope is the wrong spread, and curvature at the ends is tail misfit.",
        "theoretical": theo,
        "series": [
            {
                "id": name,
                "label": {"pooled": "rows pooled across genes",
                          "blocked": "blocks = gene"}[name],
                "sample": [round(float(v), 4)
                           for v in np.quantile(df.loc[is_ctl, "z"].dropna().to_numpy(), probs)],
            }
            for name, (_, df) in fits.items()
        ],
    }

    # --- FIGURE 2: the null curve ------------------------------------------------------
    figures["null_curve"] = {
        "title": "What the score reads when nothing is happening",
        "question": "The null's mean and spread as a function of observation count. "
                    "The slope is the bias a raw ranking would inherit.",
        "series": [
            {
                "id": name,
                "label": {"pooled": "rows pooled (slope too steep)",
                          "blocked": "blocks = gene"}[name],
                "rise": round(float(null.mean[-1] - null.mean[0]), 4),
                "points": [
                    {"n": int(n), "mean": round(float(m), 4), "sd": round(float(s), 4),
                     "lo": round(float(m - s), 4), "hi": round(float(m + s), 4)}
                    for n, m, s in zip(null.counts, null.mean, null.sd)
                ],
            }
            for name, (null, _) in fits.items()
        ],
    }

    # --- FIGURE 2b: the null's SHAPE at each observation count ---------------------------
    # The null curve reports two moments. The ridgeline reports the distribution they came
    # from -- which matters because a mean and an sd describe a normal, and nothing here
    # promised the null was normal. Skew and tail weight are exactly what a top-k operator
    # produces, and they are invisible in a mean+-sd band.
    ridge = {}
    for name, kw in (("pooled", {}), ("blocked", {"blocks": blocks})):
        rows = []
        for n_at in null_grid_points(fits[name][0].counts):
            draws = draw_null(control, stat, int(n_at), N_DRAWS, kw.get("blocks"))
            lo, hi = float(np.quantile(draws, 0.001)), float(np.quantile(draws, 0.999))
            rows.append({
                "n": int(n_at),
                "lo": round(lo, 4), "hi": round(hi, 4),
                "mean": round(float(draws.mean()), 4),
                "p99": round(float(np.quantile(draws, 0.99)), 4),
                "density": hist(draws, lo, hi, bins=48),
            })
        ridge[name] = rows
    figures["null_ridgeline"] = {
        "title": "The null is not a mean and a spread - it has a shape",
        "question": "The distribution of the statistic under no effect, at each observation "
                    "count. A top-k operator produces a skewed null, which a band hides.",
        "series": ridge,
    }

    # --- FIGURE 3: the funnel -----------------------------------------------------------
    # The form institutional statisticians settled on for exactly this problem
    # (Spiegelhalter 2005): the score against its own precision, with null limits that
    # widen as n falls. Sampled, because 17,916 dots do not need to all be drawn.
    null_b, df_b = fits["blocked"]
    # Stratified by count, not uniform: 95.4% of genes sit at n=1178, so a uniform
    # sample would be 95% one vertical line and would hide the genes that actually
    # carry the count variation.
    rng = np.random.default_rng(0)
    take = []
    for _, grp in df_b.groupby("n"):
        k = min(len(grp), 400 if len(grp) < 2000 else 900)
        take.append(grp.iloc[rng.choice(len(grp), size=k, replace=False)])
    sample = pd.concat(take).sort_values("n")
    figures["funnel"] = {
        "title": "Score against the precision behind it",
        "question": "A raw score is not comparable across counts. The funnel says how "
                    "far from the null a score has to be, given how well it was measured.",
        "limits": [
            {"n": int(r["n"]), "mean": round(float(r["null_mean"]), 4),
             "p95": round(float(r["p95"]), 4), "p99": round(float(r["p99"]), 4)}
            for _, r in null_b.to_frame().iterrows()
        ],
        "points": [
            {"n": int(r["n"]), "score": round(float(r["score"]), 4),
             "z": round(float(r["z"]), 2), "entity": str(r["entity"]),
             "cls": ("essential" if r["entity"] in ess
                     else "control" if r["entity"] in set(non) else "other")}
            for _, r in sample.iterrows()
        ],
    }

    # --- FIGURE 4: what calibration did to the ranking -----------------------------------
    # A slopegraph of class medians. The claim of the library is a claim about ranking,
    # so the figure that tests it must be about ranking.
    df = fits["blocked"][1].copy()
    df["rank_raw"] = df["score"].rank(ascending=False)
    df["rank_cal"] = df["z"].rank(ascending=False)
    total = len(df)
    classes = [
        ("pan-essential", is_ess, "the confound: kills everything"),
        ("nonessential control", is_ctl, "known to do nothing"),
    ]
    figures["rank_shift"] = {
        "title": "What calibration did to the ranking",
        "question": "The library's only claim is about ordering, so this is the figure "
                    "that tests it. Controls should fall; the confound should be visible.",
        "total": int(total),
        "classes": [
            {"id": name, "note": note,
             "n": int(mask.sum()),
             "raw": int(df.loc[mask, "rank_raw"].median()),
             "cal": int(df.loc[mask, "rank_cal"].median())}
            for name, mask, note in classes
        ],
        "top": [
            {"entity": str(r["entity"]),
             "raw": int(r["rank_raw"]), "cal": int(r["rank_cal"]),
             "essential": bool(r["entity"] in ess)}
            for _, r in df.nsmallest(12, "rank_cal").iterrows()
        ],
    }

    # --- FIGURE 5: the count distribution ------------------------------------------
    # The chart that explains figures 3 and 4. Drawn last, read first: if n does not
    # vary, calibration is one common monotone transform and cannot reorder anything.
    vc = genes["n"].value_counts().sort_index()
    figures["count_distribution"] = {
        "title": "How much does the observation count actually vary?",
        "question": "The correction reorders a ranking only when counts differ. So the "
                    "first thing to plot about any screen is whether they do.",
        "total": int(len(genes)),
        "distinct": int(len(vc)),
        "modal_n": int(vc.idxmax()),
        "modal_share": round(float(vc.max() / len(genes)), 4),
        "bars": [{"n": int(n), "genes": int(c),
                  "share": round(float(c / len(genes)), 5)} for n, c in vc.items()],
    }

    text = json.dumps(figures, indent=1) + "\n"
    path = DEST / "depmap.json"
    if "--check" in sys.argv:
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current != text:
            print("STALE: %s" % path)
            return 1
        print("figure data is current")
        return 0
    path.write_text(text, encoding="utf-8")
    print("wrote %s (%d figures, %.0f KB)"
          % (path.relative_to(ROOT), len(figures), len(text) / 1024))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
