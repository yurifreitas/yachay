"""Ways into 18,140 genes that are not a search box.

THE PROBLEM. The navigator opens on a text field and four suggestions. That serves a reader
who already knows the symbol — and the people this project is aimed at often do not. A
curator wants every kinase. A therapy team wants the genes their cancer subgroup needs. A
clinician wants the genes whose variants nobody can interpret, because those are the reports
that come back inconclusive. None of them can type their way there.

So this builds the other index: not symbol to record, but PROPERTY to symbols. Every facet is
a measurement already on disk — nothing here is authored, and a facet with three genes in it
is published with three, because a browse surface that hides its small classes is telling the
reader the field is tidier than it is.

## The facets, and what each one is FOR

    domain        UniProt domain families, normalised. "Every protein kinase", "every
                  zinc finger" — the closest thing to browsing by molecular part.
    constraint    gnomAD LOEUF bands. The constrained tenth is where a new disease gene is
                  most likely to be hiding.
    lineage       cancer subgroups from the DepMap contrast: which genes THIS cancer needs.
    interpretation the ClinVar VUS share, banded. The top band is the set of genes whose
                  reports come back "uncertain" — the working definition of a gene the
                  clinic cannot use yet.
    breadth       how many cell types express it. A gene in three is a different target
                  from a gene in seventy-eight.
    route         how the gene breaks, when one route dominates: loss of function against
                  missense. It decides whether replacement could help.

Run after the other gene tools:  `python tools/gene_facets.py`
"""

from __future__ import annotations

import json
import pathlib
import re
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
DEST = ROOT / "web" / "public" / "data" / "gene" / "facets.json"

# A facet value with fewer than this many genes is kept but not offered as a browse entry:
# the list would be a curiosity rather than a way in. The number is stated in the payload.
MIN_MEMBERS = 8
# How many symbols to ship per facet value. Enough to render a page of results; the full
# count is always reported so the reader knows what they are seeing a slice of.
MAX_MEMBERS = 300

# Domain names carry qualifiers that split one family into forty near-duplicates:
# "Protein kinase 1", "Protein kinase; degenerate", "EGF-like 3". Stripping the trailing
# ordinal and the qualifier after a semicolon is the whole normalisation, and it is
# deliberately crude — a real domain ontology is InterPro, which is not on disk.
TRAILING_ORDINAL = re.compile(r"\s+\d+$")


def normalise_domain(label: str) -> str:
    name = label.split(";")[0].strip()
    name = TRAILING_ORDINAL.sub("", name).strip()
    return name


def band_loeuf(v: float | None) -> str | None:
    if v is None:
        return None
    if v < 0.35:
        return "constrained"
    if v < 1.0:
        return "middling"
    return "tolerant"


def band_vus(share: float, total: int) -> str | None:
    # Under twenty variants the share is noise; the interpretation facet would otherwise be
    # dominated by genes with two reports and one of them uncertain.
    if total < 20:
        return None
    if share >= 0.8:
        return "mostly uninterpretable"
    if share >= 0.5:
        return "half uninterpretable"
    if share >= 0.2:
        return "partly interpreted"
    return "largely interpreted"


def band_breadth(types: int, total: int) -> str:
    frac = types / max(1, total)
    if frac < 0.15:
        return "narrow"
    if frac < 0.6:
        return "regional"
    return "everywhere"


def main() -> int:
    index_path = OUT / "gene_index.json"
    if not index_path.exists():
        print("out/gene_index.json absent — run tools/gene_index.py first")
        return 1

    index = json.loads(index_path.read_text(encoding="utf-8"))
    world = json.loads((OUT / "gene_world.json").read_text(encoding="utf-8")) \
        if (OUT / "gene_world.json").exists() else {"genes": {}, "scope": {}}
    geo = json.loads((OUT / "gene_geometry.json").read_text(encoding="utf-8")) \
        if (OUT / "gene_geometry.json").exists() else {"genes": {}}
    dom = json.loads((OUT / "gene_domains.json").read_text(encoding="utf-8")) \
        if (OUT / "gene_domains.json").exists() else {"genes": {}}

    cell_types = (world.get("scope", {}).get("expression", {}) or {}).get("cellTypes", 1)

    facets: dict[str, dict[str, list[str]]] = {
        k: defaultdict(list)
        for k in ("domain", "constraint", "lineage", "interpretation", "breadth", "route")
    }

    for sym, rec in index["genes"].items():
        w = world["genes"].get(sym, {})
        g = geo["genes"].get(sym, {})
        d = dom["genes"].get(sym, {})

        # --- molecular parts -------------------------------------------------------------
        seen: set[str] = set()
        for f in d.get("features", []):
            if f.get("kind") != "domain" or not f.get("label"):
                continue
            name = normalise_domain(f["label"])
            if name and name not in seen:
                seen.add(name)
                facets["domain"][name].append(sym)

        # --- how badly it breaks ---------------------------------------------------------
        band = band_loeuf((w.get("con") or {}).get("loeuf"))
        if band:
            facets["constraint"][band].append(sym)

        # --- which cancers need it -------------------------------------------------------
        for hit in rec.get("cancer", []) or []:
            if hit.get("level") == "lineage" and hit.get("subgroup"):
                facets["lineage"][hit["subgroup"]].append(sym)

        # --- can its variants be read ----------------------------------------------------
        clin = w.get("clin")
        if clin:
            b = band_vus(clin.get("vusShare", 0.0), clin.get("total", 0))
            if b:
                facets["interpretation"][b].append(sym)

        # --- where it acts ---------------------------------------------------------------
        exp = w.get("exp")
        if exp:
            facets["breadth"][band_breadth(exp.get("typesAbove", 0), cell_types)].append(sym)

        # --- how it breaks, when one route dominates -------------------------------------
        cons = g.get("consequence") or {}
        total = sum(cons.values())
        if total >= 20:
            lof = cons.get("stopGained", 0) + cons.get("frameshift", 0) + cons.get("splice", 0)
            mis = cons.get("missense", 0)
            if lof / total >= 0.5:
                facets["route"]["mostly loss of function"].append(sym)
            elif mis / total >= 0.6:
                facets["route"]["mostly missense"].append(sym)

    out: dict[str, dict] = {}
    for kind, values in facets.items():
        rows = []
        for value, syms in values.items():
            if len(syms) < MIN_MEMBERS:
                continue
            rows.append({
                "value": value,
                "count": len(syms),
                "genes": sorted(syms)[:MAX_MEMBERS],
            })
        rows.sort(key=lambda r: -r["count"])
        out[kind] = {
            "values": rows,
            "distinct": len(values),
            "offered": len(rows),
            "belowFloor": len(values) - len(rows),
        }

    payload = {
        "generated": "tools/gene_facets.py",
        "premise": (
            "The other index: property to symbols, not symbol to record. A search box serves "
            "a reader who already knows the symbol, and the people this is aimed at often do "
            "not — a curator wants every kinase, a clinician wants the genes whose reports "
            "come back uncertain."
        ),
        "minMembers": MIN_MEMBERS,
        "maxMembers": MAX_MEMBERS,
        "facets": out,
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    size = DEST.stat().st_size / 1024
    print(f"wrote {DEST.relative_to(ROOT)}  ({size:,.0f} kB)\n")
    for kind, block in out.items():
        top = block["values"][0] if block["values"] else None
        print(f"  {kind:<15} {block['offered']:>4} offered of {block['distinct']:>5} distinct"
              f"   {('largest: ' + top['value'][:34] + f' ({top['count']})') if top else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
