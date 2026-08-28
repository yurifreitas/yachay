#!/usr/bin/env python
"""Who was counted, and where — the population axis the atlas never read.

WHY THIS EXISTS. `tools/prevalence_audit.py` opened the Orphanet prevalence records and found
that a prevalence is a LIST of measurements, not a number. It reported geography as a
by-product: 65% of records carry no named place. This file takes the geography seriously,
because the field it was skipping is the only place in any catalogue on disk where a
POPULATION appears at all.

That matters for a reason that is statistical and not political. A recessive disorder's
prevalence is not a property of the disorder — it is a property of the disorder IN A
POPULATION, and founder history, drift and consanguinity move it by orders of magnitude.
Tay-Sachs, sickle cell trait, Finnish disease heritage: same allele, same protein, wildly
different rates. Every rare-disease number this project has published treats prevalence as a
scalar. This measures how wrong that is, and where.

FIVE MEASUREMENTS, and the fifth is the one that hurts.

  1. THE SHAPE OF THE CORPUS. How many records are placed at all, how many are 'Worldwide'
     (which is a claim, not an absence), how many name a supranational region, and how many
     use the 'Specific population' tag — the catalogue's only slot for an ethnic group.

  2. RECORDS PER CAPITA, BY COUNTRY. A count says a country is present. A rate says how
     differently it was looked at. The disparity between the best- and worst-covered
     populations is computed as an explicit ratio rather than left to the reader.

  3. REPRESENTATION BY WORLD REGION. Each region's share of records against its share of
     world population. A ratio of 1.0 is proportional; the numbers are not near 1.0.

  4. SINGLE-POPULATION DISORDERS. Disorders whose every placed record names one country.
     This is the founder-effect signature as the catalogue can see it — with the confound
     stated: a disorder described once in one country looks identical to a disorder that
     only exists in one country, and nothing here can separate them.

  5. CLASS DISCORDANCE ACROSS PLACES. Disorders whose prevalence CLASS differs between
     countries. Every one of these is a disorder for which 'the prevalence' is a category
     error, and every one is currently collapsed to a single band by every other tab here.

WHAT THIS FILE CANNOT DO, stated up front because the temptation is strong. Geography is not
ancestry. A record placed in Brazil describes a population that is Indigenous, African,
European and Japanese in different proportions by region, and the catalogue records none of
that. Nothing below should be read as a statement about a genetic ancestry group. It is a
statement about WHERE SOMEONE PUBLISHED, which is exactly the ascertainment quantity
`tools/atlas_bias.py` measures at +0.2357.

    python tools/ancestry_geography.py     # writes out/rare/ancestry_geography.json

Stdlib only.
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter, defaultdict
from xml.etree import ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
XML = ROOT / "data" / "ontology" / "en_product9_prev.xml"
DEST = ROOT / "out" / "rare"

# ---------------------------------------------------------------------------------------
# THE AUTHORED CONSTANTS. Two tables, and they are the only things in this file a person
# wrote. Both are checkable in one search, and changing either changes every number below.
#
# Populations are round UN mid-2023 estimates in millions. They exist so counts can be read
# as RATES. Countries absent from this table still appear in the raw counts; they are simply
# excluded from the per-capita ranking, and the file says how many were excluded.
# ---------------------------------------------------------------------------------------
POPULATION_M = {
    "India": 1428, "China": 1426, "United States": 340, "Indonesia": 278, "Pakistan": 240,
    "Nigeria": 224, "Brazil": 216, "Bangladesh": 173, "Russian Federation": 144,
    "Mexico": 128, "Ethiopia": 127, "Japan": 123, "Philippines": 117, "Egypt": 113,
    "Viet Nam": 99, "Congo, Democratic Republic": 102, "Turkey": 86, "Iran, Islamic Republic of": 89,
    "Germany": 83, "Thailand": 72, "United Kingdom": 68, "Tanzania, United Republic of": 67,
    "France": 65, "South Africa": 60, "Italy": 59, "Kenya": 55, "Myanmar": 54,
    "Colombia": 52, "Korea, Republic of": 52, "Sudan": 48, "Uganda": 49, "Spain": 48,
    "Algeria": 46, "Iraq": 45, "Argentina": 46, "Afghanistan": 42, "Yemen": 34,
    "Canada": 39, "Poland": 41, "Morocco": 38, "Saudi Arabia": 37, "Ukraine": 38,
    "Angola": 36, "Uzbekistan": 35, "Peru": 34, "Malaysia": 34, "Mozambique": 33,
    "Ghana": 34, "Venezuela": 28, "Nepal": 31, "Australia": 26, "Sri Lanka": 22,
    "Cameroon": 28, "Cote d'Ivoire": 28, "Niger": 27, "Mali": 23, "Burkina Faso": 23,
    "Syrian Arab Republic": 23, "Taiwan, Province of China": 23, "Chile": 19,
    "Netherlands": 18, "Kazakhstan": 20, "Guatemala": 18, "Ecuador": 18, "Zimbabwe": 16,
    "Cambodia": 17, "Senegal": 17, "Zambia": 20, "Somalia": 18, "Belgium": 12,
    "Tunisia": 12, "Bolivia": 12, "Cuba": 11, "Greece": 10, "Portugal": 10, "Sweden": 11,
    "Czech Republic": 11, "Jordan": 11, "Dominican Republic": 11, "Hungary": 10,
    "Belarus": 9, "Austria": 9, "Israel": 9, "Switzerland": 9, "Papua New Guinea": 10,
    "Serbia": 7, "Bulgaria": 6, "Denmark": 6, "Finland": 6, "Slovakia": 5, "Norway": 5,
    "Ireland": 5, "New Zealand": 5, "Costa rica": 5, "Singapore": 6, "Lebanon": 5,
    "Libyan Arab Jamahiriya": 7, "Paraguay": 7, "Hong Kong": 7, "El Salvador": 6,
    "Honduras": 10, "Nicaragua": 7, "Kuwait": 4, "Panama": 4, "Croatia": 4, "Georgia": 4,
    "Uruguay": 3, "Bosnia and Herzegovina": 3, "Moldova, Republic of": 3, "Armenia": 3,
    "Albania": 3, "Jamaica": 3, "Qatar": 3, "Lithuania": 3, "Puerto rico": 3,
    "United Arab Emirates": 9, "Mauritania": 5, "Eritrea": 4, "Oman": 5, "Panama ": 4,
    "Slovenia": 2, "Latvia": 2, "North Macedonia": 2, "Estonia": 1, "Cyprus": 1,
    "Bahrain": 2, "Togo": 9, "Sierra leone": 8, "Lesotho": 2, "Guyana": 1,
    "Trinidad and Tobago": 2, "Malta": 0.5, "Iceland": 0.4, "Luxembourg": 0.7,
    "Brunei Darussalam": 0.5, "Guadeloupe": 0.4, "Martinique": 0.4, "Reunion": 0.9,
    "New Caledonia": 0.3, "French Polynesia": 0.3, "Faroe Islands": 0.05,
    "Greenland": 0.06, "Liechtenstein": 0.04, "Belize": 0.4, "Haiti": 11,
    "Palestinian Territory, occupied": 5, "Mongolia": 3, "Azerbaijan": 10,
    "Korea, Democratic People's Republic of": 26, "Romania": 19, "Indonesia ": 278,
}

# Region assignment, with each region's share of world population (UN 2023, world ~8.05 bn).
# The share is what turns a record count into a representation ratio.
REGION_OF = {
    # Europe
    **{c: "Europe" for c in [
        "United Kingdom", "France", "Italy", "Netherlands", "Germany", "Spain", "Norway",
        "Finland", "Sweden", "Denmark", "Ireland", "Portugal", "Czech Republic", "Poland",
        "Switzerland", "Belgium", "Austria", "Croatia", "Estonia", "Malta", "Slovakia",
        "Bulgaria", "Latvia", "Lithuania", "Iceland", "Slovenia", "Hungary", "Greece",
        "Ukraine", "Romania", "Russian Federation", "Serbia", "Belarus", "Luxembourg",
        "Bosnia and Herzegovina", "North Macedonia", "Faroe Islands", "Moldova, Republic of",
        "Albania", "Liechtenstein", "Cyprus",
    ]},
    # Northern America
    **{c: "Northern America" for c in ["United States", "Canada", "Greenland"]},
    # Latin America and the Caribbean
    **{c: "Latin America & Caribbean" for c in [
        "Brazil", "Mexico", "Argentina", "Chile", "Cuba", "Uruguay", "Peru", "Colombia",
        "Martinique", "Costa rica", "Bolivia", "Ecuador", "Puerto rico", "Venezuela",
        "Jamaica", "Guadeloupe", "Belize", "Dominican Republic", "El Salvador",
        "Guatemala", "Honduras", "Nicaragua", "Panama", "Paraguay", "Guyana", "Haiti",
        "Trinidad and Tobago",
    ]},
    # Africa
    **{c: "Africa" for c in [
        "South Africa", "Egypt", "Tunisia", "Sudan", "Nigeria", "Algeria", "Morocco",
        "Senegal", "Sierra leone", "Kenya", "Togo", "Zimbabwe", "Tanzania, United Republic of",
        "Cameroon", "Mauritania", "Uganda", "Lesotho", "Libyan Arab Jamahiriya", "Eritrea",
        "Reunion", "Ethiopia", "Ghana", "Angola", "Mozambique", "Zambia", "Somalia",
        "Niger", "Mali", "Burkina Faso", "Cote d'Ivoire", "Congo, Democratic Republic",
    ]},
    # Asia
    **{c: "Asia" for c in [
        "Japan", "China", "Taiwan, Province of China", "Korea, Republic of", "Israel",
        "Turkey", "Iran, Islamic Republic of", "Saudi Arabia", "Singapore", "India",
        "Thailand", "United Arab Emirates", "Hong Kong", "Kuwait", "Pakistan", "Lebanon",
        "Malaysia", "Iraq", "Jordan", "Bahrain", "Bangladesh", "Oman", "Viet Nam",
        "Sri Lanka", "Mongolia", "Brunei Darussalam", "Azerbaijan", "Georgia", "Armenia",
        "Indonesia", "Nepal", "Philippines", "Uzbekistan", "Kazakhstan", "Cambodia",
        "Myanmar", "Afghanistan", "Yemen", "Syrian Arab Republic",
        "Palestinian Territory, occupied", "Korea, Democratic People's Republic of",
    ]},
    # Oceania
    **{c: "Oceania" for c in [
        "Australia", "New Zealand", "New Caledonia", "French Polynesia", "Papua New Guinea",
    ]},
}

# UN 2023 population shares, as fractions of ~8.05 billion.
REGION_POPULATION_SHARE = {
    "Asia": 0.5900,
    "Africa": 0.1800,
    "Europe": 0.0920,
    "Latin America & Caribbean": 0.0810,
    "Northern America": 0.0470,
    "Oceania": 0.0055,
}

# Names in the geography vocabulary that are not countries. Kept explicit so a supranational
# tag is never silently counted as a place.
SUPRANATIONAL = {
    "Worldwide", "Europe", "Africa", "Latin America", "North America", "South East Asia",
    "Oceania", "Eastern Mediterranean Asia", "Western Asia",
}
POPULATION_TAG = "Specific population"

# The prevalence classes, rarest first. Orphanet gives them as strings with no order, and
# an ordered variable read as unordered labels is the most common charting error there is.
CLASS_ORDER = [
    "<1 / 1 000 000",
    "1-9 / 1 000 000",
    "1-9 / 100 000",
    "1-5 / 10 000",
    "6-9 / 10 000",
    ">1 / 1000",
]


def text_of(node, path):
    el = node.find(path)
    return el.text.strip() if el is not None and el.text else None


def load(xml_path: pathlib.Path):
    """Return {orpha: {'name': str, 'records': [ ... ]}} for every disorder with prevalence."""
    out: dict[str, dict] = {}
    for _, disorder in ET.iterparse(str(xml_path), events=("end",)):
        if disorder.tag != "Disorder":
            continue
        code = text_of(disorder, "OrphaCode")
        if code:
            recs = []
            for prev in disorder.findall("./PrevalenceList/Prevalence"):
                recs.append({
                    "type": text_of(prev, "PrevalenceType/Name"),
                    "class": text_of(prev, "PrevalenceClass/Name"),
                    "value": text_of(prev, "ValMoy"),
                    "geography": text_of(prev, "PrevalenceGeographic/Name"),
                    "validation": text_of(prev, "PrevalenceValidationStatus/Name"),
                })
            if recs:
                out[code] = {"name": text_of(disorder, "Name") or code, "records": recs}
        disorder.clear()
    return out


def main() -> int:
    if not XML.exists():
        raise SystemExit("missing %s — run the ingest first" % XML.relative_to(ROOT))

    disorders = load(XML)
    all_records = [r for d in disorders.values() for r in d["records"]]

    # ---- 1. the shape of the corpus ---------------------------------------------------
    geo_counts = Counter(r["geography"] for r in all_records if r["geography"])
    countries = {g: n for g, n in geo_counts.items()
                 if g not in SUPRANATIONAL and g != POPULATION_TAG}

    shape = {
        "records": len(all_records),
        "withGeographyTag": sum(geo_counts.values()),
        "worldwide": geo_counts.get("Worldwide", 0),
        "supranational": sum(n for g, n in geo_counts.items()
                             if g in SUPRANATIONAL and g != "Worldwide"),
        "specificPopulation": geo_counts.get(POPULATION_TAG, 0),
        "namedCountry": sum(countries.values()),
        "distinctCountries": len(countries),
    }
    shape["worldwideShare"] = round(shape["worldwide"] / shape["withGeographyTag"], 4)
    shape["namedCountryShare"] = round(shape["namedCountry"] / shape["withGeographyTag"], 4)

    # ---- 2. records per capita --------------------------------------------------------
    per_capita = []
    unpriced = []
    for country, n in countries.items():
        pop = POPULATION_M.get(country)
        if pop is None:
            unpriced.append({"country": country, "records": n})
            continue
        per_capita.append({
            "country": country,
            "records": n,
            "populationM": pop,
            "region": REGION_OF.get(country),
            "recordsPer100M": round(n / pop * 100, 1),
        })
    per_capita.sort(key=lambda r: -r["recordsPer100M"])

    top, bottom = per_capita[0], per_capita[-1]
    disparity = {
        "best": top,
        "worst": bottom,
        "ratio": round(top["recordsPer100M"] / bottom["recordsPer100M"], 1),
        "says": (
            "%s contributes %.1f prevalence records per hundred million people; %s contributes "
            "%.1f. The ratio is %.0fx, and it is a ratio of epidemiological publishing, not of "
            "disease." % (top["country"], top["recordsPer100M"], bottom["country"],
                          bottom["recordsPer100M"],
                          top["recordsPer100M"] / bottom["recordsPer100M"])
        ),
    }

    # ---- 3. representation by world region --------------------------------------------
    region_records = Counter()
    for country, n in countries.items():
        region = REGION_OF.get(country)
        if region:
            region_records[region] += n
    placed_total = sum(region_records.values())

    regions = []
    for region, share in sorted(REGION_POPULATION_SHARE.items(), key=lambda kv: -kv[1]):
        got = region_records.get(region, 0)
        record_share = got / placed_total if placed_total else 0.0
        regions.append({
            "region": region,
            "records": got,
            "recordShare": round(record_share, 4),
            "populationShare": share,
            "representationRatio": round(record_share / share, 2),
        })

    # ---- 4. single-population disorders ------------------------------------------------
    placed_by_disorder: dict[str, set] = defaultdict(set)
    for code, d in disorders.items():
        for r in d["records"]:
            g = r["geography"]
            if g and g not in SUPRANATIONAL and g != POPULATION_TAG:
                placed_by_disorder[code].add(g)

    single = [c for c, places in placed_by_disorder.items() if len(places) == 1]
    multi = [c for c, places in placed_by_disorder.items() if len(places) > 1]
    unplaced = [c for c in disorders if c not in placed_by_disorder]

    single_by_country = Counter(next(iter(placed_by_disorder[c])) for c in single)

    concentration = {
        "disordersWithAnyPlacedRecord": len(placed_by_disorder),
        "disordersPlacedInExactlyOneCountry": len(single),
        "disordersPlacedInMoreThanOneCountry": len(multi),
        "disordersWithNoPlacedRecord": len(unplaced),
        "topCountriesForSinglePlaceDisorders": single_by_country.most_common(15),
        "confound": (
            "A disorder described once, in one country, is indistinguishable here from a "
            "disorder that only occurs in one population. Founder effect and single-report "
            "ascertainment produce the identical pattern in this field, and nothing in this "
            "catalogue separates them. These counts are an upper bound on founder structure "
            "and a lower bound on nothing."
        ),
    }

    # ---- 5. class discordance across places -------------------------------------------
    discordant = []
    for code in multi:
        by_place: dict[str, set] = defaultdict(set)
        for r in disorders[code]["records"]:
            g, cls = r["geography"], r["class"]
            if g and cls and g not in SUPRANATIONAL and g != POPULATION_TAG:
                by_place[g].add(cls)
        classes = {c for cs in by_place.values() for c in cs}
        if len(by_place) > 1 and len(classes) > 1:
            discordant.append({
                "orpha": code,
                "name": disorders[code]["name"],
                "places": len(by_place),
                "classes": sorted(classes),
                "byPlace": {p: sorted(cs) for p, cs in sorted(by_place.items())},
            })
    # An ordered rarity axis, rarest first. Without it "the classes disagree" is a set
    # membership fact; with it, a disorder has a SPREAD measured in bands, which is what
    # makes the rows rankable and the chart a scale rather than a list of labels.
    for row in discordant:
        ranks = [CLASS_ORDER.index(c) for c in row["classes"] if c in CLASS_ORDER]
        row["spanBands"] = (max(ranks) - min(ranks) + 1) if ranks else None
        row["rarestClass"] = CLASS_ORDER[min(ranks)] if ranks else None
        row["commonestClass"] = CLASS_ORDER[max(ranks)] if ranks else None

    discordant.sort(key=lambda d: (-(d["spanBands"] or 0), -len(d["classes"]), -d["places"]))

    with_classes_multi = sum(
        1 for code in multi
        if len({r["class"] for r in disorders[code]["records"]
                if r["class"] and r["geography"] not in SUPRANATIONAL
                and r["geography"] != POPULATION_TAG}) >= 1
        and len({r["geography"] for r in disorders[code]["records"]
                 if r["class"] and r["geography"]
                 and r["geography"] not in SUPRANATIONAL
                 and r["geography"] != POPULATION_TAG}) > 1
    )

    # The full table ships, not a sample. The interface ranks and filters 386 rows and a
    # truncated `examples` list would have quietly become the population it drew from —
    # which is the selection error this whole repository is about, committed in a UI.
    discordance = {
        "comparableDisorders": with_classes_multi,
        "discordant": len(discordant),
        "share": round(len(discordant) / with_classes_multi, 4) if with_classes_multi else None,
        "rows": discordant,
        "says": (
            "For these disorders the prevalence CLASS — the band every other tab in this "
            "project collapses to a single string — takes different values in different "
            "countries. Each one is a disorder for which 'the prevalence' is a category "
            "error, and each is currently rendered with one band."
        ),
    }

    # ---- the specific-population tag ---------------------------------------------------
    specific = []
    for code, d in disorders.items():
        for r in d["records"]:
            if r["geography"] == POPULATION_TAG:
                specific.append({
                    "orpha": code, "name": d["name"],
                    "class": r["class"], "type": r["type"], "validation": r["validation"],
                })
    specific_tag = {
        "records": len(specific),
        "disorders": len({s["orpha"] for s in specific}),
        "examples": specific[:20],
        "says": (
            "'Specific population' is the entire vocabulary this catalogue has for an ethnic "
            "group, a founder community or an isolate. It is one string with no identifier, "
            "no population named, and nothing to join on. Compare the gene axis, which has "
            "HGNC, or the phenotype axis, which has HPO. The population axis has this."
        ),
    }

    payload = {
        "generated": "tools/ancestry_geography.py",
        "input": str(XML.relative_to(ROOT)).replace("\\", "/"),
        "premise": (
            "A recessive disorder's prevalence is a property of the disorder IN A POPULATION, "
            "not of the disorder. Every rare-disease number this project has published treats "
            "it as a scalar. This measures how wrong that is, and where."
        ),
        "caveat": (
            "Geography is not ancestry. A record placed in a country describes whoever was "
            "studied there, and the catalogue records nothing about ancestry, admixture or "
            "community. Nothing here is a statement about a genetic ancestry group; every "
            "number is a statement about where someone published, which is the ascertainment "
            "quantity tools/atlas_bias.py measures at +0.2357."
        ),
        "authoredConstants": {
            "populationTable": len(POPULATION_M),
            "regionTable": len(REGION_OF),
            "note": (
                "The two tables are the only authored things in this file. Round UN mid-2023 "
                "populations and standard region assignments; both checkable in one search, "
                "and changing either changes every rate below."
            ),
        },
        "classOrder": CLASS_ORDER,
        "shape": shape,
        "perCapita": per_capita,
        "countriesWithoutPopulation": sorted(unpriced, key=lambda r: -r["records"]),
        "disparity": disparity,
        "regions": regions,
        "concentration": concentration,
        "discordance": discordance,
        "specificPopulationTag": specific_tag,
    }

    DEST.mkdir(parents=True, exist_ok=True)
    dest = DEST / "ancestry_geography.json"
    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("wrote %s" % dest.relative_to(ROOT))
    print("  %d records, %d with a geography tag, %d naming a country (%d distinct)"
          % (shape["records"], shape["withGeographyTag"], shape["namedCountry"],
             shape["distinctCountries"]))
    print("  worldwide: %.1f%% of tagged records" % (100 * shape["worldwideShare"]))
    print("  disparity: %s" % disparity["says"])
    for r in regions:
        print("    %-26s %6d records  %5.1f%% of placed  vs %4.1f%% of people  ratio %.2f"
              % (r["region"], r["records"], 100 * r["recordShare"],
                 100 * r["populationShare"], r["representationRatio"]))
    print("  %d disorders placed in exactly one country, %d in more than one, %d nowhere"
          % (concentration["disordersPlacedInExactlyOneCountry"],
             concentration["disordersPlacedInMoreThanOneCountry"],
             concentration["disordersWithNoPlacedRecord"]))
    print("  %d of %d multi-country disorders disagree on the prevalence CLASS"
          % (discordance["discordant"], discordance["comparableDisorders"]))
    print("  'Specific population' tag: %d records over %d disorders"
          % (specific_tag["records"], specific_tag["disorders"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
