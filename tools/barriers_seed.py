#!/usr/bin/env python
"""What actually blocks a therapy, per disease — and the modern route that is underused.

WHY THIS LAYER EXISTS. Every other tab says what is known. None of them says what is
*stopping* anything. A dossier that lists 94 trials and 47 signs still does not tell a
researcher why the disease is hard, and "hard" is not one thing: a gene too large for its
vector is a different problem from a tissue a drug cannot reach, which is different again
from a cohort too small to power an endpoint.

FOUR BARRIER CLASSES, kept separate because the fix differs:

    molecular   the lesion itself resists the available chemistry
    delivery    the agent works but cannot reach the tissue at dose
    trial       the biology is tractable and the evidence base is not
    economic    everything works and nobody will pay to find out

THE UNDERUSED COLUMN is the point of the file. For each disease, a modern approach that
exists, is used elsewhere, and is not much applied here — with the reason it is not, so
the entry is a hypothesis rather than an exhortation.

PROVENANCE. Written from working knowledge. Mechanistic and pharmacological claims are
well established in their fields; the judgement that something is *underused* is exactly
that — a judgement — and is marked with lower confidence throughout. Nothing here is
clinical guidance or a treatment recommendation.

    python tools/barriers_seed.py     # writes out/rare/barriers.json
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "out" / "rare"

# --- cross-cutting theory: the ideas a strategy is chosen from ------------------------
THEORIES = [
    dict(id="haplo", name="Haploinsufficiency vs dominant negative",
         field="Medical genetics",
         says="Half the normal protein is not enough (haploinsufficiency) versus the mutant "
              "product actively poisoning the normal one (dominant negative).",
         decides="It decides the entire strategy. Haploinsufficiency wants MORE gene — add "
                 "a copy, upregulate the healthy allele. A dominant negative wants LESS — "
                 "silence the mutant allele specifically. Getting this backwards makes the "
                 "disease worse, not merely unhelped.",
         confidence="high"),
    dict(id="chaperone", name="Pharmacological chaperones",
         field="Protein folding / medicinal chemistry",
         says="A small molecule that binds a misfolded protein can stabilise it enough to "
              "escape degradation and reach its post.",
         decides="Turns a 'missing protein' disease into a 'mislocated protein' one, which "
                 "is a far easier target. The CFTR correctors are the proof it works at "
                 "scale; the logic transfers wherever the mutant protein is made but "
                 "destroyed.",
         confidence="high"),
    dict(id="readthrough", name="Nonsense read-through",
         field="Translation biology",
         says="A premature stop codon can sometimes be read through, restoring a full-length "
              "protein at low efficiency.",
         decides="Applies to whatever fraction of a disease's patients carry a nonsense "
                 "variant — often 10-20%. That fraction is a sub-population inside a rare "
                 "disease, which is the ultra-rare arithmetic again.",
         confidence="medium"),
    dict(id="splice", name="Splice modulation",
         field="RNA biology",
         says="An antisense oligonucleotide bound to a splice site can force an exon in or "
              "out of the final message.",
         decides="It is the fastest route from a variant to a construct, and the n-of-1 "
                 "precedent. It works only where the lesion is legible at the RNA level.",
         confidence="high"),
    dict(id="substrate", name="Substrate reduction vs replacement",
         field="Metabolic medicine",
         says="If an enzyme is missing you can supply the enzyme, or you can reduce how much "
              "of its substrate is made.",
         decides="Reduction reaches tissues an infused enzyme cannot — including, sometimes, "
                 "the brain. Replacement is more direct but stops at every barrier the "
                 "protein cannot cross.",
         confidence="high"),
    dict(id="aav_ceiling", name="The AAV ceiling",
         field="Gene therapy",
         says="A single AAV carries about 4.7 kb, and neutralising antibodies after the "
              "first dose usually make a second one impossible.",
         decides="Two hard limits at once: the gene must fit, and you get one attempt. Both "
                 "are underappreciated in early strategy discussions, and both are why "
                 "non-viral delivery keeps returning.",
         confidence="high"),
    dict(id="mosaic", name="Mosaicism and the unit of treatment",
         field="Developmental genetics",
         says="In X-linked disease and somatic mosaicism the genotype differs between cells "
              "of the same person.",
         decides="The target is a cell population, not a patient — so a therapy that "
                 "corrects 30% of cells may or may not be enough depending on whether the "
                 "corrected cells have an advantage. See the Lyon transform.",
         confidence="high"),
    dict(id="natural_history", name="Natural history as infrastructure",
         field="Clinical trial methodology",
         says="Without knowing how a disease progresses untreated, a single-arm trial has "
              "nothing to be compared against.",
         decides="For most ultra-rare diseases this, not the molecule, is the blocking step "
                 "— and it takes years that a progressive disease does not give.",
         confidence="high"),
]

# --- per disease. `catalogueName` matches tools/dossier.py so the UI can join. ---------
BARRIERS = [
    dict(
        catalogueName="Duchenne muscular dystrophy",
        mechanism="Dystrophin is absent from the sarcolemma, so the membrane tears under "
                  "contraction. The protein is structural, not enzymatic — there is nothing "
                  "to supplement.",
        barriers=[
            dict(kind="molecular",
                 what="The dystrophin coding sequence is about 11 kb. A single AAV carries "
                      "roughly 4.7 kb.",
                 why="Every approved AAV product for this disease delivers a shortened "
                     "micro-dystrophin, which is a different protein from the one that is "
                     "missing — the trade is made because the full gene cannot fit."),
            dict(kind="delivery",
                 what="Muscle is 30-40% of body mass.",
                 why="The dose required to transduce it systemically is at the edge of what "
                     "capsid load and liver toxicity allow. This is a mass problem, not a "
                     "targeting problem."),
            dict(kind="molecular",
                 what="A patient who has never made dystrophin can see it as foreign.",
                 why="Immune response to the restored protein is a real failure mode, and it "
                     "is more likely for larger deletions."),
        ],
        underused=[
            dict(approach="mRNA or non-viral delivery of full-length dystrophin",
                 why_it_fits="Removes the 4.7 kb ceiling entirely and is re-dosable, which "
                             "the AAV route is not.",
                 why_not_used="Durability and repeat-dose tolerability in muscle are "
                              "unproven; the field has capital committed to capsids.",
                 confidence="low"),
            dict(approach="CRISPR reframing rather than exon skipping",
                 why_it_fits="A permanent edit removes lifelong repeat dosing, and the same "
                             "guide covers a whole mutation hotspot rather than one exon.",
                 why_not_used="Editing muscle stem cells at scale, and the one-shot AAV "
                              "delivery problem again.",
                 confidence="medium"),
        ],
        confidence="high",
    ),
    dict(
        catalogueName="Cystic fibrosis",
        mechanism="CFTR is a chloride channel. Different variant classes break it in "
                  "different ways — not made, not folded, not opened, not enough.",
        barriers=[
            dict(kind="molecular",
                 what="The modulators work by variant CLASS, and the rarest classes have no "
                      "modulator.",
                 why="A therapy that reaches ~90% of patients leaves the last 10% with a "
                     "disease that is now, for them, still untreatable — and they are the "
                     "hardest to run a trial in, because the comparator population left."),
            dict(kind="trial",
                 what="Success has removed the endpoint.",
                 why="With most patients stable on modulators, the outcome measures that "
                     "powered the original trials no longer move, so a new agent has "
                     "nothing to demonstrate against."),
        ],
        underused=[
            dict(approach="Theratyping in patient-derived organoids",
                 why_it_fits="Tests a modulator on the individual's own cells, which makes "
                             "an n-of-1 decision possible for a variant too rare to trial.",
                 why_not_used="Reimbursement rarely recognises an organoid response as "
                              "evidence, so the assay exists and the pathway does not.",
                 confidence="medium"),
            dict(approach="Read-through and nonsense suppression for class I variants",
                 why_it_fits="Addresses precisely the group modulators cannot reach.",
                 why_not_used="Efficiency has been too low to reach a clinically meaningful "
                              "protein level; the chemistry has repeatedly disappointed.",
                 confidence="medium"),
        ],
        confidence="high",
    ),
    dict(
        catalogueName="Full NF2-related schwannomatosis",
        mechanism="Merlin is lost, releasing YAP/TAZ-TEAD. The tumours are benign, "
                  "multiple, and lifelong; the damage is anatomical — nerve compression and "
                  "hearing loss — rather than metastatic.",
        barriers=[
            dict(kind="molecular",
                 what="It is a tumour suppressor. You cannot inhibit an absence.",
                 why="The drug target has to be a downstream dependency, not the lesion — "
                     "which is why the whole approach hangs on Hippo being the right "
                     "downstream axis."),
            dict(kind="trial",
                 what="The endpoint is hearing, not tumour size.",
                 why="A tumour can shrink without hearing returning, and hearing is what the "
                     "patient came for. Radiographic response is the easy endpoint and the "
                     "wrong one."),
            dict(kind="molecular",
                 what="Benign, slow, lifelong.",
                 why="Cytotoxicity acceptable in metastatic cancer is not acceptable here. "
                     "The therapeutic window is far narrower than the oncology precedent "
                     "the drugs come from."),
        ],
        underused=[
            dict(approach="Local delivery to the internal auditory canal",
                 why_it_fits="The tumours sit in a small, anatomically defined compartment. "
                             "Systemic exposure buys nothing and costs the whole toxicity "
                             "profile.",
                 why_not_used="Delivery devices and the surgical route are a development "
                              "programme of their own, and the trial population is small.",
                 confidence="low"),
            dict(approach="Hearing preservation as the primary endpoint from the start",
                 why_it_fits="Aligns the measurement with the thing that matters, and would "
                             "have changed which of the existing agents looked promising.",
                 why_not_used="Audiometric endpoints are noisier and slower than imaging, so "
                              "they cost sample size a rare disease does not have.",
                 confidence="medium"),
        ],
        confidence="medium",
    ),
    dict(
        catalogueName="Proximal spinal muscular atrophy",
        mechanism="SMN1 is lost; the near-identical SMN2 makes a small amount of full-length "
                  "protein because of a splice defect. The therapeutic idea is to fix SMN2's "
                  "splicing rather than replace SMN1.",
        barriers=[
            dict(kind="delivery",
                 what="Motor neurons sit behind the blood-brain barrier.",
                 why="The approved oligonucleotide is given intrathecally for life; the gene "
                     "therapy is a single systemic dose with an antibody ceiling."),
            dict(kind="trial",
                 what="Newborn screening changed the disease.",
                 why="Treating before symptoms produces outcomes the original trials could "
                     "not measure, so the historical natural history no longer describes "
                     "the treated population — a good problem that invalidates the "
                     "comparator."),
        ],
        underused=[
            dict(approach="Treating the muscle as well as the neuron",
                 why_it_fits="Survivors of early treatment reveal residual muscle pathology "
                             "the neuron-directed agents do not address.",
                 why_not_used="Combination trials in a now-scarce untreated population are "
                              "difficult to power and to justify ethically.",
                 confidence="medium"),
        ],
        confidence="high",
    ),
    dict(
        catalogueName="Dravet syndrome",
        mechanism="SCN1A haploinsufficiency reduces Nav1.1 in inhibitory interneurons, so "
                  "the brain loses its brakes rather than gaining an accelerator.",
        barriers=[
            dict(kind="molecular",
                 what="Sodium-channel blockers make it worse.",
                 why="The intuitive antiepileptic is contraindicated, because blocking the "
                     "channel deepens the interneuron deficit. A mechanism can invert a "
                     "whole drug class."),
            dict(kind="molecular",
                 what="It is haploinsufficiency, so the goal is MORE gene.",
                 why="Upregulating an allele is harder than silencing one; there is no "
                     "established modality for 'make this gene produce more'."),
            dict(kind="delivery",
                 what="The target cell is a specific interneuron population.",
                 why="Broad CNS delivery risks raising Nav1.1 where it is not wanted."),
        ],
        underused=[
            dict(approach="TANGO-style antisense upregulation",
                 why_it_fits="Directly answers the haploinsufficiency problem by blocking a "
                             "non-productive splice event, raising output from the healthy "
                             "allele — the rare modality that increases a gene.",
                 why_not_used="Newer than the silencing platforms and requires the gene to "
                              "have an exploitable non-productive isoform; not every "
                              "haploinsufficiency does.",
                 confidence="medium"),
        ],
        confidence="high",
    ),
    dict(
        catalogueName="CDKL5-deficiency disorder",
        mechanism="A kinase is lost in neurons. Unlike Dravet the downstream substrates are "
                  "not well mapped, so there is no pathway to target instead of the gene.",
        barriers=[
            dict(kind="molecular",
                 what="X-linked, and most patients are mosaic.",
                 why="A female patient's cells are a mixture of expressing and silenced — so "
                     "'correct the gene' means correcting a fraction of cells, and nobody "
                     "knows what fraction suffices."),
            dict(kind="trial",
                 what="Seizure count is a poor proxy for the thing families care about.",
                 why="Development and communication are what matters and they change over "
                     "years, not weeks."),
        ],
        underused=[
            dict(approach="Protein replacement across the blood-brain barrier via a "
                         "transferrin-receptor shuttle",
                 why_it_fits="Delivers the missing kinase itself, sidestepping both the "
                             "mosaicism question and the need to edit every neuron.",
                 why_not_used="Shuttle platforms are new, and an intracellular kinase is a "
                              "much harder cargo than a secreted enzyme.",
                 confidence="low"),
        ],
        confidence="medium",
    ),
    dict(
        catalogueName="Zellweger syndrome",
        mechanism="Peroxisome biogenesis fails, so an entire organelle is missing or empty. "
                  "This is not one enzyme.",
        barriers=[
            dict(kind="molecular",
                 what="The defect is an organelle, not a reaction.",
                 why="There is no single substrate to reduce or product to replace; several "
                     "pathways fail at once."),
            dict(kind="trial",
                 what="The severe end presents in the newborn period.",
                 why="Any intervention window is measured in weeks, which no conventional "
                     "development timeline meets."),
        ],
        underused=[
            dict(approach="Variant-specific base editing in the milder PEX genotypes",
                 why_it_fits="The mild end of the spectrum has residual function and a slower "
                             "course — the group where an edit has time to matter.",
                 why_not_used="The severe end drives the urgency and the funding, so the "
                              "tractable subgroup gets less attention than the intractable "
                              "one.",
                 confidence="low"),
        ],
        confidence="medium",
    ),
    dict(
        catalogueName="Fibrodysplasia ossificans progressiva",
        mechanism="A gain-of-function ACVR1 variant makes BMP signalling constitutive, so "
                  "soft tissue turns to bone after injury.",
        barriers=[
            dict(kind="molecular",
                 what="Gain of function — more gene is the problem.",
                 why="Inverts the usual logic: nothing to add, and the target must be "
                     "inhibited without touching normal BMP signalling."),
            dict(kind="trial",
                 what="Biopsy is contraindicated.",
                 why="Trauma triggers the disease, so the standard tissue evidence cannot be "
                     "collected. The measurement itself is harmful — a constraint almost no "
                     "other disease imposes."),
            dict(kind="trial",
                 what="Flare-ups are episodic and unpredictable.",
                 why="An endpoint has to catch an event nobody can schedule."),
        ],
        underused=[
            dict(approach="Allele-selective silencing of the mutant ACVR1",
                 why_it_fits="Leaves wild-type BMP signalling intact, which every "
                             "small-molecule inhibitor cannot promise.",
                 why_not_used="Allele-selective knockdown against a single-base difference "
                              "is technically hard and the population is tiny.",
                 confidence="low"),
        ],
        confidence="medium",
    ),
    dict(
        catalogueName="Alkaptonuria",
        mechanism="Homogentisate oxidase is missing, so homogentisic acid accumulates and "
                  "deposits in cartilage over decades. Garrod's original inborn error.",
        barriers=[
            dict(kind="trial",
                 what="Damage accumulates over forty years.",
                 why="An endpoint that takes decades cannot be run in a normal trial, so the "
                     "field needed a biochemical surrogate before it could test anything."),
            dict(kind="economic",
                 what="Slow, non-fatal, and very rare.",
                 why="Every commercial incentive points elsewhere, which is why the "
                     "successful agent was repurposed rather than discovered."),
        ],
        underused=[
            dict(approach="The repurposing-plus-surrogate template itself",
                 why_it_fits="This disease solved a general problem: an existing molecule "
                             "plus a validated biochemical surrogate turned an untestable "
                             "endpoint into a testable one.",
                 why_not_used="It is a methodological result, and methodological results "
                              "travel between diseases far more slowly than molecules do.",
                 confidence="medium"),
        ],
        confidence="high",
    ),
    dict(
        catalogueName="Systemic lupus erythematosus",
        mechanism="Failed clearance of dying cells feeds nucleic-acid sensing, which drives "
                  "type I interferon, which licenses autoreactive B cells. A loop, not a "
                  "pathway.",
        barriers=[
            dict(kind="trial",
                 what="Heterogeneity defeats the endpoint.",
                 why="Composite responder indices average across patients whose disease is "
                     "driven by different arms of the loop, so a real effect in a subgroup "
                     "disappears into the mean. This is the atlas's own argument about "
                     "summaries, in a trial."),
            dict(kind="molecular",
                 what="Long-lived plasma cells do not express CD20.",
                 why="B-cell depletion leaves the antibody factory standing, which is the "
                     "usual explanation for incomplete responses."),
            dict(kind="trial",
                 what="Background immunosuppression is ethically required.",
                 why="Every arm is already treated, so the measurable increment is small."),
        ],
        underused=[
            dict(approach="Interferon signature stratification at enrolment",
                 why_it_fits="Splits the loop into the arm each patient actually runs on. "
                             "The signature is measurable today and mostly used descriptively.",
                 why_not_used="Stratifying shrinks an already difficult recruitment, and "
                              "regulators have not required it.",
                 confidence="medium"),
            dict(approach="Targeting clearance rather than the amplifier",
                 why_it_fits="Complement and clearance are the two mechanisms with the "
                             "strongest monogenic evidence and nothing pointed at them — "
                             "measured in this atlas's own network tab.",
                 why_not_used="Restoring a clearance function is harder than blocking a "
                              "cytokine, and the monogenic evidence sits in ultra-rare "
                              "patients while the market is the common disease.",
                 confidence="medium"),
        ],
        confidence="medium",
    ),
    dict(
        catalogueName="Rett syndrome",
        mechanism="MECP2 loss in neurons. The protein is dose-sensitive in BOTH directions — "
                  "duplication causes a separate disease.",
        barriers=[
            dict(kind="molecular",
                 what="Too much MECP2 is also a disease.",
                 why="Gene replacement has to land inside a narrow window, per cell. This is "
                     "the clearest case in medicine where 'add a working copy' is actively "
                     "dangerous."),
            dict(kind="molecular",
                 what="X-linked mosaicism.",
                 why="Each neuron has already chosen an X. A therapy meets a checkerboard of "
                     "expressing and silent cells."),
        ],
        underused=[
            dict(approach="Reactivating the silent wild-type X",
                 why_it_fits="Every female patient carries a healthy MECP2 that is switched "
                             "off. Reactivating it delivers exactly one copy in exactly the "
                             "cells that need it — no dosage problem by construction.",
                 why_not_used="X reactivation is not selective for one gene, so the risk of "
                              "waking the rest of the chromosome is unresolved.",
                 confidence="medium"),
        ],
        confidence="high",
    ),
    dict(
        catalogueName="Sickle cell anemia",
        mechanism="A single base changes haemoglobin so it polymerises when deoxygenated. "
                  "The most-studied point mutation in medicine.",
        barriers=[
            dict(kind="delivery",
                 what="Approved gene therapies require myeloablative conditioning.",
                 why="The cure requires chemotherapy with its own mortality and infertility "
                     "risk — the barrier is the conditioning, not the edit."),
            dict(kind="economic",
                 what="The burden is concentrated where the therapy is least available.",
                 why="A per-patient cost in the millions, in populations largely in "
                     "sub-Saharan Africa and India. The scientific problem is closer to "
                     "solved than the delivery problem, by a wide margin."),
        ],
        underused=[
            dict(approach="In vivo editing without conditioning",
                 why_it_fits="Removes the transplant entirely, which is the whole barrier: "
                             "no conditioning, no apheresis, no manufacturing per patient.",
                 why_not_used="Targeting haematopoietic stem cells in situ is unsolved, "
                              "though non-viral delivery has made it credible.",
                 confidence="medium"),
            dict(approach="Fetal haemoglobin induction by small molecule",
                 why_it_fits="An oral agent scales to the populations that carry the burden "
                             "in a way an ex vivo product never will.",
                 why_not_used="Existing inducers are partial, and the field's attention "
                              "followed the curative story rather than the scalable one.",
                 confidence="medium"),
        ],
        confidence="high",
    ),
]


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    kinds = Counter(b["kind"] for d in BARRIERS for b in d["barriers"])
    conf = Counter(u["confidence"] for d in BARRIERS for u in d["underused"])
    payload = {
        "generated": "2026-08-27",
        "premise": (
            "Every other tab says what is known. This one says what is stopping anything — "
            "and 'hard' is not one thing. A gene too large for its vector is a different "
            "problem from a tissue a drug cannot reach, which is different again from a "
            "cohort too small to power an endpoint."
        ),
        "provenance": (
            "Written from working knowledge. Mechanistic and pharmacological claims are well "
            "established in their fields; the judgement that an approach is UNDERUSED is a "
            "judgement, and is marked with lower confidence throughout. Not clinical "
            "guidance and not a treatment recommendation."
        ),
        "barrierKinds": [
            {"id": "molecular", "name": "Molecular",
             "note": "The lesion itself resists the available chemistry."},
            {"id": "delivery", "name": "Delivery",
             "note": "The agent works but cannot reach the tissue at dose."},
            {"id": "trial", "name": "Trial design",
             "note": "The biology is tractable and the evidence base is not."},
            {"id": "economic", "name": "Economic",
             "note": "Everything works and nobody will pay to find out."},
        ],
        "theories": THEORIES,
        "diseases": BARRIERS,
        "summary": {
            "diseases": len(BARRIERS),
            "barriers": sum(len(d["barriers"]) for d in BARRIERS),
            "byKind": dict(kinds),
            "underusedApproaches": sum(len(d["underused"]) for d in BARRIERS),
            "underusedByConfidence": dict(conf),
            "theories": len(THEORIES),
        },
    }
    path = DEST / "barriers.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    s = payload["summary"]
    print("wrote %s" % path.relative_to(ROOT))
    print("  %d diseases · %d barriers · %d underused approaches · %d cross-cutting theories"
          % (s["diseases"], s["barriers"], s["underusedApproaches"], s["theories"]))
    print("  barriers by kind: %s" % s["byKind"])
    print("  underused, by confidence in the JUDGEMENT: %s" % s["underusedByConfidence"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
