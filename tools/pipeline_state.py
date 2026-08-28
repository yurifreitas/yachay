#!/usr/bin/env python
"""Publish the pipeline's own state, so freshness stops being a terminal-only fact.

WHY. `describe()` prints which stages are fresh, which are stale, and what changed under them.
That is the single most useful thing anyone can know before reading a number on this site —
and it was visible only to whoever ran the command. A dashboard that renders results while
hiding whether those results are current is asking to be believed on trust.

WHAT IT WRITES. Every stage with its summary, its declared inputs and outputs, its
dependencies, whether it is stale and why, and — for each output — whether the file exists and
when it was last written. The staleness rule is the pipeline's own, including the part that
tracks SOURCE CODE as an input: an analysis whose code changed is stale even if its data did
not, which is how the defective null was caught.

    python tools/pipeline_state.py     # writes out/pipeline.json
"""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline import runner, stages as stage_mod  # noqa: E402


def as_list(x):
    return list(x) if x else []


def rel(p) -> str:
    try:
        return str(pathlib.Path(p).resolve().relative_to(ROOT)).replace("\\", "/")
    except (ValueError, TypeError):
        return str(p)


def stamp(p) -> str | None:
    path = pathlib.Path(p)
    if not path.exists():
        return None
    return _dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def main() -> int:
    table = stage_mod.STAGES if hasattr(stage_mod, "STAGES") else stage_mod.ALL
    # topological() wants explicit targets; every stage is a target here.
    order = runner.topological(table, list(table))
    names = [s if isinstance(s, str) else s.name for s in order]

    rows = []
    for name in names:
        st = table[name] if isinstance(table, dict) else next(x for x in table if x.name == name)
        stale, reason = st.is_stale()
        outputs = [
            {"path": rel(o), "exists": pathlib.Path(o).exists(),
             "written": stamp(o),
             "bytes": pathlib.Path(o).stat().st_size if pathlib.Path(o).exists() else 0}
            for o in as_list(getattr(st, "outputs", ()))
        ]
        rows.append({
            "name": name,
            "summary": getattr(st, "summary", ""),
            "needs": as_list(getattr(st, "needs", ())),
            "inputs": [{"path": rel(i), "exists": pathlib.Path(i).exists()}
                       for i in as_list(getattr(st, "inputs", ()))],
            "outputs": outputs,
            "code": [rel(c) for c in as_list(getattr(st, "code", ()))],
            "stale": bool(stale),
            "reason": reason or "",
            "missingInputs": [rel(i) for i in as_list(getattr(st, "inputs", ()))
                              if not pathlib.Path(i).exists()],
        })

    stale = [r for r in rows if r["stale"]]
    blocked = [r for r in rows if r["missingInputs"]]
    produced = sum(len(r["outputs"]) for r in rows)
    present = sum(1 for r in rows for o in r["outputs"] if o["exists"])

    payload = {
        "generated": "tools/pipeline_state.py",
        "premise": (
            "Which stages are current, and which are not. A dashboard that renders results "
            "while hiding whether they are current is asking to be believed on trust, so the "
            "pipeline's own freshness check is published rather than left in a terminal."
        ),
        "rule": (
            "A stage is stale when an output is missing, when an input is newer than an "
            "output, or when its SOURCE CODE is newer than its outputs. The last clause is the "
            "one that matters: an analysis whose code changed is stale even though its data did "
            "not, and that is how the defective pooled null was caught rather than shipped."
        ),
        "stages": rows,
        "summary": {
            "stages": len(rows),
            "stale": len(stale),
            "fresh": len(rows) - len(stale),
            "blocked": len(blocked),
            "artifacts": produced,
            "artifactsPresent": present,
            "staleNames": [r["name"] for r in stale],
        },
    }

    out = ROOT / "out" / "pipeline.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    s = payload["summary"]
    print("wrote %s" % out.relative_to(ROOT))
    print("  %d stages · %d fresh · %d stale%s"
          % (s["stages"], s["fresh"], s["stale"],
             (" (" + ", ".join(s["staleNames"]) + ")") if s["staleNames"] else ""))
    print("  %d declared artifacts, %d present on disk" % (s["artifacts"], s["artifactsPresent"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
