#!/usr/bin/env python
"""The genotype layer: what the extraction was throwing away.

`tools/patient_frequencies.py` reads 10,377 phenopackets and keeps two things per patient —
the disease, and which HPO terms were observed or excluded. A field census showed what that
discards, and it is most of the record:

    variant allelic state   11,454  (100% of genomic interpretations)
    variant gene context    11,385  (99%)
    variant ACMG class      11,243  (98%)
    variant VCF coordinates 10,812  (94%)
    variant HGVS            10,810  (94%)
    subject sex              9,578  (92% of patients)
    subject age              7,939  (77%)

So the project has had per-patient genotype on disk and has been reading phenotype only.
This file reads the rest, and asks the three questions the genotype makes possible.

  1. THE ALLELIC SPECTRUM. Per gene: how many DISTINCT variants, over how many patients, and
     what share of variants were seen exactly once. This is the honest test of what a
     "causal gene" attribution rests on - a characterised locus with recurrent alleles, or
     one variant in one family reported once.

  2. ZYGOSITY AGAINST THE DECLARED INHERITANCE. HPO records a mode of inheritance per
     disease; the patients record an allelic state per variant. This is the
     authored-versus-measured confrontation the rest of this repository keeps running
     (docs/audit.md A13, A14, A18), pointed at inheritance and settled with individuals -
     and the first version of it was WRONG in an instructive way, described at the check
     itself: it flagged compound heterozygosity, which is the normal case, 61 times.

  3. THE CONSEQUENCE MIX. Nonsense, frameshift, missense and splice are different mechanisms
     with different therapeutic implications - readthrough works on a premature stop and not
     on a missense. The class is derived from the HGVS protein expression, conservatively:
     anything the rules below cannot place is `unclassified` rather than guessed.

AND ONE FIELD THAT LOOKS LIKE SURVIVAL DATA AND IS NOT. `vitalStatus` appears on 707
patients (7%) and **every one of them is DECEASED**. `ALIVE` is never recorded. So the field
is a death register, not a survival denominator, and a mortality rate computed from it would
be 100% by construction. It is reported here with that warning rather than omitted, because
the trap is easier to fall into than to notice.

    python tools/patient_variants.py     # writes out/rare/patient_variants.json

Stdlib only.
"""

from __future__ import annotations

import csv
import json
import pathlib
import re
import sys
import zipfile
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

RARE = ROOT / "out" / "rare"

# Consequence from the HGVS protein expression, in the order the rules are tried. These are
# textual rules over a nomenclature, not a variant effect predictor: they place what HGVS
# states plainly and refuse the rest. `unclassified` is a value, and its count is published
# beside the others so nobody reads this as a complete annotation.
def consequence(hgvs_p: str, hgvs_c: str) -> str:
    p, c = hgvs_p or "", hgvs_c or ""
    if "fs" in p:
        return "frameshift"
    if "Ter" in p or p.endswith("*") or "*" in p.split("p.")[-1][:12]:
        return "nonsense"
    if re.search(r"c\.[-\d_+*]+[+-]\d", c) or "splice" in c.lower():
        return "splice region"
    if "del" in c and "ins" in c:
        return "indel"
    if "dup" in c:
        return "duplication"
    if "del" in c:
        return "deletion"
    if "ins" in c:
        return "insertion"
    if re.search(r"p\.\(?[A-Z][a-z]{2}\d+[A-Z][a-z]{2}\)?", p):
        return "missense"
    if "p.(=)" in p or "p.=" in p:
        return "synonymous"
    return "unclassified"


def inheritance_by_disease() -> dict[str, set[str]]:
    """Mode of inheritance per disease, from HPO aspect I — the authored side."""
    out: dict[str, set[str]] = defaultdict(set)
    labels = {
        "HP:0000006": "autosomal dominant",
        "HP:0000007": "autosomal recessive",
        "HP:0001417": "X-linked",
        "HP:0001419": "X-linked recessive",
        "HP:0001423": "X-linked dominant",
        "HP:0001427": "mitochondrial",
        "HP:0010985": "gonosomal",
        "HP:0001428": "somatic",
    }
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            header = line.rstrip("\n").split("\t")
            break
        idx = {n: i for i, n in enumerate(header)}
        for row in csv.reader(fh, delimiter="\t"):
            if len(row) > idx["aspect"] and row[idx["aspect"]] == "I":
                term = row[idx["hpo_id"]]
                if term in labels:
                    out[row[idx["database_id"]]].add(labels[term])
    return out


