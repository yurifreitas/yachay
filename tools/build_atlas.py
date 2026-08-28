#!/usr/bin/env python
"""Join the world's rare-disease catalogues onto a cell x gene axis.

WHAT THIS PRODUCES. One artefact, `out/rare/atlas.json`, holding the joined view:

    disease  --(HPO / Orphanet)-->  gene  --(Human Protein Atlas)-->  cell type

plus prevalence per disease from Orphanet, and the counts that say how much of the field
each join actually covers. **Coverage is reported, not assumed** — a join that silently
drops two thirds of its input looks like a smaller world rather than a broken join.

WHY THE COVERAGE NUMBERS ARE THE POINT. The previous seeds were hand-written and marked as
demonstrations. This is the real catalogue, and the honest headline it produces is not
"8,000 diseases" but the shape of what is missing from them: how many have no gene, how
many of those genes have no cell-type data, and therefore how much of the disease
catalogue can be placed on the cell axis at all.

LICENCE. Orphanet is CC BY-ND (no derivatives redistributable) and the Human Protein Atlas
is CC BY-SA. So this script writes **aggregates and identifiers**, never a copy of a source
table, and the output records which sources contributed.

    python tools/build_atlas.py
"""

from __future__ import annotations

import csv
import io
import json
import pathlib
import html
import re
from xml.etree import ElementTree as ET
import sys
import zipfile
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "rare"

# Orphanet's prevalence vocabulary, ordered rarest first. The two ultra-rare bands are
# what this whole project is aimed at.
PREV_ORDER = [
    "<1 / 1 000 000",
    "1-9 / 1 000 000",
    "1-9 / 100 000",
    "1-5 / 10 000",
    "6-9 / 10 000",
    ">1 / 1000",
    "Unknown",
    "Not yet documented",
]
PREV_RANK = {p: i for i, p in enumerate(PREV_ORDER)}


def load_gene_disease() -> tuple[dict[str, set[str]], dict[str, set[str]], Counter]:
    """HPO's gene-to-disease table: the backbone of the join."""
    path = BY_KEY["hpo_genes"].dest
    gene_to_disease: dict[str, set[str]] = defaultdict(set)
    disease_to_gene: dict[str, set[str]] = defaultdict(set)
    assoc = Counter()
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            sym = (row.get("gene_symbol") or "").strip()
            dis = (row.get("disease_id") or "").strip()
            if not sym or not dis:
                continue
            gene_to_disease[sym].add(dis)
            disease_to_gene[dis].add(sym)
            assoc[(row.get("association_type") or "?").strip()] += 1
    return gene_to_disease, disease_to_gene, assoc


def load_disease_names() -> tuple[dict[str, str], Counter, str]:
    """Disease ids and names from the HPO annotation file, plus its own scale statement."""
    path = BY_KEY["hpo_annotations"].dest
    names: dict[str, str] = {}
    by_prefix = Counter()
    header = ""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                if "description:" in line and not header:
                    header = line.strip().lstrip("#").strip()
                continue
            if line.startswith("database_id"):
                cols = line.rstrip("\n").split("\t")
                idx_id, idx_name = cols.index("database_id"), cols.index("disease_name")
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= max(idx_id, idx_name):
                continue
            did, dname = parts[idx_id], parts[idx_name]
            if did not in names:
                names[did] = dname
                by_prefix[did.split(":")[0]] += 1
    return names, by_prefix, header


