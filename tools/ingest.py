#!/usr/bin/env python
"""Download the public catalogues. Stdlib only, resumable, honest about licences.

    python tools/ingest.py            # fetch anything missing
    python tools/ingest.py --list     # what would be fetched, and why
    python tools/ingest.py --force    # re-fetch everything

Not part of the build graph, for the same reason `fetch` is not: a missing catalogue
should stop a build with a message, never trigger a silent 100 MB download in the middle
of an analysis.
"""

from __future__ import annotations

import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import ONTOLOGY, SOURCES, TOTAL_MB  # noqa: E402

UA = {"User-Agent": "sieve-pipeline/0.1 (research; contact via repository)"}


def human(n: float) -> str:
    return f"{n/1e6:.1f} MB" if n >= 1e6 else f"{n/1e3:.0f} KB"


def listing() -> None:
    print(f"{len(SOURCES)} sources, ~{TOTAL_MB:.0f} MB total\n")
    for s in SOURCES:
        have = s.dest.exists() and s.dest.stat().st_size > 0
        mark = "have" if have else "----"
        size = human(s.dest.stat().st_size) if have else f"~{s.approx_mb:.0f} MB"
        print(f"  [{mark}] {s.name:<38} {size:>10}")
        print(f"         {s.gives}")
        print(f"         licence: {s.licence}"
              f"{'' if s.redistributable else '  (NOT redistributable)'}")
        print()


def fetch(force: bool = False) -> int:
    ONTOLOGY.mkdir(parents=True, exist_ok=True)
    # A note beside the data, so nobody has to go looking for the terms later.
    (ONTOLOGY / "SOURCES.md").write_text(
        "# Ingested catalogues\n\n"
        "Downloaded by `python tools/ingest.py`. **This directory is gitignored.**\n\n"
        + "\n".join(
            f"- **{s.name}** — {s.gives}\n"
            f"  - `{s.filename}` · {s.url}\n"
            f"  - licence: {s.licence}"
            f"{' — **not redistributable**' if not s.redistributable else ''}\n"
            for s in SOURCES
        ),
        encoding="utf-8",
    )

    failed = 0
    for s in SOURCES:
        if s.dest.exists() and s.dest.stat().st_size > 0 and not force:
            print(f"have {s.name} ({human(s.dest.stat().st_size)})")
            continue
        print(f"fetching {s.name} (~{s.approx_mb:.0f} MB) ...", flush=True)
        tmp = s.dest.with_suffix(s.dest.suffix + ".part")
        try:
            req = urllib.request.Request(s.url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as fh:
                while chunk := r.read(1 << 20):
                    fh.write(chunk)
            # Rename only on success, so an interrupted download never looks complete.
            tmp.replace(s.dest)
            print(f"  {human(s.dest.stat().st_size)}")
        except Exception as e:  # noqa: BLE001 — the message matters more than the type
            tmp.unlink(missing_ok=True)
            print(f"  FAILED: {type(e).__name__}: {e}")
            failed += 1
    return 1 if failed else 0


def main() -> int:
    if "--list" in sys.argv:
        listing()
        return 0
    return fetch(force="--force" in sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
