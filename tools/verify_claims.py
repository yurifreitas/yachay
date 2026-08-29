#!/usr/bin/env python
"""Every number the prose quotes, checked against the artefact that produced it.

WHY THIS EXISTS, AND WHY IT IS LATE. This is **F1** of `docs/audit.md`, proposed during the
first sweep and unbuilt through twelve more. Its own finding said why it was needed:

    A1 — `CITATION.cff` advertised two anomalies that were resolved. The header block, the
    thing a citing author copies, still read `-4.09` after the defect was fixed and the
    manifest updated. Root cause: nothing links a manifest's numbers to the prose that
    quotes them.

Then A11 proved the same failure at larger scale: the ultra-rare count read **770** in three
documents while the artefact said **4,586**, because one regeneration was not propagated.
Both were caught by a person reading carefully. That is not a control.

`tools/paper_numbers.py` already solves this for the manuscript - no number is typed into
the LaTeX, each is a macro generated from a manifest, and a missing one fails the build
loudly. Markdown has no equivalent, which is exactly why the drift lands there.

HOW IT WORKS, AND WHAT IT CANNOT DO. Prose is not LaTeX: a number cannot be a macro. So this
is a **checker**, not a generator. Each registered claim names an artefact, a path into it, a
formatter, and the documents that cite it. The check is two-sided:

    1. the artefact still produces the value  (a renamed key fails here)
    2. every document listed still contains it (a stale quotation fails here)

It cannot find a number nobody registered. The registry is therefore a curated list of the
LOAD-BEARING figures - the ones a reader would act on - and adding to it is part of
publishing a new claim.

    python tools/verify_claims.py            # check, exit 1 on drift
    python tools/verify_claims.py --list     # what is registered

Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def fmt_int(v) -> list[str]:
    return [f"{int(v):,}", str(int(v))]


def fmt_raw(v) -> list[str]:
    return [str(v)]


# A FORMATTER RETURNS EVERY ACCEPTABLE RENDERING, NOT ONE.
# The first version demanded an exact string and flagged `52 %` as drift because it computed
# `52.0`. That is the checker being wrong, not the prose: a percentage is legitimately
# written several ways, and a verifier that fails on typography teaches people to disable it.
# Precision is still enforced - `52 %` and `51 %` do not both match - but presentation is not.
def fmt_pct1(v) -> list[str]:
    x = 100 * float(v)
    return [f"{x:.1f}", f"{x:.0f} %", f"{x:.0f}%", f"{x:.1f} %", f"{x:.1f}%"]


def fmt_pct0(v) -> list[str]:
    x = round(100 * float(v))
    return [f"{x}", f"{x} %", f"{x}%"]


def fmt_2dp(v) -> list[str]:
    return [f"{float(v):.2f}"]


def fmt_3dp(v) -> list[str]:
    return [f"{float(v):.3f}"]


def fmt_4dp(v) -> list[str]:
    return [f"{float(v):.4f}"]


# ---------------------------------------------------------------------------------------
# THE REGISTRY. One row per load-bearing number: where it comes from, how it is written in
# prose, and which documents quote it. A claim with no document listed is not a claim this
# file can protect - and adding a row is part of publishing a figure, not an afterthought.
# ---------------------------------------------------------------------------------------
CLAIMS = [
    # --- the atlas, and the A11 correction that has to stay corrected -------------------
    ("ultra-rare diseases", "out/rare/atlas.json", ["scale", "ultraRare"], fmt_int,
     ["docs/references/rare-disease-scale.md", "docs/audit.md"]),
    ("ultra-rare with a gene", "out/rare/atlas.json", ["scale", "ultraRareWithGene"], fmt_int,
     ["docs/references/rare-disease-scale.md", "docs/audit.md"]),
    ("diseases joined", "out/rare/atlas.json", ["scale", "diseases"], fmt_int,
     ["docs/references/rare-disease-scale.md", "docs/references/rare-layers.md"]),

    # --- the population axis -------------------------------------------------------------
    ("prevalence records", "out/rare/ancestry_geography.json", ["shape", "records"], fmt_int,
     ["docs/references/rare-disease-ancestry.md", "docs/references/rare-disease-scale.md"]),
    ("discordant disorders", "out/rare/ancestry_geography.json",
     ["discordance", "discordant"], fmt_int,
     ["docs/references/rare-disease-ancestry.md", "docs/references/rare-layers.md"]),
    ("countries with a record", "out/rare/ancestry_geography.json",
     ["shape", "distinctCountries"], fmt_int,
     ["docs/references/rare-disease-ancestry.md"]),

    # --- the evidence atlas ---------------------------------------------------------------
    ("annotations graded", "out/rare/evidence_atlas.json", ["profile", "annotations"], fmt_int,
     ["docs/references/rare-disease-scale.md", "docs/references/rare-layers.md"]),
    ("diseases with a quantified sign", "out/rare/evidence_atlas.json",
     ["profile", "diseasesWithAQuantifiedSign"], fmt_int,
     ["docs/references/rare-disease-scale.md"]),
    ("share with a quantified sign", "out/rare/evidence_atlas.json",
     ["profile", "shareWithAQuantifiedSign"], fmt_pct1,
     ["docs/references/rare-disease-scale.md", "docs/references/rare-layers.md"]),
    ("median denominator", "out/rare/evidence_atlas.json",
     ["profile", "denominators", "median"], fmt_raw,
     ["docs/references/rare-disease-scale.md", "docs/references/patient-data.md"]),

    # --- the patient layers ---------------------------------------------------------------
    ("patients", "out/rare/patient_frequencies.json", ["scale", "patients"], fmt_int,
     ["docs/references/patient-data.md", "docs/audit.md"]),
    ("patient diseases", "out/rare/patient_frequencies.json",
     ["scale", "distinctDiseases"], fmt_int, ["docs/references/patient-data.md"]),
    ("comparable pairs", "out/rare/patient_frequencies.json",
     ["agreement", "comparable"], fmt_int, ["docs/references/patient-data.md"]),
    ("variants", "out/rare/patient_variants.json", ["scale", "variants"], fmt_int,
     ["docs/references/patient-data.md", "docs/audit.md"]),
    ("genes with variants", "out/rare/patient_variants.json", ["scale", "genes"], fmt_int,
     ["docs/references/patient-data.md", "docs/audit.md"]),
    ("genes all-private", "out/rare/patient_variants.json",
     ["allelicSpectrum", "genesWhereEveryVariantIsPrivate"], fmt_int,
     ["docs/references/patient-data.md", "docs/audit.md"]),

    # --- ClinVar ----------------------------------------------------------------------
    ("clinvar VUS share", "out/rare/clinvar_evidence.json",
     ["significance", "vusShare"], fmt_pct1,
     ["docs/references/patient-data.md", "docs/audit.md", "docs/references/rare-layers.md"]),
    ("clinvar low-star share", "out/rare/clinvar_evidence.json",
     ["reviewStatus", "shareAtOneStarOrLess"], fmt_pct1,
     ["docs/audit.md", "docs/references/rare-layers.md"]),
    ("our variants absent from clinvar", "out/rare/clinvar_evidence.json",
     ["crossCheck", "notInClinVar"], fmt_int, ["docs/audit.md"]),

    # --- the self-audit ------------------------------------------------------------------
    ("layer contradictions", "out/rare/consistency.json",
     ["summary", "contradictions"], fmt_raw,
     ["docs/audit.md", "docs/references/rare-layers.md"]),
    ("genotype-phenotype tests", "out/rare/genotype_phenotype.json", ["scale", "tests"], fmt_int,
     ["docs/references/patient-data.md", "docs/audit.md"]),
    ("genotype-phenotype powered", "out/rare/genotype_phenotype.json",
     ["scale", "powered"], fmt_raw, ["docs/references/patient-data.md", "docs/audit.md"]),

    # --- ADR 0007: the promoted constructs. Registered the day they were published, which
    # --- is the point - A1 and A11 both happened because a figure was published first and
    # --- protected later.
    ("gene-scale excess information", "out/rare/scale_information.json",
     ["scales", "gene", "excess_bits"], fmt_4dp,
     ["docs/references/theory-atlas.md", "docs/references/deep/multiscale-formalism.md"]),
    ("pathway retention", "out/rare/scale_information.json",
     ["scales", "pathway", "retained_vs_gene"], fmt_pct0,
     ["docs/references/theory-atlas.md", "docs/references/deep/foundations.md", "README.md"]),
    ("cell-type retention", "out/rare/scale_information.json",
     ["scales", "cell_type", "retained_vs_gene"], fmt_pct0,
     ["docs/references/theory-atlas.md", "README.md"]),
    ("gene-scale asymmetry ratio", "out/rare/scale_information.json",
     ["scales", "gene", "asymmetry_ratio"], fmt_2dp,
     ["docs/references/theory-atlas.md", "docs/references/deep/multiscale-formalism.md",
      "README.md"]),
    ("morphogenetic retention", "out/rare/scale_information.json",
     ["morphogenesis_prediction", "morphogenetic", "mean_pathway_retention"], fmt_3dp,
     ["docs/references/theory-atlas.md", "docs/references/deep/foundations.md"]),
    ("physiological retention", "out/rare/scale_information.json",
     ["morphogenesis_prediction", "physiological", "mean_pathway_retention"], fmt_3dp,
     ["docs/references/theory-atlas.md", "docs/references/deep/foundations.md"]),
    ("morphogenesis difference", "out/rare/scale_information.json",
     ["morphogenesis_prediction", "difference"], fmt_3dp,
     ["docs/references/theory-atlas.md", "docs/references/deep/foundations.md"]),
    ("morphogenesis p-value", "out/rare/scale_information.json",
     ["morphogenesis_prediction", "permutation_p_one_sided"], fmt_raw,
     ["docs/references/theory-atlas.md", "docs/references/deep/foundations.md"]),

    # --- the language axis ----------------------------------------------------------------
    ("portuguese annotation coverage", "out/rare/language_coverage.json",
     ["by_language", "pt", "annotation_coverage"], fmt_pct1,
     ["docs/references/theory-atlas.md", "docs/references/deep/multiscale-formalism.md",
      "tools/README.md", "README.md"]),
    ("portuguese system spread", "out/rare/language_coverage.json",
     ["by_language", "pt", "system_spread"], fmt_pct1,
     ["docs/references/theory-atlas.md", "docs/references/deep/multiscale-formalism.md",
      "tools/README.md", "README.md"]),

    # --- conflict against context ----------------------------------------------------------
    ("conflicting variants in clinvar", "out/rare/evidence_conflict.json",
     ["totals", "conflicting"], fmt_int,
     ["docs/references/theory-atlas.md", "docs/references/deep/multiscale-formalism.md"]),
    ("conflict risk ratio", "out/rare/evidence_conflict.json",
     ["marginal_risk_ratio_4plus_vs_1"], fmt_2dp,
     ["docs/references/theory-atlas.md", "docs/references/deep/multiscale-formalism.md",
      "tools/README.md"]),
    ("variants in conflict", "out/rare/conflict_decomposition.json",
     ["counts", "variants_in_conflict"], fmt_int,
     ["docs/references/theory-atlas.md", "docs/references/deep/multiscale-formalism.md"]),
    ("across-condition share", "out/rare/conflict_decomposition.json",
     ["headline", "across_condition_share"], fmt_pct1,
     ["docs/references/theory-atlas.md", "docs/references/deep/multiscale-formalism.md",
      "tools/README.md", "README.md"]),
    ("across-condition share, umbrellas removed", "out/rare/conflict_decomposition.json",
     ["sensitivity_umbrella_removed", "result", "across_condition_share"], fmt_pct1,
     ["docs/references/theory-atlas.md", "docs/references/deep/multiscale-formalism.md",
      "tools/README.md", "README.md"]),
]


def dig(obj, path):
    for key in path:
        if not isinstance(obj, dict) or key not in obj:
            return None, f"key {'.'.join(path)!r} not found"
        obj = obj[key]
    return obj, None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="show the registry and exit")
    args = ap.parse_args()

    if args.list:
        for name, art, path, _, docs in CLAIMS:
            print(f"  {name:36s} {art} :: {'.'.join(path)}  -> {len(docs)} doc(s)")
        return 0

    cache: dict[str, dict] = {}
    problems: list[str] = []
    checked = 0
    missing_artefacts = set()

    for name, artefact, path, formatter, docs in CLAIMS:
        p = ROOT / artefact
        if not p.exists():
            missing_artefacts.add(artefact)
            continue
        if artefact not in cache:
            cache[artefact] = json.loads(p.read_text(encoding="utf-8"))
        value, err = dig(cache[artefact], path)
        if err:
            problems.append(f"{name}: {artefact} no longer has {'.'.join(path)} "
                            f"— a renamed key is drift too")
            continue

        try:
            acceptable = formatter(value)
        except (TypeError, ValueError):
            problems.append(f"{name}: value {value!r} cannot be formatted")
            continue

        checked += 1
        for doc in docs:
            d = ROOT / doc
            if not d.exists():
                problems.append(f"{name}: cites {doc}, which does not exist")
                continue
            text = d.read_text(encoding="utf-8")
            if not any(w in text for w in acceptable):
                problems.append(
                    f"{name}: artefact says {acceptable[0]!r} and {doc} contains no "
                    f"rendering of it — the prose has drifted from {artefact}")

    print(f"  {checked} claims checked across {len(cache)} artefacts and "
          f"{len({d for *_, ds in CLAIMS for d in ds})} documents")
    if missing_artefacts:
        print(f"  {len(missing_artefacts)} artefact(s) not on disk, skipped:")
        for a in sorted(missing_artefacts):
            print(f"    {a}")
    if not problems:
        print("  no drift")
        return 0

    print()
    print(f"  {len(problems)} PROBLEM(S):")
    for p in problems:
        print(f"    {p}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
