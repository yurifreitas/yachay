#!/usr/bin/env python
"""Lupus: the disease where the gene is not the unit of action — the cell is.

WHY LUPUS, AND WHY HERE
-----------------------
This repository's core data structure is a matrix of **cell lines x genes**, and its
central statistic is a top-k over the *cell lines* in which a gene matters. The whole
library rests on the claim that a gene's effect is not a property of the gene — it is a
property of the gene in a context.

Lupus is the clinical form of that claim.

  - Systemic lupus is **polygenic**: a hundred-plus loci of small effect. Naming a gene
    tells you almost nothing about what to do.
  - **Monogenic lupus** exists, is ultra-rare, and is mechanistically legible: complement
    deficiencies, nucleic-acid sensing and clearance defects, interferon-pathway gain of
    function. These are the diseases where one gene *is* enough.
  - The same pathway acts in different cells to different ends. Type I interferon produced
    by a plasmacytoid dendritic cell is not the same event as an autoantibody made by a
    plasma cell, and a therapy that works on one does nothing to the other.
  - The most striking recent result in the field is a **cell** therapy, not a gene therapy:
    CD19 CAR-T depleting B cells has produced drug-free remission in refractory SLE.

So lupus lets the atlas carry three things it could not before: a disease at the *boundary*
of the rare-disease definition, a monogenic ultra-rare subset inside a common disease, and
an explicit cell-versus-gene axis.

PROVENANCE
----------
Written from working knowledge. Gene-disease relationships below are well established in
the literature; **the cell-type attributions are simplifications** — most of these genes
act in several cell types, and the "primary cell" column names where the mechanism is
usually described, not the only place it operates. Every row carries a confidence mark.
Nothing here is clinical guidance.

    python tools/lupus_seed.py     # writes out/rare/lupus.json
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "out" / "rare"

# --- the cell types the disease is actually played out in ------------------------------
CELLS = [
    {"id": "pdc", "name": "Plasmacytoid dendritic cell", "role": "The main producer of type I interferon", "lineage": "myeloid"},
    {"id": "bcell", "name": "B cell", "role": "Presents antigen, matures into the antibody-producing plasma cell", "lineage": "lymphoid"},
    {"id": "plasma", "name": "Plasma cell", "role": "Secretes autoantibodies; long-lived and largely drug-resistant", "lineage": "lymphoid"},
    {"id": "tcell", "name": "T cell", "role": "Provides help to B cells; the Tfh subset drives germinal centres", "lineage": "lymphoid"},
    {"id": "mono", "name": "Monocyte / macrophage", "role": "Clears apoptotic debris — the failure that starts the cycle", "lineage": "myeloid"},
    {"id": "neut", "name": "Neutrophil", "role": "NETosis releases chromatin, feeding the nucleic-acid sensors", "lineage": "myeloid"},
    {"id": "kidney", "name": "Kidney resident cell", "role": "Where immune-complex deposition becomes organ damage", "lineage": "non-immune"},
]

# --- the mechanistic axes, so a gene can be placed on more than one ---------------------
AXES = [
    {"id": "clearance", "name": "Clearance of dying cells", "note": "Debris that is not cleared becomes the antigen."},
    {"id": "sensing", "name": "Nucleic-acid sensing", "note": "Self DNA/RNA read as if it were viral."},
    {"id": "ifn", "name": "Type I interferon", "note": "The amplifier; the signature most SLE patients carry."},
    {"id": "tolerance", "name": "B-cell tolerance", "note": "Autoreactive B cells that should have been deleted."},
    {"id": "complement", "name": "Complement", "note": "Paradox: deficiency causes lupus, consumption marks it."},
]

# --- monogenic lupus: where one gene IS enough ------------------------------------------
# confidence refers to the gene-disease relationship being established, not to the
# cell-type attribution, which is a simplification throughout.
MONOGENIC = [
    dict(gene="C1QA", alt=["C1QB", "C1QC"], axis="complement", cell="mono",
         effect="loss", inherit="AR", penetrance="very high",
         note="C1q deficiency is the strongest known single-gene risk for lupus — over 90% of "
              "those affected develop it. Also the cleanest statement of the clearance model.",
         confidence="high"),
    dict(gene="C1R", alt=["C1S"], axis="complement", cell="mono", effect="loss", inherit="AR",
         penetrance="high", note="Early classical-pathway deficiency, same mechanism as C1q.",
         confidence="medium"),
    dict(gene="C4A", alt=["C4B"], axis="complement", cell="mono", effect="loss", inherit="AR",
         penetrance="high",
         note="Complement C4 copy number varies between people, so 'the gene' is not even a "
              "fixed quantity — dosage is the risk factor.",
         confidence="high"),
    dict(gene="C2", alt=[], axis="complement", cell="mono", effect="loss", inherit="AR",
         penetrance="moderate", note="Commonest classical-pathway deficiency; lower penetrance than C1q.",
         confidence="medium"),
    dict(gene="DNASE1L3", alt=["DNASE1"], axis="clearance", cell="mono", effect="loss",
         inherit="AR", penetrance="high",
         note="Cannot degrade extracellular chromatin. Causes early-onset lupus with "
              "anti-dsDNA — the antigen is literally the undigested debris.",
         confidence="high"),
    dict(gene="TREX1", alt=[], axis="sensing", cell="mono", effect="loss", inherit="AD/AR",
         penetrance="high",
         note="A cytosolic DNase; its loss leaves self DNA to be sensed as viral. Also causes "
              "Aicardi-Goutieres syndrome — the same gene, a different disease, by dose.",
         confidence="high"),
    dict(gene="SAMHD1", alt=["RNASEH2A", "RNASEH2B", "RNASEH2C", "ADAR1"], axis="sensing",
         cell="pdc", effect="loss", inherit="AR", penetrance="high",
         note="The interferonopathy genes. Lupus and Aicardi-Goutieres sit on one continuum "
              "of nucleic-acid handling.",
         confidence="high"),
    dict(gene="IFIH1", alt=["DDX58", "STING1"], axis="sensing", cell="pdc", effect="gain",
         inherit="AD", penetrance="high",
         note="GAIN of function — the sensor is constitutively on. The therapeutic logic "
              "inverts: you want less signal, not more gene.",
         confidence="high"),
    dict(gene="TMEM173", alt=[], axis="ifn", cell="pdc", effect="gain", inherit="AD",
         penetrance="high", note="STING gain of function (SAVI). Vasculopathy with lupus features.",
         confidence="medium"),
    dict(gene="PRKCD", alt=[], axis="tolerance", cell="bcell", effect="loss", inherit="AR",
         penetrance="high", note="Loss of B-cell apoptosis; autoreactive clones survive selection.",
         confidence="medium"),
    dict(gene="TNFAIP3", alt=[], axis="tolerance", cell="bcell", effect="loss", inherit="AD",
         penetrance="moderate",
         note="A20 haploinsufficiency. Also a common-variant SLE locus — the same gene appears "
              "as an ultra-rare mendelian cause and as a small-effect population risk.",
         confidence="high"),
    dict(gene="FAS", alt=["FASLG"], axis="tolerance", cell="tcell", effect="loss", inherit="AD",
         penetrance="high", note="ALPS; lupus-like autoimmunity from failed lymphocyte apoptosis.",
         confidence="high"),
]

# --- the boundary case: SLE itself ------------------------------------------------------
SLE = {
    "name": "Systemic lupus erythematosus",
    "architecture": "polygenic",
    "loci": "180+ associated loci, individually small effect",
    "note": (
        "SLE sits ON the rare-disease boundary rather than inside or outside it. The EU "
        "threshold is 5 in 10 000 (= 50 per 100 000). Reported SLE prevalence spans roughly "
        "20-150 per 100 000 depending on population, ancestry and case definition — so the "
        "same disease is legally rare in one country and not in another, and the deciding "
        "factor is partly who was counted."
    ),
    "confidence": "medium",
    "disparity": (
        "Prevalence and severity are substantially higher in people of African, Hispanic "
        "and Asian ancestry than in European-ancestry populations. Most genetic studies "
        "were done in the latter, so the evidence base is thinnest where the burden is "
        "heaviest."
    ),
}

# --- therapy, arranged by the CELL it acts on rather than the gene -----------------------
THERAPIES = [
    dict(name="Hydroxychloroquine", target="endosomal TLR signalling", cell="pdc",
         modality="small molecule", status="standard of care",
         note="Backbone therapy; blunts nucleic-acid sensing.", confidence="high"),
    dict(name="Belimumab", target="BAFF / BLyS", cell="bcell", modality="antibody",
         status="approved", note="Removes a B-cell survival signal.", confidence="high"),
    dict(name="Anifrolumab", target="type I IFN receptor", cell="pdc", modality="antibody",
         status="approved",
         note="Blocks the amplifier rather than the trigger — the interferon signature made "
              "actionable.", confidence="high"),
    dict(name="Rituximab", target="CD20", cell="bcell", modality="antibody",
         status="off-label", note="Depletes B cells but spares CD20-negative plasma cells, "
              "which is the usual explanation for incomplete responses.", confidence="high"),
    dict(name="Voclosporin", target="calcineurin", cell="tcell", modality="small molecule",
         status="approved", note="Approved for lupus nephritis.", confidence="medium"),
    dict(name="CD19 CAR-T", target="CD19", cell="bcell", modality="cell therapy",
         status="investigational",
         note="The result that reframed the field: deep B-cell depletion has produced "
              "drug-free remission in refractory SLE. A CELL therapy, not a gene therapy — "
              "the unit of intervention is the cell, which is the point of this section.",
         confidence="medium"),
    dict(name="Anti-CD38 / plasma-cell directed", target="CD38", cell="plasma",
         modality="antibody", status="investigational",
         note="Aimed at the long-lived plasma cell that B-cell depletion leaves behind.",
         confidence="low"),
]


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)

    # The cell x gene incidence matrix — the same shape as the DepMap matrix this
    # repository is built on, and the reason this section exists.
    matrix = []
    for m in MONOGENIC:
        row = {"gene": m["gene"], "axis": m["axis"], "effect": m["effect"]}
        for c in CELLS:
            # Primary cell = 2, same-lineage plausible = 1, otherwise 0. Deliberately
            # coarse: a finer scale would imply a precision the source does not have.
            primary = c["id"] == m["cell"]
            same_lineage = c["lineage"] == next(
                (x["lineage"] for x in CELLS if x["id"] == m["cell"]), None
            )
            row[c["id"]] = 2 if primary else (1 if same_lineage and c["id"] != "kidney" else 0)
        matrix.append(row)

    payload = {
        "generated": "2026-08-27",
        "provenance": (
            "Written from working knowledge. Gene-disease relationships are well established; "
            "CELL-TYPE ATTRIBUTIONS ARE SIMPLIFICATIONS — most of these genes act in several "
            "cell types, and the primary-cell column names where the mechanism is usually "
            "described. Not clinical guidance."
        ),
        "cells": CELLS,
        "axes": AXES,
        "monogenic": MONOGENIC,
        "sle": SLE,
        "therapies": THERAPIES,
        "matrix": matrix,
        "summary": {
            "monogenicGenes": len(MONOGENIC),
            "withAlternates": sum(len(m["alt"]) for m in MONOGENIC),
            "gainOfFunction": sum(1 for m in MONOGENIC if m["effect"] == "gain"),
            "byAxis": dict(Counter(m["axis"] for m in MONOGENIC)),
            "byCell": dict(Counter(m["cell"] for m in MONOGENIC)),
            "therapiesByCell": dict(Counter(t["cell"] for t in THERAPIES)),
            "cellsWithNoTherapy": [
                c["id"] for c in CELLS if not any(t["cell"] == c["id"] for t in THERAPIES)
            ],
        },
    }

    path = DEST / "lupus.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    s = payload["summary"]
    print("wrote %s" % path.relative_to(ROOT))
    print("  %d monogenic genes (+%d alternates) across %d cell types and %d axes"
          % (s["monogenicGenes"], s["withAlternates"], len(CELLS), len(AXES)))
    print("  %d act by GAIN of function, where more gene is the problem" % s["gainOfFunction"])
    print("  cells with no therapy pointed at them: %s"
          % (", ".join(s["cellsWithNoTherapy"]) or "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
