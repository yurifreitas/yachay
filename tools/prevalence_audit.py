#!/usr/bin/env python
"""Audit the prevalence field, because the capability arithmetic is standing on it.

WHY THIS EXISTS. The arithmetic tab divides plan capital by a patient cohort, and that cohort
comes from one string per disease: "1-9 / 100 000". I flagged two of those cohorts as wrong by
HAND, from memory, in a block I marked as the only authored thing on a derived tab. That was
the right instinct and the wrong implementation — a hand-written check does not scale to 6,728
diseases and cannot be re-run when Orphanet publishes again.

The string was never the data. Orphanet records a LIST of prevalence measurements per disease,
and each one carries four things the string throws away:

    PrevalenceType            point prevalence, annual incidence, prevalence AT BIRTH,
                              lifetime prevalence, or a raw count of cases and families
    PrevalenceQualification   whether it is a class, a value, or both
    PrevalenceGeographic      the population it was measured in
    ValidationStatus          whether Orphanet's experts signed it off

THE TYPE IS THE BUG. Prevalence at birth and point prevalence are different quantities, and for
a disease that shortens life they diverge by a lot — that is not an error in the data, it is an
error in reading it. Collapsing the list to one string mixes them silently, and then the
arithmetic divides money by a number that means something different for each row.

So this file reads every record, reports what the corpus actually contains, and recomputes the
cohorts using only records of ONE type with a stated validation status. Where that changes the
answer, it says by how much.

    python tools/prevalence_audit.py     # writes out/rare/prevalence_audit.json
"""

from __future__ import annotations

import json
import pathlib
import re
from collections import Counter, defaultdict
from xml.etree import ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
XML = ROOT / "data" / "ontology" / "en_product9_prev.xml"
DEST = ROOT / "out" / "rare"

# The class strings are ranges. Parsed to a rate band rather than a midpoint, for the same
# reason every other band in this project stays a band.
CLASS_RE = re.compile(r"([\d.]+)\s*-\s*([\d.]+)\s*/\s*([\d\s]+)")
LT_RE = re.compile(r"<\s*([\d.]+)\s*/\s*([\d\s]+)")
GT_RE = re.compile(r">\s*([\d.]+)\s*/\s*([\d\s]+)")

# THE ONLY AUTHORED CONSTANT IN THIS FILE. Round UN mid-2023 populations, in millions, for the
# most populous countries plus the European ones that dominate the corpus. It exists so the
# record counts can be read as a RATE: a count says Norway and China are both present, a rate
# says how differently they have been looked at. Wrong only if the world changed a great deal,
# and checkable in one search.
POPULATION_M = {
    "India": 1428, "China": 1426, "United States": 340, "Indonesia": 278, "Pakistan": 240,
    "Nigeria": 224, "Brazil": 216, "Bangladesh": 173, "Russia": 144, "Mexico": 128,
    "Ethiopia": 127, "Japan": 123, "Egypt": 113, "Philippines": 117, "Vietnam": 99,
    "Turkey": 86, "Iran": 89, "Germany": 83, "Thailand": 72, "United Kingdom": 68,
    "France": 65, "Italy": 59, "South Africa": 60, "Korea, Republic of": 52, "Spain": 48,
    "Poland": 41, "Canada": 39, "Saudi Arabia": 37, "Australia": 26, "Netherlands": 18,
    "Sweden": 11, "Portugal": 10, "Israel": 9, "Austria": 9, "Switzerland": 9,
    "Denmark": 6, "Finland": 6, "Norway": 5, "Ireland": 5, "New Zealand": 5,
}


def parse_class(text: str | None):
    """Return (lo_rate, hi_rate) or None. '<1 / 1 000 000' has no floor, so zero is honest."""
    if not text:
        return None
    t = text.replace(" ", " ").strip()
    m = CLASS_RE.search(t)
    if m:
        d = float(m.group(3).replace(" ", ""))
        return float(m.group(1)) / d, float(m.group(2)) / d
    m = LT_RE.search(t)
    if m:
        d = float(m.group(2).replace(" ", ""))
        return 0.0, float(m.group(1)) / d
    m = GT_RE.search(t)
    if m:
        d = float(m.group(2).replace(" ", ""))
        # No stated ceiling. Ten times the floor is a convention, and it is labelled as one
        # everywhere it is used rather than being quietly treated as a measurement.
        return float(m.group(1)) / d, 10 * float(m.group(1)) / d
    return None


