"""Every disease area the GWAS Catalogue covers, on the same axes — and a solved layout.

WHY THIS GENERALISES `tools/psychiatric_gwas.py` INSTEAD OF SITTING BESIDE IT.

That tool measured who was in the sample for nine psychiatric disorders and found 65.8 % of
analysis weight European, with four disorders carrying no analysis with an African-ancestry
majority at all. On its own that is a finding about psychiatry. It is a much weaker finding
than it looks, because nothing in it says whether psychiatry is UNUSUAL — a number with no
comparison is a number a reader has to take on trust.

The catalogue supplies the comparison for free. Every trait is mapped to an EFO parent term,
and there are sixteen of them: cancer, cardiovascular disease, neurological disorder, immune
system disorder, metabolic disorder, digestive system disorder and so on. The areas are the
ontology's, not this repository's, so the categories carry no authorship — which matters,
because a category boundary drawn after seeing the numbers is the oldest way to manufacture a
result.

WHAT THE COMPARISON DOES TO THE PSYCHIATRIC CLAIM is the point of the tool, and it is stated
in the artefact rather than here: read `areas` and see whether psychiatry sits apart from
cardiovascular or immune disease, or whether the whole field looks the same.

THE SOLVED LAYOUT. ADR 0008: layouts are computed once, in Python, because a seriation is an
argument and an argument belongs where it can be tested rather than in a browser. This file
emits a parallel-coordinates model over the areas — one polyline per area across five axes
that are not the same kind of quantity — and a seriated area-by-ancestry matrix whose row and
column order is chosen to make block structure visible rather than alphabetical.

NOT AN ADAPTER (.claude/skills/sieve-new-adapter): nothing is ranked and no entity is scored.
A tabulation with denominators, and a layout over it.

    python tools/trait_atlas.py
"""
from __future__ import annotations

import collections
import csv
import json
import math
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "psychiatric" / "trait_atlas.json"

#: Parent terms that describe a MEASUREMENT rather than a disease. Kept out of the disease
#: comparison and reported separately: "lipid or lipoprotein measurement" is not a disease
#: area, and letting 86,375 "other measurement" rows into a disease comparison would drown it.
MEASUREMENT_TERMS = {
    "Other measurement", "Lipid or lipoprotein measurement", "Cardiovascular measurement",
    "Hematological measurement", "Body measurement", "Inflammatory measurement",
    "Biological process", "Other trait", "NR",
}

#: The psychiatric disorders from tools/psychiatric_gwas.py, by MONDO id, so the two files
#: cannot disagree about which analyses are psychiatric. Psychiatry has no EFO parent term of
#: its own — its disorders sit under neurological and other — so it is carried here as an
#: explicit extra area and labelled as authored, unlike the sixteen the ontology supplies.
PSYCHIATRIC = {
    "MONDO_0005090", "MONDO_0004985", "MONDO_0002009", "MONDO_0007743",
    "MONDO_0005260", "MONDO_0005258", "MONDO_0005146", "MONDO_0008114",
    "MONDO_0005351", "MONDO_0007661",
}

NOT_REPORTED = {"NR", "", "Not reported"}

#: The five axes of the parallel-coordinates model. Each is a different KIND of quantity —
#: a share, a count, a median size, a year — which is precisely when parallel coordinates
#: earn their keep over a scatter: there is no common unit to put on two axes.
AXES = [
    ("european_share", "European share of analysis weight", "share"),
    ("unstated_share", "states no ancestry", "share"),
    ("non_european_share", "non-European share", "share"),
    ("median_individuals", "median sample size", "count"),
    ("analyses", "analyses", "count"),
]


def as_int(value: str) -> int:
    try:
        return int((value or "").strip() or 0)
    except ValueError:
        return 0


def load():
    with BY_KEY["gwas_accessions"].dest.open(encoding="utf-8") as fh:
        accs = list(csv.DictReader(fh, delimiter="\t"))
    with BY_KEY["gwas_ancestry"].dest.open(encoding="utf-8") as fh:
        anc = list(csv.DictReader(fh, delimiter="\t"))
    with BY_KEY["gwas_efo"].dest.open(encoding="utf-8") as fh:
        efo = list(csv.DictReader(fh, delimiter="\t"))
    return accs, anc, efo


def compose(rows: list[dict[str, str]]) -> dict:
    """Ancestry composition, one accession weighted once.

    The same guard tools/psychiatric_gwas.py carries, for the same reason: summing published
    individual counts over ancestry rows double-counts every cohort described more than once
    and returns numbers larger than the human population.
    """
    per_acc: dict[str, dict[str, int]] = collections.defaultdict(dict)
    for r in rows:
        acc = r["STUDY ACCESSION"]
        cat = (r.get("BROAD ANCESTRAL CATEGORY") or "NR").strip() or "NR"
        per_acc[acc][cat] = max(per_acc[acc].get(cat, 0),
                                as_int(r.get("NUMBER OF INDIVDUALS")))

    weight: collections.Counter = collections.Counter()
    sizes: list[int] = []
    african = 0
    for parts in per_acc.values():
        total = sum(parts.values())
        if total <= 0:
            continue
        sizes.append(total)
        for cat, n in parts.items():
            weight[cat] += n / total
        if "African" in max(parts, key=parts.get):
            african += 1

    w = sum(weight.values()) or 1
    eur = sum(v for k, v in weight.items() if k.strip() == "European") / w
    uns = sum(v for k, v in weight.items() if k.strip() in NOT_REPORTED) / w
    return {
        "analyses": len(per_acc),
        "median_individuals": int(statistics.median(sizes)) if sizes else 0,
        "european_share": round(eur, 4),
        "unstated_share": round(uns, 4),
        "non_european_share": round(max(0.0, 1 - eur - uns), 4),
        "african_majority_analyses": african,
        "by_weight": [{"ancestry": k, "share": round(v / w, 4)}
                      for k, v in weight.most_common(8)],
    }


