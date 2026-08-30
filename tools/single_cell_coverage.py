"""Which diseases has anyone actually sequenced at single-cell resolution?

THE QUESTION THIS EXISTS TO ASK, and it is a question about the rest of this repository.

Four separate layers here place a disease on a CELL TYPE. `tools/scale_information.py`
collapses causal genes onto 154 cell types and measures what survives. `tools/autism_convergence.py`
reports the autism gene set concentrated by cell type rather than by pathway, and calls the
convergence spatial. `tools/gap_taxonomy.py` counts 9,437 missing cell-type assignments and
types most of them as accessibility. `tools/knowledge_void.py` carries a cellular axis in its
five-dimensional lattice.

Every one of those reads the Human Protein Atlas, which measures expression in NORMAL tissue.
So each is a statement about where a gene sits in healthy biology, plus an inference that the
disease sits there too. That inference may be right. It is not an observation, and nothing in
this repository has ever said how often it could be checked.

CZ CELLxGENE Discover indexes the single-cell datasets that exist, each annotated with the
MONDO disease its cells came from. Joining that index to the catalogue answers the question
directly: for how many of these diseases has anyone ever collected a cell?

WHAT MAKES THIS DIFFERENT FROM THE OTHER GAP COUNTS. `gap_taxonomy` can only see whether a
FIELD is filled in some catalogue. This sees whether the underlying observation was ever made
anywhere in the field's public record. A gap the crosswalk calls "accessibility — the fact may
exist and be unreachable" is a different thing from a disease no one has ever put under a
sequencer, and until now this repository could not tell them apart.

THE FIT TEST (.claude/skills/sieve-new-adapter): this is not an adapter and claims nothing
about ranking. There is no entity being scored, no null and no selection operator — it is a
JOIN and a set of counts, reported with the denominators. Question 1 already fails. It is
listed here so nobody looks for the Stage 1 apparatus and concludes it was forgotten.

    python tools/single_cell_coverage.py
"""
from __future__ import annotations

import collections
import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "rare" / "single_cell_coverage.json"

#: PATO:0000461 is "normal" — a dataset of healthy tissue. It is not a disease and is counted
#: separately rather than filtered silently, because the ratio is the finding.
NORMAL = "PATO:0000461"


def cellxgene_index():
    """MONDO term -> datasets, tissues and assays; plus the normal-tissue count."""
    path = BY_KEY["cellxgene_collections"].dest
    payload = json.loads(path.read_text(encoding="utf-8"))

    per_disease: dict[str, dict] = {}
    normal_datasets = 0
    total_datasets = 0
    for collection in payload:
        for ds in collection.get("datasets") or []:
            total_datasets += 1
            terms = ds.get("disease") or []
            if all(t.get("ontology_term_id") == NORMAL for t in terms):
                normal_datasets += 1
            for t in terms:
                term = t.get("ontology_term_id")
                if not term or term == NORMAL:
                    continue
                rec = per_disease.setdefault(
                    term, {"label": t.get("label"), "datasets": 0,
                           "tissues": set(), "assays": set(), "collections": set()})
                rec["datasets"] += 1
                rec["collections"].add(collection.get("collection_id"))
                for x in ds.get("tissue") or []:
                    if x.get("label"):
                        rec["tissues"].add(x["label"])
                for x in ds.get("assay") or []:
                    if x.get("label"):
                        rec["assays"].add(x["label"])
    return per_disease, normal_datasets, total_datasets


def mondo_crosswalk() -> tuple[dict[str, set[str]], dict[str, str]]:
    """MONDO term -> the OMIM/ORPHA ids it cross-references, and its label.

    Read the same way tools/gap_taxonomy.py reads it, deliberately: two tools parsing the
    same ontology two different ways is how two files come to disagree about what a disease
    is while both looking correct.
    """
    xwalk: dict[str, set[str]] = {}
    label: dict[str, str] = {}
    term: str | None = None
    xrefs: list[str] = []
    name: str | None = None

    def flush() -> None:
        if term:
            ids = {f"OMIM:{x.split(':', 1)[1]}" for x in xrefs if x.startswith("OMIM:")}
            ids |= {f"ORPHA:{x.split(':', 1)[1]}" for x in xrefs if x.startswith("Orphanet:")}
            xwalk[term] = ids
            if name:
                label[term] = name

    for line in BY_KEY["mondo"].dest.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("[Term]"):
            flush()
            term, xrefs, name = None, [], None
        elif line.startswith("id: MONDO"):
            term = line[4:].strip()
        elif line.startswith("name:") and term:
            name = line[5:].strip()
        elif line.startswith("xref:") and term:
            xrefs.append(line[6:].split()[0])
    flush()
    return xwalk, label


def catalogue_diseases() -> tuple[set[str], dict[str, set[str]]]:
    """Every disease the atlas knows, and the genes each carries."""
    genes: dict[str, set[str]] = collections.defaultdict(set)
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            d = (row.get("disease_id") or "").strip()
            g = (row.get("gene_symbol") or "").strip()
            if d and g:
                genes[d].add(g)
    known: set[str] = set(genes)
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        rows = (line for line in fh if not line.startswith("#"))
        for row in csv.DictReader(rows, delimiter="\t"):
            d = (row.get("database_id") or "").strip()
            if d:
                known.add(d)
    return known, dict(genes)


