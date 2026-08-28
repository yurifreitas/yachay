#!/usr/bin/env python
"""Ten more ways of looking — the half of the field the first pass left out.

WHY THIS FILE EXISTS SEPARATELY. `tools/dimensions.py` produced seven transforms and every
one of them came from a man. That was not a sampling accident: it is what happens when you
reach for the names that are famous rather than the ones whose work you are standing on.
Sex chromosomes, X-inactivation, transposition, the karyotype of trisomy 21, the
translocation-to-drug path, and the refusal that kept thalidomide out of one country are
all *load-bearing* for a rare-disease atlas, and all were done by women.

Alan Turing is here for a reason that is not decoration either: morphogenesis. "The
Chemical Basis of Morphogenesis" (1952) asks how pattern arises from uniformity — which is
the deepest form of the cell-versus-gene question this atlas is built on. One genome,
many cell types.

Same rule as the first file: **a name earns a place only if it yields a transform that
runs on data already here and produces a number.** Where the point is historical rather
than computational it is marked as such rather than dressed up.

    python tools/dimensions_two.py     # writes out/rare/dimensions_two.json
"""

from __future__ import annotations

import csv
import io
import json
import pathlib
import sys
import zipfile
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

RARE = ROOT / "out" / "rare"

# HPO inheritance terms, from hp.obo. Named here so the counts below are readable.
INHERITANCE = {
    "HP:0000006": "Autosomal dominant",
    "HP:0000007": "Autosomal recessive",
    "HP:0001417": "X-linked",
    "HP:0001419": "X-linked recessive",
    "HP:0001423": "X-linked dominant",
    "HP:0001427": "Mitochondrial",
    "HP:0001442": "Somatic mosaicism",
    "HP:0003743": "Genetic anticipation",
    "HP:0003745": "Sporadic",
    "HP:0003829": "Incomplete penetrance",
    "HP:0010985": "Gonosomal inheritance",
    "HP:0001450": "Y-linked",
}
X_LINKED = {"HP:0001417", "HP:0001419", "HP:0001423"}


def read_annotations() -> dict:
    """One pass over phenotype.hpoa, keeping the columns the first pass ignored."""
    path = BY_KEY["hpo_annotations"].dest
    inherit_by_disease: dict[str, set[str]] = defaultdict(set)
    sex_rows = Counter()
    freq_stated = 0
    total_rows = 0
    cols = None
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            if line.startswith("database_id"):
                cols = line.rstrip("\n").split("\t")
                continue
            if cols is None:
                continue
            row = dict(zip(cols, line.rstrip("\n").split("\t")))
            total_rows += 1
            if row.get("aspect") == "I":
                inherit_by_disease[row["database_id"]].add(row["hpo_id"])
            if row.get("sex"):
                sex_rows[row["sex"]] += 1
            if row.get("frequency"):
                freq_stated += 1
    return {
        "inheritByDisease": inherit_by_disease,
        "sexRows": sex_rows,
        "freqStated": freq_stated,
        "totalRows": total_rows,
    }


def read_cell_breadth() -> dict:
    """How many cell types express each gene — Turing's question, made countable.

    A gene is not a phenotype. The same sequence is read in every cell and produces a
    different outcome in each, which is the thing morphogenesis is about.
    """
    path = BY_KEY["hpa_single_cell"].dest
    per_gene = Counter()
    per_gene_total = Counter()
    with zipfile.ZipFile(path) as z:
        inner = next(n for n in z.namelist() if n.endswith(".tsv"))
        with z.open(inner) as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"), delimiter="\t"):
                g = (row.get("Gene name") or "").strip()
                if not g:
                    continue
                per_gene_total[g] += 1
                try:
                    v = float(row.get("nCPM") or row.get("nTPM") or 0)
                except ValueError:
                    continue
                if v >= 1.0:                      # a floor, so "expressed" means something
                    per_gene[g] += 1
    return {"expressedIn": per_gene, "measuredIn": per_gene_total}


