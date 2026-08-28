"""Order the stages, skip what is fresh, run the rest, say what happened.

Deliberately small. This is not a workflow engine — there is no scheduler, no remote
execution and no retry policy, because a six-stage pipeline that runs on one laptop needs
none of them and every one of them is a thing that can break between you and your data.

What it does have is the three properties the ad-hoc version lacked:

  * **order by dependency**, so `python tasks.py figures` cannot silently read a manifest
    that a prior stage has not written;
  * **skip what is fresh**, so re-running is cheap and therefore actually gets done;
  * **explain itself**, so a skip is a sentence rather than silence.
"""

from __future__ import annotations

import time
from typing import Iterable

from . import paths
from .stage import Stage


class PipelineError(RuntimeError):
    pass


def topological(stages: dict[str, Stage], targets: Iterable[str]) -> list[Stage]:
    """Depth-first resolution of `needs`, with an explicit cycle error.

    A cycle here would be a bug in the stage declarations rather than in user input, so
    it names the stages involved instead of failing with a recursion limit.
    """
    order: list[Stage] = []
    seen: set[str] = set()
    path: list[str] = []

    def visit(name: str) -> None:
        if name in seen:
            return
        if name in path:
            cycle = " -> ".join([*path[path.index(name):], name])
            raise PipelineError(f"cycle in the pipeline: {cycle}")
        if name not in stages:
            known = ", ".join(sorted(stages))
            raise PipelineError(f"unknown stage {name!r}. Known stages: {known}")
        path.append(name)
        for dep in stages[name].needs:
            visit(dep)
        path.pop()
        seen.add(name)
        order.append(stages[name])

    for t in targets:
        visit(t)
    return order


def run(
    stages: dict[str, Stage],
    targets: Iterable[str],
    *,
    force: bool = False,
    dry_run: bool = False,
) -> int:
    """Execute the plan. Returns a process exit code."""
    paths.ensure_dirs()
    plan = topological(stages, targets)

    print("plan: " + " -> ".join(s.name for s in plan))
    print()

    ran = 0
    for s in plan:
        stale, why = s.is_stale()
        if force and s.outputs:
            stale, why = True, "forced"

        if not stale:
            print(f"  SKIP  {s.name:<10} {why}")
            continue

        missing = s.missing_inputs()
        if missing:
            # A missing input is a user-facing problem with a fix, so say the fix.
            print(f"  BLOCK {s.name:<10} missing input: "
                  f"{', '.join(paths.rel(p) for p in missing)}")
            print(f"        {s.summary}")
            return 2

        if dry_run:
            print(f"  WOULD {s.name:<10} {why}")
            continue

        print(f"  RUN   {s.name:<10} {why}")
        if s.run is None:
            raise PipelineError(f"stage {s.name!r} is stale but has no run function")
        t0 = time.perf_counter()
        s.run()
        ran += 1
        print(f"        done in {time.perf_counter() - t0:.1f}s")

    print()
    print(f"{ran} stage(s) ran, {len(plan) - ran} skipped.")
    return 0


def describe(stages: dict[str, Stage]) -> None:
    """`list`, with the freshness of each stage — the question people actually have."""
    width = max(len(n) for n in stages) if stages else 10
    for name, s in stages.items():
        stale, why = s.is_stale()
        mark = "stale" if stale else "fresh"
        print(f"  {name:<{width}}  [{mark}]  {s.summary}")
        if s.needs:
            print(f"  {'':<{width}}           needs: {', '.join(s.needs)}")
        if stale and not s.always:
            print(f"  {'':<{width}}           {why}")