def main() -> int:
    path = BY_KEY["phenopackets"].dest
    if not path.exists():
        raise SystemExit("missing %s — run python tools/ingest.py" % path.name)

    variants = []
    per_patient = []
    deceased = 0
    vital_recorded = Counter()

    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith(".json"):
                continue
            p = json.loads(z.read(name))
            subject = p.get("subject", {}) or {}

            diseases = set()
            for interp in p.get("interpretations", []) or []:
                d = (interp.get("diagnosis") or {}).get("disease") or {}
                if d.get("id"):
                    diseases.add((d["id"], d.get("label") or d["id"]))
            if not diseases:
                continue
            did, dlabel = sorted(diseases)[0]

            vs = (subject.get("vitalStatus") or {}).get("status")
            if vs:
                vital_recorded[vs] += 1
                if vs == "DECEASED":
                    deceased += 1

            age = subject.get("timeAtLastEncounter") or {}
            per_patient.append({
                "id": p.get("id"),
                "disease": did,
                "diseaseLabel": dlabel,
                "sex": subject.get("sex"),
                "hasAge": bool(age),
                "vitalStatus": vs,
            })

            for interp in p.get("interpretations", []) or []:
                for g in (interp.get("diagnosis") or {}).get("genomicInterpretations", []) or []:
                    vi = g.get("variantInterpretation") or {}
                    vd = vi.get("variationDescriptor") or {}
                    expr = {e.get("syntax"): e.get("value")
                            for e in (vd.get("expressions") or [])}
                    gene = (vd.get("geneContext") or {}).get("symbol")
                    vcf = vd.get("vcfRecord") or {}
                    key = (f"{vcf.get('chrom')}:{vcf.get('pos')}{vcf.get('ref')}>{vcf.get('alt')}"
                           if vcf else expr.get("hgvs.c") or vd.get("id"))
                    variants.append({
                        "patient": p.get("id"),
                        "disease": did,
                        "diseaseLabel": dlabel,
                        "gene": gene,
                        "key": key,
                        "hgvsC": expr.get("hgvs.c"),
                        "hgvsP": expr.get("hgvs.p"),
                        "acmg": vi.get("acmgPathogenicityClassification"),
                        "zygosity": (vd.get("allelicState") or {}).get("label"),
                        "consequence": consequence(expr.get("hgvs.p"), expr.get("hgvs.c")),
                    })

    # ---- 1. the allelic spectrum, per gene ----------------------------------------------
    by_gene: dict[str, list] = defaultdict(list)
    for v in variants:
        if v["gene"]:
            by_gene[v["gene"]].append(v)

    spectrum = []
    for gene, vs in by_gene.items():
        counts = Counter(v["key"] for v in vs if v["key"])
        singletons = sum(1 for c in counts.values() if c == 1)
        spectrum.append({
            "gene": gene,
            "patients": len({v["patient"] for v in vs}),
            "distinctVariants": len(counts),
            "seenOnce": singletons,
            "privateShare": round(singletons / len(counts), 3) if counts else None,
            "mostRecurrent": counts.most_common(1)[0][1] if counts else 0,
            # Counted over variant RECORDS (one per patient carrying it), not over distinct
            # alleles. A recurrent allele therefore contributes its patient count, which is
            # the right weighting for "what would an editing strategy have to address".
            "consequenceRecords": dict(Counter(v["consequence"] for v in vs).most_common()),
        })
    spectrum.sort(key=lambda r: -r["patients"])

    all_private = [r["privateShare"] for r in spectrum if r["privateShare"] is not None]
    genes_all_private = sum(1 for r in spectrum if r["privateShare"] == 1.0)

    # ---- 2. zygosity against the declared inheritance -----------------------------------
    # THE FIRST VERSION OF THIS CHECK WAS WRONG, and the comment above it said why without
    # the code doing anything about it: it flagged "recessive disease, all patients
    # heterozygous, no homozygote" as a conflict, and that is the EXPECTED signature of
    # COMPOUND HETEROZYGOSITY. A recessive patient carrying two different variants is
    # recorded as two heterozygous calls and never as a homozygote. The rule reported 65
    # conflicts, 61 of them of exactly that shape - a check that fires on the normal case is
    # not a check.
    #
    # So the test moved to the PATIENT, where the question actually lives: a recessive
    # diagnosis explained by a single heterozygous variant and nothing else is the anomaly,
    # because one hit does not explain a recessive disease. Diseases with both modes
    # declared are skipped rather than judged - HPO records dominant AND recessive for many
    # entries, and neither expectation applies.
    modes = inheritance_by_disease()

    by_patient: dict[str, list] = defaultdict(list)
    for v in variants:
        by_patient[v["patient"]].append(v)

    checked, conflicts = 0, []
    ambiguous = 0
    per_disease_single_hit: dict[str, dict] = defaultdict(
        lambda: {"patients": 0, "singleHet": 0})

    for patient, vs in by_patient.items():
        did = vs[0]["disease"]
        declared = modes.get(did)
        if not declared:
            continue
        recessive = "autosomal recessive" in declared
        dominant = "autosomal dominant" in declared
        if recessive and dominant:
            ambiguous += 1
            continue
        if not recessive:
            continue

        checked += 1
        row = per_disease_single_hit[did]
        row["patients"] += 1
        zyg = [v["zygosity"] for v in vs if v["zygosity"]]
        # One heterozygous call, nothing else, for a disease that needs two hits.
        if len(zyg) == 1 and zyg[0] == "heterozygous":
            row["singleHet"] += 1

    for did, row in per_disease_single_hit.items():
        if row["patients"] >= 3 and row["singleHet"] == row["patients"]:
            conflicts.append({
                "disease": did,
                "declared": sorted(modes.get(did, [])),
                "patients": row["patients"],
                "singleHeterozygousPatients": row["singleHet"],
                "reads": ("every patient of a recessive disease is explained by ONE "
                          "heterozygous variant, which does not explain a recessive disease"),
            })
    conflicts.sort(key=lambda r: -r["patients"])

    # ---- 3. the consequence mix ---------------------------------------------------------
    cons = Counter(v["consequence"] for v in variants)
    acmg = Counter(v["acmg"] for v in variants if v["acmg"])
    zyg_all = Counter(v["zygosity"] for v in variants if v["zygosity"])
    sexes = Counter(p["sex"] for p in per_patient if p["sex"])

    payload = {
        "generated": "tools/patient_variants.py",
        "input": str(path.relative_to(ROOT)).replace("\\", "/"),
        "premise": (
            "The phenopacket extraction kept phenotype and discarded genotype. A field "
            "census showed allelic state on 100% of genomic interpretations, gene on 99%, "
            "ACMG class on 98% and VCF coordinates on 94% - per patient, already on disk."
        ),
        "scale": {
            "patients": len(per_patient),
            "variants": len(variants),
            "genes": len(by_gene),
            "diseases": len({p["disease"] for p in per_patient}),
        },
        "allelicSpectrum": {
            "genes": len(spectrum),
            "medianPrivateShare": (round(sorted(all_private)[len(all_private) // 2], 3)
                                   if all_private else None),
            "genesWhereEveryVariantIsPrivate": genes_all_private,
            "shareOfGenesAllPrivate": (round(genes_all_private / len(spectrum), 3)
                                       if spectrum else None),
            "says": (
                "A gene whose every reported variant was seen exactly once is a gene whose "
                "'causal' attribution rests on unreplicated alleles. That is not evidence "
                "against the gene - it is the state of the evidence for it, and it is the "
                "distinction docs/references/rare-disease-scale.md keeps making between a "
                "measurement and a report."
            ),
            # Every gene, not a head: sieve.stages.target reads this per gene and a
            # truncated list would silently limit which genes can be assessed.
            "all": spectrum,
            "top": spectrum[:40],
        },
        "zygosityVsInheritance": {
            "recessivePatientsChecked": checked,
            "patientsSkippedAsAmbiguous": ambiguous,
            "conflicts": conflicts,
            "note": (
                "Tested per PATIENT, not per disease. A recessive patient carrying two "
                "different variants is two heterozygous calls and never a homozygote, so "
                "'no homozygote' is the normal case and flagging it - which the first "
                "version of this check did, 61 times - is a false alarm. What is reported "
                "is a recessive diagnosis where every patient is explained by a SINGLE "
                "heterozygous variant. Diseases with both modes declared are skipped, not "
                "judged. This is a flag to read, never a verdict: a second variant can be "
                "absent from the record without being absent from the patient."
            ),
        },
        "consequences": dict(cons.most_common()),
        "acmgClasses": dict(acmg.most_common()),
        "zygosity": dict(zyg_all.most_common()),
        "sex": dict(sexes.most_common()),
        "vitalStatusTrap": {
            "recorded": dict(vital_recorded),
            "deceased": deceased,
            "aliveRecorded": vital_recorded.get("ALIVE", 0),
            "warning": (
                "vitalStatus is recorded on %d of %d patients and EVERY ONE IS DECEASED. "
                "ALIVE is never written down. A mortality rate computed from this field "
                "would be 100%% by construction. It is a death register, not a survival "
                "denominator." % (sum(vital_recorded.values()), len(per_patient))
            ),
        },
    }

    RARE.mkdir(parents=True, exist_ok=True)
    dest = RARE / "patient_variants.json"
    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    s, a = payload["scale"], payload["allelicSpectrum"]
    print("wrote %s" % dest.relative_to(ROOT))
    print("  %s variants over %s patients, %s genes, %s diseases"
          % (f"{s['variants']:,}", f"{s['patients']:,}", f"{s['genes']:,}",
             f"{s['diseases']:,}"))
    print("  allelic spectrum: median private share %.3f — %s of %s genes have EVERY variant "
          "seen exactly once" % (a["medianPrivateShare"], f"{a['genesWhereEveryVariantIsPrivate']:,}",
                                 f"{a['genes']:,}"))
    print("  consequences: " + " · ".join(f"{k} {v:,}" for k, v in list(cons.most_common())[:6]))
    print("  zygosity: " + " · ".join(f"{k} {v:,}" for k, v in zyg_all.most_common()))
    print("  inheritance: %s recessive patients checked, %s skipped as ambiguous, "
          "%d diseases flagged" % (f"{checked:,}", f"{ambiguous:,}", len(conflicts)))
    print("  %s" % payload["vitalStatusTrap"]["warning"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
