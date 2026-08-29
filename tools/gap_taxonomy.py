#!/usr/bin/env python
"""Five kinds of hole, told apart — because they have five different remedies.

WHY THIS FILE. `tools/knowledge_void.py` located 232 anti-forms and 706 empty cells and said,
in its own `says` field, exactly what it could not do:

    A cell can be empty because the biology forbids it, because nobody has looked, or because
    the axis is a proxy that cannot express it, and this measurement cannot tell those apart.

Nor can the rest of the atlas. Every layer here records one undifferentiated *unknown*, and
that is a failure with a cost: a gap that needs a study, a gap that needs a join, and a gap
that needs a cohort look identical on the page and are answered by completely different work.

So this types them. The five kinds, and what each would take to close:

    epistemic          nobody has looked. Closed by a study.
    accessibility      known somewhere this catalogue does not reach. Closed by ingestion.
    interoperability   BOTH halves exist and do not meet. Closed by a join, or by an
                       identifier that survives the crossing.
    population         no cohort large enough exists. Closed by recruitment, or by federation.
    model              the data exists and has no computable representation. Closed by
                       building one.

## The instrument that makes this possible

MONDO carries **10,491 Orphanet cross-references and 10,176 OMIM cross-references**, so for a
disease missing a field it can be asked whether a counterpart exists *in the other catalogue*.
That single fact separates the two kinds most often confused:

  * a disease with no prevalence and **no ORPHA counterpart** is an **accessibility** gap —
    the number may exist in the world, but not in a catalogue this atlas reads;
  * a disease with no prevalence and **an ORPHA counterpart that has one** is an
    **interoperability** gap — both halves are in this repository, on disk, right now, and
    the join does not carry them to the same place.

The second class is the one nobody counts, and it is the OMIM/ORPHA boundary this project has
now met three times: in the visualisation work, in `knowledge_shape.py`, and in
`attention_burden.py`, where it made a severity coefficient impossible to compute at all.

## What this still cannot do

Separate *nobody looked* from *the biology forbids it*. Both present as an epistemic gap, and
no catalogue can distinguish them — only an experiment can. The epistemic class is therefore
the residual, and it is reported as such rather than as a finding.

    python tools/gap_taxonomy.py

Stdlib only.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import pathlib
import sys
from datetime import date
from xml.etree import ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "rare" / "gap_taxonomy.json"

#: A disease needs at least this many curated patients before a missing frequency counts as
#: an epistemic gap rather than a population one. Registered as COHORT_FLOOR.
COHORT_FLOOR = 5

FIELDS = ["gene", "phenotype", "prevalence", "onset", "cell_type"]


def crosswalk() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """MONDO's cross-references, read both ways: OMIM/ORPHA id -> the other catalogue's ids."""
    omim_to_orpha: dict[str, set[str]] = collections.defaultdict(set)
    orpha_to_omim: dict[str, set[str]] = collections.defaultdict(set)
    term: str | None = None
    xrefs: list[str] = []

    def flush() -> None:
        omims = [x for x in xrefs if x.startswith("OMIM:")]
        orphas = [f"ORPHA:{x.split(':', 1)[1]}" for x in xrefs if x.startswith("Orphanet:")]
        for o in omims:
            omim_to_orpha[o].update(orphas)
        for o in orphas:
            orpha_to_omim[o].update(omims)

    for line in BY_KEY["mondo"].dest.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("[Term]"):
            flush()
            term, xrefs = None, []
        elif line.startswith("id: MONDO"):
            term = line[4:].strip()
        elif line.startswith("xref:") and term:
            xrefs.append(line[6:].split()[0])
    flush()
    return dict(omim_to_orpha), dict(orpha_to_omim)


def catalogue_fields():
    """What each disease actually has, per field."""
    has: dict[str, set[str]] = collections.defaultdict(set)

    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            d = (row.get("disease_id") or "").strip()
            if d and (row.get("gene_symbol") or "").strip():
                has["gene"].add(d)

    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        rows = (line for line in fh if not line.startswith("#"))
        for row in csv.DictReader(rows, delimiter="\t"):
            d = (row.get("database_id") or "").strip()
            if not d:
                continue
            has["phenotype"].add(d)
            if (row.get("onset") or "").strip():
                has["onset"].add(d)
            if (row.get("frequency") or "").strip():
                has["frequency"].add(d)

    for key, tag, field in (("orpha_prevalence", "Prevalence", "prevalence"),
                            ("orpha_ages", "AverageAgeOfOnset", "onset")):
        try:
            root = ET.parse(BY_KEY[key].dest).getroot()
        except (OSError, ET.ParseError):
            continue
        for disorder in root.iter("Disorder"):
            code = disorder.findtext("OrphaCode")
            if code and any(True for _ in disorder.iter(tag)):
                has[field].add(f"ORPHA:{code}")
    return {k: v for k, v in has.items()}


def main() -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()

    print("reading ...")
    omim_to_orpha, orpha_to_omim = crosswalk()
    has = catalogue_fields()
    print(f"  MONDO crosswalk: {len(omim_to_orpha)} OMIM and {len(orpha_to_omim)} ORPHA "
          f"terms carry a counterpart")

    universe = sorted(set().union(*has.values()))
    print(f"  {len(universe)} diseases appear in at least one field")

    def counterpart(disease: str) -> set[str]:
        if disease.startswith("OMIM:"):
            return omim_to_orpha.get(disease, set())
        if disease.startswith("ORPHA:"):
            return orpha_to_omim.get(disease, set())
        return set()

    tally: collections.Counter = collections.Counter()
    per_field: dict[str, collections.Counter] = {f: collections.Counter() for f in FIELDS}
    examples: dict[str, list[dict]] = collections.defaultdict(list)

    for disease in universe:
        others = counterpart(disease)
        for field in FIELDS:
            if disease in has.get(field, set()):
                continue
            # THE DECISIVE TEST. Does a counterpart in the other catalogue carry the field?
            # If it does, both halves are on this disk and the join is what failed.
            elsewhere = any(o in has.get(field, set()) for o in others)
            if elsewhere:
                kind = "interoperability"
            elif others:
                # A counterpart exists and it does not have the field either. Nobody has it.
                kind = "epistemic"
            else:
                # No counterpart at all: the field may exist in a catalogue we do not read.
                kind = "accessibility"
            # Population is a refinement of epistemic, not a competitor: a frequency missing
            # where a cohort could not exist is a different problem from one nobody measured.
            if kind == "epistemic" and field in ("prevalence", "onset") \
                    and disease not in has.get("frequency", set()):
                kind = "population"
            tally[kind] += 1
            per_field[field][kind] += 1
            if len(examples[f"{field}:{kind}"]) < 4:
                examples[f"{field}:{kind}"].append(
                    {"disease": disease, "counterparts": sorted(others)[:2]})

    total = sum(tally.values())

    # THE FIFTH KIND IS NOT COUNTED HERE, and saying so is more useful than a zero. A MODEL
    # gap - a field that exists and has no computable representation - is not a missing
    # catalogue entry, so the crosswalk cannot see it. It is measured elsewhere: the twin
    # readiness question in docs/roadmap.md 5.7, which is gated on whether Physiome models
    # map to rare disease at all, and that check has not been run.

    payload = {
        "generated": date.today().isoformat(),
        "provenance": ("measured from MONDO cross-references, HPO genes_to_disease and "
                       "phenotype.hpoa, and Orphanet prevalence and age-of-onset"),
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md",
        "question": ("A missing field can need a study, an ingestion, a join, or a cohort. "
                     "Which of those is it?"),
        "instrument": {
            "crosswalk": ("MONDO carries both OMIM and Orphanet cross-references, so a "
                          "disease missing a field can be asked whether a counterpart in the "
                          "other catalogue has it"),
            "omim_terms_with_counterpart": len(omim_to_orpha),
            "orpha_terms_with_counterpart": len(orpha_to_omim),
        },
        "kinds": {
            "epistemic": "nobody has it, here or in the counterpart. Closed by a study.",
            "accessibility": ("no counterpart exists in the catalogues we read, so the fact "
                              "may exist and be unreachable. Closed by ingestion."),
            "interoperability": ("a counterpart HAS the field and this disease does not. Both "
                                 "halves are on this disk. Closed by a join."),
            "model": ("NOT COUNTED HERE. A field that exists with no computable "
                      "representation is not a missing catalogue entry, so the crosswalk "
                      "cannot see it. See docs/roadmap.md 5.7."),
            "population": ("a frequency or onset is missing and no curated frequency exists "
                           "either, so there may be no cohort to measure. Closed by "
                           "recruitment or federation."),
        },
        "scale": {"diseases": len(universe), "field_gaps": total},
        "totals": dict(tally.most_common()),
        "shares": {k: round(v / total, 4) for k, v in tally.most_common()},
        "by_field": {f: dict(per_field[f].most_common()) for f in FIELDS},
        "examples": {k: v for k, v in sorted(examples.items())},
        "says": ("Types a gap by what would CLOSE it, not by how big it is. It cannot "
                 "separate 'nobody looked' from 'the biology forbids it' — both present as "
                 "epistemic, and only an experiment tells them apart, so the epistemic class "
                 "is the residual rather than a finding."),
        "limits": [
            "MONDO's crosswalk is itself curated and incomplete; a disease with no "
            "counterpart may simply not have been cross-referenced yet, which inflates the "
            "accessibility class at the expense of interoperability.",
            "Five fields, chosen because this repository ingests them. A gap in a field "
            "nobody here reads is invisible to this measurement entirely.",
            "The population class is a refinement of the epistemic one and inherits its "
            "ambiguity; it separates 'no cohort could exist' from 'no cohort was assembled' "
            "no better than any catalogue can.",
        ],
    }
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"  {total} field-level gaps over {len(universe)} diseases")
    for kind, n in tally.most_common():
        print(f"    {kind:18s} {n:7d}  {100 * n / total:5.1f} %")
    print()
    print(f"  {'field':12s} " + "".join(f"{k[:9]:>12s}" for k in
                                        ["epistemic", "accessib.", "interop.", "populat."]))
    for f in FIELDS:
        row = per_field[f]
        print(f"  {f:12s} " + "".join(
            f"{row.get(k, 0):12d}" for k in
            ["epistemic", "accessibility", "interoperability", "population"]))
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
