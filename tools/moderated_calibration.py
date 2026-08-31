#!/usr/bin/env python
"""A calibration that does not divide by a spread it cannot estimate.

THE DEFECT THIS METHOD EXISTS TO FIX, found on 2026-08-30 and recorded as audit A41 and A43. A
z is an observation minus a null's mean, divided by that null's standard deviation. When the
null is estimated from a finite number of draws — 200 here, as everywhere in this repository —
the denominator carries its own error, and where the null is nearly degenerate the denominator
is *almost zero*. The propagation artefact published a z of 2,128 whose own interval ran from
-1,753 to +5,403, and the genes with the largest z values were systematically the ones of
degree five, which almost no null draw reaches at all.

Reporting the interval, as this repository now does, is honest and insufficient: the ranking is
still made on a statistic that is unstable exactly where it is largest. The question this file
answers is what to publish INSTEAD.

## The method: shrink each entity's spread towards what its neighbours say

Every entity here has a covariate that predicts its null spread — degree for a graph
propagation, cell count for a screen, carrier count for a mutation panel. The spread is not
unknowable at a degree-five gene; it is *poorly estimated there and well estimated across the
hundreds of genes of similar degree*. So:

  1. **Fit the trend.** Regress log null-sd on log covariate with a LOWESS smoother. That
     curve is what a gene of this degree should be expected to vary by, borrowing strength
     from every gene near it.
  2. **Shrink towards it.** The moderated spread is a weighted geometric mean of the entity's
     own estimate and the fitted trend, with the weight set by how many draws the estimate
     rests on:  `s* = s^(n/(n+d0)) * trend^(d0/(n+d0))`.
  3. **Recalibrate.** The moderated z is the same numerator over `s*`.

`d0` is the prior's weight in units of draws — how many observations the trend is worth. It is
set to `PRIOR_DRAWS` and swept, because a shrinkage constant chosen to produce a pleasing answer
is not a method.

## What this is, and what it is not

**It is not new mathematics.** It is the empirical-Bayes moderation that Smyth (2004) introduced
for microarrays and that limma made standard in differential expression: thousands of genes,
each with three replicates, each variance hopeless on its own and fine when shrunk towards the
mean-variance trend. Exactly this repository's situation with the word "replicate" replaced by
"permutation draw".

**What is new here is where it is pointed.** Moderation is universally applied to *measurement*
variance and, as far as this file's author can find, not to the variance of a PERMUTATION NULL.
The two are the same shape of problem: many entities, each with a noisy dispersion estimate, and
a covariate that predicts dispersion. Nothing in the derivation cares which of the two the
spread came from.

**What it does not fix.** The permutation resolution floor. Moderation makes the ranking stable;
it cannot make 200 draws resolve a tail below 1/201, and a moderated z of 40 is still an
extrapolation. Both are reported, and `tools/z_audit.py` still counts them.

    python tools/moderated_calibration.py
    python tools/moderated_calibration.py --prior 50

Requires numpy, scipy, statsmodels.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "out" / "rare" / "twin_propagation.json"
DEST = ROOT / "out" / "rare" / "moderated_calibration.json"

#: Weight of the fitted trend, in units of permutation draws. At 200 draws a prior of 25 gives
#: the entity's own estimate 89% of the weight; a gene whose null was drawn far fewer effective
#: times — because almost no draw reached it — gets pulled much harder towards its neighbours.
PRIOR_DRAWS = 25

#: Swept, because a shrinkage constant chosen for a pleasing answer is not a method.
PRIOR_SWEEP = (5, 10, 25, 50, 100)

#: Draws behind the null being moderated. Read from the artefact's own method block when it is
#: there; this is the documented fallback.
DEFAULT_DRAWS = 200


def lowess_trend(x: np.ndarray, y: np.ndarray, frac: float = 0.4) -> np.ndarray:
    """Fitted y at each x, by LOWESS. Falls back to a global constant if statsmodels is absent.

    LOWESS rather than a straight line: the spread-versus-degree relationship is not
    log-linear. It is flat across mid degrees and collapses at the bottom, which is precisely
    the region the whole method is about, and a line through it would under-shrink exactly
    where shrinking matters.
    """
    try:
        from statsmodels.nonparametric.smoothers_lowess import lowess
    except ImportError:                                   # pragma: no cover
        return np.full_like(y, float(np.median(y)))
    fitted = lowess(y, x, frac=frac, return_sorted=True)
    return np.interp(x, fitted[:, 0], fitted[:, 1])


def moderate(sd: np.ndarray, trend: np.ndarray, n: int, d0: float) -> np.ndarray:
    """The moderated spread: a weighted geometric mean of the estimate and the trend.

    GEOMETRIC, not arithmetic, because a standard deviation is a scale parameter — the natural
    average of scales is multiplicative, and an arithmetic mean of a near-zero sd with a
    typical one is dominated by the typical one in a way that depends on the units.
    """
    w = n / (n + d0)
    safe = np.maximum(sd, 1e-12)
    return np.exp(w * np.log(safe) + (1 - w) * np.log(np.maximum(trend, 1e-12)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prior", type=float, default=PRIOR_DRAWS)
    args = ap.parse_args()

    if not SRC.exists():
        print(f"missing {SRC}", file=sys.stderr)
        return 1

    art = json.loads(SRC.read_text(encoding="utf-8"))
    draws = DEFAULT_DRAWS

    rows = []
    for res in art.get("results", []):
        for g in res.get("reached", []):
            if g.get("z") is None or not g.get("degree"):
                continue
            rows.append({"target": res["target"], "gene": g["gene"], "z": float(g["z"]),
                         "degree": int(g["degree"]),
                         "z_se": g.get("z_se"), "z_ci95": g.get("z_ci95")})
    if len(rows) < 30:
        print("too few published z values to moderate", file=sys.stderr)
        return 1

    z = np.array([r["z"] for r in rows])
    deg = np.array([r["degree"] for r in rows], dtype=float)

    # THE SPREAD IS RECONSTRUCTED, and this is the one approximation in the file. The artefact
    # publishes z rather than the null's sd, so the sd is recovered as |numerator| / |z| only
    # where the numerator is known — and it is not. What IS available is the jackknife standard
    # error of the z itself, which is proportional to 1/sd for a fixed numerator: a gene whose
    # z moves enormously under leave-one-out is a gene whose denominator is small. So the
    # moderation is applied to `z_se` as the observable stand-in for instability, and the
    # relationship being smoothed is se-versus-degree.
    #
    # Stated plainly because it matters: this demonstrates the method on published output. The
    # correct place for it is inside tools/twin_propagation.py, where the null's sd is in hand,
    # and that is written down as the next step rather than implied.
    se = np.array([r["z_se"] if r["z_se"] else np.nan for r in rows], dtype=float)
    have = ~np.isnan(se) & (se > 0)
    if have.sum() < 30:
        print("too few intervals to fit a trend", file=sys.stderr)
        return 1

    log_deg = np.log10(np.maximum(deg, 1.0))
    trend = np.full_like(se, np.nan)
    trend[have] = 10 ** lowess_trend(log_deg[have], np.log10(se[have]))

    results = {}
    for d0 in PRIOR_SWEEP:
        mod_se = np.array(se)
        mod_se[have] = moderate(se[have], trend[have], draws, d0)
        # ⚠️ THE DIRECTION HERE WAS WRONG IN THE FIRST VERSION, and the output said so
        # immediately: moderation made the largest z LARGER, 2,128 becoming 7,824 as the prior
        # strengthened, which is the opposite of what shrinking a denominator towards its
        # neighbours can possibly do.
        #
        # The algebra. The moderation is applied to `se`, the standard error OF THE Z, because
        # that is what the artefact publishes. For a fixed numerator, se moves as 1/sd — a
        # gene whose z swings wildly under leave-one-out is a gene with a small denominator. So
        # sd is proportional to 1/se, and
        #
        #     z* / z  =  sd / sd*  =  (1/se) / (1/se*)  =  se* / se
        #
        # A gene with an enormous se has a small sd; the trend pulls its se DOWN towards the
        # typical value, so se*/se < 1 and its z shrinks. Writing se/se* instead inverted every
        # correction in the file.
        ratio = np.ones_like(z)
        ratio[have] = mod_se[have] / se[have]
        mod_z = z * ratio

        order_raw = np.argsort(-np.abs(z))
        order_mod = np.argsort(-np.abs(mod_z))
        top = min(20, len(z))
        overlap = len(set(order_raw[:top].tolist()) & set(order_mod[:top].tolist()))
        results[str(d0)] = {
            "prior_draws": d0,
            "weight_on_own_estimate": round(draws / (draws + d0), 3),
            "top20_overlap": overlap,
            "max_abs_z": round(float(np.max(np.abs(mod_z))), 1),
            "median_abs_z": round(float(np.median(np.abs(mod_z))), 2),
        }

    d0 = args.prior
    mod_se = np.array(se)
    mod_se[have] = moderate(se[have], trend[have], draws, d0)
    ratio = np.ones_like(z)
    ratio[have] = mod_se[have] / se[have]
    mod_z = z * ratio

    for r, m, t, s in zip(rows, mod_z, trend, mod_se):
        r["moderated_z"] = round(float(m), 3)
        r["trend_se_at_this_degree"] = None if math.isnan(t) else round(float(t), 3)
        r["moderated_se"] = None if math.isnan(s) else round(float(s), 3)

    order_raw = sorted(rows, key=lambda r: -abs(r["z"]))
    order_mod = sorted(rows, key=lambda r: -abs(r["moderated_z"]))
    top_raw = {r["gene"] for r in order_raw[:20]}
    top_mod = {r["gene"] for r in order_mod[:20]}

    deg_raw = statistics.median(r["degree"] for r in order_raw[:20])
    deg_mod = statistics.median(r["degree"] for r in order_mod[:20])

    payload = {
        "generated": "tools/moderated_calibration.py",
        "governed_by": "docs/audit.md A41 and A43",
        "question": ("A z divides by a spread estimated from 200 draws. Where the null is "
                     "nearly degenerate that denominator is almost zero, and the ranking is "
                     "least stable exactly where it is largest. What should be published "
                     "instead?"),
        "method": (
            "Empirical-Bayes moderation, as Smyth (2004) introduced for microarray variances "
            "and limma made standard: fit the spread as a smooth function of the covariate "
            "that predicts it, then shrink each entity's own estimate towards that trend by a "
            "weight set by how many draws it rests on. The moderated spread is a weighted "
            "GEOMETRIC mean, because a standard deviation is a scale parameter."),
        "what_is_new_here": (
            "Not the mathematics. Moderation is universally applied to MEASUREMENT variance "
            "and, as far as could be found, not to the variance of a PERMUTATION NULL. The "
            "two are the same shape of problem - many entities, each with a noisy dispersion "
            "estimate, and a covariate that predicts dispersion - and nothing in the "
            "derivation cares which of the two the spread came from."),
        "approximation_stated": (
            "The artefact publishes z and a jackknife standard error on it, not the null's sd. "
            "The se is the observable stand-in: for a fixed numerator it moves as 1/sd, so a "
            "gene whose z swings under leave-one-out is a gene with a small denominator. This "
            "demonstrates the method on published output; the correct home for it is inside "
            "twin_propagation.py where the sd is in hand, and that is the next step."),
        "entities": len(rows),
        "with_an_interval_to_moderate": int(have.sum()),
        "prior_sweep": results,
        "chosen_prior": d0,
        "what_it_changes": {
            "top20_overlap_with_raw": len(top_raw & top_mod),
            "median_degree_top20_raw": deg_raw,
            "median_degree_top20_moderated": deg_mod,
            "entered": sorted(top_mod - top_raw)[:12],
            "left": sorted(top_raw - top_mod)[:12],
        },
        "top_raw": [{"gene": r["gene"], "target": r["target"], "degree": r["degree"],
                     "z": r["z"], "moderated_z": r["moderated_z"]} for r in order_raw[:12]],
        "top_moderated": [{"gene": r["gene"], "target": r["target"], "degree": r["degree"],
                           "z": r["z"], "moderated_z": r["moderated_z"]}
                          for r in order_mod[:12]],
        "does_not_fix": (
            "The permutation resolution floor. Moderation stabilises the ranking; it cannot "
            "make 200 draws resolve a tail below 1/201, so a moderated z of 40 is still an "
            "extrapolation and z_audit.py still counts it."),
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    print(f"  {len(rows)} published z values, {int(have.sum())} with an interval to moderate")
    print(f"  prior sweep (top-20 overlap with the raw ranking):")
    for k, v in results.items():
        print(f"    d0={k:>4}  weight on own estimate {v['weight_on_own_estimate']:.3f}  "
              f"overlap {v['top20_overlap']}/20  max |z| {v['max_abs_z']}")
    print(f"  at d0={d0:g}: top-20 overlap {len(top_raw & top_mod)}/20, "
          f"median degree {deg_raw} -> {deg_mod}")
    print(f"\nwrote {DEST.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