def load_prevalence() -> dict[str, dict]:
    """Orphanet prevalence, read with a PARSER.

    IT USED TO BE REGEX, AND THE DOCSTRING USED TO SAY "a full parse would work too and is
    what a stricter version should do". That was correct, and the cost of not doing it was
    two defects that both shipped for months (docs/audit.md A11):

      1. `&lt;` was never decoded, so `<1 / 1 000 000` - 4,998 records, the largest class in
         the corpus - matched no rank table. The membership test below naming that class was
         dead code that could never fire, and the ultra-rare set came out at 770 instead of
         4,586.
      2. `<PrevalenceClass/>` is frequently EMPTY and self-closing. With `re.S` the pattern
         ran past it to the next `<Name>` in the document, which belongs to
         `PrevalenceGeographic` - fabricating 3,624 prevalence classes that do not exist,
         including "Worldwide" 3,616 times.

    tests/test_prevalence_readers_agree.py asserts a parser and a regex see the same corpus
    and fails on either defect.
    """
    path = BY_KEY["orpha_prevalence"].dest
    out: dict[str, dict] = {}

    def _text(node, sub):
        el = node.find(sub)
        return el.text.strip() if el is not None and el.text else None

    for _, disorder in ET.iterparse(str(path), events=("end",)):
        if disorder.tag != "Disorder":
            continue
        code = _text(disorder, "OrphaCode")
        if not code:
            disorder.clear()
            continue
        orpha = f"ORPHA:{code}"
        name = _text(disorder, "Name")
        classes, types = [], []
        for rec in disorder.findall("./PrevalenceList/Prevalence"):
            cls = _text(rec, "PrevalenceClass/Name")
            typ = _text(rec, "PrevalenceType/Name")
            if cls:
                classes.append(cls)
            if typ:
                types.append(typ)
        # A disease carries several prevalence records (by country, by type). Keep the
        # rarest stated class: the question here is whether it is ultra-rare anywhere.
        best = min(classes, key=lambda c: PREV_RANK.get(c, 99), default=None)
        out[orpha] = {
            "name": name,
            "prevalence": best,
            "rank": PREV_RANK.get(best, 99) if best else 99,
            "records": len(classes),
            "types": sorted(set(types)),
        }
        disorder.clear()
    return out


