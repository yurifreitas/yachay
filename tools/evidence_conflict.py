#!/usr/bin/env python
"""Is a scientific conflict a contradiction, or two statements about different things?

WHY THIS FILE. `docs/references/theory-atlas.md` records sheaf theory as the most attractive
formalism proposed for this atlas: assign evidence to contexts, and let a genuine global
contradiction show up as a cohomological obstruction rather than as two rows that disagree.
`docs/references/deep/multiscale-formalism.md` 4 then refuses to build it, for a specific
reason:

    If nearly every apparent conflict dissolves once context is conditioned on, the sheaf is
    describing a real structure and is worth building. If nearly none does, the conflicts are
    genuinely global and cohomology is an expensive way to say what a contingency table
    already said. That number does not exist yet. Building the machinery before it exists
    would be deciding the answer by choosing the tool.

This file produces that number, as far as public data allows.

## The corpus, and why it is the right one

ClinVar is the largest curated body of *explicitly recorded disagreement* in human genetics:
4,488,337 variants on GRCh38, of which **165,843 carry the aggregate classification
"Conflicting classifications of pathogenicity"**. The disagreement is not inferred by us; the
archive states it.

Each variant also carries the **conditions** it was submitted against (`PhenotypeList`). So the
sheaf question has a direct empirical form:

    Does the chance of a variant carrying conflicting classifications rise with the number of
    DIFFERENT CONDITIONS it has been submitted against?

If it does, a large share of what the field records as contradiction is *context*: the same
variant judged against different diseases, by people asking different questions. If it does
not, the conflicts live inside single contexts and are contradictions in the ordinary sense.

## The confound, measured rather than disclaimed

A variant with more submitters has more chances to be listed against another condition AND more
chances for somebody to disagree. Number of submitters therefore drives both sides and could
manufacture the whole effect. This is Stage 3 of the library's own method, so the answer is not
a disclaimer: the rate is reported **inside submitter strata**, where the confound is held
fixed, and the marginal is shown beside it so the two can be compared.

## What this cannot show, and the file that would settle it

`variant_summary.txt.gz` aggregates a variant's classifications across all of its conditions
into one string. It therefore cannot say whether a given conflict is *within* one condition or
*across* two, only whether conflict is associated with carrying more conditions. The file that
would settle it is ClinVar's **`submission_summary.txt.gz`**, which holds each submitter's
classification with the condition it was made against; it is not ingested here. Naming it is
how this row moves from evidence to proof.

    python tools/evidence_conflict.py

Stdlib only.
"""

from __future__ import annotations

import argparse
import collections
import csv
import gzip
import json
import math
import pathlib
import sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "rare" / "evidence_conflict.json"

#: The aggregate string ClinVar uses for a variant its submitters disagree about.
CONFLICT_LABEL = "Conflicting classifications of pathogenicity"

#: Placeholders that are not conditions. A variant submitted only against these has been
#: submitted against no stated context at all, which is its own stratum and not a zero.
NOT_A_CONDITION = {"not provided", "not specified", "see cases", "none provided", "-", ""}

#: One assembly only. The archive lists most variants twice, once per genome build, and
#: counting both would double every denominator without adding an observation.
ASSEMBLY = "GRCh38"

#: A cell smaller than this is not reported. Registered in manifests/thresholds.yaml.
MIN_CELL = 200


def wilson(k: int, n: int) -> tuple[float, float]:
    """Wilson score interval. Normal approximation fails at the rates in the sparse cells."""
    if n == 0:
        return (float("nan"), float("nan"))
    z = 1.96
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def submitter_stratum(n: int) -> str:
    if n == 2:
        return "2"
    if n == 3:
        return "3"
    if n <= 5:
        return "4-5"
    if n <= 9:
        return "6-9"
    return "10+"


def condition_bin(n: int) -> str:
    return "0" if n == 0 else str(n) if n < 4 else "4+"


STRATA = ["2", "3", "4-5", "6-9", "10+"]
BINS = ["0", "1", "2", "3", "4+"]


