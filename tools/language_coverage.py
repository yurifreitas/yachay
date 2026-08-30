#!/usr/bin/env python
"""What a reader loses by not reading English.

WHY THIS FILE. The explorer publishes in English and Portuguese, and this repository had no
measurement of what the second language costs a reader. "Available in Portuguese" was doing the
work that a number should do - which is the failure this project refuses everywhere else.

Language belongs beside ancestry and geography, not under presentation. `ancestry_geography.py`
already measures whose populations the prevalences describe (Europe 8.10, Africa 0.07); a reader
who cannot read the page is excluded by a barrier of the same kind, and the literature treats it
that way (Jain et al. 2020, access to trials by non-English speakers).

The data exists because HPO made internationalisation the headline of its 2024 release -
Gargano et al., "phenotypes around the world" - shipping thirteen language profiles besides
English. **That headline is an aggregate**, and an aggregate over subgroups of wildly unequal
size is the object this whole library was built to distrust.

## The two coverages, and why the second one is the real one

**Term coverage** - what fraction of HPO's terms have a label in language L. This is what a
translation project reports about itself, and it treats every term as equally important.

**Annotation-weighted coverage** - what fraction of the *actual disease-phenotype annotations*
in `phenotype.hpoa` land on a term that has a label in L. A clinician reading about a real
disease meets terms in proportion to how often they are annotated, not uniformly. If a
translation covers the vocabulary's long tail but misses the terms diseases are actually
annotated with, term coverage looks fine and the reader still cannot read the page.

**The gap between the two is the finding this tool exists to produce**, in either direction.

**And then per organ system**, because a language can look adequate in aggregate and be
unusable for a whole class of disease. The spread max-min across organ systems is reported per
language: a defect confined to one subgroup is divided by the number of subgroups in any pooled
figure, so a wide spread is the signature of exactly what a headline number hides. This is
Stage 3 of the method - measure the confound rather than disclaim it - pointed at language.

## What this is not

Not a judgement of any translation effort. Several of these profiles are explicitly partial and
their maintainers say so; the number here is a measurement of the *reader's* position, not of
anyone's work. Coverage is counted on OFFICIAL-status `rdfs:label` rows only, so a draft is not
credited as a delivery and a language is not penalised for having drafts.

    python tools/language_coverage.py

Stdlib only.
"""

from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import pathlib
import re
import sys
import tarfile
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "rare" / "language_coverage.json"

#: Only rows a translation project itself marks as delivered are counted. Registered in
#: manifests/thresholds.yaml as TRANSLATION_STATUS.
TRANSLATION_STATUS = "OFFICIAL"

PHENOTYPIC_ABNORMALITY = "HP:0000118"

#: Endonyms where a bare ISO code would be unreadable in a table. Authored, and marked so.
LANGUAGE_NAMES = {
    "ar": "Arabic", "cs": "Czech", "de": "German", "dtp": "Kadazan Dusun", "es": "Spanish",
    "fr": "French", "it": "Italian", "ja": "Japanese", "nl": "Dutch", "nna": "Nyangumarta",
    "pt": "Portuguese", "tr": "Turkish", "tw": "Twi", "zh": "Chinese",
}

#: AUTHORED. The World Bank region carrying most of each language's speakers, so a coverage
#: figure can be set beside the representation ratio tools/ancestry_geography.py measured for
#: that region. Deliberately coarse - one region per language, the modal one - because the
#: question being asked is ordinal (does coverage track representation at all?) and a finer
#: mapping would imply a precision this crossing does not have. Portuguese is assigned to
#: Latin America & Caribbean on speaker mass, not on the ontology's provenance.
LANGUAGE_REGION = {
    "ar": "Africa", "cs": "Europe", "de": "Europe", "dtp": "Asia", "es": "Latin America & Caribbean",
    "fr": "Europe", "it": "Europe", "ja": "Asia", "nl": "Europe", "nna": "Oceania",
    "pt": "Latin America & Caribbean", "tr": "Europe", "tw": "Africa", "zh": "Asia",
}