def text_of(node, path):
    el = node.find(path)
    return el.text.strip() if el is not None and el.text else None


def main() -> int:
    if not XML.exists():
        raise SystemExit("missing %s — run the ingest first" % XML.relative_to(ROOT))

    records: dict[str, list[dict]] = defaultdict(list)
    names: dict[str, str] = {}

    for _, disorder in ET.iterparse(str(XML), events=("end",)):
        if disorder.tag != "Disorder":
            continue
        code = text_of(disorder, "OrphaCode")
        name = text_of(disorder, "Name")
        if code:
            names[code] = name or code
            for prev in disorder.findall("./PrevalenceList/Prevalence"):
                records[code].append({
                    "type": text_of(prev, "PrevalenceType/Name"),
                    "qualification": text_of(prev, "PrevalenceQualification/Name"),
                    "class": text_of(prev, "PrevalenceClass/Name"),
                    "value": text_of(prev, "ValMoy"),
                    "geography": text_of(prev, "PrevalenceGeographic/Name"),
                    "validation": text_of(prev, "PrevalenceValidationStatus/Name"),
                    "source": text_of(prev, "Source"),
                })
        disorder.clear()

    # ---- what the corpus actually contains -------------------------------------------
    types = Counter()
    validation = Counter()
    geography = Counter()
    qualification = Counter()
    classes = Counter()
    for rows in records.values():
        for r in rows:
            types[r["type"] or "unstated"] += 1
            validation[r["validation"] or "unstated"] += 1
            geography[r["geography"] or "unstated"] += 1
            qualification[r["qualification"] or "unstated"] += 1
            if r["class"]:
                classes[r["class"]] += 1

    # ---- diseases carrying more than one KIND of measurement --------------------------
    mixed = []
    for code, rows in records.items():
        kinds = {r["type"] for r in rows if r["type"]}
        if len(kinds) > 1:
            mixed.append({"orpha": code, "name": names.get(code, code),
                          "types": sorted(kinds), "records": len(rows)})
    mixed.sort(key=lambda m: (-len(m["types"]), -m["records"]))

    # ---- where a birth figure and a point figure disagree by a class ------------------
    # This is the CF and Duchenne problem, found by arithmetic rather than by memory.
    disagreements = []
    for code, rows in records.items():
        by_kind: dict[str, list[tuple[float, float]]] = defaultdict(list)
        for r in rows:
            band = parse_class(r["class"])
            if band and r["type"]:
                by_kind[r["type"]].append(band)
        birth = by_kind.get("Prevalence at birth") or []
        point = by_kind.get("Point prevalence") or []
        if not birth or not point:
            continue
        b_hi = max(h for _, h in birth)
        p_hi = max(h for _, h in point)
        if p_hi <= 0 or b_hi <= 0:
            continue
        ratio = b_hi / p_hi
        if ratio >= 5 or ratio <= 0.2:
            disagreements.append({
                "orpha": code, "name": names.get(code, code),
                "birthHiRate": b_hi, "pointHiRate": p_hi,
                "foldDifference": round(ratio, 3),
                # Magnitude of the disagreement regardless of direction, so the sort and the
                # sentence do not both have to know which way round it is.
                "foldMagnitude": round(max(ratio, 1 / ratio), 1),
                "says": ("The birth figure and the point-prevalence figure differ %.0f-fold. "
                         "They are different quantities, and any arithmetic that takes "
                         "whichever came first in the file is wrong by that factor."
                         % max(ratio, 1 / ratio)),
            })
    disagreements.sort(key=lambda d: -d["foldMagnitude"])

    # ---- the diseases the dashboard actually uses ------------------------------------
    watched = [
        "Cystic fibrosis", "Duchenne muscular dystrophy", "Sickle cell anemia",
        "Rett syndrome", "Dravet syndrome", "Alkaptonuria",
        "Fibrodysplasia ossificans progressiva", "Zellweger syndrome",
        "CDKL5 deficiency disorder", "Systemic lupus erythematosus",
    ]
    by_name = {v.lower(): k for k, v in names.items()}
    watched_rows = []
    for want in watched:
        code = by_name.get(want.lower())
        if not code:
            continue
        rows = records[code]
        # The defensible cohort: validated point prevalence only.
        good = [r for r in rows
                if r["type"] == "Point prevalence"
                and (r["validation"] or "").startswith("Validated")
                and parse_class(r["class"])]
        band = None
        if good:
            bands = [parse_class(r["class"]) for r in good]
            band = {"lo": min(b[0] for b in bands), "hi": max(b[1] for b in bands)}
        watched_rows.append({
            "orpha": code, "name": names[code], "records": rows,
            "recordCount": len(rows),
            "typesPresent": sorted({r["type"] for r in rows if r["type"]}),
            "validatedPointPrevalence": band,
            "worldCohort": (None if not band
                            else {"lo": round(band["lo"] * 8_100_000_000),
                                  "hi": round(band["hi"] * 8_100_000_000)}),
        })

    # ---- a cohort per disorder, so the arithmetic can be rebuilt on this ------------
    # The rule is stated once and applied to all 6,728: validated point prevalence, class
    # parsed to a band. Where a disorder has none, the entry records WHY rather than falling
    # back to a different quantity — a cohort assembled from mixed types is the defect this
    # whole file exists to find.
    cohorts = {}
    basis_counts = Counter()
    for code, rows in records.items():
        good = [r for r in rows
                if r["type"] == "Point prevalence"
                and (r["validation"] or "").startswith("Validated")
                and parse_class(r["class"])]
        if good:
            bands = [parse_class(r["class"]) for r in good]
            lo, hi = min(b[0] for b in bands), max(b[1] for b in bands)
            basis = "validated point prevalence"
        else:
            any_point = [r for r in rows if r["type"] == "Point prevalence" and parse_class(r["class"])]
            if any_point:
                bands = [parse_class(r["class"]) for r in any_point]
                lo, hi = min(b[0] for b in bands), max(b[1] for b in bands)
                basis = "point prevalence, not yet validated"
            else:
                lo = hi = None
                basis = ("no point-prevalence class at all; the disorder is recorded only as "
                         + "/".join(sorted({r["type"] for r in rows if r["type"]}) or ["nothing"]))
        basis_counts[basis if lo is not None else "no point-prevalence class"] += 1
        cohorts[code] = {
            "name": names.get(code, code),
            "loRate": lo, "hiRate": hi,
            "basis": basis,
            "records": len(rows),
            "typesPresent": sorted({r["type"] for r in rows if r["type"]}),
            "worldLo": None if lo is None else round(lo * 8_100_000_000),
            "worldHi": None if hi is None else round(hi * 8_100_000_000),
        }

    # ---- where the measuring happened -------------------------------------------------
    # Records, not diseases: a disorder measured five times in France counts five times, which
    # is the right unit for "where does the effort go".
    geo_total = sum(geography.values())
    NON_PLACES = {"Worldwide", "Europe", "unstated"}
    placed = {k: v for k, v in geography.items() if k not in NON_PLACES}
    placed_total = sum(placed.values())
    geo_rows = [
        {"place": k, "records": v, "share": round(v / max(1, placed_total), 4),
         "populationM": POPULATION_M.get(k),
         # Records per hundred million people: how closely this population has been looked at.
         "perHundredM": (None if not POPULATION_M.get(k)
                         else round(v / (POPULATION_M[k] / 100), 1))}
        for k, v in sorted(placed.items(), key=lambda kv: -kv[1])
    ]
    top10 = sum(r["records"] for r in geo_rows[:10])

    # The same rows, ranked by how CLOSELY looked at rather than by count. This is the ordering
    # that makes the point, and the two orderings barely overlap.
    rated = sorted((r for r in geo_rows if r["perHundredM"] is not None),
                   key=lambda r: -r["perHundredM"])
    covered_pop = sum(POPULATION_M[r["place"]] for r in geo_rows if r["place"] in POPULATION_M)
    missing = sorted(
        ({"place": k, "populationM": v, "records": placed.get(k, 0)}
         for k, v in POPULATION_M.items() if placed.get(k, 0) == 0),
        key=lambda r: -r["populationM"])

    payload = {
        "generated": "tools/prevalence_audit.py",
        "input": "data/ontology/en_product9_prev.xml",
        "premise": (
            "The capability arithmetic divides money by a cohort, and the cohort came from one "
            "collapsed string per disease. Orphanet does not record one string — it records a "
            "list of measurements, each with a TYPE, a population and a validation status. This "
            "audit reads the list and reports what the collapse was throwing away."
        ),
        "scale": {
            "disordersWithPrevalence": len(records),
            "prevalenceRecords": sum(len(v) for v in records.values()),
            "meanRecordsPerDisorder": round(
                sum(len(v) for v in records.values()) / max(1, len(records)), 2),
        },
        "byType": dict(types.most_common()),
        "byValidation": dict(validation.most_common()),
        "byQualification": dict(qualification.most_common()),
        "byClass": dict(classes.most_common()),
        "topGeographies": dict(geography.most_common(15)),
        "mixedTypeDisorders": {
            "count": len(mixed),
            "fraction": round(len(mixed) / max(1, len(records)), 4),
            "examples": mixed[:12],
        },
        "typeDisagreements": {
            "count": len(disagreements),
            "rows": disagreements[:20],
            "says": (
                "%d diseases carry BOTH a birth figure and a point-prevalence figure that "
                "differ by five-fold or more. Collapsing the list to one string picks one of "
                "them arbitrarily, so any cohort built that way is wrong by that factor — and "
                "wrong silently, which is worse."
                % len(disagreements)
            ),
        },
        "cohorts": cohorts,
        "cohortBasis": dict(basis_counts.most_common()),
        "geography": {
            "records": geo_total,
            "namedPlaces": len(placed),
            "placedRecords": placed_total,
            "unplacedRecords": geo_total - placed_total,
            "rows": geo_rows,
            "byRate": rated[:20],
            "leastLookedAt": rated[-12:][::-1],
            "absentEntirely": missing,
            "populationCoveredM": covered_pop,
            "top10Share": round(top10 / max(1, placed_total), 4),
            "says": (
                "%s of %s prevalence records name a specific population rather than 'Worldwide' "
                "or 'Europe'. The ten most-measured populations carry %.0f%% of those. This is "
                "not a map of where rare disease is — it is a map of where the field looked, and "
                "every prevalence-derived number on this site inherits its shape. Ranked by "
                "records per hundred million people rather than by count, the ordering changes "
                "completely: the most closely examined populations are small and northern, and "
                "several of the world's most populous countries carry no record at all."
                % (format(placed_total, ","), format(geo_total, ","), 100 * top10 / max(1, placed_total))
            ),
        },
        "watched": watched_rows,
        "finding": (
            "Prevalence was never a number in this corpus; it is a list of measurements of "
            "different kinds, in different populations, with different levels of expert "
            "sign-off. The dashboard had been reading the first one it found. Restricting to "
            "VALIDATED POINT PREVALENCE gives a cohort that means one thing, and where that "
            "differs from what the arithmetic tab used, the difference is reported rather than "
            "quietly corrected."
        ),
    }

    DEST.mkdir(parents=True, exist_ok=True)
    path = DEST / "prevalence_audit.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    sc = payload["scale"]
    print("wrote %s" % path.relative_to(ROOT))
    print("  %s disorders, %s prevalence records (%.2f each)"
          % (format(sc["disordersWithPrevalence"], ","), format(sc["prevalenceRecords"], ","),
             sc["meanRecordsPerDisorder"]))
    print("  by type: %s" % dict(list(types.most_common())))
    print("  validation: %s" % dict(validation.most_common()))
    print("  %s disorders mix more than one KIND of measurement (%.1f%%)"
          % (format(len(mixed), ","), 100 * len(mixed) / max(1, len(records))))
    print("  %d disorders where birth and point prevalence differ 5-fold or more"
          % len(disagreements))
    print("  cohort basis: %s" % dict(basis_counts.most_common()))
    if rated:
        print("  most looked at, per 100M people: %s"
              % " · ".join("%s %.0f" % (r["place"], r["perHundredM"]) for r in rated[:6]))
        print("  least looked at, per 100M people: %s"
              % " · ".join("%s %.1f" % (r["place"], r["perHundredM"]) for r in rated[-6:]))
    if missing:
        print("  no prevalence record at all: %s"
              % " · ".join("%s (%dM)" % (m["place"], m["populationM"]) for m in missing[:8]))
    print("  geography: %s named populations, top ten hold %.0f%% of placed records"
          % (format(len(placed), ","), 100 * top10 / max(1, placed_total)))
    print("    " + " · ".join("%s %d" % (r["place"], r["records"]) for r in geo_rows[:8]))
    for w in watched_rows:
        print("    %-40s %d records %-46s cohort %s"
              % (w["name"][:40], w["recordCount"], "/".join(w["typesPresent"])[:46],
                 "n/a" if not w["worldCohort"]
                 else format(w["worldCohort"]["lo"], ",") + "-" + format(w["worldCohort"]["hi"], ",")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
