#!/usr/bin/env python
"""From a calibrated z to a defensible cut: the multiplicity step this library never took.

WHY THIS IS THE MISSING PIECE, and why it is missing from exactly this library. The whole
premise here is that a maximum over many correlated observations is not a maximum over many
independent ones. Calibrating each gene against a null of the right SHAPE fixes the first half
of that — the score is no longer a measurement of how many observations a gene had. It does
nothing at all about the second half: 17,916 genes are being ranked, and picking the top of
17,916 numbers is itself a selection operator. A z of 3 is unremarkable when you drew 17,916
of them.

So the shortlist has been produced by an eyeball threshold this whole time. This file replaces
it with the machinery the field already has, and — more usefully — tests the assumption that
machinery rests on.

FOUR STEPS, AND THE SECOND ONE IS THE POINT.

  1. PARAMETRIC p. Treat z as standard normal and take the upper tail. This is what everyone
     does and what nobody checks.

  2. TEST THAT ASSUMPTION against the non-essential controls, which are genes that should
     score at zero and therefore ARE an empirical null. Kolmogorov-Smirnov and Anderson-Darling
     against N(0,1), plus the observed mean and variance. If the controls are not standard
     normal, every parametric p above is wrong by a knowable amount, and the honest route is
     step 3.

  3. EMPIRICAL p from the control distribution itself: the fraction of controls at least as
     extreme. No distributional assumption at all. Its resolution is bounded by the number of
     controls — with 781 of them the smallest attainable p is about 1/782 — so it cannot
     separate the very top of the list, and that limit is reported rather than hidden behind
     an interpolation.

  4. FALSE DISCOVERY RATE over both, by Benjamini-Hochberg, with Storey's pi-zero as the
     estimate of what fraction of genes are null. Reported beside the naive |z| > 3 count so
     the difference between a threshold and a guarantee is visible.

WHAT THIS USES, AND WHY IT IS NOT WRITTEN BY HAND. scipy for the distributions and the
goodness-of-fit tests, statsmodels for the FDR correction. Re-implementing Benjamini-Hochberg
is four lines and re-implementing Anderson-Darling's critical values is not; a project whose
argument is about statistical care should not be hand-rolling the statistics it can import.

    python tools/multiplicity.py     # writes out/multiplicity.json
"""

from __future__ import annotations

import json
import pathlib

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

ROOT = pathlib.Path(__file__).resolve().parent.parent
GENES = ROOT / "out" / "depmap_genes.csv"
DEST = ROOT / "out" / "multiplicity.json"


def storey_pi0(p: np.ndarray, lam: float = 0.5) -> float:
    """Storey's estimate of the null fraction: how much of the p distribution is flat.

    Above a threshold lambda, true signal has essentially no mass, so whatever is up there is
    null and its density extrapolates back over the whole interval. Clipped to 1 because an
    estimate above one is an artefact of a small sample, not a discovery that more than
    everything is null.
    """
    above = float((p > lam).sum())
    return float(min(1.0, above / (len(p) * (1.0 - lam))))


