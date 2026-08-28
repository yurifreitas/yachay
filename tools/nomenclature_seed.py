#!/usr/bin/env python
"""Names, and what they carry: etymology, taxonomy, history, and the cost of a bad one.

WHY THIS IS NOT DECORATION. It closes a loop the rest of the atlas leaves open.

    a disease's NAME decides what a literature search finds
      -> which decides what evidence is discoverable
        -> which is the ASCERTAINMENT BIAS measured in tools/atlas_bias.py (+0.236)

So etymology is not a curiosity here; it is upstream of the statistics. A disease renamed
in 2022 has two literatures, and a searcher who knows one name sees half the evidence.

FOUR THINGS A NAME CAN DO, and all four appear below:

  1. **Describe** what was seen — and stay right (alkaptonuria: dark urine).
  2. **Describe** what was seen — and be wrong about why (dystrophy: 'bad nourishment',
     a nutritional theory of muscle wasting that the name outlived).
  3. **Point at a person** rather than the disease (eponyms) — which carries whatever that
     person did, including things the field later refused to keep honouring.
  4. **Encode a metaphor** from before any mechanism was known (lupus: 'wolf').

PROVENANCE. Historical and etymological claims written from working knowledge, each with a
confidence mark. Dates and attributions of first description are the least reliable field
here and are marked accordingly; the renaming cases are well documented. Nothing here is
clinical guidance, and the ethical entries describe documented history rather than
adjudicating it.

    python tools/nomenclature_seed.py     # writes out/rare/nomenclature.json
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "out" / "rare"

# --- the eras a disease name can come from ------------------------------------------
# Taxonomy is stratigraphic: each era left names behind, and they are all still in use at
# once. That is why one disease carries four incompatible identifiers.
ERAS = [
    dict(id="metaphor", name="Metaphor and appearance", span="antiquity – 1800s",
         basis="What it looked like, to the naked eye",
         note="Names from before any mechanism existed. They survive because clinicians "
              "kept using them, not because they were ever explanatory."),
    dict(id="eponym", name="The eponym", span="1800s – mid 1900s",
         basis="Who described it first, or loudest",
         note="Priority as authorship. Efficient for citation, opaque for anyone who does "
              "not already know, and it carries the describer's history with it."),
    dict(id="clinical", name="Clinical syndrome", span="early–mid 1900s",
         basis="A reproducible cluster of signs",
         note="The first taxonomy that could be checked between clinicians. Splits and "
              "lumps according to what a physical examination can distinguish."),
    dict(id="organ", name="Organ and tissue", span="mid 1900s",
         basis="Where the damage is",
         note="Useful for the specialist who will treat it; useless for the mechanism, "
              "since one mechanism damages several organs."),
    dict(id="mechanism", name="Mechanism", span="1902 – present",
         basis="What is broken, biochemically",
         note="Begins with Garrod's 'inborn errors of metabolism' — the first claim that a "
              "disease IS a molecular defect rather than has one."),
    dict(id="molecular", name="Gene and variant", span="1980s – present",
         basis="Which gene, which change",
         note="The current default. It splits clinical entities that share a gene and "
              "lumps ones that do not — which is why the older names never went away."),
]

# --- word-parts that recur, so a name can be read rather than memorised ---------------
ROOTS = [
    dict(part="-osis", origin="Greek", means="condition, process", example="alkaptonuria → ochronosis"),
    dict(part="-itis", origin="Greek", means="inflammation", example="polyangiitis"),
    dict(part="-oma", origin="Greek", means="swelling, tumour", example="schwannoma, neurofibroma"),
    dict(part="-pathy", origin="Greek pathos", means="suffering, disease", example="neuropathy"),
    dict(part="-trophy", origin="Greek trophē", means="nourishment", example="dystrophy, atrophy"),
    dict(part="dys-", origin="Greek", means="bad, difficult", example="dysplasia, dystrophy"),
    dict(part="a-/an-", origin="Greek", means="without", example="alkaptonuria, aplasia"),
    dict(part="-plasia", origin="Greek plassein", means="to form", example="dysplasia"),
    dict(part="-uria", origin="Greek ouron", means="in the urine", example="alkaptonuria, porphyria"),
    dict(part="scler-", origin="Greek sklēros", means="hard", example="sclerosis"),
    dict(part="erythema-", origin="Greek erythros", means="red", example="lupus erythematosus"),
    dict(part="-penia", origin="Greek penia", means="poverty, lack", example="neutropenia"),
]

# --- the cases ------------------------------------------------------------------------
# `verdict` is about the NAME, not the disease: does it still describe what we now think
# is true?
NAMES = [
    dict(
        id="lupus", current="Systemic lupus erythematosus", era="metaphor",
        etymology="Latin lupus, 'wolf' + Greek erythema, 'redness'.",
        story="The facial rash was likened to a wolf's bite — a description attributed to "
              "13th-century usage and in wide medical use by the 1800s. 'Erythematosus' "
              "was added for the redness. The name is a picture of a face, recorded before "
              "anyone could know that the disease is systemic autoimmunity.",
        verdict="metaphor outlived its era",
        consequence="Harmless but uninformative: the name tells a searcher nothing about "
                    "mechanism, so the literature is organised by a visual sign.",
        confidence="medium",
    ),
    dict(
        id="dmd", current="Duchenne muscular dystrophy", era="eponym",
        etymology="Eponym + Greek dys- 'bad' + trophē 'nourishment'.",
        story="Guillaume Duchenne de Boulogne characterised it in the 1860s. 'Dystrophy' "
              "encodes the then-current theory that the muscle was wasting from faulty "
              "NOURISHMENT. The cause is a structural protein, dystrophin, absent from the "
              "muscle membrane — nothing to do with nutrition.",
        verdict="NAME PRESERVES A DISPROVEN THEORY",
        consequence="The protein was named after the disease (dystrophin, 1987), so the "
                    "wrong theory is now embedded in the gene name as well. A mistake can "
                    "be inherited downward through a vocabulary.",
        confidence="high",
    ),
    dict(
        id="nf2", current="NF2-related schwannomatosis", era="molecular",
        etymology="Gene symbol + Schwann (eponym) + -oma 'tumour' + -osis 'condition'.",
        story="Called neurofibromatosis type 2 for decades, then renamed by international "
              "consensus in 2022. The tumours are schwannomas and meningiomas, not "
              "neurofibromas: the old name described the wrong lesion and grouped it with "
              "NF1, a different gene on a different chromosome.",
        verdict="renamed because it misdescribed",
        consequence="TWO LITERATURES. Twenty years of papers sit under the old name; a "
                    "searcher who queries only the new one sees a fraction of the evidence. "
                    "This is the ascertainment bias, created by a rename.",
        confidence="high",
    ),
    dict(
        id="gpa", current="Granulomatosis with polyangiitis", era="clinical",
        etymology="granuloma + poly- 'many' + angeion 'vessel' + -itis 'inflammation'.",
        story="Known as Wegener's granulomatosis until 2011, when rheumatology societies "
              "adopted a descriptive name. Friedrich Wegener's membership of the Nazi party "
              "had come to light, and the field decided an eponym is an honour it can "
              "withdraw.",
        verdict="eponym withdrawn on ethical grounds",
        consequence="The descriptive replacement is more informative anyway — it names the "
                    "lesion and the vessels — which is the argument for descriptive naming "
                    "independent of the ethics.",
        confidence="high",
    ),
    dict(
        id="reactive", current="Reactive arthritis", era="clinical",
        etymology="Latin re- + agere 'to act' — arthritis reacting to an infection elsewhere.",
        story="Formerly Reiter's syndrome. Hans Reiter was convicted at Nuremberg for "
              "experiments on prisoners; the eponym was abandoned in favour of a name that "
              "states the mechanism.",
        verdict="eponym withdrawn on ethical grounds",
        consequence="Same shape as GPA: the old name persists in older literature, so both "
                    "must be searched.",
        confidence="high",
    ),
    dict(
        id="pkan", current="Pantothenate kinase-associated neurodegeneration (PKAN)", era="molecular",
        etymology="The enzyme, then the process it degenerates.",
        story="Formerly Hallervorden–Spatz disease. Julius Hallervorden obtained brains "
              "from victims of the Nazi euthanasia programme. The renaming to a mechanism-"
              "based name happened in the early 2000s once the gene (PANK2) was found.",
        verdict="eponym withdrawn on ethical grounds",
        consequence="Here the ethics and the science pointed the same way: the gene was "
                    "found at about the time the field wanted the name gone.",
        confidence="medium",
    ),
    dict(
        id="down", current="Down syndrome / trisomy 21", era="eponym",
        etymology="Eponym; the earlier term was a racial comparison.",
        story="Called 'mongolism' after John Langdon Down's 1866 description, which "
              "compared affected people to a racial 'type'. The term was abandoned after "
              "the 1960s, following an objection raised by Mongolian delegates; the "
              "cytogenetic name, trisomy 21, is exact and carries none of it.",
        verdict="racial term abandoned",
        consequence="The clearest case that naming is a social act with a cost borne by "
                    "patients, not by the field that chose the name.",
        confidence="high",
    ),
    dict(
        id="alkaptonuria", current="Alkaptonuria", era="mechanism",
        etymology="Arabic al-qali 'alkali' + Greek haptein 'to bind' + -uria 'in the urine'.",
        story="Named for the chemistry: the urine darkens on standing in alkali. Archibald "
              "Garrod used it in 1902 to argue that a disease could BE a blocked metabolic "
              "step, inherited in a Mendelian ratio — the first molecular disease concept, "
              "decades before anyone could see the enzyme.",
        verdict="descriptive and still correct",
        consequence="A name derived from an observation that turned out to be mechanistic. "
                    "It aged well because it described what the substance did, not what the "
                    "patient looked like.",
        confidence="high",
    ),
    dict(
        id="cf", current="Cystic fibrosis", era="organ",
        etymology="Greek kystis 'bladder, sac' + Latin fibra — 'cystic fibrosis of the "
                  "pancreas', the appearance of the organ at autopsy.",
        story="Named by Dorothy Andersen in 1938 for what the pancreas looked like after "
              "death. Centuries earlier a Northern European saying held that a child whose "
              "brow tasted salty when kissed was fated to die — a folk observation of the "
              "sweat chloride defect, recorded long before the ion channel that causes it.",
        verdict="organ name for a systemic channel defect",
        consequence="The name points at the organ the pathologist saw, not the CFTR channel "
                    "that fails in every epithelium. Folk knowledge had the more general "
                    "observation, and no way to use it.",
        confidence="medium",
    ),
    dict(
        id="dravet", current="Dravet syndrome", era="eponym",
        etymology="Eponym, replacing a descriptive clinical name.",
        story="Charlotte Dravet described it in 1978 as 'severe myoclonic epilepsy in "
              "infancy' (SMEI). The field moved TOWARD the eponym — the descriptive name "
              "was inaccurate, since not every patient has prominent myoclonus.",
        verdict="eponym adopted because the description was wrong",
        consequence="Runs against the usual direction and shows the rule is not 'eponyms "
                    "bad': a wrong description is worse than an opaque name.",
        confidence="medium",
    ),
    dict(
        id="zellweger", current="Zellweger spectrum disorder", era="eponym",
        etymology="Eponym + 'spectrum', added when the boundaries dissolved.",
        story="Hans Zellweger described the syndrome in the 1960s. 'Spectrum' was appended "
              "once it became clear that several once-separate entities were the same "
              "peroxisome-biogenesis defect at different severities.",
        verdict="lumped, and the name records the lumping",
        consequence="A rare case where the name carries its own taxonomic history: "
                    "'spectrum' is the scar left by merging entities.",
        confidence="medium",
    ),
    dict(
        id="swan", current="SWAN — syndrome without a name", era="clinical",
        etymology="An acronym for an absence.",
        story="The term families use for a child whose condition has no diagnosis and "
              "therefore no name. It exists because the naming system's failure is itself "
              "something people needed a word for.",
        verdict="a name for having no name",
        consequence="Invisible to every catalogue keyed on identifiers — the same entries "
                    "the lexicon models as UNKNOWN rather than as blank.",
        confidence="high",
    ),
]


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated": "2026-08-27",
        "premise": (
            "A disease's name decides what a literature search finds, which decides what "
            "evidence is discoverable, which is the ascertainment bias measured elsewhere "
            "in this atlas (+0.236). Etymology sits upstream of the statistics."
        ),
        "provenance": (
            "Historical and etymological claims written from working knowledge, each with a "
            "confidence mark. Dates and first-description attributions are the least "
            "reliable field here. The renaming cases are well documented. The ethical "
            "entries describe documented history; they do not adjudicate it."
        ),
        "eras": ERAS,
        "roots": ROOTS,
        "names": NAMES,
        "summary": {
            "cases": len(NAMES),
            "byEra": dict(Counter(n["era"] for n in NAMES)),
            "renamedForEthics": sum(1 for n in NAMES if "ethical" in n["verdict"] or "racial" in n["verdict"]),
            "namePreservesError": sum(1 for n in NAMES if "DISPROVEN" in n["verdict"].upper()
                                      or "misdescrib" in n["verdict"]),
            "twoLiteratures": sum(1 for n in NAMES if "TWO LITERATURES" in n["consequence"]),
            "byConfidence": dict(Counter(n["confidence"] for n in NAMES)),
        },
    }
    path = DEST / "nomenclature.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    s = payload["summary"]
    print("wrote %s" % path.relative_to(ROOT))
    print("  %d cases across %d naming eras and %d recurring word-parts"
          % (s["cases"], len(ERAS), len(ROOTS)))
    print("  %d renamed on ethical or racial grounds" % s["renamedForEthics"])
    print("  %d whose name preserves an error the field has corrected" % s["namePreservesError"])
    print("  confidence: %s" % s["byConfidence"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
