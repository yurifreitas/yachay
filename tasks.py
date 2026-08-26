#!/usr/bin/env python
"""Task runner — the single place naming every operation. Stdlib only."""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data" / "depmap"
PY = sys.executable

# DepMap 24Q4 Public, figshare mirror. The portal itself is behind a bot check, so we
# use the official figshare distribution rather than scraping it.
FILES = {
    "CRISPRGeneEffect.csv": 51064667,
    "AchillesNonessentialControls.csv": 51063566,
    "AchillesCommonEssentialControls.csv": 51063560,
    "AchillesHighVarianceGeneControls.csv": 51063563,
}

TASKS: dict[str, object] = {}


def task(fn):
    TASKS[fn.__name__] = fn
    return fn


def run(*args):
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    print("$ " + " ".join(args), flush=True)
    r = subprocess.run(args, cwd=ROOT, env=env)
    if r.returncode:
        raise SystemExit(r.returncode)


@task
def test():
    """Unit tests — offline, no dataset needed."""
    run(PY, "-m", "pytest", "tests", "-q")


@task
def fetch():
    """Download the DepMap release files (~429 MB, resumable by re-running)."""
    DATA.mkdir(parents=True, exist_ok=True)
    for name, fid in FILES.items():
        dest = DATA / name
        if dest.exists() and dest.stat().st_size > 0:
            print("have %s (%.1f MB)" % (name, dest.stat().st_size / 1e6))
            continue
        url = f"https://ndownloader.figshare.com/files/{fid}"
        print("fetching %s ..." % name, flush=True)
        urllib.request.urlretrieve(url, dest)
        print("  %.1f MB" % (dest.stat().st_size / 1e6))


@task
def depmap():
    """Run the reference analysis on DepMap."""
    run(PY, str(ROOT / "analyses" / "depmap_selective_dependency.py"))


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print("sieve tasks:\n")
        for name, fn in TASKS.items():
            print("  %-10s %s" % (name, (fn.__doc__ or "").strip().split("\n")[0]))
        return
    for name in args:
        if name not in TASKS:
            raise SystemExit("unknown task %r" % name)
        TASKS[name]()


if __name__ == "__main__":
    main()
