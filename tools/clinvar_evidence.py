#!/usr/bin/env python
"""ClinVar as an evidence-grading problem, and as a check on the patient corpus.

WHY THIS SOURCE AND WHY NOW. `docs/references/patient-data.md` §2e recorded a selection
effect that limits everything built on phenopackets: **every one of its 11,243 ACMG
classifications is PATHOGENIC**. It is an answer key, not a diagnostic pile. That is fine as
long as nothing pretends otherwise - and it leaves one question open that only a wider
corpus can answer: *what does everyone else say about those same variants?*

ClinVar is that corpus. It carries the classifications the field actually submits, including
the two categories phenopackets cannot contain: **uncertain significance**, which is where
rare-disease diagnosis really lives, and **conflicting interpretations**, which is two
laboratories disagreeing about one variant in writing.

FOUR MEASUREMENTS.

  1. THE VUS SHARE. What fraction of submitted variants are uncertain, overall and per gene.
     A gene whose variants are mostly VUS is a gene where a new patient's variant will
     probably be uninterpretable, and that is a property worth knowing before promising
     anyone a diagnosis.

  2. REVIEW STATUS AS AN EVIDENCE GRADE. ClinVar already grades its own evidence, from "no
     assertion criteria provided" to "reviewed by expert panel" and "practice guideline".
     This repository has spent its whole audit inventing grades for other people's data
     (docs/audit.md A12); here the grade is supplied, and the question is only how much of
     the corpus sits at the bottom of it.

  3. DISAGREEMENT BETWEEN SUBMITTERS. Conflicting classifications, counted. Every other
     authored-versus-measured confrontation in this project (A13, A14, A18) was ours against
     a catalogue. This one is the field against itself, and it needs no adjudication from us
     to be informative.

  4. THE CROSS-CHECK. Our 11,454 phenopacket variants, looked up in ClinVar by genomic
     coordinate. They are all PATHOGENIC in the patient corpus. How many are pathogenic in
     ClinVar, how many are uncertain, and how many are not there at all?

    python tools/clinvar_evidence.py     # writes out/rare/clinvar_evidence.json

Reads a 442 MB gzip in one pass; expect a minute or two. Stdlib only.
"""

from __future__ import annotations

import gzip
import json
import pathlib
import sys
import zipfile
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

RARE = ROOT / "out" / "rare"

# ClinVar's own review status vocabulary, ordered. The star count is ClinVar's, not ours -
# this is the rare case where the evidence grade arrives with the data instead of having to
# be invented for it.
STARS = {
    "practice guideline": 4,
    "reviewed by expert panel": 3,
    "criteria provided, multiple submitters, no conflicts": 2,
    "criteria provided, conflicting classifications": 1,
    "criteria provided, conflicting interpretations": 1,
    "criteria provided, single submitter": 1,
    "no assertion criteria provided": 0,
    "no classification provided": 0,
    "no assertion provided": 0,
    "no classifications from unflagged records": 0,
    "no classification for the single variant": 0,
}


def bucket(significance: str) -> str:
    """Collapse ClinVar's free-ish significance strings into the categories people act on."""
    s = (significance or "").lower()
    if "conflicting" in s:
        return "conflicting"
    if "pathogenic" in s and "likely" in s and "benign" not in s:
        return "likely pathogenic"
    if "pathogenic" in s and "benign" not in s:
        return "pathogenic"
    if "uncertain" in s:
        return "uncertain significance"
    if "likely benign" in s:
        return "likely benign"
    if "benign" in s:
        return "benign"
    if not s or s == "not provided":
        return "not provided"
    return "other"


def phenopacket_variants() -> set[str]:
    """The hg38 coordinates of every variant in the patient corpus, for the cross-check."""
    keys: set[str] = set()
    path = BY_KEY["phenopackets"].dest
    if not path.exists():
        return keys
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith(".json"):
                continue
            p = json.loads(z.read(name))
            for i in p.get("interpretations", []) or []:
                for g in (i.get("diagnosis") or {}).get("genomicInterpretations", []) or []:
                    vd = (g.get("variantInterpretation") or {}).get("variationDescriptor") or {}
                    v = vd.get("vcfRecord") or {}
                    if v.get("chrom") and v.get("pos"):
                        chrom = str(v["chrom"]).replace("chr", "")
                        keys.add(f"{chrom}:{v['pos']}:{v.get('ref')}:{v.get('alt')}")
    return keys


