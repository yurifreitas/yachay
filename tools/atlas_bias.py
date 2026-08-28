#!/usr/bin/env python
"""Interrogate the atlas: which of its numbers are measuring the world, and which are
measuring who did the measuring.

THE PREMISE. A disease catalogue is a screen. Entities (diseases) carry aggregate scores
(genes found, phenotypes annotated) estimated from a varying number of observations
(patients seen, papers written, panels sequenced). That is exactly the shape this library
exists for, so the library's own argument applies to its own data source — and refusing to
apply it there would be the most obvious failure available.

WHAT THIS TESTS. Six named biases, each stated as a mechanism and then measured against
the ingested catalogues. Some come out real, some come out small, and one of them
compromises a chart this project has already drawn. That last one is the point of running
it: a dashboard that only interrogates other people's data is decoration.

    python tools/atlas_bias.py     # writes out/rare/bias.json
"""

from __future__ import annotations

import csv
import io
import json
import math
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

ULTRA = {"<1 / 1 000 000", "1-9 / 1 000 000"}
PREV_ORDER = ["<1 / 1 000 000", "1-9 / 1 000 000", "1-9 / 100 000", "1-5 / 10 000",
              "6-9 / 10 000", ">1 / 1000"]
PREV_RANK = {p: i for i, p in enumerate(PREV_ORDER)}


