#!/usr/bin/env python
"""Is a recorded conflict a contradiction about one thing, or two claims about two things?

WHAT THIS SETTLES. `tools/evidence_conflict.py` measured an association: a variant's chance of
carrying conflicting classifications rises 2.14x with the number of conditions it was submitted
against, and the rise survives every submitter stratum. It could not go further, because
`variant_summary.txt.gz` collapses a variant's classifications across all of its conditions
into one string. Its own artefact named the file that would settle it:

    ClinVar submission_summary.txt.gz, which holds each submitter's classification beside the
    condition it was made against. Not ingested here.

It is ingested now, and this file does the decomposition the other one could only point at. For
every variant whose submitters disagree, the question is answerable exactly:

  * **within-condition conflict** - two submitters disagree about the SAME condition. A
    contradiction in the ordinary sense. Somebody is wrong.
  * **across-condition conflict only** - every individual condition is internally consistent,
    and the disagreement appears only when the conditions are pooled. Nobody need be wrong;
    the archive is answering two questions in one column.

The second class is the entire empirical case for a context-aware representation of evidence
(`docs/references/deep/multiscale-formalism.md` 4). If it is small, a sheaf is machinery in
search of a problem. If it is large, then a knowledge graph that stores `A -> refutes -> B`
without its context is destroying the thing that resolves the conflict.

## The classification rule, stated rather than inherited

ClinVar's own aggregate label has changed its rules over time, so it is not used to define
disagreement here. Submissions are collapsed to three ordered bins:

    pathogenic  {Pathogenic, Likely pathogenic}
    uncertain   {Uncertain significance}
    benign      {Benign, Likely benign}

Everything else - drug response, risk factor, association, protective, not provided, and the
somatic-only vocabularies - is **excluded**, because those are not answers to the same question
and calling their coexistence a conflict would be the very error this file exists to measure.
A variant is in conflict when its submissions span two or more bins. The overlap with ClinVar's
own label is reported as an anchor, not as a target.

**A conservative choice, deliberately.** P-vs-LP and B-vs-LB disagreements are NOT counted as
conflict. That understates the total and it protects the finding: the split being measured is
between classes that would change a clinical decision.

    python tools/conflict_decomposition.py

Stdlib only. Reads a 387 MB gzip in two passes; about two minutes.
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

DEST = ROOT / "out" / "rare" / "conflict_decomposition.json"

BIN_OF = {
    "pathogenic": "pathogenic", "likely pathogenic": "pathogenic",
    "uncertain significance": "uncertain",
    "benign": "benign", "likely benign": "benign",
}

#: Conditions that name no condition. A submission carrying only one of these has no context,
#: so it cannot be evidence either way about whether context explains a conflict.
NOT_A_CONDITION = {"not provided", "not specified", "see cases", "none provided", "-", "",
                   "not applicable", "unknown"}

#: A variant needs at least this many classifiable submissions to be able to conflict at all.
MIN_SUBMISSIONS = 2

#: A condition carrying at least this many submissions is treated as an UMBRELLA indication
#: rather than a disease - "Inborn genetic diseases", "Hereditary cancer-predisposing
#: syndrome", "Cardiovascular phenotype" are panel orders, not answers to "which disease".
#: Registered in manifests/thresholds.yaml as UMBRELLA_SUBMISSIONS, and honestly marked
#: EMPIRICAL: the distribution was inspected first, and 50,000 is the gap in it - the three
#: terms above sit at 362k, 257k and 95k, and the next condition down is at 36k.
UMBRELLA_SUBMISSIONS = 50000


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def condition_key(reported: str) -> str | None:
    """`C3150901:Hereditary spastic paraplegia 48` -> the MedGen id, which is the stable half.

    The label is free text and the same disease reaches ClinVar under several spellings; the
    identifier does not drift. Where there is no identifier the trimmed label is used, and
    where there is no condition at all the submission is dropped.
    """
    value = (reported or "").strip()
    if not value or value.lower() in NOT_A_CONDITION:
        return None
    head = value.split(":", 1)
    ident = head[0].strip()
    label = head[1].strip() if len(head) > 1 else ""

    # THE LABEL IS CHECKED FIRST, AND THIS IS THE WHOLE CORRECTNESS OF THE FILE. ClinVar
    # issues identifiers to its placeholders - "CN169374:not provided" is a real row - so a
    # rule that trusts the identifier admits "not provided" and "not specified" as CONDITIONS.
    # The first version of this file did exactly that, reported only 174 submissions without a
    # condition, and counted 3.2 million placeholder rows as context. A variant classified
    # Pathogenic for a disease and Uncertain for "not provided" then read as two claims about
    # two different things, which is the precise error the measurement exists to detect.
    if label.lower() in NOT_A_CONDITION:
        return None
    if ident and ident.lower() not in NOT_A_CONDITION and not ident.lower().startswith("na"):
        return ident
    return label.lower() or None


def read_submissions():
    """variant -> {condition: set(bins)}, keeping only what could possibly conflict."""
    per_variant: dict[str, dict[str, set[str]]] = collections.defaultdict(
        lambda: collections.defaultdict(set))
    counts = collections.Counter()
    condition_size: collections.Counter = collections.Counter()
    condition_label: dict[str, str] = {}
    per_condition_n: collections.Counter = collections.Counter()
    with gzip.open(BY_KEY["clinvar_submissions"].dest, "rt",
                   encoding="utf-8", errors="replace") as fh:
        header = None
        for line in fh:
            if line.startswith("#"):
                if line.startswith("#VariationID\t"):
                    header = line[1:].rstrip("\n").split("\t")
                continue
            if header is None:
                continue
            row = dict(zip(header, line.rstrip("\n").split("\t")))
            counts["rows"] += 1
            bucket = BIN_OF.get((row.get("ClinicalSignificance") or "").strip().lower())
            if bucket is None:
                counts["unclassifiable"] += 1
                continue
            reported = row.get("ReportedPhenotypeInfo", "")
            label = reported.split(":", 1)[1].strip() if ":" in reported else reported.strip()
            condition = condition_key(reported)
            if condition is None:
                counts["no_condition"] += 1
                continue
            vid = row.get("VariationID") or ""
            if not vid:
                continue
            counts["usable"] += 1
            per_variant[vid][condition].add(bucket)
            per_condition_n[(vid, condition)] += 1
            condition_size[condition] += 1
            condition_label.setdefault(condition, label)
    return per_variant, counts, condition_size, condition_label, per_condition_n


def redundancy_curve(per_variant, per_condition_n):
    """Does adding submitters resolve a disagreement, or manufacture one?

    Von Neumann's 1956 problem - build a reliable organism from unreliable components - has one
    canonical answer, multiplexing: replicate the unreliable element and take a majority, and
    the error rate falls. ClinVar is that construction running in public. Each submitter is an
    unreliable component; the archive aggregates them; a clinician consumes the aggregate.

    So the construction can be checked. Hold the CONTEXT fixed - one variant, one condition -
    and ask how the probability of internal disagreement moves as submitters are added. If
    multiplexing describes what the archive does, the rate should fall with redundancy. If it
    rises, then adding submitters is adding variety faster than it adds agreement, and the
    aggregate is not a consensus device but a disagreement detector.

    The unit here is the (variant, condition) pair, not the variant: pooling conditions is the
    very thing the rest of this file exists to separate out.
    """
    buckets: dict[int, list[int]] = {}
    for vid, by_condition in per_variant.items():
        for condition, bins in by_condition.items():
            n = per_condition_n[(vid, condition)]
            if n < 2:
                continue
            key = n if n < 6 else 6 if n < 11 else 11
            k, total = buckets.get(key, (0, 0)) if key in buckets else (0, 0)
            buckets[key] = (k + (1 if len(bins) >= 2 else 0), total + 1)
    rows = []
    for key in sorted(buckets):
        k, n = buckets[key]
        lo, hi = wilson(k, n)
        rows.append({"submitters": {6: "6-10", 11: "11+"}.get(key, str(key)),
                     "pairs": n, "split": k, "split_rate": round(k / n, 4),
                     "ci95": [round(lo, 4), round(hi, 4)]})
    return {
        "asks": ("With the condition held fixed, does the chance of internal disagreement "
                 "fall as submitters are added? Von Neumann 1956: reliable organisms from "
                 "unreliable components, by multiplexing."),
        "unit": "(variant, condition) pair with at least two classifiable submissions",
        "rows": rows,
        "says": ("If the rate rises with redundancy, the archive's aggregation is not acting "
                 "as a consensus device on this axis. That is not a criticism of ClinVar - it "
                 "is what an archive that records rather than adjudicates should look like - "
                 "but it decides what an aggregate classification can be used for."),
    }


def main() -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    print("reading submissions ...")
    per_variant, counts, condition_size, condition_label, per_condition_n = read_submissions()
    print(f"  {counts['rows']} submission rows; {counts['usable']} usable "
          f"({counts['unclassifiable']} not a germline classification, "
          f"{counts['no_condition']} with no stated condition)")

    def split(drop_umbrella: bool):
        """The decomposition. Run twice: as recorded, and with umbrella indications removed."""
        within = across = agree = 0
        single = 0
        widths: collections.Counter = collections.Counter()
        found: list[dict] = []
        for vid, by_condition in per_variant.items():
            if drop_umbrella:
                by_condition = {c: b for c, b in by_condition.items()
                                if condition_size[c] < UMBRELLA_SUBMISSIONS}
                if not by_condition:
                    continue
            all_bins: set[str] = set()
            for bins in by_condition.values():
                all_bins |= bins
            n_sub = sum(len(b) for b in by_condition.values())
            if n_sub < MIN_SUBMISSIONS or len(all_bins) < 2:
                if all_bins and n_sub >= MIN_SUBMISSIONS:
                    agree += 1
                continue
            if any(len(b) >= 2 for b in by_condition.values()):
                within += 1
                if len(by_condition) == 1:
                    single += 1
            else:
                across += 1
                widths[min(len(by_condition), 5)] += 1
                if len(found) < 8 and len(by_condition) == 2:
                    found.append({"variation_id": vid,
                                  "conditions": {condition_label.get(c, c): sorted(b)
                                                 for c, b in by_condition.items()}})
        n = within + across
        lo_, hi_ = wilson(across, n)
        return {"variants_in_agreement": agree, "variants_in_conflict": n,
                "within_condition": within, "across_condition_only": across,
                "within_and_single_condition": single,
                "across_condition_share": round(across / n, 4) if n else None,
                "ci95": [round(lo_, 4), round(hi_, 4)],
                "conditions_when_across_only": {str(k): v for k, v in sorted(widths.items())},
                "examples": found}

    print("measuring the redundancy curve ...")
    redundancy = redundancy_curve(per_variant, per_condition_n)

    as_recorded = split(False)
    specific_only = split(True)

    umbrellas = sorted(((n, condition_label.get(c, c)) for c, n in condition_size.items()
                        if n >= UMBRELLA_SUBMISSIONS), reverse=True)

    within = as_recorded["within_condition"]
    across = as_recorded["across_condition_only"]
    agree = as_recorded["variants_in_agreement"]
    single_condition_conflicts = as_recorded["within_and_single_condition"]
    conflicts = as_recorded["variants_in_conflict"]
    conditions_when_across = as_recorded["conditions_when_across_only"]
    examples = as_recorded["examples"]
    lo, hi = as_recorded["ci95"]

    payload = {
        "generated": date.today().isoformat(),
        "provenance": "measured from ClinVar submission_summary.txt.gz, per-submission rows",
        "question": ("Of the variants whose submitters disagree, how many disagree about the "
                     "SAME condition (a contradiction) and how many only disagree once "
                     "different conditions are pooled (context)?"),
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md",
        "rule": {
            "bins": {"pathogenic": ["Pathogenic", "Likely pathogenic"],
                     "uncertain": ["Uncertain significance"],
                     "benign": ["Benign", "Likely benign"]},
            "excluded": ("drug response, risk factor, association, protective, somatic-only "
                         "vocabularies, and anything with no stated condition"),
            "conservative": ("P-vs-LP and B-vs-LB are NOT conflicts here, so the totals "
                             "understate disagreement and the split is between classes that "
                             "would change a decision"),
            "condition_identity": "MedGen identifier where present, else the trimmed label",
        },
        "counts": {
            "submission_rows": counts["rows"],
            "usable_submissions": counts["usable"],
            "variants_with_two_or_more": agree + conflicts,
            "variants_in_agreement": agree,
            "variants_in_conflict": conflicts,
            "within_condition": within,
            "across_condition_only": across,
            "within_and_single_condition": single_condition_conflicts,
        },
        "headline": {
            "across_condition_share": round(across / conflicts, 4) if conflicts else None,
            "ci95": [lo, hi],
            "within_condition_share": round(within / conflicts, 4) if conflicts else None,
        },
        "conditions_when_across_only": conditions_when_across,
        "examples_across_condition": examples,
        "redundancy_within_condition": redundancy,
        "sensitivity_umbrella_removed": {
            "asks": ("Is the across-condition share an artefact of granularity? A variant "
                     "called Pathogenic for a disease and Uncertain for a panel indication "
                     "like \"Inborn genetic diseases\" is arguably one question asked at two "
                     "resolutions, not two questions."),
            "rule": f"conditions with >= {UMBRELLA_SUBMISSIONS} submissions are dropped",
            "dropped": [{"submissions": n, "condition": lab} for n, lab in umbrellas],
            "result": specific_only,
        },
        "says": ("A decomposition, not an association - this is the number "
                 "tools/evidence_conflict.py could not compute. It answers the precondition "
                 "docs/references/deep/multiscale-formalism.md 4 set for building anything "
                 "sheaf-shaped."),
        "limits": [
            "A submitter who reports against a broad condition and one who reports against a "
            "narrow one are counted as two conditions, so some 'context' is really "
            "granularity. The MedGen identifier reduces this but does not remove it.",
            "Submissions with no stated condition are dropped, not counted as agreement; a "
            "variant can therefore be in conflict in ClinVar and absent here.",
            "Only germline classification. Somatic and oncogenicity columns are ignored.",
        ],
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"  variants with >= {MIN_SUBMISSIONS} classifiable submissions: {agree + conflicts}")
    print(f"    in agreement                : {agree}")
    print(f"    in conflict                 : {conflicts}")
    print(f"      within a condition        : {within:8d}  "
          f"({100*within/conflicts:.1f}%)  <- a contradiction")
    print(f"      across conditions only    : {across:8d}  "
          f"({100*across/conflicts:.1f}%)  <- context, 95% CI "
          f"[{100*lo:.1f}%, {100*hi:.1f}%]")
    print(f"\n  of the within-condition conflicts, {single_condition_conflicts} "
          f"({100*single_condition_conflicts/max(within,1):.1f}%) involve one condition only")
    so = specific_only
    print()
    print(f"  sensitivity - {len(umbrellas)} umbrella indications dropped "
          f"({', '.join(lab for _, lab in umbrellas)}):")
    print(f"    conflicts {so['variants_in_conflict']}, across-condition only "
          f"{100*so['across_condition_share']:.1f}% "
          f"[{100*so['ci95'][0]:.1f}%, {100*so['ci95'][1]:.1f}%]")
    print()
    print("  redundancy within a fixed condition (von Neumann 1956)")
    print(f"    {'submitters':>10} {'pairs':>9} {'internally split':>18}")
    for row in redundancy["rows"]:
        print(f"    {row['submitters']:>10} {row['pairs']:9d} "
              f"{100*row['split_rate']:15.1f}%   "
              f"[{100*row['ci95'][0]:.1f}, {100*row['ci95'][1]:.1f}]")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
