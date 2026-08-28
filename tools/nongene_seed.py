#!/usr/bin/env python
"""What fills the gene slot when there is no gene — the equivalences, and the mechanisms.

WHY THIS LAYER EXISTS, AND WHY IT IS THE ATLAS'S BLINDEST SPOT. Every join in this project is
keyed on a gene. The world atlas reaches 14,831 diseases and finds a causal gene for 11,030 of
them; the cell axis exists only because a gene can be looked up in an expression table. That
architecture is a choice, and it has a cost that shows up as a number: the diseases with no
gene are not merely missing a column — they are structurally invisible to every downstream
computation on this site. The cell tab cannot place them. The dependency screen cannot score
them. The dossier shows them as gaps.

So this file asks the question the architecture suppresses: when the causal unit is not a
gene, WHAT IS IT? And the answer is not "nothing" or "unknown". It is a protein conformation,
an antibody clone, a molecule at a dose in a developmental window, a methylation mark, a
somatic mosaic confined to one tissue, a repeat length that changes during life, or an amount
of delivered mechanical energy. Each of those fills every slot the gene fills — it has a
perturbation, a dose-response, a carrier, an assay that detects it, an intervention aimed at
it, and a reason it recurs. Writing that mapping out is the point of the file.

THE SEVEN SLOTS. The gene pipeline has a fixed shape, and naming it lets the equivalence be
checked rather than asserted:

    causal unit      what the disease is "of"
    perturbation     the thing that went wrong with the unit
    dose             what decides whether and how severely it shows
    carrier          who or what holds it
    assay            the test that finds it, and why sequencing does not
    intervention     what a therapy aimed at the unit looks like
    recurrence       why it happens again, in the same person or the next

PHENOCOPY PAIRS ARE THE PROOF. The strongest argument that these are genuine equivalences and
not a metaphor is that the two routes converge on the same clinical picture. Thalidomide
degrades SALL4 and produces the limb phenotype of SALL4 mutation. Lead inhibits ALAD and
produces the porphyria of ALAD deficiency. An antibody against the NMDA receptor internalises
it and produces the encephalopathy of GRIN loss-of-function. Same endpoint, different causal
unit — which means the mechanism is the real object and the gene was only ever one way in.

PROVENANCE. Written from working knowledge; the mechanisms and the phenocopy pairs are well
established in their fields and each names the enzyme, receptor or mark it turns on, so each
is checkable. The count of gene-less diseases is read live from the atlas, not typed. Nothing
here is clinical guidance.

    python tools/nongene_seed.py     # writes out/rare/nongene.json
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "out" / "rare"

SLOTS = [
    dict(id="unit", name="Causal unit", gene="A gene",
         note="What the disease is 'of' — the thing a catalogue would key on."),
    dict(id="perturbation", name="Perturbation", gene="A variant",
         note="What went wrong with the unit."),
    dict(id="dose", name="Dose and threshold", gene="Penetrance and expressivity",
         note="What decides whether it shows at all, and how severely."),
    dict(id="carrier", name="Carrier", gene="A person, in every cell",
         note="Who or what holds it — and this row is where the gene model breaks first."),
    dict(id="assay", name="The assay", gene="Sequencing",
         note="The test that finds it, and the reason sequencing does not."),
    dict(id="intervention", name="Intervention at the unit", gene="Gene therapy",
         note="What a therapy aimed at the causal unit itself looks like."),
    dict(id="recurrence", name="Recurrence", gene="Inheritance",
         note="Why it happens again — in this person, or in the next one."),
]


def cls(id, name, oneLine, unit, perturbation, dose, carrier, assay, intervention, recurrence,
        mechanism, whyGeneThinkingFails, examples, confidence="high"):
    return dict(id=id, name=name, oneLine=oneLine,
                slots=dict(unit=unit, perturbation=perturbation, dose=dose, carrier=carrier,
                           assay=assay, intervention=intervention, recurrence=recurrence),
                mechanism=mechanism, whyGeneThinkingFails=whyGeneThinkingFails,
                examples=examples, confidence=confidence)


CLASSES = [
    cls("conformational", "Conformation", "The information is in a shape, not a sequence.",
        unit="A conformer of a protein — the same amino acid chain folded a different way.",
        perturbation="Templated misfolding: an already-misfolded molecule imposes its fold on a "
                     "normally folded one.",
        dose="Seeding dose and the concentration of available substrate. Lower substrate means "
             "slower propagation, which is why the therapeutic target is the normal protein.",
        carrier="Any tissue holding the substrate. The conformer is transmissible between "
                "individuals, which no genotype is.",
        assay="Real-time quaking-induced conversion amplifies the CONFORMATION the way a "
              "polymerase amplifies a sequence: seed, shake, fragment, repeat. Sequencing the "
              "gene tells you nothing, because the sequence is often normal.",
        intervention="Lower the substrate. A PrP-lowering antisense oligonucleotide is the "
                     "clearest case in the file where the treatment for a non-genetic disease "
                     "is a gene-directed drug — the arrow runs the other way.",
        recurrence="Exposure, or spontaneous nucleation, or an inherited variant that raises "
                   "the spontaneous rate. All three routes converge on one conformer.",
        mechanism="A beta-sheet-rich conformer recruits the normally folded protein onto the end "
                  "of a growing fibril. Fibrils then FRAGMENT, and fragmentation is what makes "
                  "the process exponential rather than linear: each break creates two new "
                  "growing ends. Strain differences — incubation time, lesion distribution — are "
                  "carried in the conformation itself, so a single sequence supports several "
                  "heritable phenotypes. That is inheritance without nucleic acid, and it is why "
                  "the word 'genotype' has a real analogue here.",
        whyGeneThinkingFails="The sequence can be entirely normal in a fatal, transmissible "
                             "disease. Every gene-keyed database records it as having no cause.",
        examples=["Creutzfeldt-Jakob disease, sporadic and acquired",
                  "Fatal familial insomnia — same gene, different conformer, different disease",
                  "The prion-like templating now described for alpha-synuclein, tau and "
                  "amyloid-beta spread",
                  "Serpin polymerisation in alpha-1 antitrypsin deficiency"]),

    cls("autoimmune", "Antibody clone",
        "A phenocopy of loss-of-function, produced by a protein that binds instead of a gene "
        "that fails.",
        unit="An epitope, plus the B-cell clone that recognises it. The pair is the unit; "
             "neither alone is.",
        perturbation="A clone escaping tolerance — by mimicry, by bystander activation, or by "
                     "an antigen becoming visible that should not have been.",
        dose="Titre and affinity, and whether the antibody merely binds or actually blocks. "
             "Receptor occupancy is the threshold, and it is a continuous variable, which is "
             "why severity fluctuates within one patient.",
        carrier="The clone, not the person's genome. Remove the clone and the disease goes.",
        assay="A cell-based assay presenting the antigen in its native conformation. This "
              "matters: an antibody that only recognises the folded receptor is missed by a "
              "denatured-antigen test, which is how seronegative patients are made.",
        intervention="Clone-specific depletion is the direct analogue of allele-specific "
                     "silencing — anti-CD19 or anti-CD20, or CAR-T aimed at the B lineage. "
                     "Removing the product rather than the source is the FcRn blockade, which "
                     "is the analogue of protein knockdown.",
        recurrence="Not meiosis. Persistence of a memory clone, and epitope spreading widening "
                   "the target over time.",
        mechanism="Anti-NMDA-receptor encephalitis is the cleanest equivalence in this file. The "
                  "antibody crosslinks the receptor's GluN1 subunit and drives it into the cell "
                  "by internalisation. The receptor is not destroyed and the gene is untouched — "
                  "surface density falls, and the clinical result is the encephalopathy of GRIN1 "
                  "loss of function. An antibody has performed a reversible functional knockdown. "
                  "Rheumatic heart disease shows the other route: streptococcal M protein shares "
                  "epitopes with cardiac myosin, so the immune response to an infection lands on "
                  "the heart — molecular mimicry, where the causal unit is a resemblance.",
        whyGeneThinkingFails="Reversibility. A genetic loss of function is permanent; this one "
                             "resolves when the antibody is cleared, which means the natural "
                             "history has a shape no genotype produces.",
        examples=["Anti-NMDA-receptor encephalitis, against GRIN1/GRIN2B encephalopathy",
                  "Myasthenia gravis (anti-AChR, anti-MuSK), against congenital myasthenic "
                  "syndromes",
                  "Acquired thrombotic thrombocytopenic purpura (anti-ADAMTS13), against "
                  "hereditary TTP",
                  "Rheumatic heart disease, by mimicry rather than by blockade"]),

    cls("exposure", "Molecule, dose and window",
        "A drug that degrades a protein produces the syndrome of losing that protein's gene.",
        unit="A molecule, at a dose, inside a developmental window. All three are required; the "
             "window is what a gene never needs.",
        perturbation="Binding an endogenous target — an enzyme inhibited, or a degradation "
                     "machine redirected onto a protein it should not touch.",
        dose="A real dose-response, with a threshold and a timing dependence. Penetrance in the "
             "genetic sense is replaced by something measurable in milligrams and days.",
        carrier="Nobody. The exposure is over. What remains is the injury, which is why "
                "'carrier' is the slot where this class has no entry at all.",
        assay="Exposure biomarkers, adducts, or the surviving injury pattern. Usually the window "
              "has closed before the question is asked, which makes attribution the hard part.",
        intervention="Remove or antagonise the exposure; chelate, or replace what was blocked. "
                     "In the porphyria case the intervention is substrate-level, exactly as in "
                     "the inherited form.",
        recurrence="A shared environment. Families exposed together look inherited, and this is "
                   "the single most productive source of false genetic hypotheses in medicine.",
        mechanism="Thalidomide binds cereblon, the substrate receptor of an E3 ubiquitin ligase, "
                  "and redirects it onto neosubstrates it would never normally degrade — SALL4 "
                  "among them. Degrading SALL4 reproduces the limb and ear phenotype of SALL4 "
                  "mutation. The drug did not damage DNA; it removed a protein, and the body "
                  "cannot tell the difference between a protein removed by a small molecule and "
                  "one never made. Lead makes the same point at the enzyme level: it inhibits "
                  "delta-aminolevulinic acid dehydratase, the very enzyme deficient in ALAD "
                  "porphyria, and the biochemical picture converges. Methylmercury at Minamata "
                  "adds the window: the same exposure gives adults a peripheral syndrome and "
                  "prenatally exposed children a cerebral palsy phenotype, because timing, not "
                  "dose alone, selects the phenotype.",
        whyGeneThinkingFails="It is preventable, which no genotype is, and the causal unit "
                             "leaves the body. The disease outlives its cause.",
        examples=["Thalidomide embryopathy, against SALL4-related syndromes",
                  "Lead poisoning, against ALAD-deficiency porphyria",
                  "Warfarin embryopathy, against chondrodysplasia punctata",
                  "Minamata disease — the same toxin, two diseases, selected by window",
                  "Aminoglycoside ototoxicity, where an exposure and the m.1555A>G variant are "
                  "each necessary and neither is sufficient"]),

    cls("nutritional", "Substrate availability",
        "The deficiency and the transporter defect are the same disease from opposite ends.",
        unit="The concentration of a required substrate or cofactor at the tissue that needs it.",
        perturbation="Too little supplied, or too much of an antagonist — the balance, not the "
                     "molecule.",
        dose="Continuous and reversible, with a lag. The tissue accumulates a deficit and then "
             "crosses a threshold, which is why onset can look abrupt in a gradual process.",
        carrier="A diet, a soil, a supply chain. The unit is held by a region rather than by a "
                "person, which is why these diseases have maps and genes do not.",
        assay="The nutrient level plus a functional marker downstream of it. The level alone is "
              "insufficient — tissue function can fail while plasma looks adequate.",
        intervention="Supplementation. This is substrate replacement, which is the identical "
                     "strategy used against the inherited form of the same block.",
        recurrence="Seasonal, geographic, economic. It recurs on a harvest cycle.",
        mechanism="Pellagra and Hartnup disease converge exactly: pellagra is dietary niacin and "
                  "tryptophan deficiency; Hartnup is a defect in the neutral amino acid "
                  "transporter that absorbs tryptophan. Same missing molecule at the tissue, same "
                  "dermatitis-diarrhoea-dementia picture, one caused by the world and one by a "
                  "gene. Konzo is the sharper case: cassava carries cyanogenic glycosides, and "
                  "detoxifying cyanide to thiocyanate consumes sulphur amino acids. A diet that "
                  "supplies the poison and withholds the antidote produces an abrupt, permanent, "
                  "symmetrical upper-motor-neuron paralysis that is clinically a hereditary "
                  "spastic paraplegia and is caused by processing food in a hurry.",
        whyGeneThinkingFails="It is a property of a place. Move the patient and the cause does "
                             "not travel with them — the reverse of every genetic disease.",
        examples=["Pellagra, against Hartnup disease",
                  "Konzo, against hereditary spastic paraplegia",
                  "B12 deficiency, against cblC and the inherited methylmalonic acidurias",
                  "Iodine deficiency, against thyroid dyshormonogenesis",
                  "Neural tube defects and folate — where a supply and a variant interact"]),

    cls("infection", "Pathogen and window",
        "The timing of the infection selects the phenotype, the way an expression window does.",
        unit="A pathogen, plus when in development it arrived.",
        perturbation="Direct cytopathic damage, or the immune response to it, or a resemblance "
                     "between pathogen and host.",
        dose="Gestational age is the dominant variable, far more than inoculum. This is the "
             "closest thing in the file to a developmental expression window.",
        carrier="Nobody afterwards. The sequela persists after the organism has gone, which "
                "makes causal attribution decades later genuinely hard.",
        assay="Serology or nucleic acid at the right moment. Late, only the scar is testable, "
              "and the scar does not name its cause.",
        intervention="Vaccination — whose real analogue is not gene therapy but preconception "
                     "carrier screening: both act before the patient exists.",
        recurrence="Outbreaks. It clusters in time rather than in pedigrees.",
        mechanism="Congenital rubella makes the window explicit. Infection before about eight "
                  "weeks gives cardiac and ocular malformation; the same infection in the second "
                  "trimester gives deafness alone, because the organ under construction at the "
                  "moment of infection is the organ that is damaged. That is exactly the logic "
                  "of a developmental gene expressed in a narrow window. Post-polio syndrome "
                  "adds a second mechanism entirely: decades after recovery, surviving motor "
                  "neurons that had sprouted to reinnervate orphaned muscle fibres fail under "
                  "the metabolic load of maintaining oversized motor units. The late disease is "
                  "not the virus — it is the cost of the repair.",
        whyGeneThinkingFails="Preventable at the population level, invisible at the individual "
                             "genome, and separated from its cause by decades.",
        examples=["Congenital rubella syndrome",
                  "Post-polio syndrome",
                  "HTLV-1-associated myelopathy",
                  "Rheumatic heart disease, shared with the antibody class"]),

    cls("mosaic", "A tissue, not a person",
        "The gene is right and the blood test is negative, because the carrier is a body part.",
        unit="A variant present in some cells and absent from others, arising after "
             "fertilisation.",
        perturbation="A post-zygotic mutation. How early it happened sets how much of the body "
                     "carries it.",
        dose="Allele fraction in the affected tissue, and which lineage was hit. The same "
             "variant gives a different disease depending on when in development it appeared.",
        carrier="A region of tissue. This is the row where the gene model breaks outright: the "
                "unit of carriage stops being the person.",
        assay="Deep sequencing of the LESION. Blood is negative and reported as normal, which "
              "is precisely how these diseases stayed unexplained until sequencing got deep "
              "enough and someone thought to biopsy.",
        intervention="Inhibit the pathway, not the allele — the variants are activating and "
                     "converge on a small number of kinases.",
        recurrence="None, usually. Post-zygotic means not transmitted, unless the gonad is "
                   "among the tissues involved.",
        mechanism="A single activating base change in AKT1, GNAS or PIK3CA, arising in one cell "
                  "of an embryo, produces a mosaic overgrowth whose distribution maps the "
                  "descendants of that cell. The germline version of the same variant is "
                  "generally lethal early — which is why these conditions can only exist as "
                  "mosaics, and why the search for a heritable cause was always going to fail. "
                  "The therapeutic consequence is unusually clean: the variants activate a "
                  "pathway that already has approved inhibitors, so a PIK3CA-driven overgrowth "
                  "is treatable with a drug developed for breast cancer.",
        whyGeneThinkingFails="Every step of the standard pipeline samples blood. The variant is "
                             "not there, and the report says nothing was found.",
        examples=["Proteus syndrome (AKT1)",
                  "McCune-Albright syndrome (GNAS)",
                  "Sturge-Weber syndrome (GNAQ)",
                  "PIK3CA-related overgrowth spectrum, where a cancer drug treats a "
                  "malformation"]),

    cls("imprint", "A mark, not a letter",
        "The sequence is normal. What is wrong is which parent's copy is switched on.",
        unit="A methylation state at an imprinted locus — an epigenetic mark, not a base.",
        perturbation="Loss of the mark, uniparental disomy, or a deletion on the one parental "
                     "copy that was doing the work.",
        dose="Which parent, and how completely. A partial imprinting defect gives a partial "
             "phenotype, which sequencing cannot grade because there is nothing to grade.",
        carrier="A parental origin. The unit is inherited but it is not the sequence that is "
                "inherited.",
        assay="A methylation-specific assay. Exome and genome sequencing are BLIND here by "
              "construction: they read the letters and the letters are correct.",
        intervention="Unsilence the intact copy. In Angelman syndrome the paternal UBE3A is "
                     "present and silenced by an antisense transcript, so an oligonucleotide "
                     "against that transcript releases a gene the patient already has.",
        recurrence="Depends on the mechanism, and the counselling differs by an order of "
                   "magnitude between deletion, disomy and imprinting-centre defect — which is "
                   "why the assay is not optional.",
        mechanism="At the 15q11-13 locus, some genes are expressed only from the paternal "
                  "chromosome and some only from the maternal one. Lose the paternal "
                  "contribution and the result is Prader-Willi; lose the maternal and it is "
                  "Angelman. The same piece of DNA, missing from different parents, gives two "
                  "diseases with almost nothing in common — which is as direct a demonstration "
                  "as exists that sequence is not the whole of the information. The Angelman "
                  "unsilencing strategy is structurally identical to the Rett X-reactivation "
                  "plan already in the capability layer: in both, the good copy is present and "
                  "the therapeutic problem is a switch rather than a sequence.",
        whyGeneThinkingFails="A normal genome sequence, in a severe disease with a known locus. "
                             "The pipeline returns a clean result and the patient is undiagnosed.",
        examples=["Prader-Willi and Angelman syndromes",
                  "Beckwith-Wiedemann and Silver-Russell syndromes",
                  "Transient neonatal diabetes mellitus, 6q24"]),

    cls("dynamic", "A length that changes during life",
        "The genotype is not a value. It is a distribution that drifts in the tissue that dies.",
        unit="A repeat tract, whose length differs between tissues and increases with age.",
        perturbation="Expansion — in the germline between generations, and somatically within "
                     "the target tissue across a lifetime.",
        dose="Inherited length sets the age of onset; SOMATIC expansion in the vulnerable cells "
             "appears to set the pace. Two different doses of the same variable.",
        carrier="The person, but unequally. A blood measurement is not the striatal measurement, "
                "and the striatum is where the disease happens.",
        assay="Long reads that span the tract and can report a distribution rather than a "
              "number. A sizing gel returns a single length and thereby destroys the finding.",
        intervention="Target the modifier rather than the gene: mismatch-repair components such "
                     "as MSH3 govern the somatic expansion, so slowing expansion is a therapeutic "
                     "route that never touches the disease gene.",
        recurrence="Anticipation — worse and earlier each generation, which classical Mendelian "
                   "genetics recorded as an artefact for decades before the mechanism was found.",
        mechanism="Slipped-strand structures at a repeat are recognised by mismatch repair, "
                  "which — in this specific context — resolves them in a way that ADDS units. "
                  "The repair pathway is the expansion pathway, which is why disabling parts of "
                  "it slows disease in models. Because expansion continues in post-mitotic "
                  "neurons, the causal quantity is a moving target, and human genetic modifier "
                  "studies converge on repair genes rather than on anything about the protein.",
        whyGeneThinkingFails="One genotype per person is the founding assumption of the pipeline, "
                             "and here it is false within a single body.",
        examples=["Huntington disease and the MSH3/FAN1 modifiers",
                  "Myotonic dystrophy type 1",
                  "Fragile X, where the mark and the repeat interact",
                  "The late-onset repeat expansions found only once long reads existed"]),

    cls("mechanical", "Delivered energy",
        "The causal unit is measured in joules, and it is transduced by a pathway this project "
        "already screens.",
        unit="Mechanical or radiant energy delivered to a tissue — force, pressure, dose, "
             "vibration.",
        perturbation="Tissue injury, or sustained loading that never resolves into repair.",
        dose="Genuinely physical: magnitude, duration, repetition, and whether the tissue had "
             "time to recover between insults.",
        carrier="An occupation, a posture, a procedure. Held by what a person does rather than "
                "by what they are.",
        assay="Dosimetry and load history — which almost nobody records, so the exposure is "
              "usually reconstructed from memory and is the weakest measurement in the file.",
        intervention="Do not deliver the energy. In fibrodysplasia ossificans progressiva the "
                     "single most effective intervention known is to not perform the biopsy.",
        recurrence="Every time the exposure repeats. There is no immunity and no fixation.",
        mechanism="Cells read mechanical force through the cytoskeleton into the Hippo pathway: "
                  "stiff substrate and high tension keep YAP and TAZ in the nucleus, soft and "
                  "relaxed conditions push them out. That is the same pathway Merlin regulates, "
                  "and the same pathway the NF2 tab of this project screens as a positive "
                  "control — so mechanical force and a tumour suppressor converge on one "
                  "transcriptional output. In fibrodysplasia ossificans progressiva the "
                  "convergence is clinical: trauma triggers a flare because injury plus a "
                  "hypersensitive ACVR1 receptor drives soft tissue down an ossification "
                  "programme. The gene sets the threshold; the energy pulls the trigger, and "
                  "neither alone produces the disease.",
        whyGeneThinkingFails="The exposure is an event, not a state, and it is recorded nowhere. "
                             "Retrospective study designs measure recall.",
        examples=["Heterotopic ossification after burn or joint replacement",
                  "Fibrodysplasia ossificans progressiva flares",
                  "Radiation-induced sarcoma and second cancers",
                  "Hand-arm vibration syndrome"]),

    cls("idiopathic", "The honest empty slot",
        "Not a mechanism. The name of the boundary of the instruments currently in use.",
        unit="Unknown — and the word is doing work it should not be doing.",
        perturbation="Unknown.",
        dose="Unknown, and usually not even framed as a question, because framing it requires "
             "a candidate unit.",
        carrier="Unknown.",
        assay="Whatever was run and came back normal. The result is a statement about the test "
              "menu, not about the patient.",
        intervention="Symptomatic. Not aimed at any unit, because none has been named.",
        recurrence="Observed empirically and unexplained.",
        mechanism="'Idiopathic' is a boundary marker wearing the costume of a diagnosis. Every "
                  "class above spent time in this category: mosaic overgrowth was idiopathic "
                  "until tissue was sequenced deeply, prion disease was a slow virus until a "
                  "protein-only mechanism was accepted, and repeat expansions past the length of "
                  "a short read were invisible until long reads existed. The pattern is "
                  "consistent — a disease is idiopathic until an instrument that could have seen "
                  "its causal unit is invented AND pointed at it. The second half of that "
                  "sentence is what the capability tab is about, and it is where this file "
                  "connects to the money.",
        whyGeneThinkingFails="It does not fail; it never engaged. The disease was excluded from "
                             "the gene pipeline before the pipeline ran.",
        examples=["The gene-less remainder of the atlas, counted live below",
                  "Every class in this file, at some point in the last sixty years"],
        confidence="this entry is a claim about the field, not about a mechanism"),
]

# --- phenocopy pairs: the same clinical endpoint, reached by two different causal units
PHENOCOPIES = [
    dict(nonGene="Thalidomide exposure in the fourth to sixth week",
         genetic="SALL4-related syndromes (Duane-radial ray, Okihiro)",
         classId="exposure",
         convergesOn="Loss of SALL4 protein in the developing limb and ear",
         mechanism="The drug binds cereblon and redirects an E3 ubiquitin ligase onto SALL4, "
                   "degrading a protein the genetic form never makes. The cell cannot "
                   "distinguish a protein destroyed from a protein never synthesised."),
    dict(nonGene="Lead poisoning", genetic="ALAD-deficiency porphyria", classId="exposure",
         convergesOn="Inhibited delta-aminolevulinic acid dehydratase, with the same metabolite "
                     "pattern",
         mechanism="Lead displaces the enzyme's zinc. The inherited form has a defective enzyme; "
                   "the acquired form has a poisoned one, and the biochemistry is the same "
                   "downstream."),
    dict(nonGene="Anti-NMDA-receptor encephalitis",
         genetic="GRIN1 and GRIN2B loss-of-function encephalopathy",
         classId="autoimmune",
         convergesOn="Reduced NMDA receptor density at the synapse",
         mechanism="The antibody crosslinks GluN1 and drives receptor internalisation. Surface "
                   "density falls without the gene being touched — a reversible functional "
                   "knockdown performed by a protein."),
    dict(nonGene="Pellagra", genetic="Hartnup disease", classId="nutritional",
         convergesOn="Insufficient tryptophan and niacin reaching the tissue",
         mechanism="One withholds the amino acid at the plate, the other fails to absorb it at "
                   "the brush border. The tissue experiences an identical shortage."),
    dict(nonGene="Konzo", genetic="Hereditary spastic paraplegia", classId="nutritional",
         convergesOn="Symmetrical upper motor neuron degeneration",
         mechanism="Cyanide detoxification consumes sulphur amino acids; a diet supplying the "
                   "toxin and withholding the antidote injures the same tract that the "
                   "inherited axonopathies degenerate."),
    dict(nonGene="Acquired thrombotic thrombocytopenic purpura",
         genetic="Congenital TTP (Upshaw-Schulman)", classId="autoimmune",
         convergesOn="Absent ADAMTS13 activity, so von Willebrand multimers stay uncleaved",
         mechanism="An inhibitory autoantibody versus a defective gene. Both leave the protease "
                   "missing from plasma, and both are treated by supplying the enzyme."),
    dict(nonGene="Aminoglycoside exposure", genetic="m.1555A>G in mitochondrial 12S rRNA",
         classId="exposure",
         convergesOn="Irreversible cochlear hair cell loss",
         mechanism="The variant makes the human ribosome resemble its bacterial target more "
                   "closely, so the drug binds where it should not. Neither the exposure alone "
                   "nor the variant alone causes deafness — the causal unit is the pair."),
    dict(nonGene="Congenital rubella infection", genetic="CHARGE and other developmental "
                                                         "syndromes",
         classId="infection",
         convergesOn="Ocular, cardiac and cochlear malformation from a disrupted developmental "
                     "window",
         mechanism="A virus present during organogenesis damages exactly what is being built. "
                   "The window does the work a stage-specific gene would do."),
]

# --- how a non-gene cause hides inside a gene-keyed database ---------------------------
FAILURE_MODES = [
    dict(id="blood", name="The sample is wrong, not the sequencer",
         says="Mosaic disease is negative in blood and positive in the lesion. The pipeline "
              "samples what is easy to draw, and reports its own sampling choice as a result."),
    dict(id="normal_letters", name="A normal sequence in a locus disease",
         says="Imprinting disorders have correct letters and an incorrect mark. Sequencing "
              "returns clean and the diagnosis is missed by a test that worked perfectly."),
    dict(id="length", name="Longer than the read",
         says="A repeat past the insert size cannot be measured by a method that assembles short "
              "fragments. The expansion is not rare — it was unobservable."),
    dict(id="reversible", name="It got better",
         says="A treatable antibody-mediated disease resolves. Databases built around permanent "
              "genotypes have no field for a cause that leaves."),
    dict(id="environment", name="It clusters in families because they eat together",
         says="Shared exposure produces pedigrees that look dominant. This is the most productive "
              "generator of false genetic hypotheses in the history of the field."),
    dict(id="no_unit", name="No unit was ever proposed",
         says="'Idiopathic' enters the database as a value, and downstream every count treats it "
              "as if it were a finding rather than an absence."),
]


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)

    # The denominator is read live rather than typed: the atlas is the authority on how many
    # diseases its own gene-keyed architecture cannot place.
    atlas = json.loads((DEST / "atlas.json").read_text(encoding="utf-8"))
    total = atlas["scale"]["diseases"]
    with_gene = atlas["scale"]["diseasesWithGene"]
    without = total - with_gene

    ids = {c["id"] for c in CLASSES}
    for p in PHENOCOPIES:
        if p["classId"] not in ids:
            raise SystemExit("phenocopy references unknown class: %s" % p["classId"])

    payload = {
        "generated": "tools/nongene_seed.py",
        "premise": (
            "Every join in this project is keyed on a gene, so a disease without one is not "
            "merely missing a column — it is invisible to every computation downstream. This "
            "layer asks what fills the gene slot when there is no gene, and answers it slot by "
            "slot: the causal unit, the perturbation, the dose, the carrier, the assay, the "
            "intervention and the reason it recurs."
        ),
        "provenance": (
            "Mechanisms and phenocopy pairs are established in their fields and each names the "
            "enzyme, receptor, mark or pathway it turns on, so each is checkable rather than "
            "merely plausible. The count of gene-less diseases is read live from the atlas at "
            "build time, not typed here. Nothing in this file is clinical guidance."
        ),
        "blindSpot": {
            "diseases": total,
            "withGene": with_gene,
            "withoutGene": without,
            "fractionWithoutGene": round(without / total, 4),
            "says": (
                "%s of %s catalogued diseases have no causal gene in the join — %.1f%%. Not all "
                "of them belong to the classes below; many are simply not yet solved. But every "
                "one of them is excluded from the cell axis, from the dependency screen and from "
                "every ranking on this site, because the architecture needs a gene to key on. "
                "That is the cost of the design, stated as a number rather than as a caveat."
                % (format(without, ","), format(total, ","), 100 * without / total)
            ),
        },
        "slots": SLOTS,
        "classes": CLASSES,
        "phenocopies": PHENOCOPIES,
        "failureModes": FAILURE_MODES,
        "summary": {
            "classes": len(CLASSES),
            "slots": len(SLOTS),
            "phenocopies": len(PHENOCOPIES),
            "failureModes": len(FAILURE_MODES),
            "examples": sum(len(c["examples"]) for c in CLASSES),
            "byClassPhenocopies": dict(Counter(p["classId"] for p in PHENOCOPIES)),
        },
    }

    path = DEST / "nongene.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    s = payload["summary"]
    print("wrote %s" % path.relative_to(ROOT))
    print("  %d non-gene causal classes x %d slots · %d phenocopy pairs · %d pipeline failure modes"
          % (s["classes"], s["slots"], s["phenocopies"], s["failureModes"]))
    print("  atlas blind spot, read live: %s of %s diseases have no gene (%.1f%%)"
          % (format(without, ","), format(total, ","), 100 * without / total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
