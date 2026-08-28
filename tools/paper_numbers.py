#!/usr/bin/env python
"""Generate paper/generated/numbers.tex from the analysis manifests.

Stage 8 says every claim needs an executable assertion behind it. Applied to a
manuscript, that means **no number is ever typed into the LaTeX source**. Each one
becomes a macro defined here from `out/*.manifest.json`, so a number cannot drift
between the code that measured it and the paper that reports it.

If a macro is missing, the build fails loudly with an undefined control sequence — which
is the LaTeX equivalent of jidoka: stop the line rather than ship a wrong figure.

Stdlib only.

    python tools/paper_numbers.py          # writes paper/generated/numbers.tex
    python tools/paper_numbers.py --check  # exit 1 if the file is stale
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
DEST = ROOT / "paper" / "generated" / "numbers.tex"

# Numbers measured outside a manifest (the obesity screen predates the manifest format).
# Each entry: macro suffix -> (value, provenance). Provenance is emitted as a comment so
# the .tex file itself says where every number came from.
LITERAL: dict[str, tuple[str, str]] = {
    "ObesityTrainingMax": ("2.0047", "obesity screen, top-3-of-12, the celebrated training maximum"),
    "ObesityNullMeanAtOne": ("0.845", "obesity screen, null mean of the same statistic at n=1"),
    "ObesityNullPNNAtOne": ("2.434", "obesity screen, null p99 at n=1"),
    "ObesityConfoundRaw": ("-0.57", "obesity screen, corr(score, observation count), raw"),
    "ObesityConfoundCal": ("0.07", "obesity screen, same correlation after calibration"),
    "ObesityRankBefore": ("12", "rank of the key entity before calibration"),
    "ObesityRankAfter": ("1", "rank of the key entity after calibration"),
}


def _tex_name(prefix: str, key: str) -> str:
    """A LaTeX macro name: letters only, so \\DepMapGenesScored not \\depmap_genes."""
    parts = [p for p in key.replace("-", "_").split("_") if p]
    return prefix + "".join(p.capitalize() for p in parts)


def _fmt(value: object) -> str:
    """Emit through siunitx so formatting is one decision, made in the preamble."""
    if isinstance(value, bool):
        return r"\text{%s}" % value
    if isinstance(value, (int, float)):
        return r"\num{%s}" % repr(value)
    return str(value)


def build() -> str:
    lines = [
        "% GENERATED FILE - DO NOT EDIT.",
        "% Written by tools/paper_numbers.py from out/*.manifest.json.",
        "% Every number in the manuscript is a macro defined here, so it cannot drift",
        "% from the code that measured it. Edit the analysis, re-run, never edit this.",
        "",
    ]

    manifests = sorted(OUT.glob("*.manifest.json"))
    if not manifests:
        lines.append("% (no manifests found in out/ - run `python tasks.py depmap` first)")

    for path in manifests:
        data = json.loads(path.read_text(encoding="utf-8"))
        ident = data.get("id", path.stem)
        prefix = "".join(p.capitalize() for p in ident.replace("-", "_").split("_"))
        lines.append("%% ---- %s (%s) ----" % (ident, path.name))
        for key, value in (data.get("headline") or {}).items():
            lines.append(r"\newcommand{\%s}{%s}" % (_tex_name(prefix, key), _fmt(value)))
        lines.append("")

    lines.append("% ---- measured outside the manifest format ----")
    for name, (value, why) in LITERAL.items():
        lines.append(r"\newcommand{\%s}{\num{%s}}  %% %s" % (name, value, why))
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    text = build()
    check = "--check" in sys.argv
    if check:
        current = DEST.read_text(encoding="utf-8") if DEST.exists() else ""
        if current != text:
            print("STALE: %s does not match the manifests. Run tools/paper_numbers.py." % DEST)
            return 1
        print("numbers.tex is current")
        return 0
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(text, encoding="utf-8")
    n = text.count(r"\newcommand")
    print("wrote %s (%d macros)" % (DEST.relative_to(ROOT), n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
