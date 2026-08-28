#!/usr/bin/env python
"""Seed the rare-disease knowledge layer: a cross-ontology lexicon with the gaps kept.

WHY THIS SHAPE
--------------
Rare-disease knowledge is not missing so much as *fragmented*. The same disease carries a
different identifier in every system that touches it — Orphanet for European rare-disease
practice, OMIM for the genetics literature, MONDO for the merged ontology, ICD-11 for
billing and mortality, HPO for the phenotype, GARD for patient-facing information. A study
indexed by one cannot be joined to a registry indexed by another without a crosswalk, and
the crosswalk is exactly what a lexicon is (see `docs/references/nf2.md` §6 for the
single-disease version of the same idea).

WHAT MAKES THIS DIFFERENT FROM A DISEASE LIST
---------------------------------------------
**The unknown is a first-class field, not a blank.** Roughly half of rare-disease patients
have no molecular diagnosis; a large share of catalogued diseases have no known causal
gene, no measured prevalence, and no approved treatment. A schema that models those as
missing values produces a dashboard that quietly under-reports the size of the problem. So
every gap here is typed:

    gene       : symbol | UNKNOWN_GENE       (catalogued, cause not found)
    prevalence : class  | UNKNOWN_PREVALENCE (never measured, not "zero")
    mechanism  : text   | UNKNOWN_MECHANISM
    therapy    : class  | NONE_APPROVED

⚠️ PROVENANCE. Every identifier below is written from working knowledge, NOT retrieved from
the source ontologies, and each row carries its own confidence mark. This file is a
*schema demonstration with real examples*, not a reference database. Before any of it is
used for anything but a UI, the ids must be resolved against Orphanet, OMIM, MONDO and
HPO. The `confidence` column exists so that check can be prioritised rather than assumed.

    python tools/rare_disease_seed.py        # writes out/rare/lexicon.json
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "out" / "rare"

# --- the typed unknowns ---------------------------------------------------------------
UNKNOWN_GENE = "UNKNOWN_GENE"
UNKNOWN_PREVALENCE = "UNKNOWN_PREVALENCE"
UNKNOWN_MECHANISM = "UNKNOWN_MECHANISM"
NONE_APPROVED = "NONE_APPROVED"

# --- Orphanet's prevalence bands, which are the field's shared vocabulary --------------
# Ordered from rarest. "Ultra-rare" has no single legal definition; the EU convention of
# <1 in 50,000 and the commonly used <1 in 1,000,000 both appear in the literature, which
# is itself an instance of the problem this file is about.
PREVALENCE_BANDS = [
    {"id": "P_LT_1M", "label": "<1 / 1 000 000", "note": "ultra-rare by the strictest convention", "rank": 0},
    {"id": "P_1_9_1M", "label": "1-9 / 1 000 000", "note": "ultra-rare", "rank": 1},
    {"id": "P_1_9_100K", "label": "1-9 / 100 000", "note": "rare", "rank": 2},
    {"id": "P_1_5_10K", "label": "1-5 / 10 000", "note": "at the EU rare-disease threshold", "rank": 3},
    {"id": UNKNOWN_PREVALENCE, "label": "never measured", "note": "catalogued, prevalence unknown", "rank": 4},
]

# --- how "rare" is defined, which differs by jurisdiction ------------------------------
DEFINITIONS = [
    {"where": "European Union", "rule": "<= 5 in 10 000", "basis": "prevalence",
     "source": "EU Regulation 141/2000 on orphan medicinal products"},
    {"where": "United States", "rule": "< 200 000 persons affected", "basis": "absolute count",
     "source": "Orphan Drug Act 1983"},
    {"where": "Japan", "rule": "< 50 000 patients", "basis": "absolute count",
     "source": "Japanese orphan drug regulation"},
    {"where": "Australia", "rule": "< 5 in 10 000", "basis": "prevalence", "source": "TGA orphan designation"},
]

# --- the ontologies a lexicon has to bridge --------------------------------------------
ONTOLOGIES = [
    {"id": "MONDO", "name": "Mondo Disease Ontology", "role": "the merge target — exists to unify the others",
     "pattern": "MONDO:0000000", "scope": "all diseases"},
    {"id": "ORPHA", "name": "Orphanet", "role": "European rare-disease reference; prevalence and expert centres",
     "pattern": "ORPHA:0000", "scope": "rare diseases"},
    {"id": "OMIM", "name": "Online Mendelian Inheritance in Man", "role": "the genetics literature's index",
     "pattern": "OMIM:000000", "scope": "mendelian traits and genes"},
    {"id": "HPO", "name": "Human Phenotype Ontology", "role": "the phenotype vocabulary that makes cases comparable",
     "pattern": "HP:0000000", "scope": "phenotypic abnormalities"},
    {"id": "ICD11", "name": "ICD-11", "role": "billing, mortality, health statistics; first ICD with real rare-disease coverage",
     "pattern": "LD00.0", "scope": "all conditions"},
    {"id": "GARD", "name": "Genetic and Rare Diseases Information Center", "role": "patient-facing summaries (NIH)",
     "pattern": "GARD:0000", "scope": "rare diseases"},
    {"id": "UMLS", "name": "Unified Medical Language System", "role": "concept ids that bridge clinical terminologies",
     "pattern": "C0000000", "scope": "biomedical concepts"},
]

# --- the seed rows ----------------------------------------------------------------------
# Deliberately includes the two diseases this repository already works on, several
# well-characterised rare diseases, and a set of entries whose point is what is MISSING.
# `confidence` is about the identifiers, not about the disease existing.
D = [
    dict(name="NF2-related schwannomatosis", mondo="MONDO:0007039", orpha="ORPHA:637",
         omim="OMIM:101000", gene="NF2", inherit="autosomal dominant", onset="adolescent",
         prevalence="P_1_9_100K", mechanism="merlin loss releases YAP/TAZ-TEAD (Hippo)",
         therapy="OFF_LABEL", system="nervous", confidence="medium",
         synonyms=["neurofibromatosis type 2", "NF2-SWN", "bilateral vestibular schwannoma",
                   "neurofibromatose tipo 2", "neurofibromatosis tipo 2", "神経線維腫症2型"],
         note="Renamed in the 2022 consensus. The old name still dominates the corpus."),
    dict(name="Duchenne muscular dystrophy", mondo="MONDO:0010679", orpha="ORPHA:98896",
         omim="OMIM:310200", gene="DMD", inherit="X-linked recessive", onset="early childhood",
         prevalence="P_1_9_100K", mechanism="dystrophin absence; sarcolemma fragility",
         therapy="APPROVED", system="musculoskeletal", confidence="medium",
         synonyms=["DMD", "distrofia muscular de Duchenne", "distrofia muscolare di Duchenne",
                   "Duchenne-Muskeldystrophie", "デュシェンヌ型筋ジストロフィー"],
         note="Exon-skipping and gene therapy approved for subsets; not curative."),
    dict(name="Cystic fibrosis", mondo="MONDO:0009061", orpha="ORPHA:586", omim="OMIM:219700",
         gene="CFTR", inherit="autosomal recessive", onset="neonatal", prevalence="P_1_5_10K",
         mechanism="CFTR chloride channel dysfunction", therapy="APPROVED",
         system="respiratory", confidence="high",
         synonyms=["CF", "mucoviscidose", "fibrose cistica", "fibrosis quistica", "嚢胞性線維症"],
         note="The modifier-therapy success story rare disease is measured against."),
    dict(name="Spinal muscular atrophy", mondo="MONDO:0001516", orpha="ORPHA:70", omim="OMIM:253300",
         gene="SMN1", inherit="autosomal recessive", onset="infantile", prevalence="P_1_9_100K",
         mechanism="SMN protein deficiency; motor neuron loss", therapy="APPROVED",
         system="nervous", confidence="medium",
         synonyms=["SMA", "atrofia muscular espinhal", "amyotrophie spinale", "脊髄性筋萎縮症"],
         note="Three approved therapies; the proof that ultra-rare economics can work."),
    dict(name="Zellweger spectrum disorder", mondo="MONDO:0019234", orpha="ORPHA:79205",
         omim="OMIM:214100", gene="PEX1", inherit="autosomal recessive", onset="neonatal",
         prevalence="P_1_9_1M", mechanism="peroxisome biogenesis failure", therapy=NONE_APPROVED,
         system="metabolic", confidence="low",
         synonyms=["cerebrohepatorenal syndrome", "sindrome de Zellweger"],
         note="Base editing repaired liver function in a mouse model (Broad, 2026)."),
    dict(name="Dravet syndrome", mondo="MONDO:0100135", orpha="ORPHA:33069", omim="OMIM:607208",
         gene="SCN1A", inherit="autosomal dominant (mostly de novo)", onset="infantile",
         prevalence="P_1_9_100K", mechanism="Nav1.1 loss of function in interneurons",
         therapy="APPROVED", system="nervous", confidence="medium",
         synonyms=["severe myoclonic epilepsy of infancy", "SMEI", "sindrome de Dravet"],
         note="A rare genetic epilepsy of the class CTG's ARPA-H programme targets."),
    dict(name="CDKL5 deficiency disorder", mondo="MONDO:0010726", orpha="ORPHA:3095",
         omim="OMIM:300672", gene="CDKL5", inherit="X-linked", onset="infantile",
         prevalence="P_1_9_1M", mechanism=UNKNOWN_MECHANISM, therapy=NONE_APPROVED,
         system="nervous", confidence="low",
         synonyms=["CDD", "early infantile epileptic encephalopathy 2"],
         note="Gene known, mechanism not. The common ultra-rare situation."),
    dict(name="Progressive myoclonic epilepsy, unsolved subgroup", mondo=None, orpha=None,
         omim=None, gene=UNKNOWN_GENE, inherit="unknown", onset="childhood",
         prevalence=UNKNOWN_PREVALENCE, mechanism=UNKNOWN_MECHANISM, therapy=NONE_APPROVED,
         system="nervous", confidence="none",
         synonyms=["PME unsolved", "SWAN — syndrome without a name"],
         note="A real clinical grouping with no ontology id, because it is defined by "
              "what was NOT found. Entries like this are invisible to any pipeline "
              "keyed on identifiers."),
    dict(name="Undiagnosed multisystem syndrome (UDN-style)", mondo=None, orpha=None, omim=None,
         gene=UNKNOWN_GENE, inherit="unknown", onset="variable", prevalence=UNKNOWN_PREVALENCE,
         mechanism=UNKNOWN_MECHANISM, therapy=NONE_APPROVED, system="multisystem",
         confidence="none",
         synonyms=["SWAN", "sindrome sem nome", "undiagnosed disease"],
         note="The Undiagnosed Diseases Network's caseload. Not a disease entry — a "
              "placeholder for a patient the catalogue cannot name."),
    dict(name="Fibrodysplasia ossificans progressiva", mondo="MONDO:0007606", orpha="ORPHA:337",
         omim="OMIM:135100", gene="ACVR1", inherit="autosomal dominant", onset="childhood",
         prevalence="P_LT_1M", mechanism="constitutive BMP signalling; heterotopic ossification",
         therapy="APPROVED", system="musculoskeletal", confidence="medium",
         synonyms=["FOP", "stone man syndrome", "fibrodisplasia ossificante progressiva"],
         note="Roughly one in two million. An ultra-rare disease with a solved mechanism."),
    dict(name="Alkaptonuria", mondo="MONDO:0008753", orpha="ORPHA:56", omim="OMIM:203500",
         gene="HGD", inherit="autosomal recessive", onset="adult", prevalence="P_1_9_1M",
         mechanism="homogentisate oxidase deficiency", therapy="APPROVED",
         system="metabolic", confidence="medium",
         synonyms=["ochronosis", "alcaptonuria"],
         note="Garrod's original inborn error of metabolism, 1902."),
    dict(name="Ultra-rare de novo variant syndrome, n<5 reported", mondo=None, orpha=None,
         omim=None, gene=UNKNOWN_GENE, inherit="de novo", onset="neonatal",
         prevalence="P_LT_1M", mechanism=UNKNOWN_MECHANISM, therapy=NONE_APPROVED,
         system="multisystem", confidence="none",
         synonyms=["n-of-few", "private mutation syndrome"],
         note="The regime CTG is built for, and the regime where every statistic in "
              "this repository is at its limit: n = 1."),
]

# Field-level facts about the domain as a whole. Each is widely cited; each is ⚠️ from
# working knowledge and carries the check that would confirm it.
FIELD_FACTS = [
    {"claim": "approximately 7 000-8 000 distinct rare diseases are catalogued",
     "verify": "Orphanet's current entity count", "confidence": "medium"},
    {"claim": "350-400 million people worldwide live with a rare disease",
     "verify": "quoted directly in the Broad/CTG announcement, 2026-07-21", "confidence": "high"},
    {"claim": "fewer than 1 in 20 rare diseases has an approved treatment",
     "verify": "quoted directly in the Broad/CTG announcement, 2026-07-21", "confidence": "high"},
    {"claim": "roughly 70-80% of rare diseases are genetic in origin",
     "verify": "Orphanet / IRDiRC summary statistics", "confidence": "medium"},
    {"claim": "roughly 70% have paediatric onset",
     "verify": "Orphanet / EURORDIS", "confidence": "medium"},
    {"claim": "around half of patients referred for rare-disease diagnosis end without a "
              "molecular diagnosis",
     "verify": "diagnostic-yield literature for exome/genome sequencing", "confidence": "low"},
    {"claim": "the diagnostic odyssey averages roughly 5 years",
     "verify": "EURORDIS survey data", "confidence": "low"},
]


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    for d in D:
        d["unknowns"] = sum([
            d["gene"] == UNKNOWN_GENE,
            d["prevalence"] == UNKNOWN_PREVALENCE,
            d["mechanism"] == UNKNOWN_MECHANISM,
            d["therapy"] == NONE_APPROVED,
            d["mondo"] is None,
        ])
        d["orphan_of_ontologies"] = d["mondo"] is None and d["orpha"] is None and d["omim"] is None

    payload = {
        "generated": "2026-08-27",
        "provenance": (
            "Written from working knowledge as a schema demonstration. Every identifier "
            "must be resolved against Orphanet, OMIM, MONDO and HPO before use. The "
            "`confidence` field marks which rows to check first."
        ),
        "unknownTokens": {
            "gene": UNKNOWN_GENE, "prevalence": UNKNOWN_PREVALENCE,
            "mechanism": UNKNOWN_MECHANISM, "therapy": NONE_APPROVED,
        },
        "definitions": DEFINITIONS,
        "prevalenceBands": PREVALENCE_BANDS,
        "ontologies": ONTOLOGIES,
        "fieldFacts": FIELD_FACTS,
        "diseases": D,
        "summary": {
            "entries": len(D),
            "withoutGene": sum(1 for d in D if d["gene"] == UNKNOWN_GENE),
            "withoutMechanism": sum(1 for d in D if d["mechanism"] == UNKNOWN_MECHANISM),
            "withoutTherapy": sum(1 for d in D if d["therapy"] == NONE_APPROVED),
            "withoutAnyOntologyId": sum(1 for d in D if d["orphan_of_ontologies"]),
            "bySystem": dict(Counter(d["system"] for d in D)),
            "byConfidence": dict(Counter(d["confidence"] for d in D)),
        },
    }

    path = DEST / "lexicon.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    s = payload["summary"]
    print("wrote %s" % path.relative_to(ROOT))
    print("  %d entries · %d without a causal gene · %d without a mechanism · "
          "%d without an approved therapy · %d with no ontology id at all"
          % (s["entries"], s["withoutGene"], s["withoutMechanism"],
             s["withoutTherapy"], s["withoutAnyOntologyId"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
