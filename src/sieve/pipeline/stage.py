"""A stage, and what makes one stale.

A stage declares what it reads, what it writes, and how to produce it. The runner does
the rest: order the stages by dependency, skip the ones whose outputs are already newer
than everything they depend on, and run the rest.

WHAT COUNTS AS AN INPUT — the part worth getting right:

  1. **Data files.** Obvious.
  2. **The code that produces the output.** A stage whose analysis changed must re-run
     even though no data moved. Leaving this out is the failure that makes people stop
     trusting a cache: you fix a bug, re-run, and the old artifact comes back.
  3. **Upstream outputs.** Expressed as a dependency on another stage, so the graph is
     declared once rather than inferred from overlapping path lists.

Staleness is by modification time, not by content hash. Hashing a 429 MB matrix on every
invocation costs more than the check is worth, and mtime is wrong only in the direction
that causes an unnecessary re-run — never in the direction that silently serves a stale
artifact. That asymmetry is why the cheap check is the right one here.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Callable, Sequence

from . import paths


@dataclass(frozen=True)
class Stage:
    """One unit of the pipeline."""

    name: str
    #: One line, shown by `list`. What this produces, not how.
    summary: str
    #: Files that must exist before this can run.
    inputs: Sequence[pathlib.Path] = field(default_factory=tuple)
    #: Files this produces. Emptiness means "always runs" (a check, not a build).
    outputs: Sequence[pathlib.Path] = field(default_factory=tuple)
    #: Names of stages that must run first.
    needs: Sequence[str] = field(default_factory=tuple)
    #: Source files whose change should invalidate the outputs.
    code: Sequence[pathlib.Path] = field(default_factory=tuple)
    #: The work. Takes no arguments; reads and writes through `paths`.
    run: Callable[[], None] | None = None
    #: A stage that verifies rather than builds is never skipped.
    always: bool = False

    def missing_inputs(self) -> list[pathlib.Path]:
        return [p for p in self.inputs if not p.exists()]

    def newest_dependency(self) -> float:
        """The mtime of the most recently touched thing this output depends on."""
        times = [p.stat().st_mtime for p in (*self.inputs, *self.code) if p.exists()]
        return max(times, default=0.0)

    def oldest_output(self) -> float | None:
        """None when any declared output is missing — which is maximally stale."""
        if not self.outputs:
            return None
        times = []
        for p in self.outputs:
            if not p.exists():
                return None
            times.append(p.stat().st_mtime)
        return min(times)

    def is_stale(self) -> tuple[bool, str]:
        """Whether this needs to run, and the sentence explaining why."""
        if self.always:
            return True, "verification stage, never cached"
        if not self.outputs:
            return True, "declares no outputs"
        out = self.oldest_output()
        if out is None:
            missing = [paths.rel(p) for p in self.outputs if not p.exists()]
            return True, f"missing output: {', '.join(missing)}"
        dep = self.newest_dependency()
        if dep > out:
            newer = [
                paths.rel(p)
                for p in (*self.inputs, *self.code)
                if p.exists() and p.stat().st_mtime > out
            ]
            return True, f"changed since last run: {', '.join(newer[:3])}"
        return False, "up to date"


def sources(*globs: str) -> tuple[pathlib.Path, ...]:
    """Resolve code-dependency globs relative to the repo root, sorted for determinism."""
    found: list[pathlib.Path] = []
    for g in globs:
        found.extend(sorted(paths.ROOT.glob(g)))
    return tuple(found)
