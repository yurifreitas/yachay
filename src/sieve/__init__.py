"""sieve — turn a large, noisy, confounded screen into a defensible shortlist.

The problem class this library is for:

    You have many candidate entities. Each carries a noisy aggregate score estimated
    from a VARYING number of observations. Confounds correlate with that score. A
    downstream validation is expensive and can test only a handful. Produce a shortlist
    you can defend.

That shape appears in perturbation screens, drug screens, A/B triage, feature selection,
materials discovery, and security alert triage. The stages are domain-agnostic; the
adapters are not.

The stages, in the order they must run:

    0  objective    decode the metric and its degeneracies
    1  null         calibrate the metric against its own null AT the observation count
    2  power        reliability weighting / shrinkage
    3  confound     separate real signal from technical and viability artifacts
    4  baseline     beat a simple model OUT OF FOLD, or drop the complexity
    5  validation   leakage-safe splits; validate against something you did not optimize
    6  prior        fold in mechanism knowledge, at lower weight than measurement
    7  shortlist    nominate, diversify, disclose concentration
    8  report       every claim carries an executable assertion
    9  repro        deterministic, offline, fingerprinted

Stage 1 is why this library exists separately from its predecessor. See stages/null.py.
"""

from .contracts import Column, ContractError, Schema, entity_scores
from .stages.null import NullModel, calibrate, fit_null, top_k_mean
from .stages.power import (
    Detectable,
    PowerError,
    min_detectable_effect,
    min_detectable_proportion_difference,
    required_n,
    underpowered,

)
from .stages.target import Assessment, Evidence, Gate, Strategy, assess, shortlist

__version__ = "0.1.0"

__all__ = [
    "Column",
    "ContractError",
    "Schema",
    "entity_scores",
    "NullModel",
    "calibrate",
    "fit_null",
    "top_k_mean",
    # Stage 2 - Power
    "Detectable",
    "PowerError",
    "min_detectable_effect",
    "min_detectable_proportion_difference",
    "required_n",
    "underpowered",
]