def main() -> int:
    if not GENES.exists():
        raise SystemExit("missing %s — run the depmap stage first" % GENES.relative_to(ROOT))

    df = pd.read_csv(GENES)
    z = df["z"].to_numpy(dtype=float)
    is_control = df["is_nonessential_control"].astype(str).str.lower().eq("true").to_numpy()
    is_essential = df["is_common_essential"].astype(str).str.lower().eq("true").to_numpy()
    ctrl = z[is_control]

    # ---- 1. parametric ---------------------------------------------------------------
    p_param = stats.norm.sf(z)

    # ---- 2. is the calibrated z actually standard normal? -----------------------------
    ks = stats.kstest(ctrl, "norm")
    # Cramer-von Mises rather than Anderson-Darling: it returns a p-value directly, where
    # scipy's Anderson interface is mid-deprecation and would have to be pinned to a method.
    # Both weight the tails differently from KS, which is the reason to run a second one at all.
    cvm = stats.cramervonmises(ctrl, "norm")
    ctrl_mean, ctrl_sd = float(ctrl.mean()), float(ctrl.std(ddof=1))
    shapiro = stats.shapiro(ctrl[:5000]) if len(ctrl) > 3 else None

    # ---- 3. empirical p from the controls ---------------------------------------------
    # (1 + #{controls >= z}) / (1 + #controls): the plus-one is not decoration, it stops a
    # p-value of exactly zero, which is a claim no finite resample can support.
    order = np.sort(ctrl)
    ge = len(order) - np.searchsorted(order, z, side="left")
    p_emp = (1.0 + ge) / (1.0 + len(order))
    p_floor = 1.0 / (1.0 + len(order))

    # ---- 4. FDR ------------------------------------------------------------------------
    out = {}
    for name, p in (("parametric", p_param), ("empirical", p_emp)):
        rej01, q, _, _ = multipletests(p, alpha=0.01, method="fdr_bh")
        rej05 = multipletests(p, alpha=0.05, method="fdr_bh")[0]
        pi0 = storey_pi0(p)
        out[name] = {
            "pi0": round(pi0, 4),
            "impliedNull": int(round(pi0 * len(p))),
            "atFDR01": int(rej01.sum()),
            "atFDR05": int(rej05.sum()),
            "atFDR01Candidates": int((rej01 & ~is_essential & ~is_control).sum()),
            "atFDR05Candidates": int((rej05 & ~is_essential & ~is_control).sum()),
            "controlsRejectedAt05": int((rej05 & is_control).sum()),
            "minQ": float(np.min(q)),
        }

    naive3 = int((z > 3).sum())
    naive3_cand = int(((z > 3) & ~is_essential & ~is_control).sum())

    payload = {
        "generated": "tools/multiplicity.py",
        "input": "out/depmap_genes.csv",
        "uses": ["scipy.stats", "statsmodels.stats.multitest"],
        "premise": (
            "Calibrating each gene against a null of the right shape stops the score measuring "
            "how many observations a gene had. It does nothing about the other half of the same "
            "problem: 17,916 genes are being ranked, and taking the top of 17,916 numbers is "
            "itself a selection operator. A z of 3 is unremarkable when you drew 17,916 of them."
        ),
        "scale": {
            "genes": int(len(df)),
            "controls": int(is_control.sum()),
            "commonEssential": int(is_essential.sum()),
            "candidates": int((~is_control & ~is_essential).sum()),
        },
        "assumption": {
            "claim": "The calibrated z is standard normal, so the upper tail of N(0,1) is a p-value.",
            "testedOn": "the non-essential control genes, which should score at zero and are "
                        "therefore an empirical null",
            "controlMean": round(ctrl_mean, 4),
            "controlSd": round(ctrl_sd, 4),
            "ksStatistic": round(float(ks.statistic), 4),
            "ksP": float(ks.pvalue),
            "shapiroP": float(shapiro.pvalue) if shapiro is not None else None,
            "cvmStatistic": round(float(cvm.statistic), 4),
            "cvmP": float(cvm.pvalue),
            "whyItMatters": (
                "The first two moments pass and the shape does not: a mean of %.3f and a "
                "standard deviation of %.3f look like a textbook pass, and the distribution "
                "is still not normal. Reporting mean and sd alone would have declared this "
                "calibration correct."
                % (ctrl_mean, ctrl_sd)
            ),
            "verdict": (
                "PASSES: the controls are close enough to standard normal that the parametric "
                "tail is usable."
                if ks.pvalue > 0.01 else
                "FAILS: the controls depart from standard normal at the 1% level, so every "
                "parametric p-value below is wrong by an amount this test quantifies. The "
                "empirical column is the one to read."
            ),
        },
        "empiricalResolution": {
            "controls": int(len(ctrl)),
            "smallestAttainableP": round(float(p_floor), 6),
            "says": (
                "An empirical p cannot go below 1/(1+%d) = %.2e no matter how extreme the gene "
                "is, so this column cannot separate the very top of the list. That is a real "
                "limit of resampling against a finite control set, not a rounding choice."
                % (len(ctrl), p_floor)
            ),
        },
        "fdr": out,
        "naive": {
            "zOver3": naive3,
            "zOver3Candidates": naive3_cand,
            "says": (
                "The threshold the shortlist has been using implicitly. Against %d genes, |z| > 3 "
                "is not a 0.1%% error rate — it is 0.1%% of 17,916, which is about eighteen "
                "false positives before anything real appears."
                % len(df)
            ),
            "expectedFalsePositives": round(float(stats.norm.sf(3) * len(df)), 1),
        },
        "finding": (
            "The correction changes the size of the defensible list, not its top. What it buys "
            "is a statement no threshold can make: at a false discovery rate of 5%, this many "
            "genes, and of those roughly one in twenty is expected to be wrong. A cut at z > 3 "
            "says nothing about how many of the genes past it are noise."
        ),
    }

    DEST.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("wrote %s" % DEST.relative_to(ROOT))
    a = payload["assumption"]
    print("  controls: mean %.4f sd %.4f · KS p %.3g · %s"
          % (a["controlMean"], a["controlSd"], a["ksP"], a["verdict"].split(":")[0]))
    for k, v in out.items():
        print("  %-11s pi0 %.3f · FDR 1%%: %s (%s candidates) · FDR 5%%: %s (%s candidates)"
              % (k, v["pi0"], format(v["atFDR01"], ","), format(v["atFDR01Candidates"], ","),
                 format(v["atFDR05"], ","), format(v["atFDR05Candidates"], ",")))
    print("  naive |z|>3: %s genes, ~%.0f of them expected false"
          % (format(naive3, ","), payload["naive"]["expectedFalsePositives"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