def spearman(xs: list[float], ys: list[float]) -> float:
    """Rank correlation. Rank rather than Pearson because these are counts with heavy
    tails and no reason to be linear."""
    def rank(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    if len(xs) < 3:
        return float("nan")
    rx, ry = rank(xs), rank(ys)
    n = len(rx)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)

    # ---- load, again but keeping the per-disease detail the atlas summarised away ----
    disease_genes: dict[str, set[str]] = defaultdict(set)
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            g, d = (row.get("gene_symbol") or "").strip(), (row.get("disease_id") or "").strip()
            if g and d:
                disease_genes[d].add(g)

    # Phenotype annotations per disease: a usable proxy for how much attention a disease
    # has received. Not a measure of the disease; a measure of the literature about it.
    annot = Counter()
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        idx = None
        for line in fh:
            if line.startswith("#"):
                continue
            if line.startswith("database_id"):
                idx = line.rstrip("\n").split("\t").index("database_id")
                continue
            if idx is None:
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) > idx:
                annot[parts[idx]] += 1

    # PARSER, NOT REGEX. This file audits the catalogue for invisible things, and it was
    # itself blind twice over (docs/audit.md A11): it never decoded `&lt;`, so the largest
    # band in the corpus was missing from its own streetlight table; and the pattern ran
    # past empty `<PrevalenceClass/>` elements to capture geography names as if they were
    # prevalence classes. An audit tool with the defect it audits for is the worst place in
    # the repository for this to have been.
    prevalence: dict[str, str] = {}

    def _text(node, sub):
        el = node.find(sub)
        return el.text.strip() if el is not None and el.text else None

    for _, disorder in ET.iterparse(str(BY_KEY["orpha_prevalence"].dest), events=("end",)):
        if disorder.tag != "Disorder":
            continue
        code = _text(disorder, "OrphaCode")
        if code:
            classes = [c for c in (_text(rec, "PrevalenceClass/Name")
                                   for rec in disorder.findall("./PrevalenceList/Prevalence"))
                       if c]
            best = min(classes, key=lambda c: PREV_RANK.get(c, 99), default=None)
            prevalence[f"ORPHA:{code}"] = best or "Unknown"
        disorder.clear()

    # Cell-type expression, but this time keeping how many genes each cell type MEASURES,
    # which is the quantity the burden chart never showed.
    gene_top_cell: dict[str, str] = {}
    cell_gene_count = Counter()
    with zipfile.ZipFile(BY_KEY["hpa_single_cell"].dest) as z:
        inner = next(n for n in z.namelist() if n.endswith(".tsv"))
        with z.open(inner) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"), delimiter="\t")
            best: dict[str, tuple[str, float]] = {}
            for row in reader:
                sym = (row.get("Gene name") or "").strip()
                cell = (row.get("Cell type") or "").strip()
                if not sym or not cell:
                    continue
                try:
                    v = float(row.get("nCPM") or row.get("nTPM") or 0)
                except ValueError:
                    continue
                cell_gene_count[cell] += 1
                if sym not in best or v > best[sym][1]:
                    best[sym] = (cell, v)
            gene_top_cell = {g: c for g, (c, _) in best.items()}

    findings: list[dict] = []

    # ---- 1. ASCERTAINMENT: is "has a known gene" a fact about the disease, or about
    #         how much attention it received? -----------------------------------------
    ids = [d for d in annot if d in prevalence or d.startswith("OMIM")]
    xs = [float(annot[d]) for d in ids]
    ys = [1.0 if disease_genes.get(d) else 0.0 for d in ids]
    rho_attention = spearman(xs, ys)
    med_with = sorted(annot[d] for d in ids if disease_genes.get(d))
    med_without = sorted(annot[d] for d in ids if not disease_genes.get(d))
    findings.append({
        "id": "ascertainment",
        "name": "Ascertainment bias",
        "mechanism": (
            "A gene is found in diseases that are studied, and diseases are studied when "
            "there are patients to study. So 'has a known gene' is partly a measure of "
            "attention, not of tractability."
        ),
        "test": "Rank correlation between phenotype annotations (a proxy for attention) "
                "and whether a causal gene is known.",
        "statistic": round(rho_attention, 4),
        "detail": (
            f"Median annotations: {med_with[len(med_with)//2] if med_with else 0} for diseases "
            f"with a gene, {med_without[len(med_without)//2] if med_without else 0} for those "
            f"without ({len(med_with):,} vs {len(med_without):,} diseases)."
        ),
        "verdict": "real" if abs(rho_attention) > 0.15 else "small",
    })

    # ---- 2. THE STREETLIGHT: does prevalence predict whether a gene is known? --------
    orpha = [d for d in prevalence if prevalence[d] in PREV_RANK]
    xs = [float(PREV_RANK[prevalence[d]]) for d in orpha]        # 0 = rarest
    ys = [1.0 if disease_genes.get(d) else 0.0 for d in orpha]
    rho_prev = spearman(xs, ys)
    by_band = {}
    for band in PREV_ORDER:
        members = [d for d in orpha if prevalence[d] == band]
        if members:
            by_band[band] = {
                "diseases": len(members),
                "withGene": sum(1 for d in members if disease_genes.get(d)),
                "share": round(sum(1 for d in members if disease_genes.get(d)) / len(members), 4),
            }
    findings.append({
        "id": "streetlight",
        "name": "The streetlight effect",
        "mechanism": (
            "Looking where the light is. The rarer a disease, the fewer patients exist to "
            "sequence, so the less likely its cause has been found — which means a "
            "catalogue read naively says rare diseases are less genetic. They are not; "
            "they are less studied."
        ),
        "test": "Rank correlation between prevalence band (rarest first) and whether a "
                "causal gene is known, across Orphanet diseases with a stated prevalence.",
        "statistic": round(rho_prev, 4),
        "detail": " · ".join(
            f"{b}: {v['share']*100:.0f}% of {v['diseases']:,}" for b, v in by_band.items()
        ),
        "byBand": by_band,
        "verdict": "real" if abs(rho_prev) > 0.15 else "small",
    })

    # ---- 3. THE ONE THAT COMPROMISES OUR OWN CHART ------------------------------------
    # Is the cell-type burden chart measuring biology, or panel coverage?
    burden = Counter()
    for d, genes in disease_genes.items():
        for g in genes:
            c = gene_top_cell.get(g)
            if c:
                burden[c] += 1
    cells = sorted(set(burden) | set(cell_gene_count))
    xs = [float(cell_gene_count.get(c, 0)) for c in cells]
    ys = [float(burden.get(c, 0)) for c in cells]
    rho_panel = spearman(xs, ys)
    findings.append({
        "id": "panel_coverage",
        "name": "Panel coverage masquerading as biology",
        "mechanism": (
            "A cell type that was measured for more genes has more chances to be some "
            "gene's maximum. So a chart of 'disease genes peaking in this cell type' may "
            "be a chart of how deeply each cell type was sequenced."
        ),
        "test": "Rank correlation between the number of genes measured in a cell type and "
                "the number of disease genes peaking there.",
        "statistic": round(rho_panel, 4),
        "detail": (
            f"Across {len(cells)} cell types. This tests a chart THIS PROJECT already drew "
            f"(the cell-burden bar chart in the world atlas)."
        ),
        "verdict": "compromising" if abs(rho_panel) > 0.5 else
                   "real" if abs(rho_panel) > 0.15 else "small",
        "selfTest": True,
    })

    # ---- 4. VARYING OBSERVATION COUNT: the library's own claim, on this data ----------
    counts = sorted(len(g) for g in disease_genes.values())
    n = len(counts)
    findings.append({
        "id": "varying_n",
        "name": "Varying observation count",
        "mechanism": (
            "Genes per disease ranges over orders of magnitude. Any ranking of diseases by "
            "an aggregate over their genes is therefore partly a ranking of how many genes "
            "each has — which is this repository's founding claim, applied to its own "
            "reference data."
        ),
        "test": "Distribution of genes per disease.",
        "statistic": round(counts[-1] / max(counts[0], 1), 1) if counts else 0,
        "detail": (
            f"min {counts[0]}, median {counts[n//2]}, p95 {counts[int(n*0.95)]}, "
            f"max {counts[-1]} across {n:,} diseases — a spread of "
            f"{counts[-1] // max(counts[0], 1)}x."
        ),
        "verdict": "real",
    })

    # ---- 5. MISSING NOT AT RANDOM ------------------------------------------------------
    unknown = [d for d in prevalence if prevalence[d] not in PREV_RANK]
    known = [d for d in prevalence if prevalence[d] in PREV_RANK]
    share_gene_unknown = (sum(1 for d in unknown if disease_genes.get(d)) / len(unknown)) if unknown else 0
    share_gene_known = (sum(1 for d in known if disease_genes.get(d)) / len(known)) if known else 0
    findings.append({
        "id": "mnar",
        "name": "Missing not at random",
        "mechanism": (
            "Prevalence is absent for a reason correlated with everything else: a disease "
            "nobody has counted is usually one nobody has studied. Treating 'Unknown' as a "
            "neutral category averages two different populations together."
        ),
        "test": "Share with a known gene, among diseases with a stated prevalence versus "
                "those without.",
        "statistic": round(share_gene_known - share_gene_unknown, 4),
        "detail": (
            f"{share_gene_known*100:.0f}% of the {len(known):,} with a stated prevalence have "
            f"a gene, against {share_gene_unknown*100:.0f}% of the {len(unknown):,} without."
        ),
        "verdict": "real" if abs(share_gene_known - share_gene_unknown) > 0.05 else "small",
    })

    # ---- 6. SURVIVORSHIP -----------------------------------------------------------------
    findings.append({
        "id": "survivorship",
        "name": "Survivorship of the catalogue itself",
        "mechanism": (
            "Every disease here is one somebody described, named and got accepted into a "
            "reference. Diseases too rare to have been seen twice, or seen only where no "
            "catalogue reaches, are absent — and absent in a way no statistic computed FROM "
            "the catalogue can detect."
        ),
        "test": "Not testable from this data. Stated so it is not mistaken for absent.",
        "statistic": None,
        "detail": "The denominator of every percentage on this page is the catalogue, not "
                  "the world. Nothing here can measure that gap.",
        "verdict": "untestable",
    })

    payload = {
        "generated": "2026-08-27",
        "premise": (
            "A disease catalogue is a screen: entities carry aggregate scores estimated from "
            "a varying number of observations. This library's argument therefore applies to "
            "its own reference data, and these are the results of applying it."
        ),
        "findings": findings,
        "cellPanel": [
            {"cell": c, "genesMeasured": cell_gene_count.get(c, 0), "diseaseGenes": burden.get(c, 0)}
            for c in sorted(cells, key=lambda x: -burden.get(x, 0))[:40]
        ],
    }
    path = DEST / "bias.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("wrote %s" % path.relative_to(ROOT))
    for f in findings:
        stat = "n/a" if f["statistic"] is None else f"{f['statistic']:+.3f}" if isinstance(f["statistic"], float) else f["statistic"]
        print(f"  [{f['verdict']:>13}] {f['name']:<44} {stat}")
        print(f"                  {f['detail'][:150]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
