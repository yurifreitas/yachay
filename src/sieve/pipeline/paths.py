"""Every path in the project, in one place.

Before this module each script rebuilt `ROOT` from its own `__file__` and joined its own
strings, which meant a directory could be renamed in five files and missed in a sixth. A
path constant repeated is a path constant that will disagree with itself.

Nothing here touches the filesystem on import — a module that creates directories as a
side effect of being imported is a module you cannot import to ask a question.
"""

from __future__ import annotations

import os
import pathlib

# src/sieve/pipeline/paths.py -> the repository root is four levels up.
ROOT = pathlib.Path(__file__).resolve().parents[3]

# --- inputs ---------------------------------------------------------------------------
DATA = ROOT / "data"
DEPMAP = pathlib.Path(os.environ.get("SIEVE_DATA", DATA / "depmap"))

CRISPR_GENE_EFFECT = DEPMAP / "CRISPRGeneEffect.csv"
NONESSENTIAL = DEPMAP / "AchillesNonessentialControls.csv"
COMMON_ESSENTIAL = DEPMAP / "AchillesCommonEssentialControls.csv"
MODEL = DEPMAP / "Model.csv"
DAMAGING = DEPMAP / "OmicsSomaticMutationsMatrixDamaging.csv"
CN_GENE = DEPMAP / "OmicsCNGene.csv"

# --- outputs --------------------------------------------------------------------------
OUT = ROOT / "out"
FIGURES = OUT / "figures"
RARE = OUT / "rare"

DEPMAP_MANIFEST = OUT / "depmap.manifest.json"
DEPMAP_GENES = OUT / "depmap_genes.csv"
DEPMAP_NULL = OUT / "depmap_null.csv"
#: Selective dependency by cancer subgroup, one file per nesting level.
CANCER_SUBGROUPS = tuple(OUT / f"cancer_subgroups_{lv}.json"
                         for lv in ("lineage", "disease", "subtype"))
#: Genotype-defined subgroups, with the lineage and mutational-burden confounds measured.
CANCER_GENOTYPE = OUT / "cancer_genotype.json"
MUTATIONS_DAMAGING = DEPMAP / "OmicsSomaticMutationsMatrixDamaging.csv"
DEPMAP_FINDINGS = OUT / "DEPMAP_FINDINGS.md"

NF2_MANIFEST = OUT / "nf2.manifest.json"
NF2_GENES = OUT / "nf2_genes.csv"
NF2_FINDINGS = OUT / "NF2_FINDINGS.md"

FIGURES_DEPMAP = FIGURES / "depmap.json"
LEXICON = RARE / "lexicon.json"
LUPUS = RARE / "lupus.json"

