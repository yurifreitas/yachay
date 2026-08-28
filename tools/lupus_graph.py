#!/usr/bin/env python
"""Lupus as an explicit network: gene → mechanism → cell → therapy.

WHY A GRAPH AND NOT A TABLE
---------------------------
The research question this data is actually asked is a **path** question:

    "Given this gene, is there anything that reaches it?"

A table can say which cell a gene acts in and, separately, which cell a therapy targets.
It cannot answer whether a path exists from one to the other, because a path is a
composition of edges and a table has no composition. So the data is stored as a graph and
the reachability is computed here rather than left for a reader to trace by eye.

The output of that computation is the interesting part: **which genes have no path to any
therapy at all**. That is a research output, not a rendering detail.

WHAT IS MODELLED
----------------
Four node kinds and five edge kinds, deliberately kept small:

    gene    --acts_via-->  mechanism
    gene    --acts_in-->   cell
    mechanism --plays_in-->cell
    therapy --targets-->   cell
    therapy --modulates--> mechanism

A gene reaches a therapy when some path exists through a shared cell or mechanism. That is
a coarse notion of "reaches" — sharing a cell type is not the same as being druggable in
it — and the page says so. It is a screening question, which is what this repository is
for: it produces a shortlist of gaps, not a conclusion.

PROVENANCE
----------
Written from working knowledge. Gene-disease relationships are well established; the edge
set is a **simplification** — most of these genes act in several cells through several
mechanisms, and an edge means "this is where the mechanism is usually described", not
"only here". Every node carries a confidence mark. Not clinical guidance.

    python tools/lupus_graph.py     # writes out/rare/lupus_graph.json
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter, defaultdict, deque

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "out" / "rare"

# ---------------------------------------------------------------------------- cells
CELLS = [
    ("pdc", "Plasmacytoid dendritic cell", "The main producer of type I interferon", "myeloid"),
    ("bcell", "B cell", "Presents antigen; matures into the plasma cell", "lymphoid"),
    ("plasma", "Plasma cell", "Secretes autoantibodies; long-lived, largely drug-resistant", "lymphoid"),
    ("tcell", "T cell", "Helps B cells; the Tfh subset drives germinal centres", "lymphoid"),
    ("treg", "Regulatory T cell", "Restrains autoreactivity; reduced or dysfunctional in SLE", "lymphoid"),
    ("mono", "Monocyte / macrophage", "Clears apoptotic debris — the failure that starts the cycle", "myeloid"),
    ("neut", "Neutrophil", "NETosis releases chromatin, feeding the nucleic-acid sensors", "myeloid"),
    ("nk", "NK cell", "Cytotoxic clearance; altered subsets reported in SLE", "lymphoid"),
    ("kidney", "Kidney resident cell", "Where immune-complex deposition becomes organ damage", "non-immune"),
    ("keratino", "Keratinocyte", "Photosensitivity; UV-induced apoptosis feeds the same debris", "non-immune"),
    ("endo", "Endothelial cell", "Vasculopathy and accelerated atherosclerosis", "non-immune"),
]

# ------------------------------------------------------------------------ mechanisms
MECHANISMS = [
    ("clearance", "Clearance of dying cells", "Debris that is not cleared becomes the antigen."),
    ("sensing", "Nucleic-acid sensing", "Self DNA/RNA read as if it were viral."),
    ("ifn", "Type I interferon", "The amplifier; the signature most SLE patients carry."),
    ("tolerance", "B-cell tolerance", "Autoreactive B cells that should have been deleted."),
    ("complement", "Complement", "Deficiency causes lupus; consumption marks it. A paradox worth stating."),
    ("costim", "T–B co-stimulation", "The help that lets an autoreactive B cell mature."),
    ("netosis", "NETosis", "Neutrophil extracellular traps as an antigen source."),
    ("immunecomplex", "Immune-complex deposition", "Where systemic autoimmunity becomes organ injury."),
]

# ----------------------------------------------------------------------------- genes
# (id, mechanism, primary cell, effect, inheritance, penetrance, evidence class, note, confidence)
GENES = [
    # --- complement -------------------------------------------------------------------
    ("C1QA", "complement", "mono", "loss", "AR", "very high", "monogenic",
     "Over 90% of those with C1q deficiency develop lupus — the strongest single-gene risk known, "
     "and the cleanest statement of the clearance model.", "high"),
    ("C1R", "complement", "mono", "loss", "AR", "high", "monogenic",
     "Early classical-pathway deficiency; same mechanism as C1q.", "medium"),
    ("C1S", "complement", "mono", "loss", "AR", "high", "monogenic",
     "Partner of C1R in the C1 complex.", "medium"),
    ("C4A", "complement", "mono", "loss", "AR", "high", "monogenic",
     "C4 copy number varies between people, so 'the gene' is not a fixed quantity — dosage is "
     "the risk factor, and it is also a common-variant association.", "high"),
    ("C2", "complement", "mono", "loss", "AR", "moderate", "monogenic",
     "Commonest classical-pathway deficiency; lower penetrance than C1q.", "medium"),
    ("C3", "complement", "mono", "loss", "AR", "moderate", "monogenic",
     "Deficiency gives infection more than lupus — the pathway is not uniform along its length.",
     "medium"),
    # --- clearance ---------------------------------------------------------------------
    ("DNASE1L3", "clearance", "mono", "loss", "AR", "high", "monogenic",
     "Cannot degrade extracellular chromatin. Early-onset lupus with anti-dsDNA — the antigen is "
     "literally the undigested debris.", "high"),
    ("DNASE1", "clearance", "mono", "loss", "AD", "moderate", "monogenic",
     "Rarer, same logic as DNASE1L3.", "medium"),
    ("MFGE8", "clearance", "mono", "loss", "—", "low", "candidate",
     "Bridges apoptotic cells to phagocytes; supported in models more than in patients.", "low"),
    ("MERTK", "clearance", "mono", "loss", "—", "low", "candidate",
     "Efferocytosis receptor; a clearance candidate rather than an established cause.", "low"),
    # --- sensing -----------------------------------------------------------------------
    ("TREX1", "sensing", "mono", "loss", "AD/AR", "high", "monogenic",
     "A cytosolic DNase; its loss leaves self DNA to be sensed as viral. Also causes "
     "Aicardi–Goutières — the same gene, a different disease, by dose.", "high"),
    ("SAMHD1", "sensing", "pdc", "loss", "AR", "high", "monogenic",
     "Interferonopathy gene; lupus and AGS sit on one continuum of nucleic-acid handling.", "high"),
    ("RNASEH2B", "sensing", "pdc", "loss", "AR", "high", "monogenic",
     "Removes ribonucleotides from DNA; failure leaves a sensed substrate.", "medium"),
    ("ADAR", "sensing", "pdc", "loss", "AR", "high", "monogenic",
     "RNA editing; unedited self RNA is read as foreign.", "medium"),
    ("IFIH1", "sensing", "pdc", "gain", "AD", "high", "monogenic",
     "GAIN of function — the sensor is constitutively on. The therapeutic logic inverts: you want "
     "less signal, not more gene.", "high"),
    ("TMEM173", "ifn", "pdc", "gain", "AD", "high", "monogenic",
     "STING gain of function (SAVI): vasculopathy with lupus features.", "medium"),
    ("TLR7", "sensing", "bcell", "gain", "XL", "high", "monogenic",
     "A gain-of-function variant was shown to cause lupus directly. Explains part of the female "
     "predominance, since TLR7 escapes X inactivation.", "high"),
    # --- interferon --------------------------------------------------------------------
    ("IRF5", "ifn", "pdc", "gain", "—", "small", "gwas",
     "One of the strongest and most replicated common-variant associations.", "high"),
    ("STAT4", "ifn", "tcell", "gain", "—", "small", "gwas",
     "Associated with more severe disease and nephritis.", "high"),
    ("IRF7", "ifn", "pdc", "gain", "—", "small", "gwas", "Amplifier of the same axis.", "medium"),
    # --- tolerance and co-stimulation ---------------------------------------------------
    ("PRKCD", "tolerance", "bcell", "loss", "AR", "high", "monogenic",
     "Loss of B-cell apoptosis; autoreactive clones survive selection.", "medium"),
    ("TNFAIP3", "tolerance", "bcell", "loss", "AD", "moderate", "both",
     "A20 haploinsufficiency AND a common SLE locus — the same gene at both ends of the allelic "
     "spectrum, which is exactly the gap between mendelian and population genetics.", "high"),
    ("FAS", "tolerance", "tcell", "loss", "AD", "high", "monogenic",
     "ALPS; lupus-like autoimmunity from failed lymphocyte apoptosis.", "high"),
    ("PTPN22", "costim", "tcell", "gain", "—", "small", "gwas",
     "Shared across autoimmune diseases rather than specific to lupus.", "high"),
    ("BLK", "costim", "bcell", "loss", "—", "small", "gwas", "B-cell receptor signalling.", "medium"),
    ("BANK1", "costim", "bcell", "loss", "—", "small", "gwas", "B-cell scaffold protein.", "medium"),
    ("IKZF1", "tolerance", "bcell", "loss", "—", "small", "gwas", "Lymphoid transcription factor.", "medium"),
    ("ITGAM", "clearance", "mono", "loss", "—", "small", "gwas",
     "CD11b; phagocytosis and adhesion — a clearance gene that arrived through GWAS.", "high"),
    # --- NETosis and organ injury --------------------------------------------------------
    ("PADI4", "netosis", "neut", "gain", "—", "small", "candidate",
     "Citrullination required for NET formation; better established in rheumatoid arthritis.", "low"),
    ("FCGR2A", "immunecomplex", "mono", "loss", "—", "small", "gwas",
     "Immune-complex handling; associated with nephritis.", "high"),
    ("FCGR3A", "immunecomplex", "nk", "loss", "—", "small", "gwas",
     "The same family acting through a different cell.", "medium"),
    ("APOL1", "immunecomplex", "kidney", "gain", "—", "moderate", "gwas",
     "Risk variants shape kidney outcomes in people of African ancestry — a locus where the "
     "disparity in the disease has a named genetic component.", "high"),
]

# -------------------------------------------------------------------------- therapies
# (id, name, molecular target, cell targeted, mechanism modulated, modality, status, note, confidence)
THERAPIES = [
    ("hcq", "Hydroxychloroquine", "endosomal TLR signalling", "pdc", "sensing", "small molecule",
     "standard of care", "Backbone therapy; blunts nucleic-acid sensing.", "high"),
    ("belimumab", "Belimumab", "BAFF / BLyS", "bcell", "tolerance", "antibody", "approved",
     "Removes a B-cell survival signal.", "high"),
    ("anifrolumab", "Anifrolumab", "type I IFN receptor", "pdc", "ifn", "antibody", "approved",
     "Blocks the amplifier rather than the trigger — the interferon signature made actionable.",
     "high"),
    ("rituximab", "Rituximab", "CD20", "bcell", "tolerance", "antibody", "off-label",
     "Depletes B cells but spares CD20-negative plasma cells, the usual explanation for "
     "incomplete responses.", "high"),
    ("voclosporin", "Voclosporin", "calcineurin", "tcell", "costim", "small molecule", "approved",
     "Approved for lupus nephritis.", "medium"),
    ("mmf", "Mycophenolate", "IMPDH", "tcell", "costim", "small molecule", "standard of care",
     "Antiproliferative; a mainstay for nephritis.", "high"),
    ("cart19", "CD19 CAR-T", "CD19", "bcell", "tolerance", "cell therapy", "investigational",
     "The result that reframed the field: deep B-cell depletion has produced drug-free remission "
     "in refractory SLE. A CELL therapy, not a gene therapy.", "medium"),
    ("teclistamab", "BCMA-directed", "BCMA", "plasma", "tolerance", "antibody", "investigational",
     "Aimed at the long-lived plasma cell that B-cell depletion leaves behind.", "low"),
    ("daratumumab", "Anti-CD38", "CD38", "plasma", "tolerance", "antibody", "investigational",
     "Same target cell, different antigen; case reports rather than trials.", "low"),
    ("deucravacitinib", "TYK2 inhibitor", "TYK2", "pdc", "ifn", "small molecule", "investigational",
     "Blocks interferon signalling downstream of the receptor.", "medium"),
    ("baricitinib", "JAK inhibitor", "JAK1/2", "tcell", "ifn", "small molecule", "investigational",
     "Broad cytokine blockade; trial results have been mixed.", "medium"),
    ("obinutuzumab", "Obinutuzumab", "CD20 (type II)", "bcell", "tolerance", "antibody",
     "investigational", "Deeper B-cell depletion than rituximab.", "medium"),
    ("iberdomide", "Cereblon modulator", "IKZF1/3", "bcell", "tolerance", "small molecule",
     "investigational", "Degrades the transcription factors B cells depend on.", "low"),
]


def build_graph() -> dict:
    cells = [dict(id=i, name=n, role=r, lineage=l, kind="cell") for i, n, r, l in CELLS]
    mechs = [dict(id=i, name=n, note=t, kind="mechanism") for i, n, t in MECHANISMS]
    genes = [
        dict(id=g, name=g, mechanism=m, cell=c, effect=e, inherit=inh, penetrance=p,
             evidence=ev, note=note, confidence=conf, kind="gene")
        for g, m, c, e, inh, p, ev, note, conf in GENES
    ]
    thers = [
        dict(id=i, name=n, target=t, cell=c, mechanism=m, modality=mo, status=st,
             note=note, confidence=conf, kind="therapy")
        for i, n, t, c, m, mo, st, note, conf in THERAPIES
    ]

    edges: list[dict] = []
    for g in genes:
        edges.append(dict(source=g["id"], target=g["mechanism"], kind="acts_via"))
        edges.append(dict(source=g["id"], target=g["cell"], kind="acts_in"))
    # A mechanism plays out in every cell some gene assigns to it: derived, not asserted.
    seen: set[tuple[str, str]] = set()
    for g in genes:
        key = (g["mechanism"], g["cell"])
        if key not in seen:
            seen.add(key)
            edges.append(dict(source=g["mechanism"], target=g["cell"], kind="plays_in"))
    for t in thers:
        edges.append(dict(source=t["id"], target=t["cell"], kind="targets"))
        edges.append(dict(source=t["id"], target=t["mechanism"], kind="modulates"))

    # --- reachability: can anything reach this gene? --------------------------------
    # Undirected traversal, because "reaches" here means "shares a cell or a mechanism
    # with", not "acts causally upon". Coarse on purpose, and labelled as such.
    adj: dict[str, set[str]] = defaultdict(set)
    for e in edges:
        adj[e["source"]].add(e["target"])
        adj[e["target"]].add(e["source"])

    therapy_ids = {t["id"] for t in thers}

    def reach(start: str) -> tuple[bool, int, list[str]]:
        """Shortest path length to any therapy, and the path itself."""
        prev: dict[str, str | None] = {start: None}
        q = deque([start])
        while q:
            node = q.popleft()
            if node in therapy_ids:
                path = []
                cur: str | None = node
                while cur is not None:
                    path.append(cur)
                    cur = prev[cur]
                return True, len(path) - 1, list(reversed(path))
            for nxt in sorted(adj[node]):
                if nxt not in prev:
                    prev[nxt] = node
                    q.append(nxt)
        return False, -1, []

    for g in genes:
        ok, dist, path = reach(g["id"])
        g["reachable"] = ok
        g["hops"] = dist
        g["path"] = path

    unreachable = [g["id"] for g in genes if not g["reachable"]]
    # Cells and mechanisms nothing points at — the same question one level up.
    targeted_cells = {t["cell"] for t in thers}
    targeted_mechs = {t["mechanism"] for t in thers}

    return {
        "generated": "2026-08-27",
        "provenance": (
            "Written from working knowledge. Gene-disease relationships are well established; "
            "THE EDGE SET IS A SIMPLIFICATION — most of these genes act in several cells through "
            "several mechanisms, and an edge means 'this is where it is usually described', not "
            "'only here'. 'Reaches' means sharing a cell or mechanism with a therapy, which is a "
            "screening question, not a claim of druggability. Not clinical guidance."
        ),
        "nodes": {"cells": cells, "mechanisms": mechs, "genes": genes, "therapies": thers},
        "edges": edges,
        "analysis": {
            "unreachableGenes": unreachable,
            "cellsWithNoTherapy": [c["id"] for c in cells if c["id"] not in targeted_cells],
            "mechanismsWithNoTherapy": [m["id"] for m in mechs if m["id"] not in targeted_mechs],
            "medianHops": sorted(g["hops"] for g in genes if g["reachable"])[
                max(0, sum(1 for g in genes if g["reachable"]) // 2)
            ] if any(g["reachable"] for g in genes) else -1,
        },
        "summary": {
            "genes": len(genes), "cells": len(cells), "mechanisms": len(mechs),
            "therapies": len(thers), "edges": len(edges),
            "byEvidence": dict(Counter(g["evidence"] for g in genes)),
            "byEffect": dict(Counter(g["effect"] for g in genes)),
            "byModality": dict(Counter(t["modality"] for t in thers)),
            "byStatus": dict(Counter(t["status"] for t in thers)),
        },
    }


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    g = build_graph()
    path = DEST / "lupus_graph.json"
    path.write_text(json.dumps(g, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    s, a = g["summary"], g["analysis"]
    print("wrote %s" % path.relative_to(ROOT))
    print("  %d genes · %d mechanisms · %d cells · %d therapies · %d edges"
          % (s["genes"], s["mechanisms"], s["cells"], s["therapies"], s["edges"]))
    print("  evidence: %s" % s["byEvidence"])
    print("  genes with NO path to any therapy: %s"
          % (", ".join(a["unreachableGenes"]) or "none"))
    print("  cells nothing targets:      %s" % (", ".join(a["cellsWithNoTherapy"]) or "none"))
    print("  mechanisms nothing targets: %s" % (", ".join(a["mechanismsWithNoTherapy"]) or "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