def hpo_hierarchy() -> tuple[set[str], dict[str, set[str]], dict[str, str], set[str]]:
    """Organ systems, every term's ancestors, English labels, and the live term set."""
    parents: dict[str, set[str]] = collections.defaultdict(set)
    names: dict[str, str] = {}
    term: str | None = None
    obsolete: set[str] = set()
    for line in BY_KEY["hpo_terms"].dest.read_text(encoding="utf-8").splitlines():
        if line.startswith("["):
            term = None
        elif line.startswith("id: HP:"):
            term = line[4:].strip()
        elif term and line.startswith("name:"):
            names[term] = line[5:].strip()
        elif term and line.startswith("is_a:"):
            parents[term].add(line[5:].split("!")[0].strip())
        elif term and line.startswith("is_obsolete: true"):
            obsolete.add(term)

    systems = {t for t, ps in parents.items() if PHENOTYPIC_ABNORMALITY in ps}
    ancestors: dict[str, set[str]] = {}

    def walk(t: str) -> set[str]:
        if t in ancestors:
            return ancestors[t]
        ancestors[t] = set()
        acc: set[str] = set()
        for p in parents.get(t, ()):
            acc.add(p)
            acc |= walk(p)
        ancestors[t] = acc
        return acc

    for t in list(parents):
        walk(t)
    live = {t for t in names if t not in obsolete}
    return systems, ancestors, names, live


def annotations() -> tuple[collections.Counter, dict[str, collections.Counter]]:
    """Every disease-phenotype annotation, counted once, and the same split by organ system."""
    per_term: collections.Counter = collections.Counter()
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        rows = (line for line in fh if not line.startswith("#"))
        for row in csv.DictReader(rows, delimiter="\t"):
            term = (row.get("hpo_id") or "").strip()
            disease = (row.get("database_id") or "").strip()
            if term and disease:
                per_term[term] += 1
    return per_term, {}


