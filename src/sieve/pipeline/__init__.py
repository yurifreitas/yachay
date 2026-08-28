"""The build graph: what the project produces, from what, in what order.

    from sieve.pipeline import STAGES, run, describe

Kept separate from `sieve.stages`, which is the *methodology's* ten stages. Two different
meanings of the word, one of which is a pipeline step and one of which is a scientific
gate; the package boundary is what keeps them from being confused.
"""

from .paths import ROOT, ensure_dirs, rel
from .runner import PipelineError, describe, run, topological
from .stage import Stage, sources
from .stages import DEFAULT_TARGETS, STAGES

__all__ = [
    "ROOT", "ensure_dirs", "rel",
    "PipelineError", "describe", "run", "topological",
    "Stage", "sources",
    "DEFAULT_TARGETS", "STAGES",
]
