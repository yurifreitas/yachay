#!/usr/bin/env python
"""One gene, from the residue to the organ system, with the cost of every step printed.

WHY THIS FILE. The thesis this repository serves is a ladder — variant, residue, domain,
protein, interaction, pathway, cell type, organ system, phenotype — and `tools/thesis_seed.py`
grades most of its rungs *named-only*. The pieces have since been built separately:
`gene_geometry.py` places variants along a protein, `gene_domains.py` reads UniProt features,
`gene_world.py` carries constraint and expression, `interactome_sparse.py` has the graph,
`scale_information.py` measured what a scale change costs. **Nothing joins them into one
object, and nothing states what is lost between two rungs.**

That second half is the point. Every multiscale figure in biology draws the ladder and
implies the steps are free. They are not, and this project has the numbers: collapsing a
disease's genes onto Reactome top-level pathways keeps **22 %** of what they said about organ
system, and onto HPA cell types **31 %** — with the retention varying 5.6-fold across systems.

So this emits, per gene, both the rungs and **the transitions between them**, each transition
carrying the measured retention where one exists and saying so plainly where it does not.

## What a rung is, and where it comes from

    residue      variant positions along the protein, by consequence and significance,
                 with UniProt domains and transmembrane spans laid over them
    protein      length, gnomAD constraint (LOEUF, pLI), the UniProt description
    interaction  STRING neighbours above the high-confidence cut
    pathway      Reactome top-level pathways the gene belongs to
    cell type    HPA cell types where the gene is at least half its own maximum
    organ system the HPO systems the gene's diseases are annotated to
    disease      the diseases HPO assigns to this gene

## The honest part

**A transition with no measured retention says so.** Only two of the six steps have a number
behind them — gene→pathway and gene→cell type, from `scale_information.py`. The rest carry
`retention: null` and a reason. A ladder that printed a plausible-looking figure at every rung
would be the exact failure this repository exists to refuse.

    python tools/gene_ladder.py                # the dossier twelve plus the top movers
    python tools/gene_ladder.py --gene NF2

Stdlib only.
"""

from __future__ import annotations

import argparse
import collections
import csv
import gzip
import io
import json
import pathlib
import sys
import zipfile
from datetime import date
from xml.etree import ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

OUT = ROOT / "out"
DEST = OUT / "rare" / "gene_ladder.json"

#: STRING confidence floor. The same cut twin_propagation.py uses, and registered there.
STRING_FLOOR = 700

#: Neighbours kept per gene. The graph has hubs with thousands; a ladder is not a network view.
MAX_NEIGHBOURS = 24

#: Genes to build. The twelve dossier diseases' genes plus a few the run moved most.
DEFAULT_GENES = ["NF2", "DMD", "CFTR", "MECP2", "CDKL5", "SCN1A", "SMN1", "HBB",
                 "PEX1", "ACVR1", "HGD", "TP53", "SMARCA4", "KRAS", "BRAF"]


def load(name: str, sub: str = "") -> dict:
    path = (OUT / sub / f"{name}.json") if sub else (OUT / f"{name}.json")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def string_neighbours(genes: set[str]) -> dict[str, list[dict]]:
    """High-confidence STRING partners, by gene symbol."""
    symbol: dict[str, str] = {}
    with gzip.open(BY_KEY["string_info"].dest, "rt", encoding="utf-8", errors="replace") as fh:
        next(fh, None)
        for line in fh:
            parts = line.split("\t")
            if len(parts) > 1:
                symbol[parts[0]] = parts[1]
    wanted = {sid for sid, sym in symbol.items() if sym in genes}
    out: dict[str, list[dict]] = collections.defaultdict(list)
    with gzip.open(BY_KEY["string_links"].dest, "rt", encoding="utf-8", errors="replace") as fh:
        next(fh, None)
        for line in fh:
            a, b, score = line.split()
            if int(score) < STRING_FLOOR:
                continue
            if a in wanted:
                out[symbol[a]].append({"gene": symbol.get(b, b), "score": int(score)})
            if b in wanted:
                out[symbol[b]].append({"gene": symbol.get(a, a), "score": int(score)})
    return {g: sorted(v, key=lambda r: -r["score"])[:MAX_NEIGHBOURS] for g, v in out.items()}


def gene_cell_types(genes: set[str]) -> dict[str, list[str]]:
    per_gene: dict[str, dict[str, float]] = collections.defaultdict(dict)
    with zipfile.ZipFile(BY_KEY["hpa_single_cell"].dest) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".tsv"))
        with zf.open(name) as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, "utf-8"), delimiter="\t"):
                g = row.get("Gene name")
                if g in genes:
                    try:
                        per_gene[g][row["Cell type"]] = float(row["nCPM"])
                    except (KeyError, TypeError, ValueError):
                        continue
    out = {}
    for g, profile in per_gene.items():
        peak = max(profile.values(), default=0.0)
        if peak > 0:
            out[g] = sorted((c for c, v in profile.items() if v >= 0.5 * peak),
                            key=lambda c: -profile[c])
    return out