def main() -> int:
    RARE.mkdir(parents=True, exist_ok=True)
    ann = read_annotations()
    inherit = ann["inheritByDisease"]

    disease_genes: dict[str, set[str]] = defaultdict(set)
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            g, dd = (row.get("gene_symbol") or "").strip(), (row.get("disease_id") or "").strip()
            if g and dd:
                disease_genes[dd].add(g)

    breadth = read_cell_breadth()
    lupus = json.loads((RARE / "lupus_graph.json").read_text(encoding="utf-8"))
    atlas = json.loads((RARE / "atlas.json").read_text(encoding="utf-8"))

    # --- counts the transforms below need -------------------------------------------
    mode_counts = Counter()
    for terms in inherit.values():
        for t in terms:
            mode_counts[INHERITANCE.get(t, t)] += 1
    x_diseases = [d for d, t in inherit.items() if t & X_LINKED]
    mosaic = [d for d, t in inherit.items() if "HP:0001442" in t]
    sporadic = [d for d, t in inherit.items() if "HP:0003745" in t]
    n_with_mode = len(inherit)

    dis_genes = [g for gs in disease_genes.values() for g in gs]
    widths = [breadth["expressedIn"].get(g, 0) for g in set(dis_genes)
              if g in breadth["measuredIn"]]
    widths.sort()
    n_w = len(widths)

    dims = [
        {
            "id": "stevens",
            "person": "Nettie Stevens",
            "years": "1861–1912",
            "contribution":
                "Showed in 1905 that sex is determined by a chromosome — the X/Y system — "
                "working from mealworm cells. E. B. Wilson published similar findings and "
                "for decades the discovery was attributed largely to him.",
            "transform":
                "Count what her chromosome costs: rare diseases whose inheritance HPO "
                "records as X-linked.",
            "result": {
                "headline": len(x_diseases),
                "unit": f"X-linked rare diseases, of {n_with_mode:,} with a recorded mode",
                "share": round(len(x_diseases) / max(n_with_mode, 1), 4),
                "byMode": dict(mode_counts.most_common(8)),
                "note": "Every one of these is a disease whose risk depends on which sex "
                        "chromosome you carry — a category that did not exist as a concept "
                        "before she named it.",
            },
        },
        {
            "id": "lyon",
            "person": "Mary Lyon",
            "years": "1925–2014",
            "contribution":
                "X-inactivation, 1961: in every female cell one X is silenced, at random, "
                "early in development. A female carrier is therefore not one phenotype — "
                "she is a MOSAIC of two cell populations.",
            "transform":
                "Take the cell axis to its limit. Lyonisation means the unit of disease is "
                "not the person and not the gene, but the cell — and the same woman carries "
                "cells on both sides of the lesion.",
            "result": {
                "headline": len(mosaic),
                "unit": "diseases HPO records as showing somatic mosaicism",
                "xLinked": len(x_diseases),
                "note": "This is the strongest possible statement of the cell-versus-gene "
                        "axis: in an X-linked disorder the genotype is identical in every "
                        "cell and the phenotype is not, because which X is silenced differs "
                        "cell by cell. The gene does not determine the cell; the cell "
                        "determines what the gene does.",
                "consequence": "It also means a carrier's severity is a sampling problem — "
                               "which tissue happened to inactivate which X — so two women "
                               "with the identical variant are not the same case.",
            },
        },
        {
            "id": "turing_morph",
            "person": "Alan Turing",
            "years": "1912–1954",
            "contribution":
                "'The Chemical Basis of Morphogenesis' (1952): pattern can arise from a "
                "uniform starting state, through nothing more than two substances "
                "diffusing and reacting at different rates. Written in the last two years "
                "of his life, and the reason a uniform genome can build a striped animal.",
            "transform":
                "Ask his question of the data: if every cell holds the same genome, how "
                "many cell types does one disease gene actually reach? Count the breadth of "
                "expression per gene.",
            "result": {
                "headline": widths[n_w // 2] if n_w else 0,
                "unit": f"cell types is the MEDIAN breadth of a disease gene, of "
                        f"{atlas['scale']['cellTypes']} measured",
                "min": widths[0] if n_w else 0,
                "p25": widths[int(n_w * 0.25)] if n_w else 0,
                "p75": widths[int(n_w * 0.75)] if n_w else 0,
                "max": widths[-1] if n_w else 0,
                "genes": n_w,
                "narrow": sum(1 for w in widths if w <= 5),
                "broad": sum(1 for w in widths if w >= 100),
                "note": "The broad genes are the puzzle. A gene expressed in a hundred cell "
                        "types causes a disease in one of them, and nothing in the sequence "
                        "says which — that gap is exactly what morphogenesis is about, and "
                        "why 'which gene' is a weaker answer than it sounds.",
            },
        },
        {
            "id": "gautier",
            "person": "Marthe Gautier",
            "years": "1925–2022",
            "contribution":
                "Cultured the cells in which trisomy 21 was seen, in 1958, in a lab she "
                "equipped partly at her own expense after learning tissue culture in "
                "Boston. The slides left her lab and the discovery was published with "
                "Jérôme Lejeune as first author; her role was acknowledged only decades "
                "later.",
            "transform":
                "Two of this atlas's axes meet in her: the CELL (culture is what made a "
                "karyotype visible) and CREDIT (a number's provenance is part of the "
                "number). Historical rather than computational, and marked so.",
            "result": {
                "headline": None,
                "unit": "not computed — a historical claim, stated as one",
                "note": "She belongs beside Weller in this atlas: he made the cell an "
                        "experimental unit, she used it to find the first human chromosomal "
                        "disorder. The Sidis tab asks who measured a number; this asks who "
                        "was allowed to have measured it.",
                "confidence": "medium",
            },
        },
        {
            "id": "mcclintock",
            "person": "Barbara McClintock",
            "years": "1902–1992",
            "contribution":
                "Transposable elements, from maize, in the 1940s. Largely dismissed for "
                "about thirty years; Nobel in 1983, at 81.",
            "transform":
                "Measure the field's holding pattern: how much of what is 'known' is "
                "actually unresolved — diseases with a recorded inheritance mode of "
                "sporadic, and genes still classed as candidates rather than causal.",
            "result": {
                "headline": len(sporadic),
                "unit": "diseases recorded as sporadic — no inheritance pattern resolved",
                "candidatesInLupusSeed": sum(
                    1 for g in lupus["nodes"]["genes"] if g["evidence"] == "candidate"),
                "note": "'Sporadic' is a placeholder as often as a finding. McClintock's "
                        "lesson is not that outsiders are always right; it is that the lag "
                        "between a correct result and its acceptance is a property of the "
                        "field, and it is long.",
            },
        },
        {
            "id": "rowley",
            "person": "Janet Rowley",
            "years": "1925–2013",
            "contribution":
                "Showed in 1972–73 that specific chromosomal translocations cause specific "
                "leukaemias — she identified the 9;22 and 8;21 rearrangements by looking at "
                "banded chromosomes on her dining table. It established that a named "
                "genetic lesion could be the cause of a named cancer, which is the logic "
                "that produced imatinib.",
            "transform":
                "Count how far that logic reaches here: therapies in the lupus network that "
                "act on a named molecular target versus a cell or a process.",
            "result": {
                "headline": len(lupus["nodes"]["therapies"]),
                "unit": "therapies in the network, each with a named molecular target",
                "byModality": lupus["summary"]["byModality"],
                "note": "Rowley's path — lesion to drug — is the exception in rare disease, "
                        "not the rule. The approach-chooser tab exists because for most "
                        "entries the lesion is known and the path from it is not.",
            },
        },
        {
            "id": "nightingale",
            "person": "Florence Nightingale",
            "years": "1820–1910",
            "contribution":
                "The first woman elected to the Royal Statistical Society. Her polar-area "
                "diagrams showed that preventable disease, not combat, killed most soldiers "
                "in the Crimea — a chart built to change a policy rather than to report a "
                "result.",
            "transform":
                "Read the atlas her way: not 'how many diseases exist' but 'how many are "
                "currently untreatable', which is the number that would move a decision.",
            "result": {
                "headline": round(1 - atlas["coverage"]["geneKnown"], 4),
                "unit": "share of the catalogue with no causal gene — the modern equivalent "
                        "of her preventable fraction",
                "diseases": atlas["scale"]["diseases"],
                "withoutGene": atlas["scale"]["diseases"] - atlas["scale"]["diseasesWithGene"],
                "note": "Her insight was rhetorical as much as statistical: she chose the "
                        "denominator that made the actionable quantity visible. This atlas "
                        "got that wrong once — see the denominator fallacy in the bias tab.",
            },
        },
        {
            "id": "kelsey",
            "person": "Frances Oldham Kelsey",
            "years": "1914–2015",
            "contribution":
                "As an FDA reviewer she refused to approve thalidomide, repeatedly, on the "
                "grounds that the safety data were inadequate — while it was already "
                "causing birth defects elsewhere. She was not proving harm; she was "
                "refusing to accept an absence of evidence as evidence of absence.",
            "transform":
                "That refusal is the rule of three, decades before it was routinely quoted. "
                "Take the evidence tab's own arithmetic and state what 'none observed' "
                "actually bounds.",
            "result": {
                "headline": 60,
                "unit": "percent — the true rate still consistent with ZERO events observed "
                        "in five patients",
                "note": "Nothing observed in n patients bounds the rate at about 3/n, not "
                        "at zero. At the sample sizes an ultra-rare programme actually has, "
                        "'no adverse events seen' is barely evidence — which is exactly the "
                        "position Kelsey held against considerable pressure.",
                "link": "See the evidence tab: the same number, with a slider.",
            },
        },
        {
            "id": "franklin",
            "person": "Rosalind Franklin",
            "years": "1920–1958",
            "contribution":
                "Photo 51 and the B-form measurements. Her data reached Watson and Crick "
                "without her knowledge; her own analysis of the diffraction was correct and "
                "her credit posthumous.",
            "transform":
                "Her method is the omitted one from the first pass: X-ray diffraction "
                "infers a three-dimensional structure from a two-dimensional projection. "
                "That is precisely the Roger Penrose projection this atlas listed as not "
                "implemented — named again here, still not implemented.",
            "result": {
                "headline": None,
                "unit": "not computed — the projection method remains unbuilt",
                "note": "Listing it twice without building it would be the decoration this "
                        "section refuses, so it stays on the omitted list, now with the "
                        "person whose work is the strongest argument for building it.",
            },
        },
        {
            "id": "turing_decide",
            "person": "Alan Turing",
            "years": "1912–1954",
            "contribution":
                "Undecidability, 1936: there are questions no procedure can answer, and you "
                "can prove it without knowing the answer.",
            "transform":
                "Apply it to the atlas's own limit. 'Is this catalogue complete?' cannot be "
                "answered from inside the catalogue — every statistic here has the "
                "catalogue as its denominator.",
            "result": {
                "headline": None,
                "unit": "undecidable from within",
                "note": "The bias tab lists survivorship as untestable. This is why: a "
                        "disease too rare to have been seen twice, or seen only where no "
                        "catalogue reaches, leaves no trace in the catalogue — so no "
                        "computation over the catalogue can detect it. Naming the limit is "
                        "the only available move.",
            },
        },
    ]

    payload = {
        "generated": "2026-08-27",
        "why": (
            "The first pass produced seven transforms and every one came from a man. That "
            "was not a sampling accident — it is what happens when you reach for the names "
            "that are famous rather than the ones whose work you are standing on. Sex "
            "chromosomes, X-inactivation, the trisomy-21 karyotype, the "
            "translocation-to-drug path and the refusal that kept thalidomide out of one "
            "country are all load-bearing for this atlas."
        ),
        "rule": "Same as the first pass: a transform that runs on data already here, or an "
                "explicit mark that the point is historical rather than computational.",
        "dimensions": dims,
    }
    (RARE / "dimensions_two.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("wrote out/rare/dimensions_two.json")
    for d in dims:
        r = d["result"]
        h = r["headline"]
        print(f"  {d['person']:<26} {'—' if h is None else h:>8}  {r['unit'][:66]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