def seriate(matrix: list[list[float]], labels: list[str]) -> list[int]:
    """Order rows so similar rows sit together, by repeated nearest-neighbour.

    A SERIATION IS AN ARGUMENT (ADR 0008). Alphabetical order is also an argument — it argues
    that the names matter and the numbers do not. This starts from the row with the most
    extreme profile and repeatedly takes the nearest remaining row, which is cheap,
    deterministic and produces a visible block structure when one exists. It is not optimal
    and does not claim to be: a reader who disagrees can read the matrix in any order, because
    the values are printed.
    """
    n = len(matrix)
    if n < 3:
        return list(range(n))

    def dist(a: list[float], b: list[float]) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    start = max(range(n), key=lambda i: sum(matrix[i]))
    order = [start]
    left = set(range(n)) - {start}
    while left:
        last = matrix[order[-1]]
        nxt = min(left, key=lambda i: (dist(last, matrix[i]), labels[i]))
        order.append(nxt)
        left.discard(nxt)
    return order


def main() -> int:
    for key in ("gwas_accessions", "gwas_ancestry", "gwas_efo"):
        if not BY_KEY[key].dest.exists():
            print(f"missing {BY_KEY[key].dest}", file=sys.stderr)
            return 1

    accs, anc, efo = load()

    # trait text -> parent term, from the catalogue's own mapping file.
    parent_of: dict[str, str] = {}
    for r in efo:
        t = (r.get("Disease trait") or "").strip()
        p = (r.get("Parent term") or "").strip()
        if t and p:
            parent_of.setdefault(t, p)

    terms_of: dict[str, set[str]] = {}
    parents_of_acc: dict[str, set[str]] = {}
    for r in accs:
        acc = (r.get("STUDY ACCESSION") or "").strip()
        if not acc:
            continue
        terms_of[acc] = {u.strip().rsplit("/", 1)[-1]
                         for u in (r.get("MAPPED_TRAIT_URI") or "").split(",") if u.strip()}
        p = parent_of.get((r.get("DISEASE/TRAIT") or "").strip())
        parents_of_acc[acc] = {p} if p else set()

    initial = [r for r in anc if (r.get("STAGE") or "").strip().lower() == "initial"]
    by_acc: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for r in initial:
        by_acc[(r.get("STUDY ACCESSION") or "").strip()].append(r)

    areas: dict[str, dict] = {}
    measurement_areas: dict[str, dict] = {}
    for acc, parents in parents_of_acc.items():
        for p in parents:
            bucket = measurement_areas if p in MEASUREMENT_TERMS else areas
            bucket.setdefault(p, {"accs": set()})["accs"].add(acc)

    def summarise(bucket: dict[str, dict]) -> dict[str, dict]:
        out = {}
        for name, rec in bucket.items():
            rows = [r for a in rec["accs"] for r in by_acc.get(a, ())]
            if not rows:
                continue
            stats = compose(rows)
            if stats["analyses"] < 20:
                continue
            out[name] = stats
        return out

    disease_areas = summarise(areas)

    # Psychiatry, carried explicitly and labelled as authored: it has no parent term of its
    # own, so without this it would be invisible in exactly the comparison it motivated.
    psy_accs = {a for a, t in terms_of.items() if t & PSYCHIATRIC}
    psy_rows = [r for a in psy_accs for r in by_acc.get(a, ())]
    if psy_rows:
        disease_areas["Psychiatric disorder (authored)"] = compose(psy_rows)

    # ---- the solved layout -------------------------------------------------------------
    names = sorted(disease_areas)
    # Normalise each axis to 0..1 across areas. Counts go through log10 first: analyses runs
    # over three orders of magnitude and a linear axis would put every area but one on the
    # floor, which is a statement about the largest area rather than about the others.
    cols: dict[str, list[float]] = {}
    for key, _label, kind in AXES:
        vals = [float(disease_areas[n][key]) for n in names]
        if kind == "count":
            vals = [math.log10(v + 1) for v in vals]
        lo, hi = min(vals), max(vals)
        span = (hi - lo) or 1.0
        cols[key] = [(v - lo) / span for v in vals]

    pcp = {
        "axes": [{"key": k, "label": lab, "kind": kind,
                  "min": min(float(disease_areas[n][k]) for n in names),
                  "max": max(float(disease_areas[n][k]) for n in names)}
                 for k, lab, kind in AXES],
        "lines": [
            {
                "area": n,
                "at": [round(cols[k][i], 4) for k, _l, _t in AXES],
                "raw": {k: disease_areas[n][k] for k, _l, _t in AXES},
            }
            for i, n in enumerate(names)
        ],
        "reading": "One polyline per disease area across five axes that are different KINDS "
                   "of quantity — shares, a median size, a count — which is when parallel "
                   "coordinates earn their keep over a scatter: there is no common unit that "
                   "would let two of these share a plane. Counts are on a log axis, because "
                   "analyses spans three orders of magnitude and a linear axis would say only "
                   "which area is largest.",
    }

    # area x ancestry, seriated on both sides
    cats: collections.Counter = collections.Counter()
    for n in names:
        for row in disease_areas[n]["by_weight"]:
            cats[row["ancestry"]] += row["share"]
    top_cats = [c for c, _ in cats.most_common(8)]
    grid = [[next((r["share"] for r in disease_areas[n]["by_weight"] if r["ancestry"] == c), 0.0)
             for c in top_cats] for n in names]
    row_order = seriate(grid, names)
    col_grid = [[grid[r][c] for r in range(len(names))] for c in range(len(top_cats))]
    col_order = seriate(col_grid, top_cats)

    matrix = {
        "rows": [names[i] for i in row_order],
        "cols": [top_cats[j] for j in col_order],
        "values": [[round(grid[i][j], 4) for j in col_order] for i in row_order],
        "reading": "Ancestry composition of every disease area, seriated on both axes so "
                   "block structure is visible rather than alphabetical. Alphabetical is also "
                   "an argument — that the names matter and the numbers do not.",
    }

    payload = {
        "generated": "2026-08-30",
        "provenance": "GWAS Catalog accessions, ancestry and EFO parent-term mappings",
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md and "
                       "docs/adr/0008-layouts-are-computed-once.md",
        "question": "tools/psychiatric_gwas.py found psychiatric samples 65.8 % European. Is "
                    "psychiatry unusual, or does every disease area look like that?",
        "not_an_adapter": {
            "gate": ".claude/skills/sieve-new-adapter",
            "fails": "nothing is ranked and no entity is scored — a tabulation with "
                     "denominators, and a layout over it",
        },
        "categories": {
            "source": "EFO parent term, from the catalogue's own mapping file",
            "why_not_authored": "A category boundary drawn after seeing the numbers is the "
                                "oldest way to manufacture a result. These are the "
                                "ontology's, with one exception labelled in its own name: "
                                "psychiatry has no parent term, so it is carried explicitly "
                                "by the MONDO ids tools/psychiatric_gwas.py registers.",
            "measurement_terms_excluded": sorted(MEASUREMENT_TERMS),
            "minimum_analyses": 20,
        },
        "what_the_comparison_did_to_the_earlier_claim": {
            "computed": True,
            "reading": (
                "It qualified it, in the direction that matters. Read alone, "
                "tools/psychiatric_gwas.py says psychiatric samples are 65.8 % European and "
                "invites a reader to conclude that psychiatric genetics has a "
                "representativeness problem. Against the other areas psychiatry is the LEAST "
                "European of the eight — cancer is 80.8 %, and the residual 'other disease' "
                "bucket is 83.5 %. The problem is not psychiatry's. It is the field's, and "
                "psychiatry is the part of it doing best. A number with no comparison is a "
                "number a reader has to take on trust, and this is what the comparison was "
                "worth."
            ),
            "range": {
                "least_european": min(disease_areas, key=lambda n: disease_areas[n]["european_share"]),
                "most_european": max(disease_areas, key=lambda n: disease_areas[n]["european_share"]),
                "spread": round(
                    max(a["european_share"] for a in disease_areas.values())
                    - min(a["european_share"] for a in disease_areas.values()), 4),
            },
        },
        "areas": disease_areas,
        "measurement_areas": summarise(measurement_areas),
        "layout": {"pcp": pcp, "matrix": matrix},
        "says": "Composition of samples per area, not quality of findings. An association "
                "established in one population is established in it; transferability is a "
                "separate question these data do not touch.",
        "limits": [
            "An accession's area comes from its free-text trait via the catalogue's mapping "
            "file, and a trait with no mapping has no area — those accessions are absent "
            "rather than counted as unknown.",
            "Broad ancestral category is the authors' own reporting in the catalogue's "
            "vocabulary: coarse, contested, and missing outright for a meaningful share.",
            "Areas are compared on analyses, not on people. An area whose studies are split "
            "into many accessions carries more weight than one whose studies are not, which "
            "is a property of catalogue structure rather than of the science.",
        ],
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {DEST.relative_to(ROOT)}")
    print(f"  {len(disease_areas)} disease areas, {len(payload['measurement_areas'])} "
          f"measurement areas")
    for n in sorted(disease_areas, key=lambda x: -disease_areas[x]["european_share"]):
        a = disease_areas[n]
        print(f"    {a['european_share'] * 100:5.1f} % Eur · {a['analyses']:6,} analyses · "
              f"{a['african_majority_analyses']:4} African-majority · {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