def main() -> int:
    path = BY_KEY["clinvar"].dest
    if not path.exists():
        raise SystemExit("missing %s — run python tools/ingest.py" % path.name)

    print("reading the patient corpus for the cross-check ...")
    ours = phenopacket_variants()
    print("  %s variant coordinates" % f"{len(ours):,}")

    print("reading ClinVar (442 MB, one pass) ...")
    total = 0
    kept = 0
    sig = Counter()
    stars = Counter()
    submitters = Counter()
    by_gene: dict[str, Counter] = defaultdict(Counter)
    ours_found: Counter = Counter()
    seen_ours: set[str] = set()

    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        header = next(fh).rstrip("\n").split("\t")
        idx = {c: i for i, c in enumerate(header)}
        for line in fh:
            total += 1
            row = line.rstrip("\n").split("\t")
            if len(row) < len(header):
                continue
            # One row per assembly; GRCh38 only, or every variant is counted twice.
            if row[idx["Assembly"]] != "GRCh38":
                continue
            kept += 1

            b = bucket(row[idx["ClinicalSignificance"]])
            sig[b] += 1
            rs = row[idx["ReviewStatus"]].strip().lower()
            stars[STARS.get(rs, 0)] += 1

            try:
                submitters[min(int(row[idx["NumberSubmitters"]] or 0), 10)] += 1
            except ValueError:
                pass

            gene = row[idx["GeneSymbol"]].strip()
            if gene and ";" not in gene and gene != "-":
                by_gene[gene][b] += 1

            if ours:
                chrom = row[idx["Chromosome"]].strip()
                pos = row[idx["PositionVCF"]].strip()
                ref = row[idx["ReferenceAlleleVCF"]].strip()
                alt = row[idx["AlternateAlleleVCF"]].strip()
                key = f"{chrom}:{pos}:{ref}:{alt}"
                if key in ours:
                    seen_ours.add(key)
                    ours_found[b] += 1

    # ---- per gene: where is a new patient's variant likely to be uninterpretable? -------
    gene_rows = []
    for gene, counts in by_gene.items():
        n = sum(counts.values())
        if n < 50:
            continue
        vus = counts.get("uncertain significance", 0)
        gene_rows.append({
            "gene": gene,
            "variants": n,
            "vus": vus,
            "vusShare": round(vus / n, 4),
            "pathogenic": counts.get("pathogenic", 0) + counts.get("likely pathogenic", 0),
            "conflicting": counts.get("conflicting", 0),
        })
    gene_rows.sort(key=lambda r: -r["variants"])
    worst_vus = sorted(gene_rows, key=lambda r: -r["vusShare"])[:25]

    total_kept = sum(sig.values()) or 1
    low_stars = stars.get(0, 0) + stars.get(1, 0)

    payload = {
        "generated": "tools/clinvar_evidence.py",
        "input": str(path.relative_to(ROOT)).replace("\\", "/"),
        "premise": (
            "Every ACMG class in the phenopacket corpus is PATHOGENIC - it is an answer key, "
            "not a diagnostic pile. ClinVar carries what the field actually submits, "
            "including the two categories phenopackets cannot contain: uncertain "
            "significance, and two laboratories disagreeing in writing."
        ),
        "scale": {
            "rows": total,
            "grch38Rows": kept,
            "genesWithFiftyOrMore": len(gene_rows),
        },
        "significance": {
            "counts": dict(sig.most_common()),
            "vusShare": round(sig.get("uncertain significance", 0) / total_kept, 4),
            "conflictingShare": round(sig.get("conflicting", 0) / total_kept, 4),
        },
        "reviewStatus": {
            "byStars": {str(k): v for k, v in sorted(stars.items())},
            "atOneStarOrLess": low_stars,
            "shareAtOneStarOrLess": round(low_stars / total_kept, 4),
            "says": (
                "ClinVar grades its own evidence, which is the rare case where the grade "
                "arrives with the data instead of having to be invented for it "
                "(docs/audit.md A12). The question is only how much of the corpus sits at "
                "the bottom of that scale."
            ),
        },
        "submitters": {str(k): v for k, v in sorted(submitters.items())},
        "vusByGene": {
            # The FULL table ships, not the worst 25. sieve.stages.target reads it per gene,
            # and a truncated head would silently limit which genes can be assessed - the
            # same selection error docs/audit.md keeps finding in build scripts.
            "all": gene_rows,
            "worst": worst_vus,
            "says": (
                "A gene whose variants are mostly of uncertain significance is a gene where "
                "the next patient's variant will probably be uninterpretable. That is a "
                "property of the gene's evidence base, not of the patient, and it is "
                "knowable before anyone is promised a diagnosis."
            ),
        },
        "crossCheck": {
            "patientVariants": len(ours),
            "foundInClinVar": len(seen_ours),
            "notInClinVar": len(ours) - len(seen_ours),
            "bySignificance": dict(ours_found.most_common()),
            "says": (
                "Every one of these is PATHOGENIC in the patient corpus by construction. "
                "This is what the wider field says about the same coordinates."
            ),
        },
    }

    RARE.mkdir(parents=True, exist_ok=True)
    dest = RARE / "clinvar_evidence.json"
    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print("wrote %s" % dest.relative_to(ROOT))
    print("  %s rows, %s on GRCh38" % (f"{total:,}", f"{kept:,}"))
    print("  significance:")
    for k, v in sig.most_common(7):
        print("    %-26s %9s  %5.1f%%" % (k, f"{v:,}", 100 * v / total_kept))
    print("  review status (ClinVar's own stars):")
    for k in sorted(stars):
        print("    %d star %-12s %9s  %5.1f%%"
              % (k, "", f"{stars[k]:,}", 100 * stars[k] / total_kept))
    print("  %s of %s (%.1f%%) sit at one star or less"
          % (f"{low_stars:,}", f"{total_kept:,}", 100 * low_stars / total_kept))
    print()
    cc = payload["crossCheck"]
    print("  CROSS-CHECK — our %s patient variants, all PATHOGENIC by construction:"
          % f"{cc['patientVariants']:,}")
    print("    found in ClinVar: %s   absent: %s"
          % (f"{cc['foundInClinVar']:,}", f"{cc['notInClinVar']:,}"))
    for k, v in ours_found.most_common():
        print("      %-26s %6s" % (k, f"{v:,}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