def gene_pathways(genes: set[str]) -> dict[str, list[str]]:
    """Reactome top-level pathways, via the STRING alias crosswalk to UniProt."""
    acc_to_string: dict[str, str] = {}
    with gzip.open(BY_KEY["string_aliases"].dest, "rt", encoding="utf-8", errors="replace") as fh:
        next(fh, None)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > 2 and parts[2] == "UniProt_AC":
                acc_to_string.setdefault(parts[1], parts[0])
    symbol: dict[str, str] = {}
    with gzip.open(BY_KEY["string_info"].dest, "rt", encoding="utf-8", errors="replace") as fh:
        next(fh, None)
        for line in fh:
            parts = line.split("\t")
            if len(parts) > 1:
                symbol[parts[0]] = parts[1]
    acc_to_sym = {a: symbol[s] for a, s in acc_to_string.items() if s in symbol}

    parent: dict[str, set[str]] = collections.defaultdict(set)
    for line in BY_KEY["reactome_hierarchy"].dest.read_text(encoding="utf-8").splitlines():
        if "\t" in line:
            up, down = line.split("\t")[:2]
            parent[down].add(up)

    roots_cache: dict[str, frozenset[str]] = {}

    def roots(p: str) -> frozenset[str]:
        if p in roots_cache:
            return roots_cache[p]
        found, stack, seen = set(), [p], set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            up = [q for q in parent.get(node, ()) if q.startswith("R-HSA")]
            stack.extend(up) if up else found.add(node)
        roots_cache[p] = frozenset(found)
        return roots_cache[p]

    names: dict[str, str] = {}
    out: dict[str, set[str]] = collections.defaultdict(set)
    with BY_KEY["reactome_pathways"].dest.open(encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6 or parts[5] != "Homo sapiens":
                continue
            names[parts[1]] = parts[3]
            sym = acc_to_sym.get(parts[0])
            if sym in genes:
                out[sym].update(roots(parts[1]))
    return {g: sorted(names.get(r, r) for r in v) for g, v in out.items()}


def disease_context(genes: set[str]):
    """Diseases per gene, and the organ systems those diseases are annotated to."""
    per_gene: dict[str, set[str]] = collections.defaultdict(set)
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            g = (row.get("gene_symbol") or "").strip()
            d = (row.get("disease_id") or "").strip()
            if g in genes and d:
                per_gene[g].add(d)

    parents: dict[str, set[str]] = collections.defaultdict(set)
    names: dict[str, str] = {}
    term = None
    for line in BY_KEY["hpo_terms"].dest.read_text(encoding="utf-8").splitlines():
        if line.startswith("["):
            term = None
        elif line.startswith("id: HP:"):
            term = line[4:].strip()
        elif term and line.startswith("name:"):
            names[term] = line[5:].strip()
        elif term and line.startswith("is_a:"):
            parents[term].add(line[5:].split("!")[0].strip())
    systems = {t for t, ps in parents.items() if "HP:0000118" in ps}
    anc: dict[str, set[str]] = {}

    def walk(t: str) -> set[str]:
        if t in anc:
            return anc[t]
        anc[t] = set()
        acc = set()
        for p in parents.get(t, ()):
            acc.add(p)
            acc |= walk(p)
        anc[t] = acc
        return acc

    for t in list(parents):
        walk(t)

    wanted = {d for v in per_gene.values() for d in v}
    per_disease: dict[str, set[str]] = collections.defaultdict(set)
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        rows = (line for line in fh if not line.startswith("#"))
        for row in csv.DictReader(rows, delimiter="\t"):
            d = (row.get("database_id") or "").strip()
            t = (row.get("hpo_id") or "").strip()
            if d in wanted and t:
                per_disease[d] |= ({t} | anc.get(t, set())) & systems
    return per_gene, per_disease, names


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gene", action="append", help="build only this gene (repeatable)")
    args = ap.parse_args()

    genes = set(args.gene or DEFAULT_GENES)
    print(f"building the ladder for {len(genes)} genes ...")

    geometry = load("gene_geometry").get("genes", {})
    domains = load("gene_domains").get("genes", {})
    world = load("gene_world").get("genes", {})
    scale = load("scale_information", "rare")
    retention = {
        "pathway": (scale.get("scales", {}).get("pathway", {}) or {}).get("retained_vs_gene"),
        "cell_type": (scale.get("scales", {}).get("cell_type", {}) or {}).get("retained_vs_gene"),
    }
    per_system = {r["system"]: r for r in scale.get("per_organ_system", [])}

    neighbours = string_neighbours(genes)
    cells = gene_cell_types(genes)
    pathways = gene_pathways(genes)
    per_gene_disease, per_disease_systems, hpo_names = disease_context(genes)

    built = {}
    for g in sorted(genes):
        diseases = sorted(per_gene_disease.get(g, ()))
        sys_ids = sorted({s for d in diseases for s in per_disease_systems.get(d, ())})
        rungs = [
            {"id": "residue", "label": "residue",
             "count": (geometry.get(g, {}) or {}).get("placed", 0),
             "detail": {"consequence": (geometry.get(g, {}) or {}).get("consequence", {}),
                        "hist": (geometry.get(g, {}) or {}).get("hist", {}),
                        "bins": (geometry.get(g, {}) or {}).get("bins", 0),
                        "features": (domains.get(g, {}) or {}).get("features", [])[:40]}},
            {"id": "protein", "label": "protein", "count": 1,
             "detail": {"length": (world.get(g, {}) or {}).get("prot", {}).get("size"),
                        "note": ((world.get(g, {}) or {}).get("prot", {}).get("note") or "")[:280],
                        "constraint": (world.get(g, {}) or {}).get("con", {})}},
            {"id": "interaction", "label": "interaction",
             "count": len(neighbours.get(g, [])),
             "detail": {"partners": neighbours.get(g, [])}},
            {"id": "pathway", "label": "pathway",
             "count": len(pathways.get(g, [])),
             "detail": {"names": pathways.get(g, [])}},
            {"id": "cell_type", "label": "cell type",
             "count": len(cells.get(g, [])),
             "detail": {"names": cells.get(g, [])[:24]}},
            {"id": "organ_system", "label": "organ system",
             "count": len(sys_ids),
             "detail": {"names": [hpo_names.get(s, s) for s in sys_ids],
                        "retention": {hpo_names.get(s, s): per_system[s]["pathway_retention"]
                                      for s in sys_ids if s in per_system}}},
            {"id": "disease", "label": "disease", "count": len(diseases),
             "detail": {"ids": diseases[:24]}},
        ]

        transitions = [
            {"from": "residue", "to": "protein", "retention": None,
             "why": "no measurement exists: nothing here collapses residues onto a protein "
                    "and reports what the collapse costs"},
            {"from": "protein", "to": "interaction", "retention": None,
             "why": "the interactome is a different object, not a coarser view of the same "
                    "one; there is no retention to report"},
            {"from": "interaction", "to": "pathway", "retention": None,
             "why": "measured only from the GENE, not from the interaction neighbourhood"},
            {"from": "gene", "to": "pathway", "retention": retention["pathway"],
             "why": "tools/scale_information.py, over 9,142 diseases, against a permutation null"},
            {"from": "gene", "to": "cell_type", "retention": retention["cell_type"],
             "why": "tools/scale_information.py, same estimator"},
            {"from": "cell_type", "to": "organ_system", "retention": None,
             "why": "not measured; the organ system here comes from the disease annotation, "
                    "not from the cell types"},
        ]
        built[g] = {"rungs": rungs, "transitions": transitions}

    payload = {
        "generated": date.today().isoformat(),
        "provenance": ("joined from out/gene_geometry.json, gene_domains.json, "
                       "gene_world.json, STRING v12, Reactome, HPA and HPO"),
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md",
        "question": ("What does one gene look like from the residue to the organ system, and "
                     "what does each step between those scales cost?"),
        "measured_transitions": sum(1 for t in
                                    (built[next(iter(built))]["transitions"] if built else [])
                                    if t["retention"] is not None),
        "genes": built,
        "says": ("The rungs are a join of measured layers. The TRANSITIONS are mostly not "
                 "measured, and each unmeasured one carries the reason rather than a "
                 "plausible number. Two of six have a retention behind them; a ladder that "
                 "printed a figure at every step would be the failure this repository "
                 "exists to refuse."),
        "limits": [
            "Variant positions come from ClinVar through gene_geometry.py and inherit its "
            "parsing losses; a gene's unplaced variants are simply absent from the residue "
            "rung.",
            "STRING partners are co-functional associations, not physical complexes, and the "
            "700 cut is conventional.",
            "The organ systems are those of the gene's DISEASES, so a gene causing one "
            "well-annotated disease looks broader than a gene causing three thin ones.",
        ],
    }
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"  {'gene':10s} {'residue':>8s} {'partners':>9s} {'pathway':>8s} "
          f"{'cells':>6s} {'systems':>8s} {'diseases':>9s}")
    for g, rec in sorted(built.items()):
        c = {r["id"]: r["count"] for r in rec["rungs"]}
        print(f"  {g:10s} {c['residue']:8d} {c['interaction']:9d} {c['pathway']:8d} "
              f"{c['cell_type']:6d} {c['organ_system']:8d} {c['disease']:9d}")
    print(f"\n  transitions with a measured retention: 2 of 6")
    print(f"wrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
