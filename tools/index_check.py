#!/usr/bin/env python
"""Every artefact on disk must appear in the document that claims to enumerate it.

WHY THIS EXISTS. `tools/verify_claims.py` protects a NUMBER: it holds each published figure
against the artefact that produced it and fails when they drift. Nothing protected a LIST, and
on 2026-08-29 six indexes drifted in a single day — audit finding A36:

    rare-layers.md mapped 26 of 34 artefacts while its own header said 34; tools/README.md
    advertised 14 ingested sources when 18 were registered; README.md and adr/README.md both
    said one construct was measured when three were.

The failure is not cosmetic. The indexes are how a reader decides what has been measured, and
a map that lags the territory understates the project in the direction that makes its
strongest results invisible — which is audit A2, committed again.

WHAT IT CHECKS, and each is a claim some document makes about the filesystem:

    artefacts   every out/rare/*.json appears in docs/references/rare-layers.md
    tools       every tools/*.py appears in tools/README.md
    stages      every registered pipeline stage has a tool or analysis that exists
    sources     every ingested source is named in docs/references/README.md
    adrs        every docs/adr/NNNN-*.md appears in the ADR index
    thresholds  the summary inside manifests/thresholds.yaml matches the entries it
                summarises — it was written at seven entries, the file grew to 25, and
                the summary stayed. A file whose job is auditability was publishing a
                wrong count of itself.

WHAT IT DELIBERATELY DOES NOT CHECK. Whether the DESCRIPTION beside an entry is still true.
A stale sentence next to a present filename is a real defect and this tool cannot see it; only
a reader can. Claiming otherwise would make the check comforting rather than useful, so the
limitation is printed with the result rather than buried here.

    python tools/index_check.py           # report
    python tools/index_check.py --check   # exit 1 when something is unlisted

Stdlib only, so it runs before anything else in a cold checkout.
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def check_artefacts() -> tuple[str, list[str], int]:
    """Every measured artefact appears in the layer map that exists to grade them."""
    index = read("docs/references/rare-layers.md")
    missing = []
    files = sorted((ROOT / "out" / "rare").glob("*.json"))
    for f in files:
        if f.name not in index:
            missing.append(f"out/rare/{f.name} is in no row of rare-layers.md")
    return "artefacts", missing, len(files)


def check_tools() -> tuple[str, list[str], int]:
    index = read("tools/README.md")
    missing = []
    files = sorted((ROOT / "tools").glob("*.py"))
    for f in files:
        if f.name not in index:
            missing.append(f"tools/{f.name} is in no group of tools/README.md")
    return "tools", missing, len(files)


def check_stages() -> tuple[str, list[str], int]:
    """A stage whose producer does not exist is a graph that cannot run."""
    from sieve.pipeline import STAGES  # noqa: PLC0415 - import here so --help works cold

    missing = []
    for name, stage in STAGES.items():
        sources = getattr(stage, "code", ()) or ()
        if sources and not any(pathlib.Path(s).exists() for s in sources):
            missing.append(f"stage {name!r} declares code that does not exist")
    return "stages", missing, len(STAGES)


def check_sources() -> tuple[str, list[str], int]:
    from sieve.pipeline.sources import SOURCES  # noqa: PLC0415

    index = read("docs/references/README.md") + read("tools/README.md")
    missing = []
    for s in SOURCES:
        if s.filename not in index and s.name not in index:
            missing.append(f"source {s.key!r} ({s.filename}) is named in no reference index")
    return "sources", missing, len(SOURCES)


def check_adrs() -> tuple[str, list[str], int]:
    index = read("docs/adr/README.md")
    missing = []
    files = sorted((ROOT / "docs" / "adr").glob("[0-9]*.md"))
    for f in files:
        if f.name not in index:
            missing.append(f"docs/adr/{f.name} is in no row of the ADR index")
    return "adrs", missing, len(files)




def check_thresholds() -> tuple[str, list[str], int]:
    """The manifest's own summary against the entries beneath it.

    A LIST THAT COUNTS ITSELF, which is the one kind of index that can go stale without any
    file being added or removed anywhere else. This one did: the block said "pre-registered:
    3, calibrated to seen data: 4" while the file held nineteen pre-registered and six
    calibrated thresholds, because it was written when there were seven and never recounted.
    """
    path = ROOT / "manifests" / "thresholds.yaml"
    if not path.exists():
        return "thresholds", ["manifests/thresholds.yaml is missing"], 0

    text = path.read_text(encoding="utf-8")
    pre = collections.Counter(re.findall(r"pre_registered:\s*(true|false)", text))
    kind = collections.Counter(re.findall(r"justification:\s*(\w+)", text))
    total = sum(pre.values())

    claimed = re.search(
        r"pre-registered:\s*(\d+)\s+calibrated to seen data:\s*(\d+)", text)
    kinds_claimed = re.search(
        r"kinds:\s*(\d+) mechanistic,\s*(\d+) empirical,\s*(\d+) conventional", text)

    missing = []
    if not claimed:
        missing.append("the summary block states no pre-registered/calibrated counts")
    else:
        want = (pre["true"], pre["false"])
        got = (int(claimed.group(1)), int(claimed.group(2)))
        if want != got:
            missing.append(
                f"summary says {got[0]} pre-registered and {got[1]} calibrated; "
                f"the entries are {want[0]} and {want[1]}")
    if not kinds_claimed:
        missing.append("the summary block states no kind counts")
    else:
        want = (kind["mechanistic"], kind["empirical"], kind["conventional"])
        got = tuple(int(kinds_claimed.group(i)) for i in (1, 2, 3))
        if want != got:
            missing.append(
                f"summary says {got} mechanistic/empirical/conventional; "
                f"the entries are {want}")
    return "thresholds", missing, total


CHECKS = [check_artefacts, check_tools, check_stages, check_sources, check_adrs,
          check_thresholds]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 when anything is unlisted")
    args = ap.parse_args()

    total_missing = 0
    print("index check — is everything on disk named in the document that enumerates it?\n")
    for fn in CHECKS:
        name, missing, n = fn()
        total_missing += len(missing)
        mark = "ok  " if not missing else "MISS"
        print(f"  [{mark}] {name:10s} {n:4d} on disk, {len(missing)} unlisted")
        for m in missing:
            print(f"           - {m}")

    print()
    print("  This checks PRESENCE, never accuracy: a stale sentence beside a present filename")
    print("  is a real defect and only a reader can see it. A36 is closed by this file; the")
    print("  half it cannot reach stays open.")

    if total_missing and args.check:
        print(f"\n{total_missing} unlisted. Add them to the index that claims to enumerate them.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