def load_cell_expression() -> tuple[dict[str, dict[str, float]], list[str]]:
    """Human Protein Atlas single-cell RNA: the cell axis, for every gene.

    Only the cell type with the highest expression per gene is kept, plus the number of
    cell types above a floor. Keeping the full matrix would be ~20k x 80 floats, which the
    browser does not need and the licence does not let us redistribute anyway.
    """
    path = BY_KEY["hpa_single_cell"].dest
    gene_cells: dict[str, dict[str, float]] = defaultdict(dict)
    with zipfile.ZipFile(path) as z:
        inner = next(n for n in z.namelist() if n.endswith(".tsv"))
        with z.open(inner) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"), delimiter="\t")
            value_col = None
            for row in reader:
                if value_col is None:
                    for cand in ("nTPM", "nCPM", "pTPM", "Read count", "Value"):
                        if cand in row:
                            value_col = cand
                            break
                    if value_col is None:
                        raise SystemExit(f"no expression column in {inner}: {list(row)[:8]}")
                sym = (row.get("Gene name") or "").strip()
                cell = (row.get("Cell type") or "").strip()
                if not sym or not cell:
                    continue
                try:
                    v = float(row[value_col])
                except (TypeError, ValueError):
                    continue
                gene_cells[sym][cell] = v
    cells = sorted({c for d in gene_cells.values() for c in d})
    return gene_cells, cells


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    missing = [s.name for s in BY_KEY.values() if not s.dest.exists()]
    if missing:
        print("missing catalogues: " + ", ".join(missing))
        print("run: python tools/ingest.py")
        return 2

    print("reading HPO gene-disease ...", flush=True)
    gene_to_disease, disease_to_gene, assoc = load_gene_disease()
    print("reading HPO disease annotations ...", flush=True)
    names, by_prefix, hpo_header = load_disease_names()
    print("reading Orphanet prevalence ...", flush=True)
    prevalence = load_prevalence()
    print("reading Human Protein Atlas single-cell ...", flush=True)
    gene_cells, cell_types = load_cell_expression()

    # --- the join, with coverage measured at every step --------------------------------
    diseases = sorted(set(names) | set(disease_to_gene))
    with_gene = [d for d in diseases if disease_to_gene.get(d)]
    genes = sorted(gene_to_disease)
    genes_with_cells = [g for g in genes if g in gene_cells]

    # Diseases placeable on the cell axis: at least one gene with expression data.
    placeable = [d for d in with_gene if any(g in gene_cells for g in disease_to_gene[d])]

    # Per-cell-type burden: how many rare diseases have a gene whose highest expression is
    # in that cell type. A coarse but real answer to "which cells does rare disease live in".
    top_cell_of: dict[str, str] = {}
    for g, cells in gene_cells.items():
        if cells:
            top_cell_of[g] = max(cells, key=cells.get)
    burden = Counter()
    for d in placeable:
        for g in disease_to_gene[d]:
            c = top_cell_of.get(g)
            if c:
                burden[c] += 1

    # Prevalence distribution over the Orphanet diseases we can see.
    prev_counts = Counter(
        v["prevalence"] or "Not stated" for v in prevalence.values()
    )
    ultra = [
        k for k, v in prevalence.items()
        if v["prevalence"] in ("<1 / 1 000 000", "1-9 / 1 000 000")
    ]
    ultra_with_gene = [d for d in ultra if disease_to_gene.get(d)]

    payload = {
        "generated": "2026-08-27",
        "provenance": (
            "Joined from public catalogues: HPO gene-to-disease and annotations, Orphanet "
            "prevalence, Human Protein Atlas single-cell RNA. Orphanet is CC BY-ND and HPA "
            "is CC BY-SA, so this file carries aggregates and identifiers, never a copy of "
            "a source table. Coverage numbers are measured, not assumed."
        ),
        "sourceHeader": hpo_header,
        "scale": {
            "diseases": len(diseases),
            "diseasesByPrefix": dict(by_prefix),
            "diseasesWithGene": len(with_gene),
            "genes": len(genes),
            "genesWithCellData": len(genes_with_cells),
            "cellTypes": len(cell_types),
            "diseasesPlaceableOnCellAxis": len(placeable),
            "orphanetWithPrevalence": len(prevalence),
            "ultraRare": len(ultra),
            "ultraRareWithGene": len(ultra_with_gene),
            "associationTypes": {k: v for k, v in assoc.most_common()},
        },
        "coverage": {
            "geneKnown": round(len(with_gene) / max(len(diseases), 1), 4),
            "cellPlaceable": round(len(placeable) / max(len(diseases), 1), 4),
            "ultraRareGeneKnown": round(len(ultra_with_gene) / max(len(ultra), 1), 4),
        },
        "prevalenceDistribution": [
            {"band": b, "diseases": prev_counts.get(b, 0), "rank": PREV_RANK.get(b, 99)}
            for b in PREV_ORDER
            if prev_counts.get(b, 0)
        ],
        "cellBurden": [
            {"cell": c, "diseaseGenes": n}
            for c, n in burden.most_common(40)
        ],
        "cellTypes": cell_types,
    }

    path = DEST / "atlas.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    s, c = payload["scale"], payload["coverage"]
    print()
    print("wrote %s" % path.relative_to(ROOT))
    print("  %s" % hpo_header)
    print("  %6d diseases            %s" % (s["diseases"], dict(by_prefix)))
    print("  %6d have a known gene   (%.1f%% of the catalogue)"
          % (s["diseasesWithGene"], 100 * c["geneKnown"]))
    print("  %6d genes               %d with cell-type data across %d cell types"
          % (s["genes"], s["genesWithCellData"], s["cellTypes"]))
    print("  %6d placeable on the cell axis (%.1f%%)"
          % (s["diseasesPlaceableOnCellAxis"], 100 * c["cellPlaceable"]))
    print("  %6d ultra-rare (Orphanet <1-9 / 1 000 000), %d with a gene (%.1f%%)"
          % (s["ultraRare"], s["ultraRareWithGene"], 100 * c["ultraRareGeneKnown"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
