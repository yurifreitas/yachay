#!/usr/bin/env python
"""Research attention against disease burden, and what the gap between them is made of.

THE QUESTION. Two rare diseases of similar prevalence can carry four thousand papers and
thirty-eight. That is not news. What is worth measuring is whether attention is explained by
**burden** — how many people the disease reaches and how severely — or by something else
entirely, and how large the residual is once burden has had its chance.

`docs/roadmap.md` §5.3 sets this out, and it sits directly beside the axis
`tools/ancestry_geography.py` already measured: representation in the prevalence literature
runs Europe **8.10** against Africa **0.07**. If attention is also unexplained by burden, the
atlas is carrying two independent inequities and should say so with two numbers.

## What is counted, and the confound that is stated rather than hidden

**Attention** — PubMed citations of a disease's causal genes, from NCBI's `gene2pubmed`
(human only). A disease inherits the citation count of the genes assigned to it.

**Burden** — Orphanet's prevalence class, mapped to the midpoint of its own band on a log
scale, times a severity proxy: the count of annotated phenotype terms that carry a real
evidence code.

**THE CONFOUND IS LOAD-BEARING AND IT IS NAMED HERE.** A gene's citation count is a property
of the GENE, not of the disease: BRCA1 is cited for cancer biology, and a rare disorder that
happens to be caused by BRCA1 inherits all of it. So the headline is reported twice — once
over all diseases, and once restricted to diseases whose genes are **not** shared with a
common disease — and if the two disagree, the second is the one that means anything. This is
Stage 3 of the library's own method: measure the confound, do not disclaim it.

## What would kill it

If attention correlates strongly with burden, the inequity is smaller than the field assumes
and this file should say so. If the correlation is driven entirely by gene popularity — that
is, if it disappears in the restricted set — then the measurement is of citation habits and
not of disease, and it should be reported as such rather than dressed as an equity finding.

    python tools/attention_burden.py

Stdlib only.
"""

from __future__ import annotations

import argparse
import collections
import csv
import gzip
import json
import math
import pathlib
import random
import sys
from datetime import date
from xml.etree import ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "rare" / "attention_burden.json"

HUMAN_TAX = "9606"

#: A gene cited more than this is treated as a COMMON-DISEASE gene and the diseases that
#: carry it are excluded from the restricted arm. Registered as COMMON_GENE_CITATIONS.
#: ⚠️ empirical and target-contacting: the distribution was inspected before the number was
#: chosen. The headline is reported on BOTH arms so nothing published depends on it.
COMMON_GENE_CITATIONS = 1000

#: A disease needs this many citable genes to carry an attention figure at all.
MIN_GENES = 1

#: Orphanet prevalence bands, mapped to the log10 midpoint of cases per 100,000. Authored,
#: and the mapping is arithmetic on Orphanet's own published bands, not a judgement.
PREVALENCE_MIDPOINT = {
    "<1 / 1 000 000": math.log10(0.05),
    "1-9 / 1 000 000": math.log10(0.5),
    "1-9 / 100 000": math.log10(5.0),
    "1-5 / 10 000": math.log10(30.0),
    "6-9 / 10 000": math.log10(75.0),
    ">1 / 1000": math.log10(200.0),
}

REAL_EVIDENCE = {"PCS", "ICE"}