def read() -> list[tuple[int, int, bool]]:
    """(conditions, submitters, conflicting) per variant, deduplicated."""
    seen: set[str] = set()
    out: list[tuple[int, int, bool]] = []
    with gzip.open(BY_KEY["clinvar"].dest, "rt", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row.get("Assembly") != ASSEMBLY:
                continue
            vid = row.get("VariationID") or ""
            if not vid or vid in seen:
                continue
            seen.add(vid)
            conditions = {c.strip() for c in (row.get("PhenotypeList") or "").split("|")
                          if c.strip().lower() not in NOT_A_CONDITION}
            try:
                submitters = int(row.get("NumberSubmitters") or 0)
            except ValueError:
                continue
            out.append((len(conditions), submitters,
                        (row.get("ClinicalSignificance") or "") == CONFLICT_LABEL))
    return out


def main() -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    print("reading ClinVar ...")
    data = read()
    conflicting = sum(1 for *_, c in data if c)
    print(f"  {len(data)} variants on {ASSEMBLY}, {conflicting} carrying \"{CONFLICT_LABEL}\"")

    # Conflict is only POSSIBLE above one submitter, so a variant with one is not evidence
    # of agreement and is excluded rather than counted as a non-conflict.
    multi = [(nc, ns, c) for nc, ns, c in data if ns >= 2]

    cells: dict[tuple[str, str], list[int]] = collections.defaultdict(lambda: [0, 0])
    marginal: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    for nc, ns, c in multi:
        cell = cells[(submitter_stratum(ns), condition_bin(nc))]
        cell[0] += c
        cell[1] += 1
        m = marginal[condition_bin(nc)]
        m[0] += c
        m[1] += 1

    def rate(k, n):
        lo, hi = wilson(k, n)
        return {"conflict_rate": round(k / n, 4), "ci95": [round(lo, 4), round(hi, 4)],
                "n": n}

    marginal_rows = {b: rate(*marginal[b]) for b in BINS if marginal[b][1] >= MIN_CELL}

    # The test that matters: does the effect survive inside a stratum, where the submitter
    # confound is held fixed? A risk ratio per stratum, 4+ conditions against exactly 1.
    stratified = {}
    for s in STRATA:
        row = {}
        for b in BINS:
            k, n = cells[(s, b)]
            if n >= MIN_CELL:
                row[b] = rate(k, n)
        if "1" in row and "4+" in row and row["1"]["conflict_rate"] > 0:
            row["risk_ratio_4plus_vs_1"] = round(
                row["4+"]["conflict_rate"] / row["1"]["conflict_rate"], 2)
        stratified[s] = row

    ratios = [r["risk_ratio_4plus_vs_1"] for r in stratified.values()
              if "risk_ratio_4plus_vs_1" in r]
    marg_rr = (round(marginal_rows["4+"]["conflict_rate"] / marginal_rows["1"]["conflict_rate"], 2)
               if "1" in marginal_rows and "4+" in marginal_rows else None)

    survives = bool(ratios) and min(ratios) > 1.0

    payload = {
        "generated": date.today().isoformat(),
        "provenance": f"measured from ClinVar variant_summary.txt.gz, {ASSEMBLY} rows only",
        "question": ("Does a variant's chance of carrying conflicting classifications rise "
                     "with the number of different CONDITIONS it was submitted against? If "
                     "it does, much of what the field records as contradiction is context."),
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md",
        "totals": {"variants": len(data), "conflicting": conflicting,
                   "with_two_or_more_submitters": len(multi)},
        "marginal": marginal_rows,
        "by_submitter_stratum": stratified,
        "marginal_risk_ratio_4plus_vs_1": marg_rr,
        "stratified_risk_ratios": ratios,
        "confound_survives": survives,
        "reading": ("The submitter count drives both sides and is held fixed inside each "
                    "stratum. If the risk ratio stays above 1 in every stratum, the "
                    "association is not manufactured by review depth."),
        "says": ("Association, not decomposition. variant_summary aggregates a variant's "
                 "classifications across ALL its conditions into one string, so this cannot "
                 "say whether a given conflict sits within one condition or across two. It "
                 "can say whether conflict travels with carrying more conditions."),
        "would_settle_it": ("ClinVar submission_summary.txt.gz, which holds each submitter's "
                            "classification beside the condition it was made against. Not "
                            "ingested here."),
        "limits": [
            "ClinVar's aggregate label is itself a curation product; a variant can be in "
            "conflict without being labelled so, and the label's rules have changed over time.",
            "Conditions are counted as distinct strings after dropping placeholders, so two "
            "names for one disease count twice and inflate the condition count.",
            f"Cells below {MIN_CELL} variants are not reported.",
        ],
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print("conflict rate by number of conditions, inside submitter strata")
    print(f"  {'submitters':>10} " + "".join(f"{b:>14}" for b in BINS) + "    RR 4+/1")
    for s in STRATA:
        row = stratified[s]
        line = f"  {s:>10} "
        for b in BINS:
            line += f"{100*row[b]['conflict_rate']:12.1f}%  " if b in row else f"{'-':>14}"
        rr = row.get("risk_ratio_4plus_vs_1")
        line += f"    {rr:.2f}" if rr else ""
        print(line)
    line = f"  {'MARGINAL':>10} "
    for b in BINS:
        line += (f"{100*marginal_rows[b]['conflict_rate']:12.1f}%  "
                 if b in marginal_rows else f"{'-':>14}")
    print(line + (f"    {marg_rr:.2f}" if marg_rr else ""))
    print()
    print(f"  the association survives every stratum: {survives} "
          f"(lowest stratified risk ratio {min(ratios):.2f}, marginal {marg_rr:.2f})")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