def translations() -> dict[str, set[str]]:
    """language code -> the HPO terms carrying an OFFICIAL label in it."""
    out: dict[str, set[str]] = {}
    # The subscript is written out at the call rather than bound to a name first, because
    # tools/status.py resolves a read site by walking the AST of the call itself: a variable
    # holding the path reads as "ingested and never opened" in the status report.
    with tarfile.open(BY_KEY["hpo_translations"].dest) as tar:
        for member in tar.getmembers():
            m = re.search(r"/babelon/hp-([a-z]+)\.babelon\.tsv$", member.name)
            if not m or not member.isfile():
                continue
            code = m.group(1)
            fh = tar.extractfile(member)
            if fh is None:
                continue
            terms: set[str] = set()
            reader = csv.DictReader(io.TextIOWrapper(fh, "utf-8", errors="replace"),
                                    delimiter="\t")
            for row in reader:
                if (row.get("predicate_id") or "").strip() != "rdfs:label":
                    continue
                if (row.get("translation_status") or "").strip().upper() != TRANSLATION_STATUS:
                    continue
                value = (row.get("translation_value") or "").strip()
                subject = (row.get("subject_id") or "").strip()
                if subject.startswith("HP:") and value:
                    terms.add(subject)
            out[code] = terms
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.parse_args()

    print("reading the ontology ...")
    systems, ancestors, english, live_terms = hpo_hierarchy()
    n_terms = len(live_terms)
    per_term, _ = annotations()
    total_annotations = sum(per_term.values())
    print(f"  {n_terms} live terms, {len(systems)} organ systems, "
          f"{total_annotations} disease-phenotype annotations")

    print("reading the language profiles ...")
    langs = translations()
    print(f"  {len(langs)} languages")

    # Annotation mass per organ system, so a per-system coverage is weighted the same way.
    system_mass: dict[str, int] = collections.Counter()
    term_systems: dict[str, set[str]] = {}
    for term, count in per_term.items():
        hit = ({term} | ancestors.get(term, set())) & systems
        term_systems[term] = hit
        for s in hit:
            system_mass[s] += count

    rows = []
    for code, all_terms in sorted(langs.items()):
        # A profile is versioned independently of the hp.obo on disk, so it can carry ids
        # this release does not have - obsolete, or newer. Counting those in the numerator
        # produced a Spanish term coverage of 100.5%, which is not a coverage. They are
        # excluded and reported separately, because a percentage above 100 is a defect
        # report about the join, not a fact about the language.
        terms = all_terms & live_terms
        stale = len(all_terms) - len(terms)
        covered_annotations = sum(c for t, c in per_term.items() if t in terms)
        # SORTED, AND THE TIE BROKEN EXPLICITLY. Python randomises string hashing per
        # process, so iterating a set of ids puts them in a different order every run —
        # and `min`/`max` return the FIRST extreme they meet, so a tie between two
        # systems returned a different id each time. Measured: with PYTHONHASHSEED=7 the
        # Spanish best system was HP:0000152 and with 99 it was HP:0001507. A published
        # field that changes between runs is the drift verify_claims exists to catch.
        per_system = {}
        for s in sorted(systems):
            mass = system_mass.get(s, 0)
            if mass < 500:                    # too little annotation to carry a ratio
                continue
            hit = sum(c for t, c in per_term.items()
                      if s in term_systems.get(t, ()) and t in terms)
            per_system[s] = hit / mass
        spread = (max(per_system.values()) - min(per_system.values())) if per_system else None
        worst = min(per_system, key=lambda k: (per_system[k], k)) if per_system else None
        best = max(per_system, key=lambda k: (per_system[k], k)) if per_system else None
        rows.append({
            "language": code,
            "name": LANGUAGE_NAMES.get(code, code),
            "terms_translated": len(terms),
            "terms_not_in_this_hpo_release": stale,
            "term_coverage": round(len(terms) / n_terms, 4),
            "annotation_coverage": round(covered_annotations / total_annotations, 4),
            "weighting_gain": round(covered_annotations / total_annotations
                                    - len(terms) / n_terms, 4),
            "system_spread": round(spread, 4) if spread is not None else None,
            "worst_system": ({"id": worst, "name": english.get(worst, worst),
                              "coverage": round(per_system[worst], 4)} if worst else None),
            "best_system": ({"id": best, "name": english.get(best, best),
                             "coverage": round(per_system[best], 4)} if best else None),
            "per_system": {s: round(v, 4) for s, v in sorted(per_system.items())},
        })
    rows.sort(key=lambda r: r["annotation_coverage"], reverse=True)

    # Does coverage track representation? tools/ancestry_geography.py already measured how
    # over- or under-represented each region is in the prevalence literature (Europe 8.10,
    # Africa 0.07). If translation effort followed the same gradient as the evidence base,
    # the two would rank together and language would be one more face of the same inequity.
    # If they do not, coverage is driven by something else - and saying which is not the same
    # claim at all. The comparison is ordinal and reported as such.
    crossing = None
    ancestry = ROOT / "out" / "rare" / "ancestry_geography.json"
    if ancestry.exists():
        ratios = {r["region"]: r["representationRatio"]
                  for r in json.loads(ancestry.read_text(encoding="utf-8"))["regions"]}
        paired = [(r["name"], LANGUAGE_REGION.get(r["language"]),
                   ratios.get(LANGUAGE_REGION.get(r["language"], "")),
                   r["annotation_coverage"])
                  for r in rows if LANGUAGE_REGION.get(r["language"]) in ratios]
        by_region: dict[str, list[float]] = collections.defaultdict(list)
        for _, region, _, cov in paired:
            by_region[region].append(cov)
        # min and max, not a median: three of these groups hold one or two languages, and a
        # median over two values is whichever one the index rounds to. The spread is the
        # honest summary here, and it is also the finding - Europe holds both extremes.
        summary = sorted(
            ({"region": reg, "representation_ratio": ratios[reg], "languages": len(cov),
              "min_annotation_coverage": round(min(cov), 4),
              "max_annotation_coverage": round(max(cov), 4)}
             for reg, cov in by_region.items()),
            key=lambda d: -d["representation_ratio"])
        crossing = {
            "asks": ("Does a language's coverage track how well its region is represented in "
                     "the prevalence literature?"),
            "region_mapping": "AUTHORED, one modal region per language; see LANGUAGE_REGION",
            "by_region": summary,
            "says": ("Read the two columns against each other. Europe is the most "
                     "over-represented region in the evidence base at 8.10 and it holds the "
                     "languages at BOTH extremes of coverage. Latin America and the "
                     "Caribbean is under-represented at 0.32 and holds the single best-"
                     "covered language. So the two gradients are not the same gradient: "
                     "translation coverage is driven by whether a volunteer group formed, "
                     "not by how well the region is studied, and it is a different problem "
                     "with a different remedy. Africa is the one region low on both, where "
                     "they compound."),
        }

    payload = {
        "generated": date.today().isoformat(),
        "provenance": ("measured from the HPO language profiles (Babelon TSV, "
                       "obophenotype/hpo-translations), hp.obo and phenotype.hpoa"),
        "question": ("What fraction of the rare-disease phenotype can be read in each "
                     "language - by vocabulary, and by what diseases are actually "
                     "annotated with?"),
        "method": {
            "term_coverage": "OFFICIAL rdfs:label rows / live HPO terms",
            "annotation_coverage": ("annotation instances in phenotype.hpoa whose term has "
                                    "such a label / all annotation instances"),
            "why_two": ("A clinician meets terms in proportion to how often diseases are "
                        "annotated with them, not uniformly. The difference between the two "
                        "numbers is what a translation project's own progress report cannot "
                        "show."),
            "per_system": ("organ systems carrying at least 500 annotations; the spread "
                           "max-min locates a defect confined to one subgroup, which any "
                           "pooled figure divides by the number of subgroups"),
            "status_counted": TRANSLATION_STATUS,
        },
        "totals": {"hpo_terms": n_terms, "annotations": total_annotations,
                   "languages": len(rows)},
        "languages": rows,
        # Keyed as well as ordered. The list is sorted by coverage, so a positional
        # reference into it would silently follow a rank change; tools/verify_claims.py
        # addresses this map instead.
        "by_language": {r["language"]: r for r in rows},
        "against_representation": crossing,
        "says": ("A measurement of the reader's position, not a judgement of any translation "
                 "effort. Several profiles are explicitly partial and their maintainers say "
                 "so; only OFFICIAL rows are counted, so drafts are neither credited nor "
                 "penalised."),
        "limits": [
            "English is the source language and is 100% by construction; it is not a row.",
            "Labels only. A term whose label is translated but whose definition is not is "
            "counted as covered here, which is the generous reading.",
            "phenotype.hpoa is itself unevenly curated (tools/atlas_bias.py, +0.2357), so a "
            "well-annotated disease pulls the annotation weighting toward its own terms.",
        ],
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"{'language':16s} {'terms':>7s} {'term%':>7s} {'annot%':>7s} {'gain':>7s} "
          f"{'spread':>7s}  worst system")
    for r in rows:
        if r["annotation_coverage"] < 0.001:
            continue
        print(f"{r['name'][:16]:16s} {r['terms_translated']:7d} "
              f"{100*r['term_coverage']:6.1f}% {100*r['annotation_coverage']:6.1f}% "
              f"{100*r['weighting_gain']:+6.1f}% {100*(r['system_spread'] or 0):6.1f}%  "
              f"{r['worst_system']['name'][:34] if r['worst_system'] else ''}")
    if crossing:
        print()
        print("against how well each region is represented in the prevalence literature")
        print(f"  {'region':28s} {'representation':>14s} {'langs':>6s} "
              f"{'worst':>8s} {'best':>8s}")
        for row in crossing["by_region"]:
            print(f"  {row['region']:28s} {row['representation_ratio']:14.2f} "
                  f"{row['languages']:6d} {100*row['min_annotation_coverage']:7.1f}% "
                  f"{100*row['max_annotation_coverage']:7.1f}%")

    empty = [r["name"] for r in rows if r["annotation_coverage"] < 0.001]
    if empty:
        print(f"\n{len(empty)} profiles carry no OFFICIAL labels at all: {', '.join(empty)}")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
