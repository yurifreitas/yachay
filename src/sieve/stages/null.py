"""Stage 1 — Null calibration. The stage the predecessor did not have.

The idea in one sentence: **before comparing scores, know what the score reads when
nothing is happening.**

Most screening metrics are not means. They are maxima, top-k means, quantiles,
enrichment statistics — operators that select the largest of several noisy estimates.
Every such operator is *positively biased*, and the bias grows as the estimate gets
noisier. When the number of observations varies across entities — and in a real screen
it always does — the metric is therefore **not comparable across entities**, and its
ranking is partly a ranking of who was measured least.

This is not a hypothetical failure. In the screen this library was distilled from:

  - the celebrated "maximum effect in the training data" was measured on ONE cell, and
    pure noise on one cell scores 0.845 on average and 2.43 at the 99th percentile;
  - the score correlated -0.57 with log observation count, which the analysis had
    labelled a *viability confound* — a biological story for a statistical artifact;
  - calibrating against the null moved the single most important entity in the screen
    from rank 12 to rank 1, and dropped eleven low-observation rows off the top;
  - the eligibility threshold for 90% of a prize pool was, read literally, a one-sample
    noise draw that nothing in the data could exceed.

None of that needed a better model. It needed this stage.

## The method

Given a pool of control observations, resample `n` of them, apply the *same* statistic
the screen uses, and repeat. That gives the null distribution of the statistic AT that
`n`. Do it across a grid of `n`, interpolate, and standardize:

    z = (observed - null_mean(n)) / null_sd(n)

`z` is comparable across entities; the raw score is not.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np
import pandas as pd

__all__ = ["NullModel", "calibrate", "fit_null", "top_k_mean"]

Statistic = Callable[[np.ndarray], np.ndarray]


def top_k_mean(k: int = 3) -> Statistic:
    """The mean of the k largest values per row — a very common screening aggregate.

    Provided because it is the operator that motivated this module, and because writing
    it correctly (over the LAST axis, on a 2-D block of draws) is a step people get
    wrong when they hand-roll it per entity.
    """

    def stat(block: np.ndarray) -> np.ndarray:
        block = np.asarray(block, dtype=float)
        if block.shape[-1] <= k:
            return block.mean(axis=-1)
        return np.partition(block, -k, axis=-1)[..., -k:].mean(axis=-1)

    stat.__name__ = f"top{k}_mean"  # type: ignore[attr-defined]
    return stat


@dataclass(frozen=True)
class NullModel:
    """The null distribution of a statistic as a function of observation count."""

    counts: np.ndarray          # grid of n, ascending
    mean: np.ndarray            # null mean at each n
    sd: np.ndarray              # null sd at each n
    quantiles: pd.DataFrame     # requested quantiles at each n, indexed by count
    statistic: str
    n_draws: int
    n_control: int

    def moments(self, n: np.ndarray | Sequence[int]) -> tuple[np.ndarray, np.ndarray]:
        """Null mean and sd at arbitrary counts, log-interpolated within the grid.

        Counts outside the grid are CLAMPED, which is why :func:`fit_null` insists the
        grid spans the observed range — a grid that stops short silently calibrates
        large entities against a smaller entity's null. That bug shipped once; the
        guard exists so it cannot ship twice.
        """
        n = np.asarray(n, dtype=float)
        lg = np.log(np.maximum(n, 1.0))
        grid = np.log(np.maximum(self.counts.astype(float), 1.0))
        return np.interp(lg, grid, self.mean), np.interp(lg, grid, self.sd)

    def z(self, observed: np.ndarray, n: np.ndarray) -> np.ndarray:
        mu, sd = self.moments(n)
        return (np.asarray(observed, dtype=float) - mu) / np.where(sd > 0, sd, np.nan)

    def to_frame(self) -> pd.DataFrame:
        out = pd.DataFrame({"n": self.counts, "null_mean": self.mean, "null_sd": self.sd})
        for col in self.quantiles.columns:
            out[col] = self.quantiles[col].to_numpy()
        return out

    def summary(self) -> str:
        lo, hi = self.counts[0], self.counts[-1]
        return (
            f"null[{self.statistic}] from {self.n_control:,} control observations, "
            f"{self.n_draws:,} draws per point, n grid {lo}-{hi}: "
            f"bias {self.mean[0]:.4g} at n={lo} -> {self.mean[-1]:.4g} at n={hi}"
        )


def _default_grid(lo: int, hi: int, points: int = 14) -> np.ndarray:
    """Log-spaced grid that always includes both endpoints."""
    lo = max(int(lo), 1)
    hi = max(int(hi), lo + 1)
    grid = np.unique(np.round(np.geomspace(lo, hi, points)).astype(int))
    return np.unique(np.concatenate([[lo], grid, [hi]]))


def fit_null(
    control: np.ndarray,
    statistic: Statistic,
    observed_counts: np.ndarray | Sequence[int],
    *,
    n_draws: int = 4000,
    quantiles: Sequence[float] = (0.95, 0.99),
    grid: Sequence[int] | None = None,
    seed: int = 0,
    block: int = 512,
) -> NullModel:
    """Estimate the null distribution of `statistic` as a function of observation count.

    Parameters
    ----------
    control:
        ``(n_control, n_features)`` matrix of control observations — rows that carry no
        effect. Real controls beat a parametric null: they inherit the screen's own
        correlation structure, which is exactly what inflates a top-k statistic.
    statistic:
        Applied to a ``(draws, n_features)`` block of resampled *entity means* and must
        return one value per row. Use the SAME function the screen scores with.
    observed_counts:
        Observation counts of the real entities. The grid is built to span them, so no
        entity is ever calibrated against a null fitted for a different size.
    """
    control = np.asarray(control, dtype=float)
    if control.ndim != 2:
        raise ValueError("control must be 2-D (observations x features)")
    if len(control) < 50:
        raise ValueError(
            f"only {len(control)} control observations: too few for a stable null. "
            "Widen the control definition or state that this stage could not run."
        )

    observed_counts = np.asarray(observed_counts, dtype=float)
    observed_counts = observed_counts[np.isfinite(observed_counts) & (observed_counts >= 1)]
    if observed_counts.size == 0:
        raise ValueError("observed_counts is empty")

    lo, hi = int(observed_counts.min()), int(observed_counts.max())
    counts = np.asarray(sorted(set(grid)), dtype=int) if grid is not None else _default_grid(lo, hi)
    if counts[0] > lo or counts[-1] < hi:
        raise ValueError(
            f"grid [{counts[0]}, {counts[-1]}] does not span the observed range "
            f"[{lo}, {hi}]. Interpolation clamps outside the grid, so entities beyond it "
            "would be calibrated against the wrong null."
        )

    rng = np.random.default_rng(seed)
    means, sds, qs = [], [], []
    for m in counts:
        vals = np.empty(n_draws, dtype=float)
        done = 0
        while done < n_draws:              # chunked: a 4000 x 4000 x features draw is not free
            take = min(block, n_draws - done)
            idx = rng.integers(0, len(control), size=(take, int(m)))
            vals[done:done + take] = statistic(control[idx].mean(axis=1))
            done += take
        means.append(vals.mean())
        sds.append(vals.std(ddof=1))
        qs.append(np.quantile(vals, quantiles))

    qframe = pd.DataFrame(
        np.asarray(qs),
        index=pd.Index(counts, name="n"),
        columns=[f"p{int(round(q * 100))}" for q in quantiles],
    )
    return NullModel(
        counts=counts,
        mean=np.asarray(means),
        sd=np.asarray(sds),
        quantiles=qframe,
        statistic=getattr(statistic, "__name__", "statistic"),
        n_draws=n_draws,
        n_control=len(control),
    )


def calibrate(
    df: pd.DataFrame,
    null: NullModel,
    *,
    score: str,
    count: str,
    out: str = "z",
) -> pd.DataFrame:
    """Attach the null moments and the calibrated z-score to `df`.

    Returns a copy with ``null_mean``, ``null_sd`` and `out` added. Ranking on `out`
    rather than on `score` is the entire point of the stage.
    """
    for col in (score, count):
        if col not in df.columns:
            raise KeyError(f"column {col!r} not in frame")
    work = df.copy()
    mu, sd = null.moments(work[count].to_numpy())
    work["null_mean"] = mu
    work["null_sd"] = sd
    work[out] = null.z(work[score].to_numpy(), work[count].to_numpy())
    return work