# The capability layer: what an approach physically takes. CAPABILITY is authored
# estimate; CAPABILITY_MATH is derived from it and from the dossiers, and must be
# rebuilt whenever either input moves — which is the whole reason it is a stage.
CAPABILITY = RARE / "capability.json"
CAPABILITY_MATH = RARE / "capability_math.json"
NONGENE = RARE / "nongene.json"
# Measured against the downloaded annotations, so it depends on the ontology files
# themselves rather than on any of our own outputs.
NONGENE_MEASURED = RARE / "nongene_measured.json"
PREVALENCE_AUDIT = RARE / "prevalence_audit.json"
# The evidence profile of the WHOLE catalogue, not the twelve-disease dossier: how much
# of the rare-disease phenotype is actually measured. Depends on the annotations and on
# the grading rules in tools/dossier.py, which it imports rather than restates.
EVIDENCE_ATLAS = RARE / "evidence_atlas.json"
# Frequencies computed from INDIVIDUAL PATIENTS rather than read from a catalogue. The
# only patient-level layer in the project.
PATIENT_FREQUENCIES = RARE / "patient_frequencies.json"
# The genotype half of the same patients: variants, zygosity, consequence, ACMG.
PATIENT_VARIANTS = RARE / "patient_variants.json"
# The join of the two halves, which is the only thing an aggregate catalogue cannot do.
GENOTYPE_PHENOTYPE = RARE / "genotype_phenotype.json"
# ClinVar at full scale, and the cross-check of the patient corpus against it.
CLINVAR_EVIDENCE = RARE / "clinvar_evidence.json"
# An interval on every headline number. A6, open since the first sweep.
INTERVALS = RARE / "intervals.json"
# The first DYNAMICAL component: where a disease's perturbation spreads on a real
# interactome, against a degree-matched null. The Interactome rung of the thesis ladder.
TWIN_PROPAGATION = RARE / "twin_propagation.json"
# The first CROSS-SCALE measurement: how much of what a disease's genes say about its
# organ systems survives a coarse-graining onto pathways or cell types. ADR 0007.
SCALE_INFORMATION = RARE / "scale_information.json"
# What a reader loses by not reading English: HPO's thirteen language profiles against the
# annotations diseases actually carry. Language as a subgroup axis, beside ancestry.
LANGUAGE_COVERAGE = RARE / "language_coverage.json"
# Whether a recorded scientific conflict is a contradiction or two statements about
# different conditions. The empirical question the sheaf formalism has to answer first.
EVIDENCE_CONFLICT = RARE / "evidence_conflict.json"
# The decomposition the association could not do: contradiction against context.
CONFLICT_DECOMPOSITION = RARE / "conflict_decomposition.json"
# The shape of what is known, per disease, across five axes. A negative result: the
# prediction fails and the vector largely measures which registry a disease lives in.
KNOWLEDGE_SHAPE = RARE / "knowledge_shape.json"
# Attention against burden: is what the field studies explained by who the disease reaches?
ATTENTION_BURDEN = RARE / "attention_burden.json"
# Solved layouts for the hyperdimensional views. No measurement of its own: a seriation is
# an argument, and one computed inside a component is an argument nobody can audit.
KNOWLEDGE_VOID = RARE / "knowledge_void.json"
VIEW_MODELS = RARE / "view_models.json"
GENE2PUBMED = DATA / "ontology" / "gene2pubmed.gz"
CLINVAR_SUBMISSIONS = DATA / "ontology" / "submission_summary.txt.gz"
HPO_TRANSLATIONS = DATA / "ontology" / "hpo-translations.tar.gz"
STRING_INFO = DATA / "ontology" / "9606.protein.info.v12.0.txt.gz"
STRING_ALIASES = DATA / "ontology" / "9606.protein.aliases.v12.0.txt.gz"
REACTOME_PATHWAYS = DATA / "ontology" / "UniProt2Reactome_All_Levels.txt"
REACTOME_HIERARCHY = DATA / "ontology" / "ReactomePathwaysRelation.txt"
HPA_SINGLE_CELL = DATA / "ontology" / "rna_single_cell_type.tsv.zip"
CLINVAR = DATA / "ontology" / "variant_summary.txt.gz"
PHENOPACKETS = DATA / "ontology" / "all_phenopackets.zip"
# The audit of an AUTHORED layer against the ingested catalogues. Depends on the layer it
# checks, so editing the seed makes the check stale - which is the point of it being a
# stage rather than a script somebody remembers to run.
LEXICON_CHECK = RARE / "lexicon_check.json"
# The cross-layer audit: where twenty artefacts make the same claim, do they agree? It
# depends on almost everything, which is the point - it is the only stage whose job is
# the SYSTEM rather than any one layer.
CONSISTENCY = RARE / "consistency.json"
# The population axis: reads the same Orphanet file as the prevalence audit, but the
# geography field rather than the class field. Separate stage because it answers a
# different question and must be able to go stale on its own.
ANCESTRY_GEOGRAPHY = RARE / "ancestry_geography.json"
# The thesis reads the repository itself for coverage, so it has no data input
# and is marked always-stale rather than pretending to a dependency.
THESIS = RARE / "thesis.json"
REFERENCES = RARE / "references.json"
INTERACTOME_SPARSE = OUT / "interactome_sparse.json"
# The independent graph that tests the one above. Named by confidence threshold because
# the robustness check is part of the result, not a variant of it.
INTERACTOME_STRING = OUT / "interactome_string_700.json"
GENE_NETWORK = RARE / "gene_network.json"
# The pipeline reporting on itself, so it can never be cached: any other stage
# running changes the answer.
PIPELINE_STATE = OUT / "pipeline.json"
MULTIPLICITY = OUT / "multiplicity.json"
TAIL_CALIBRATION = OUT / "tail_calibration.json"
# The tooling survey imports and greps at run time, so it is never cacheable.
ECOSYSTEM = OUT / "ecosystem.json"
ORPHA_PREVALENCE = DATA / "ontology" / "en_product9_prev.xml"
ORPHA_AGES = DATA / "ontology" / "en_product9_ages.xml"
HPOA = DATA / "ontology" / "phenotype.hpoa"
HP_OBO = DATA / "ontology" / "hp.obo"
GENES_TO_DISEASE = DATA / "ontology" / "genes_to_disease.txt"
STRING_LINKS = DATA / "ontology" / "9606.protein.links.v12.0.txt.gz"
MONDO = DATA / "ontology" / "mondo.obo"
ATLAS = RARE / "atlas.json"
DOSSIERS = RARE / "dossiers.json"
LUPUS_GRAPH = RARE / "lupus_graph.json"

PAPER_NUMBERS = ROOT / "paper" / "generated" / "numbers.tex"
REFS_BIB = ROOT / "paper" / "refs.bib"

# --- code, for staleness ---------------------------------------------------------------
# A stage is stale when its inputs change OR when the code that produces it changes. The
# second half is what most hand-rolled pipelines forget, and it is the one that bites:
# you fix an analysis, re-run, and get the old artifact back because the CSV did not move.
SRC = ROOT / "src" / "sieve"
ANALYSES = ROOT / "analyses"
TOOLS = ROOT / "tools"


def ensure_dirs() -> None:
    """Create the output directories. Called by the runner, never on import."""
    for d in (OUT, FIGURES, RARE, PAPER_NUMBERS.parent):
        d.mkdir(parents=True, exist_ok=True)


def rel(p: pathlib.Path) -> str:
    """A path as it should appear in a log line: relative to the repo, forward slashes."""
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)
