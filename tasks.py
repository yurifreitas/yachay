#!/usr/bin/env python
"""Task runner — the command line in front of the pipeline. Stdlib only.

Two kinds of task live here, and they are deliberately different:

  * **fetch** tasks download inputs. They touch the network, they are idempotent, and they
    are NOT part of the build graph — a missing 1.4 GB file should stop an analysis with a
    message, not trigger a silent download in the middle of one.
  * **everything else** delegates to `sieve.pipeline`, which orders stages by dependency,
    skips what is already fresh, and prints why.

The knowledge about what depends on what lives in `src/sieve/pipeline/stages.py`. This
file only names the commands.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
DATA = ROOT / "data" / "depmap"
PY = sys.executable

from sieve.pipeline import DEFAULT_TARGETS, STAGES, describe, run  # noqa: E402

# DepMap 24Q4 Public, figshare mirror. The portal itself is behind a bot check, so we use
# the official figshare distribution rather than scraping it.
FILES = {
    "CRISPRGeneEffect.csv": 51064667,
    "AchillesNonessentialControls.csv": 51063566,
    "AchillesCommonEssentialControls.csv": 51063560,
    "AchillesHighVarianceGeneControls.csv": 51063563,
}

# Genotype and lineage, needed only by the NF2 subgroup analysis.
NF2_FILES = {
    "Model.csv": 51065297,                                   # 0.6 MB  lineage, disease
    "OmicsSomaticMutationsMatrixDamaging.csv": 51065747,     # 148 MB  damaging calls
    "OmicsCNGene.csv": 51065324,                             # 1.4 GB  deletion
}

TASKS: dict[str, object] = {}


def task(fn):
    TASKS[fn.__name__] = fn
    return fn


def _download(files: dict[str, int]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    for name, fid in files.items():
        dest = DATA / name
        if dest.exists() and dest.stat().st_size > 0:
            print("have %s (%.1f MB)" % (name, dest.stat().st_size / 1e6))
            continue
        print("fetching %s ..." % name, flush=True)
        urllib.request.urlretrieve(f"https://ndownloader.figshare.com/files/{fid}", dest)
        print("  %.1f MB" % (dest.stat().st_size / 1e6))


# --- inputs -----------------------------------------------------------------------------

@task
def fetch():
    """Download the DepMap release files (~429 MB, resumable by re-running)."""
    _download(FILES)


@task
def fetch_nf2():
    """Download the genotype and lineage files the NF2 analysis needs (~1.5 GB)."""
    _download(NF2_FILES)


# --- the build graph ---------------------------------------------------------------------

@task
def status():
    """Show every stage and whether it is fresh or stale, and why."""
    describe(STAGES)


@task
def build():
    """Run everything that is stale, in dependency order."""
    raise SystemExit(run(STAGES, DEFAULT_TARGETS))


@task
def rebuild():
    """Run everything, ignoring freshness."""
    raise SystemExit(run(STAGES, DEFAULT_TARGETS, force=True))


@task
def plan():
    """Show what `build` would do, without doing it."""
    raise SystemExit(run(STAGES, DEFAULT_TARGETS, dry_run=True))


# --- individual stages, so one target can still be asked for -----------------------------

def _stage_task(name: str):
    def fn():
        raise SystemExit(run(STAGES, [name]))

    fn.__name__ = name
    fn.__doc__ = STAGES[name].summary
    return task(fn)


for _name in STAGES:
    _stage_task(_name)


# --- tests --------------------------------------------------------------------------------

@task
def test():
    """Unit tests — offline, no dataset needed."""
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    r = subprocess.run([PY, "-m", "pytest", "tests", "-q"], cwd=ROOT, env=env)
    if r.returncode:
        raise SystemExit(r.returncode)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print("sieve tasks\n")
        for name, fn in TASKS.items():
            print("  %-11s %s" % (name, (fn.__doc__ or "").strip().split("\n")[0]))
        print()
        print("  Stages run in dependency order and skip when fresh — `status` shows which.")
        return
    for name in args:
        if name not in TASKS:
            raise SystemExit("unknown task %r — run `python tasks.py` for the list" % name)
        TASKS[name]()


if __name__ == "__main__":
    main()