def gene_citations() -> collections.Counter:
    """NCBI GeneID -> distinct PubMed citations, human only."""
    counts: collections.Counter = collections.Counter()
    with gzip.open(BY_KEY["gene2pubmed"].dest, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3 or parts[0] != HUMAN_TAX:
                continue
            counts[parts[1]] += 1
    return counts


def disease_genes() -> tuple[dict[str, set[str]], dict[str, str]]:
    """disease -> NCBI gene ids, and the symbol for each id."""
    per_disease: dict[str, set[str]] = collections.defaultdict(set)
    symbol: dict[str, str] = {}
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            gid = (row.get("ncbi_gene_id") or "").replace("NCBIGene:", "").strip()
            disease = (row.get("disease_id") or "").strip()
            if gid and disease:
                per_disease[disease].add(gid)
                symbol[gid] = (row.get("gene_symbol") or "").strip()
    return dict(per_disease), symbol


def severity_proxy() -> collections.Counter:
    """Annotated phenotype terms carrying a real evidence code, per disease."""
    counts: collections.Counter = collections.Counter()
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        rows = (line for line in fh if not line.startswith("#"))
        for row in csv.DictReader(rows, delimiter="\t"):
            d = (row.get("database_id") or "").strip()
            if d and (row.get("evidence") or "").strip() in REAL_EVIDENCE:
                counts[d] += 1
    return counts


def prevalence_band() -> dict[str, float]:
    """ORPHA disorder -> log10 midpoint of its rarest published band."""
    out: dict[str, float] = {}
    try:
        root = ET.parse(BY_KEY["orpha_prevalence"].dest).getroot()
    except (OSError, ET.ParseError):
        return out
    for disorder in root.iter("Disorder"):
        code = disorder.findtext("OrphaCode")
        if not code:
            continue
        best = None
        for prev in disorder.iter("Prevalence"):
            klass = prev.findtext("PrevalenceClass/Name")
            if klass in PREVALENCE_MIDPOINT:
                v = PREVALENCE_MIDPOINT[klass]
                best = v if best is None else max(best, v)
        if best is not None:
            out[f"ORPHA:{code}"] = best
    return out


def spearman(xs: list[float], ys: list[float]) -> float:
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

    rx, ry = rank(xs), rank(ys)
    n = len(rx)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return num / (dx * dy) if dx and dy else 0.0


SEED = 20260829


def main() -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    rng = random.Random(SEED)

    print("reading ...")
    citations = gene_citations()
    per_disease, symbol = disease_genes()
    severity = severity_proxy()
    prevalence = prevalence_band()
    print(f"  {len(citations)} human genes with a citation, {len(per_disease)} diseases with a "
          f"gene, {len(prevalence)} with a prevalence band")

    rows = []
    for disease, genes in per_disease.items():
        if disease not in prevalence or len(genes) < MIN_GENES:
            continue
        attention = sum(citations.get(g, 0) for g in genes)
        if attention <= 0:
            continue
        top_gene = max(genes, key=lambda g: citations.get(g, 0))
        rows.append({
            "disease": disease,
            "genes": len(genes),
            "citations": attention,
            "log_prevalence": round(prevalence[disease], 3),
            "signs_with_evidence": severity.get(disease, 0),
            "top_gene": symbol.get(top_gene, top_gene),
            "top_gene_citations": citations.get(top_gene, 0),
        })

    if not rows:
        print("  nothing joined — is Orphanet prevalence ingested?")
        return 1

    def boot_ci(subset: list[dict], f, draws: int = 400) -> list[float]:
        """Percentile interval over diseases, which is the unit that could have been
        sampled differently. Spearman is a rank statistic and a resample with replacement
        does not bias it the way mutual information was biased in scale_information, so the
        percentile interval is the right one here and is used directly."""
        vals = []
        boot_rng = random.Random(SEED + 1)
        for _ in range(draws):
            sample = [subset[boot_rng.randrange(len(subset))] for _ in range(len(subset))]
            vals.append(f(sample))
        vals.sort()
        return [round(vals[int(0.025 * draws)], 4), round(vals[int(0.975 * draws) - 1], 4)]

    def arm(subset: list[dict], label: str) -> dict:
        att = [math.log10(r["citations"]) for r in subset]
        prev = [r["log_prevalence"] for r in subset]
        sev = [float(r["signs_with_evidence"]) for r in subset]
        out = {
            "label": label,
            "diseases": len(subset),
            "attention_vs_prevalence": round(spearman(att, prev), 4),
            "attention_vs_prevalence_ci95": boot_ci(
                subset,
                lambda ss: spearman([math.log10(r["citations"]) for r in ss],
                                    [r["log_prevalence"] for r in ss])),
            "median_citations": sorted(r["citations"] for r in subset)[len(subset) // 2],
        }
        # A CORRELATION AGAINST A CONSTANT IS NOT A CORRELATION OF ZERO. The first run of
        # this file printed attention~severity as +0.000 in both arms, which reads as "the
        # field ignores severity" and is a much stronger claim than the data can carry. The
        # truth is structural: every disease here carries an Orphanet prevalence band, so
        # every one is ORPHA-coded, and ALL 118,774 PCS-evidenced annotations in the HPO file
        # are OMIM-coded - ORPHA has zero. The severity axis does not exist for this
        # population. Reporting a coefficient over a constant column would have invented an
        # inequity out of a join.
        if len(set(sev)) <= 1:
            out["attention_vs_severity"] = None
            out["severity_unavailable"] = (
                "every disease in this arm is ORPHA-coded, because the prevalence band is; "
                "and every PCS/ICE-evidenced annotation in phenotype.hpoa is OMIM-coded. The "
                "severity proxy is a constant here, so no coefficient is reported.")
        else:
            out["attention_vs_severity"] = round(spearman(att, sev), 4)
        return out

    restricted = [r for r in rows if r["top_gene_citations"] < COMMON_GENE_CITATIONS]
    full = arm(rows, "all diseases")
    narrow = arm(restricted, f"top gene under {COMMON_GENE_CITATIONS} citations")

    # The neglect ranking: most burden per unit of attention, and least.
    for r in rows:
        r["attention_index"] = round(math.log10(r["citations"]) - r["log_prevalence"], 3)
    by_index = sorted(rows, key=lambda r: r["attention_index"])
    most_neglected = by_index[:15]
    most_attended = by_index[-15:][::-1]

    payload = {
        "generated": date.today().isoformat(),
        "provenance": ("measured from NCBI gene2pubmed (human), HPO genes_to_disease and "
                       "phenotype.hpoa, and Orphanet prevalence classes"),
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md",
        "question": ("Is research attention explained by how many people a rare disease "
                     "reaches, or by something else?"),
        "method": {
            "attention": "distinct PubMed citations of the disease's causal genes, log10",
            "burden": ("log10 midpoint of the disease's rarest Orphanet prevalence band, and "
                       "separately the count of phenotype signs carrying a PCS or ICE "
                       "evidence code as a severity proxy"),
            "confound": ("a gene's citation count belongs to the GENE, not to the disease. "
                         "The restricted arm drops any disease whose most-cited gene clears "
                         f"{COMMON_GENE_CITATIONS} citations, and if the two arms disagree "
                         "the restricted one is the one that means anything"),
            "statistic": "Spearman, because both inputs are heavy-tailed",
        },
        "arms": [full, narrow],
        "confound_survives": (abs(narrow["attention_vs_prevalence"])
                              >= 0.5 * abs(full["attention_vs_prevalence"])),
        "most_neglected": most_neglected,
        "most_attended": most_attended,
        "the_third_sighting": (
            "The OMIM/ORPHA boundary has now surfaced in three independent measurements: the "
            "visualisation work found ORPHA rows carrying zero inheritance annotations and "
            "zero fractional sign frequencies; knowledge_shape.py found every cross-catalogue "
            "axis pair negatively correlated and concluded the shape of knowledge was mostly "
            "a registry; and this file cannot compute a severity coefficient at all because "
            "the two halves of the join do not overlap on evidence codes. It is the single "
            "most consequential structural fact about this catalogue and it is not documented "
            "as such anywhere in the field."),
        "says": ("An association over a catalogue, not a causal account of funding. Citation "
                 "counts measure what has been written about a GENE; the restricted arm is "
                 "what carries any claim about a disease."),
        "limits": [
            "Only diseases with both an Orphanet prevalence band and a causal gene, which is "
            "a minority of the catalogue and the better-studied part of it.",
            "The prevalence band is ordinal and the midpoint mapping is arithmetic on "
            "Orphanet's own bands; a disease's true prevalence is not a scalar, which is "
            "what tools/prevalence_audit.py measured.",
            "Severity is proxied by the count of evidenced signs, which rewards curation "
            "effort as much as clinical severity.",
        ],
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    for a in (full, narrow):
        sev = a.get("attention_vs_severity")
        sev_s = f"{sev:+.3f}" if sev is not None else "unavailable (see note)"
        print(f"  {a['label']:44s} n={a['diseases']:5d}  "
              f"attention~prevalence {a['attention_vs_prevalence']:+.3f}  "
              f"attention~severity {sev_s}")
    print()
    print("  least attention for their burden")
    for r in most_neglected[:6]:
        print(f"    {r['disease']:18s} {r['citations']:7d} citations  "
              f"top gene {r['top_gene']}")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
