"""Stage 2 — Power. What the observation count you have could possibly detect.

The idea in one sentence: **before believing an effect, know the smallest effect the
sample could have found.**

Stage 1 asks what the score reads when nothing is happening. This one asks the question
immediately after it and is skipped just as often: given the number of observations behind
an estimate, what is the smallest true effect that would have shown up? An entity measured
on nine observations and one measured on nine hundred are not two estimates of differing
precision — they are an estimate and a rumour, and a ranking that mixes them is ranking
partly on how hard anyone looked.

## Why this exists as a library stage rather than as arithmetic in a script

It was arithmetic in a script. `tools/dossier.py` computed a minimum detectable effect
inline to ask whether the clinical trials on record for a rare disease could have found
anything, and the answer was severe enough to publish: across a twelve-disease portfolio,
**ten of twelve** had a median interventional trial that could not detect even a large
effect. That is a Stage 2 result, produced without a Stage 2, and `docs/audit.md` A15 named
the pattern — 10,506 lines of tooling, none of it using the library it sits beside, while
eight of the ten headline stages had no implementation at all.

So the arithmetic moved here, and gained the part a script did not need but a stage does:
**the per-entity form**. A screen does not have one sample size. It has one per entity, and
that is the whole premise of this library.

## The arithmetic, and what it assumes

For a two-arm comparison of means with total sample `n` split evenly, at significance
`alpha` (two-sided) and power `1 - beta`:

    MDE = (z(1 - alpha/2) + z(power)) * sqrt(4 / n)

in units of the outcome's standard deviation — Cohen's `d`. The inverse, `required_n`,
solves the same expression for `n`.

**Every assumption in it flatters the study**: even allocation, no dropout, one primary
endpoint, no covariate adjustment, and a normal sampling distribution. A real design
violates at least one, so a real study detects *less* than this. It is reported as a
**floor**, and the word matters: a bound that flatters the design and still comes out
damning is a bound worth publishing, and one that is quoted as a promise is a lie with a
square root in it.

For a **proportion** — which is what a phenotype frequency is, and what most of this
project's rare-disease work actually handles — the normal approximation to a difference of
two proportions is used, and it is refused below the count where it stops being honest
rather than silently returning a number.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

# The two normal quantiles this stage needs, to five decimals. Hard-coded rather than
# imported from scipy for the same reason the rest of the library is numpy-only: adding a
# dependency to look up two constants is a bad trade. `alpha` and `power` are therefore
# restricted to the conventional values, and a request for anything else raises rather than
# silently interpolating — a power calculation quietly done at the wrong alpha is precisely
# the class of error this stage exists to catch.
_Z_TWO_SIDED = {0.10: 1.64485, 0.05: 1.95996, 0.01: 2.57583}
_Z_POWER = {0.80: 0.84162, 0.85: 1.03643, 0.90: 1.28155, 0.95: 1.64485}


class PowerError(ValueError):
    """Raised when a power question cannot be answered honestly with what was given."""


def _quantiles(alpha: float, power: float) -> tuple[float, float]:
    if alpha not in _Z_TWO_SIDED:
        raise PowerError(
            f"alpha={alpha} is not one of {sorted(_Z_TWO_SIDED)}. This stage refuses to "
            "interpolate a normal quantile: the point of it is to be checkable by hand."
        )
    if power not in _Z_POWER:
        raise PowerError(
            f"power={power} is not one of {sorted(_Z_POWER)}. Same reason as alpha."
        )
    return _Z_TWO_SIDED[alpha], _Z_POWER[power]


@dataclass(frozen=True)
class Detectable:
    """What a sample of this size could and could not have found.

    `floor` is the minimum detectable standardised effect. `verdict` classifies it against
    Cohen's conventions — not because those conventions are laws, but because a reader needs
    *some* anchor and an unanchored 1.10 means nothing to anyone.
    """

    n: int
    #: Full precision, deliberately. The first version rounded here, and a test comparing
    #: `floor(49)` against the 0.8 threshold then failed for the wrong reason: the true
    #: value is 0.80045, which is above the line, and rounding put it exactly on it.
    #: Rounding inside a model rather than at the point of display is how a boundary case
    #: silently flips. Use `at(3)` to present it.
    floor: float
    verdict: str
    assumptions: str

    def at(self, places: int = 3) -> float:
        """The floor rounded for display. Presentation, not arithmetic."""
        return round(self.floor, places)

    @property
    def can_detect_large(self) -> bool:
        """Could this sample find an effect of 0.8 SD? For rare disease, often no."""
        return self.floor <= 0.8


_ASSUMPTIONS = (
    "two-arm, two-sided, even allocation, no dropout, one primary endpoint, no covariate "
    "adjustment, normal sampling distribution. Every one flatters the design, so a real "
    "study detects less than this. It is a floor, not a promise."
)


def _verdict(floor: float) -> str:
    if floor <= 0.2:
        return "can find a small effect"
    if floor <= 0.5:
        return "can find a medium effect"
    if floor <= 0.8:
        return "can find a large effect only"
    return "cannot find even a large effect"


def min_detectable_effect(n: int, *, alpha: float = 0.05, power: float = 0.80) -> Detectable:
    """Smallest standardised difference a two-arm study of total size `n` could detect.

    >>> min_detectable_effect(26).at()           # a typical rare-disease trial
    1.099
    >>> min_detectable_effect(26).can_detect_large
    False
    >>> min_detectable_effect(2000).at()         # a large registry-scale study
    0.125
    """
    if n is None or n < 4:
        raise PowerError(
            f"n={n} is too small for a two-arm comparison to mean anything. Refusing to "
            "return a number rather than returning one nobody should use."
        )
    z_a, z_b = _quantiles(alpha, power)
    floor = (z_a + z_b) * math.sqrt(4 / n)
    return Detectable(n=int(n), floor=floor, verdict=_verdict(floor), assumptions=_ASSUMPTIONS)


def required_n(effect: float, *, alpha: float = 0.05, power: float = 0.80) -> int:
    """Total sample needed to detect a standardised effect of this size. The inverse.

    Rounded UP, always: a study sized at the rounded-down n is under-powered by
    construction, and the direction of that rounding is not a matter of taste.

    >>> required_n(0.8)     # a large effect
    50
    >>> required_n(0.2)     # a small one
    785
    """
    if effect <= 0:
        raise PowerError("effect must be positive; a null effect needs an infinite sample")
    z_a, z_b = _quantiles(alpha, power)
    return math.ceil(4 * ((z_a + z_b) / effect) ** 2)


def min_detectable_proportion_difference(
    n_per_arm: int, baseline: float, *, alpha: float = 0.05, power: float = 0.80
) -> float:
    """Smallest absolute difference in a proportion this arm size could detect.

    A phenotype frequency is a proportion, and most of this project's rare-disease evidence
    is proportions with denominators in the single digits (`docs/references/rare-disease-scale.md`
    §4b: the median is five patients). The normal approximation is used and is **refused**
    when the expected successes or failures fall below five, because below that the
    approximation is not conservative — it returns a *smaller* number than the truth, which
    is the worst possible direction for a bound whose job is to say "you could not have
    seen this".
    """
    if not 0 < baseline < 1:
        raise PowerError("baseline must be a proportion strictly between 0 and 1")
    expected = n_per_arm * min(baseline, 1 - baseline)
    if expected < 5:
        raise PowerError(
            f"n={n_per_arm} at baseline {baseline} gives {expected:.1f} expected events. "
            "The normal approximation is anti-conservative here — it would understate the "
            "detectable difference. Use an exact method, or report that the question cannot "
            "be answered at this size."
        )
    z_a, z_b = _quantiles(alpha, power)
    var = 2 * baseline * (1 - baseline)
    return round((z_a + z_b) * math.sqrt(var / n_per_arm), 4)


def underpowered(
    counts: Sequence[int], effect: float, *, alpha: float = 0.05, power: float = 0.80
) -> dict:
    """The per-entity form: which entities could not have seen an effect of this size.

    THIS IS THE PART A SCRIPT DID NOT NEED AND A STAGE DOES. A screen does not have one
    sample size; it has one per entity, and the whole premise of this library is that those
    counts vary and that the variation leaks into the ranking. Stage 1 removes the leak from
    the *score*. This says which rows had no chance of showing the effect at all — a
    different question, and the one that decides whether a null result means "no effect" or
    "we did not look hard enough".

    Returns the count, the share, the threshold `n` and the entities' own floors, so a
    caller can report the shape rather than a single number.
    """
    need = required_n(effect, alpha=alpha, power=power)
    clean = [int(c) for c in counts if c is not None and c >= 4]
    dropped = len(counts) - len(clean)
    below = [c for c in clean if c < need]
    return {
        "effect": effect,
        "requiredN": need,
        "entities": len(clean),
        "tooSmallToAssess": dropped,
        "underpowered": len(below),
        "share": round(len(below) / len(clean), 4) if clean else None,
        "medianCount": sorted(clean)[len(clean) // 2] if clean else None,
        "medianFloor": (min_detectable_effect(sorted(clean)[len(clean) // 2],
                                              alpha=alpha, power=power).at()
                        if clean else None),
        "assumptions": _ASSUMPTIONS,
    }
