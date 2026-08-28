#!/usr/bin/env python
"""The research thesis this repository is one instrument of — stated, registered, and audited.

WHY THIS FILE EXISTS. Everything else here is a measurement. This is the argument the
measurements were taken in service of, written down so it can be attacked as a whole rather
than inferred from twelve tabs. It is the author's, not mine; my job is to encode it without
smoothing it, to keep its own epistemic register intact, and to check each claim against what
this repository has actually built.

THE THESIS IN ONE LINE. An ultra-rare disease should be modelled as a multiscale dynamical
system rather than as a genetic column, and the computation used to model it should be chosen
by the biological structure of the problem rather than by convention.

THE REGISTER IS THE POINT, AND IT IS THE AUTHOR'S OWN. The source material separates what is
well founded from what is a research hypothesis from what is an architectural metaphor, and
insists that making that separation STRENGTHENS the project rather than weakening it. That
separation is carried here as a first-class field: every claim below is `founded`, `hypothesis`
or `metaphor`, and nothing is quietly promoted.

WHAT IS SUPPLIED AND WHAT IS VERIFIED. Several concrete facts — programme names, funding
figures, biobank sizes, a 2026 review — were supplied by the author. This repository has not
verified any of them, and they are listed separately under `supplied` with that stated. They
are not evidence produced here; they are context the author brought.

COVERAGE IS COMPUTED, NOT CLAIMED. For each rung of the scale ladder and each insight, the
file looks on disk for the artefact that would substantiate it and reports built / partial /
named-only / absent. That is what turns a manifesto into an audit, and it is why several rows
below say the honest thing: named, not built.

    python tools/thesis_seed.py     # writes out/rare/thesis.json
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "out" / "rare"

FOUNDED = "founded"
HYPOTHESIS = "hypothesis"
METAPHOR = "metaphor"


def exists(*rel: str) -> bool:
    return all((ROOT / r).exists() for r in rel)


# --- the two theses, in the author's own formulation ----------------------------------
THESIS_SCIENTIFIC = (
    "Develop an open computational infrastructure that models ultra-rare disorders as "
    "multiscale dynamical systems, integrating genomic, structural, molecular, cellular, "
    "spatial and clinical evidence. The platform should turn individual variants into "
    "mechanistic hypotheses, represent uncertainty explicitly, simulate the propagation of "
    "perturbations, prioritise interventions, and choose the experiments with the highest "
    "expected information gain. NF2-related schwannomatosis is the first model system, chosen "
    "for its relatively defined genetic architecture, the central role of Merlin, and the "
    "existence of experimental models, a biobank and active gene-therapy programmes."
)

THESIS_COMPUTATIONAL = (
    "Investigate whether structural properties of biological data — sparsity, modularity, "
    "topology and multiscale organisation — can be exploited by adaptive runtimes and kernels "
    "to reduce data movement and accelerate network-biology, single-cell and spatial-omics "
    "workloads."
)


# --- the scale ladder: the spine of the whole argument --------------------------------
def rung(id, name, unit, changes, repo, status, gap=None):
    return dict(id=id, name=name, unit=unit, whatChanges=changes,
                repoArtifact=repo, status=status, gap=gap)


SCALES = [
    rung("genotype", "Genotype", "a variant",
         "A base changes. On its own this is a row in a table and explains nothing — which is "
         "the whole complaint the ladder is built against.",
         "out/rare/dossiers.json — causal genes per disease, from HPO gene-to-disease",
         "built" if exists("out/rare/dossiers.json") else "absent"),

    rung("structure", "Protein structure", "a fold",
         "The variant displaces atoms. Merlin is about 595 residues with functionally distinct "
         "and flexible regions, so where in the fold a substitution lands matters more than "
         "that it happened.",
         "AlphaFold/ESMFold, FoldX or Rosetta; RMSD and ddG",
         "named-only",
         "No structural stage exists in this repository. The ladder names it and the pipeline "
         "does not run it — that gap is real and is the honest answer to 'is this built'."),

    rung("dynamics", "Conformational dynamics", "a distribution over states",
         "Structure is not function. What matters is P(conformation | mutation, environment, t) "
         "— whether the mutation moved the energy landscape, not whether one static prediction "
         "looks different. Molecular dynamics hits a sampling wall here: the biologically "
         "important transitions are rare events.",
         "molecular dynamics with enhanced sampling",
         "named-only",
         "The sampling bottleneck is the reason this rung is hard, and it is a compute problem "
         "before it is a biology problem."),

    rung("interaction", "Interactome", "an edge",
         "The altered protein sits in a graph. A perturbation does not stop at the molecule; it "
         "propagates — random walk with restart, heat diffusion, network propagation.",
         "out/rare/lupus_graph.json — a curated network with propagation on it",
         "partial" if exists("out/rare/lupus_graph.json") else "absent",
         "Built for lupus as a demonstration, not for Merlin, and not from BioGRID at scale."),

    rung("pathway", "Pathway", "a signalling axis",
         "Merlin loss disorganises Hippo signalling and raises YAP/TAZ activity, and is "
         "associated with PI3K-AKT, RAC-PAK and EGFR-RAS-ERK. The Hippo axis is the positive "
         "control the NF2 screen in this repository is gated on.",
         "analyses/nf2_subgroup.py — YAP1/WWTR1/TEAD1-4/LATS1/2 as a gated positive control",
         "partial" if exists("analyses/nf2_subgroup.py") else "absent",
         "The stage exists and is STALE: its outputs predate the block-shaped null fix, so its "
         "numbers are not currently trustworthy and it is hidden from the navigation."),

    rung("cell", "Cell state", "a cell",
         "Cells carrying the perturbation occupy different states. The object is X[cell, gene], "
         "and then X[cell, gene, time] or X[cell, gene, treatment] — a tensor, mostly empty.",
         "out/rare/atlas.json — 154 single-cell types from the Human Protein Atlas",
         "partial" if exists("out/rare/atlas.json") else "absent",
         "Expression per cell type, not per cell. The single-cell tensor itself is named and "
         "not ingested."),

    rung("tissue", "Tissue and space", "a neighbourhood",
         "Position matters. A cell beside a vessel, an axon, an immune infiltrate or a hypoxic "
         "zone lives under different conditions, so expression is a function of identity, "
         "genotype, neighbourhood AND position. Spatial neighbours become graph edges, and the "
         "graphs are large and very sparse.",
         "spatial transcriptomics",
         "absent",
         "Nothing spatial is ingested. This is the largest single hole in the ladder."),

    rung("patient", "Patient", "a person over time",
         "The phenotype, its onset, its trajectory, and what has been tried. Represented as a "
         "set of HPO terms plus a timeline rather than as a diagnostic code.",
         "out/rare/dossiers.json — signs with denominators, onset ages, live trial activity",
         "built" if exists("out/rare/dossiers.json") else "absent"),
]


# --- the insights, each with its register and its status in this repository ------------
def insight(n, title, statement, register, status, note):
    return dict(n=n, title=title, statement=statement, register=register,
                status=status, note=note)


INSIGHTS = [
    insight(1, "A disease is a multiscale system, not a genetic column",
            "The interesting unit is not the mutation. It is the perturbation the mutation "
            "propagates through the scales above.",
            FOUNDED, "partial",
            "The dashboard is organised by scale — disease, cause, catalogue — and the non-gene "
            "layer exists precisely because the gene column cannot carry the argument. The "
            "molecular and spatial rungs are missing."),

    insight(2, "Small N does not imply small information",
            "With twenty patients you may still hold millions of measurements each. The "
            "objective becomes maximising information PER PATIENT rather than increasing N.",
            FOUNDED, "built",
            "This is the whole evidence tab: Wilson intervals on a sign seen in 7 of 12 "
            "patients, and the rule of three for what a case series of n can exclude."),

    insight(3, "But more measurements do not manufacture independent patients",
            "Thousands of genes measured in the same person stay correlated. Informational "
            "dimensionality and statistical sample size are different quantities and must be "
            "kept apart.",
            FOUNDED, "built",
            "The correction that keeps insight 2 from becoming a fallacy. It is the same "
            "argument as the selection-operator bias this library was built for: a maximum over "
            "many correlated tests is not a maximum over many independent ones."),

    insight(4, "The unit of transfer is a mechanism, not a patient",
            "You do not need a hundred thousand NF2 patients to learn protein physics, "
            "protein-protein interaction, Hippo signalling or Schwann cell behaviour. That "
            "knowledge transfers from other diseases; the patient count only limits the last "
            "step.",
            FOUNDED, "partial",
            "The phenocopy pairs on the non-gene tab are exactly this: two causes reaching one "
            "endpoint means the mechanism is the transferable object."),

    insight(5, "Genotype to phenotype, through every intermediate",
            "variant → structure → dynamics → interaction → pathway → cell → tissue → "
            "phenotype is a more useful architecture than gene → diagnosis.",
            FOUNDED, "partial",
            "The ladder is stated and half of it is built. Saying which half is the point of "
            "this file."),

    insight(6, "Literature and case reports are data, not bibliography",
            "For an ultra-rare disorder a single case report may carry a patient, a variant, a "
            "phenotype, a treatment and a response. That is a row, and it should be extracted "
            "as one.",
            HYPOTHESIS, "absent",
            "Nothing in this repository extracts structured data from text. Named, not built."),

    insight(7, "Uncertainty belongs inside the model",
            "The system should say P(X | evidence) = 0.72 and name where the confidence came "
            "from — literature, conservation, structure, experiment, cohort, analogy, "
            "simulation. That turns an answer generator into an evidence system.",
            FOUNDED, "built",
            "Every band on this site is a band for this reason: capital as a range, sign "
            "frequency as a Wilson interval, an HPO class drawn as the span it actually is, and "
            "a confidence field on every authored judgement."),

    insight(8, "The point of the model is to choose the next experiment",
            "Not to predict the cure. To compress ten thousand hypotheses to twenty "
            "experiments and then to two — because in rare disease the laboratory is expensive "
            "and the sample is scarce.",
            FOUNDED, "partial",
            "The approach chooser and the gated stages in the capability layer are a manual "
            "version of this. There is no expected-information-gain criterion anywhere."),

    insight(9, "Active learning is the formal version of insight 8",
            "Choose the experiment that maximises expected information gain: e* = argmax IG(e).",
            HYPOTHESIS, "absent",
            "Named, not built. It is the obvious next formalism and nothing here implements it."),

    insight(10, "Rare disease produces structurally different computation",
            "High dimensionality, extreme sparsity, irregular distribution, modular graphs, "
            "heterogeneous degree, few patients and many variables. This is not the workload "
            "dense BLAS was designed for.",
            FOUNDED, "named-only",
            "True and unexploited here: this repository does dense, small-scale numerics."),

    insight(11, "The bottleneck is memory, not FLOPS",
            "For these workloads total time is closer to time spent moving data than to time "
            "spent computing. Irregular access and data movement dominate.",
            FOUNDED, "named-only",
            "Well established in the HPC literature. This repository has no kernel work in it."),

    insight(12, "Biological topology could steer computation",
            "Communities, hubs, modularity and recurrent blocks are structure that generic "
            "sparse libraries do not use. Ordering, layout, tiling, format and kernel could be "
            "selected FROM the topology.",
            HYPOTHESIS, "named-only",
            "This is a research hypothesis and must stay one. It is not established that "
            "community-aware reordering beats a tuned general library, and the honest form is "
            "'specialised for a structural class', not 'faster than cuSPARSE'."),

    insight(13, "A domain-aware sparse compiler, not a new BLAS",
            "The defensible name for the idea is domain-aware adaptive sparse computation — a "
            "layer where domain properties influence lowering, layout and kernel selection, "
            "plausibly on MLIR. Calling it a new BLAS overstates it.",
            HYPOTHESIS, "named-only",
            "The author's own correction, kept: the earlier vocabulary was ambiguous and the "
            "narrower claim is the stronger one."),

    insight(14, "A digital twin must be probabilistic and evolutionary",
            "Not a deterministic replica. Twin(t + dt) = Update(Twin(t), new observations), "
            "carrying P(state | evidence) and revising it as evidence arrives.",
            HYPOTHESIS, "absent",
            "Named, not built, and the version worth building is the modest one: an evidence "
            "state that updates, not a simulator that pretends to certainty."),

    insight(15, "Animal models should follow the prioritisation, not precede it",
            "Do variant analysis, structure, network biology, single-cell, spatial and "
            "knowledge-graph work first; then ask which mechanism justifies a new line. The "
            "animal becomes a consequence of evidence rather than a starting point.",
            FOUNDED, "named-only",
            "A methodological commitment rather than an artefact. Nothing here contradicts it "
            "and nothing here implements it."),

    insight(16, "Causality, not correlation",
            "The useful question is do(A) → B, not A ↔ B. Perturbation screens are interesting "
            "precisely because they are closer to interventions than to observations.",
            FOUNDED, "built",
            "The DepMap CRISPR adapter is exactly this: a perturbation screen, and the null "
            "calibration exists so that a maximum over perturbations is not mistaken for an "
            "effect."),

    insight(17, "Open science is structural here, not ethical decoration",
            "Splitting already-scarce data destroys discovery power. Open means code, "
            "protocols, models, benchmarks, cell lines, plasmids, documentation and derived "
            "datasets — not just a repository.",
            FOUNDED, "partial",
            "This repository is open and its licence constraints are declared per source; "
            "Orphanet is CC BY-ND, so derived material stays local and is described rather "
            "than shipped."),

    insight(18, "One sample should yield many measurements",
            "sample → genomics + transcriptomics + proteomics + imaging + clinical phenotype, "
            "all linked by identity and provenance. In ultra-rare disease a biobank is not "
            "storage, it is the substrate.",
            FOUNDED, "named-only",
            "A wet-lab commitment this repository cannot implement, only respect."),
]


# --- the register the author drew, kept exactly ----------------------------------------
REGISTER = {
    "founded": [
        "NF2/Merlin and Hippo-YAP/TAZ",
        "Heterogeneity across schwannoma, meningioma and ependymoma",
        "NF2 gene therapy via AAV in development",
        "The importance of murine models and biobanks",
        "Single-cell and spatial transcriptomics",
        "Network biology and network propagation",
        "Sparse linear algebra as a distinct workload",
        "Molecular dynamics and its sampling bottleneck",
        "Protein structure prediction",
        "Knowledge graphs",
        "Causal perturbation",
        "Active learning",
        "N-of-1 therapeutics",
    ],
    "hypothesis": [
        "That community-aware reordering will beat a tuned general sparse library",
        "That biological topology can be learned into kernel selection",
        "That a domain-aware sparse compiler yields a real speed-up on these workloads",
        "That literature extraction can carry enough signal for an ultra-rare cohort",
        "That expected-information-gain experiment selection outperforms expert choice here",
    ],
    "metaphor": [
        "'Living network' — the defensible form is G(t), a graph whose nodes and edges change "
        "with time, expression, treatment and cell state",
        "'Informational propagation' — the defensible form names the scale: molecular "
        "diffusion, pathway transduction, expression change, network propagation, cell-cell "
        "communication",
        "Turing morphogenesis — the connection is that global pattern can emerge from simple "
        "local rules, NOT that NF2 is a reaction-diffusion system",
        "'Fractal inference' as a mechanism of NF2",
        "'HCP' and 'high complexity processing' as biomedical or computational terms — not "
        "recognised in the literature, and the author retired them",
        "Simulating a whole individual, or predicting a tumour's full evolution from one "
        "mutation",
    ],
}


# --- facts the author supplied that this repository has not verified -------------------
SUPPLIED = [
    dict(claim="NF2 sits at 22q12.2 and encodes the tumour suppressor Merlin; the classic "
               "phenotype is bilateral vestibular schwannomas, with other schwannomas, "
               "meningiomas and ependymomas.",
         status="textbook, and consistent with the ORPHA and OMIM identifiers in the dossier"),
    dict(claim="Merlin is approximately 595 amino acids, with functionally distinct and "
               "flexible regions, FERM-membrane interaction and an auto-inhibited state.",
         status="textbook; not measured in this repository"),
    dict(claim="A 2026 review reports that NF2/Merlin loss disorganises Hippo signalling and "
               "raises YAP/TAZ activity, and points to emerging mechanisms involving "
               "biomolecular condensates, phosphoinositides and ferroptosis.",
         status="SUPPLIED BY THE AUTHOR AND NOT VERIFIED HERE. No citation was resolved and no "
                "file in this repository checks it."),
    dict(claim="Cure NF2 funds an AAV NF2 gene-addition programme at Nationwide Children's "
               "Hospital, at preclinical stage, with pre-IND regulatory feedback.",
         status="SUPPLIED BY THE AUTHOR AND NOT VERIFIED HERE."),
    dict(claim="A suicide-gene programme using AAV to deliver ASC into schwannoma cells, "
               "identified as MRL-102, with a $3M SBIR Phase II award from NINDS.",
         status="SUPPLIED BY THE AUTHOR AND NOT VERIFIED HERE."),
    dict(claim="An open-access biobank hosted at MGH holding 234 samples.",
         status="SUPPLIED BY THE AUTHOR AND NOT VERIFIED HERE. If accurate it is the sharpest "
                "illustration of insight 18: in a common disease losing fifty samples is "
                "statistically irrelevant; here it can be years of accumulated disease."),
]


# --- the architecture, as layers rather than as ASCII ----------------------------------
ARCHITECTURE = [
    dict(layer="Evidence", holds="papers, databases, biobank, assays",
         note="Where literature stops being bibliography and becomes rows."),
    dict(layer="Patient", holds="phenotype, timeline, imaging, treatment",
         note="HPO terms plus a trajectory, not a diagnostic code."),
    dict(layer="Knowledge graph", holds="gene, disease, phenotype, pathway, drug, publication",
         note="The join that makes scarce data reusable across diseases."),
    dict(layer="Molecular", holds="variants, structure, dynamics",
         note="Where a variant becomes a mechanism instead of a classification."),
    dict(layer="Network", holds="interactome, pathway propagation",
         note="A = A(t, cell, state): the graph is not static."),
    dict(layer="Spatial", holds="tissue, microenvironment, mechanics",
         note="Cells read mechanical force through the cytoskeleton into Hippo — the same axis "
              "Merlin regulates, which is where the mechanics and the genetics meet."),
    dict(layer="Digital twin", holds="P(state | evidence), updated",
         note="Probabilistic and longitudinal, or it is an avatar."),
    dict(layer="Intervention", holds="ASO, AAV, small molecule, CRISPR correction",
         note="Simulated as prioritisation, never as clinical certainty."),
    dict(layer="Experiment", holds="cell model, organoid, humanised model, mouse, clinic",
         note="The loop closes here and feeds the evidence layer again."),
]

LOOP = ["data", "model", "hypotheses", "prioritisation", "experiment", "result",
        "model update"]


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)

    reg = Counter(i["register"] for i in INSIGHTS)
    st = Counter(i["status"] for i in INSIGHTS)
    scale_st = Counter(s["status"] for s in SCALES)

    payload = {
        "generated": "tools/thesis_seed.py",
        "premise": (
            "Every other tab here is a measurement. This one is the argument the measurements "
            "serve, written down so it can be attacked whole — with its own register intact, "
            "and audited against what this repository has actually built."
        ),
        "provenance": (
            "The thesis is the author's. It is encoded rather than paraphrased, and its own "
            "separation of founded claim from research hypothesis from architectural metaphor "
            "is carried as a field on every row. Coverage is not claimed: for each rung and "
            "each insight the file looks on disk for the artefact that would substantiate it "
            "and reports built, partial, named-only or absent. Several rows say 'named, not "
            "built', which is the honest answer and the reason the audit is worth running. "
            "Facts the author supplied and this repository has not verified are listed "
            "separately and marked as such."
        ),
        "thesisScientific": THESIS_SCIENTIFIC,
        "thesisComputational": THESIS_COMPUTATIONAL,
        "oneLine": (
            "Genotype → molecule → network → cell → tissue → patient, with the computation "
            "chosen by the biological structure of the problem."
        ),
        "deepest": (
            "Conventional medicine looks for Disease → Treatment. This looks for Disease → "
            "Mechanisms → Perturbations → Simulation → Experiments → Treatment, and the "
            "intermediate layer is where computation can generate the most value."
        ),
        "scales": SCALES,
        "insights": INSIGHTS,
        "register": REGISTER,
        "supplied": SUPPLIED,
        "architecture": ARCHITECTURE,
        "loop": LOOP,
        "summary": {
            "scales": len(SCALES),
            "scalesByStatus": dict(scale_st),
            "insights": len(INSIGHTS),
            "insightsByRegister": dict(reg),
            "insightsByStatus": dict(st),
            "foundedClaims": len(REGISTER["founded"]),
            "openHypotheses": len(REGISTER["hypothesis"]),
            "metaphorsRetired": len(REGISTER["metaphor"]),
            "suppliedUnverified": sum(1 for s in SUPPLIED if "NOT VERIFIED" in s["status"]),
        },
    }

    path = DEST / "thesis.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    s = payload["summary"]
    print("wrote %s" % path.relative_to(ROOT))
    print("  %d scale rungs: %s" % (s["scales"], s["scalesByStatus"]))
    print("  %d insights by register: %s" % (s["insights"], s["insightsByRegister"]))
    print("  %d insights by build status: %s" % (s["insights"], s["insightsByStatus"]))
    print("  %d founded claims · %d open hypotheses · %d metaphors kept as metaphors"
          % (s["foundedClaims"], s["openHypotheses"], s["metaphorsRetired"]))
    print("  %d supplied facts this repository has NOT verified" % s["suppliedUnverified"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