def main() -> int:
    path = BY_KEY["cellxgene_collections"].dest
    if not path.exists():
        print(f"missing {path}", file=sys.stderr)
        return 1

    per_disease, normal_datasets, total_datasets = cellxgene_index()
    xwalk, mondo_label = mondo_crosswalk()
    catalogue, disease_genes = catalogue_diseases()

    # Which catalogue diseases have cells, via MONDO.
    reachable: dict[str, dict] = {}
    unmatched_terms: list[str] = []
    for term, rec in per_disease.items():
        ids = xwalk.get(term, set())
        hits = sorted(ids & catalogue)
        if not ids:
            unmatched_terms.append(term)
        for d in hits:
            cur = reachable.setdefault(d, {"datasets": 0, "mondo": [], "tissues": set()})
            cur["datasets"] += rec["datasets"]
            cur["mondo"].append(term)
            cur["tissues"] |= rec["tissues"]

    # The tissues and assays the field has actually used, which is a second denominator: a
    # disease of a tissue nobody dissociates is unreachable for a different reason.
    tissues = collections.Counter()
    assays = collections.Counter()
    for rec in per_disease.values():
        for t in rec["tissues"]:
            tissues[t] += 1
        for a in rec["assays"]:
            assays[a] += 1

    covered = len(reachable)
    payload = {
        "generated": "2026-08-30",
        "provenance": "CZ CELLxGENE Discover collection index, joined to the catalogue "
                      "through MONDO cross-references to OMIM and Orphanet",
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md",
        "question": "Four layers here place a disease on a cell type, all of them from an "
                    "atlas of NORMAL tissue. For how many of these diseases has anyone ever "
                    "collected a cell?",
        "not_an_adapter": {
            "gate": ".claude/skills/sieve-new-adapter",
            "fails": "question 1 — nothing is being ranked. This is a join and a set of "
                     "counts, and it carries no null because there is no statistic to "
                     "calibrate. Stated so nobody looks for the Stage 1 apparatus and "
                     "concludes it was left out by accident.",
        },
        "scale": {
            "datasets_indexed": total_datasets,
            "datasets_of_normal_tissue": normal_datasets,
            "disease_terms_with_cells": len(per_disease),
            "catalogue_diseases": len(catalogue),
            "catalogue_diseases_with_cells": covered,
            "share_of_catalogue": round(covered / len(catalogue), 5) if catalogue else None,
            "cellxgene_terms_with_no_omim_or_orpha_crosswalk": len(unmatched_terms),
        },
        "the_finding": (
            f"{normal_datasets:,} of {total_datasets:,} indexed single-cell datasets are of "
            f"NORMAL tissue. {len(per_disease)} distinct disease terms carry cells at all, "
            f"and {covered} of the {len(catalogue):,} diseases in this catalogue can be "
            f"reached from one. The cell-type axis that four layers of this site reason over "
            f"is, for the overwhelming majority of these diseases, an inference from healthy "
            f"tissue and not an observation of the disease."
        ),
        "best_covered": [
            {"disease": d, "datasets": r["datasets"], "mondo": r["mondo"][0],
             "label": mondo_label.get(r["mondo"][0]),
             "tissues": sorted(r["tissues"])[:6],
             "genes": len(disease_genes.get(d, ()))}
            for d, r in sorted(reachable.items(), key=lambda kv: -kv[1]["datasets"])[:25]
        ],
        "commonest_tissues": [{"tissue": t, "diseases": n} for t, n in tissues.most_common(15)],
        "commonest_assays": [{"assay": a, "diseases": n} for a, n in assays.most_common(10)],
        "says": "A count of PUBLIC datasets in one index, not of experiments that exist. A "
                "disease studied at single-cell resolution in a paper whose data never "
                "reached CELLxGENE is invisible here and is not therefore unstudied. The "
                "number is a floor on coverage, and the direction of its error is known.",
        "limits": [
            "The join is through MONDO cross-references to OMIM and Orphanet, which is the "
            f"same boundary every other tool here runs into. {len(unmatched_terms)} disease "
            "terms with cells carry no OMIM or Orphanet xref at all, so they are counted as "
            "having cells and cannot be attached to a catalogue entry.",
            "CELLxGENE is weighted towards common disease and towards tissues that dissociate "
            "well. Absence here is partly a statement about what is easy to sample, and this "
            "file cannot separate that from what is rare.",
            "A dataset annotated with a disease term is not necessarily a study OF that "
            "disease at the resolution a claim would need — the annotation says cells came "
            "from donors carrying it, nothing about power or design.",
        ],
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {DEST.relative_to(ROOT)}")
    print(f"  {total_datasets:,} datasets indexed, {normal_datasets:,} of normal tissue")
    print(f"  {len(per_disease)} disease terms carry cells")
    print(f"  {covered} of {len(catalogue):,} catalogue diseases reachable "
          f"({100 * covered / len(catalogue):.2f} %)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
