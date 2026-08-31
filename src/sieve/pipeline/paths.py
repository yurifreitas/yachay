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
# Five kinds of hole, told apart by what would CLOSE each one.
GAP_TAXONOMY = RARE / "gap_taxonomy.json"
# One gene from the residue to the organ system, with the cost of each step where one is known.
GENE_LADDER = RARE / "gene_ladder.json"
# The second Stage 1 domain outside cancer: HIV drug resistance, where the observations are
# tips of a phylogeny rather than independent draws.
AUTISM_CONVERGENCE = RARE / "autism_convergence.json"
HIV_RESISTANCE = OUT / "hiv_resistance.json"
HIV_PI = DATA / "hiv" / "PI_DataSet.txt"
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
# The partition held to a null and an interval, which the partition itself never was.
COMMUNITY_STABILITY = RARE / "community_stability.json"
# What each of those communities is, from a source outside the loop that built the graph.
COMMUNITY_IDENTITY = RARE / "community_identity.json"
# Where the three algorithms disagree, with the communities matched first.
PARTITION_FLOW = RARE / "partition_flow.json"
# The UMAP published as an object under test rather than as a result.
GENE_EMBEDDING = RARE / "gene_embedding.json"
# The prior question the embedding raised: is there anything in the features to cluster.
CLUSTERABILITY = RARE / "clusterability.json"
# Fetched by the browser: half a megabyte of edge list belongs behind a request, not in
# the bundle every other screen loads.
NETWORK_LAYOUT = ROOT / "web" / "public" / "data" / "network_layout.json"
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

# --- artefacts that were produced by hand ------------------------------------------------
# Every path below belongs to a tool that WROTE A BUNDLED ARTEFACT WITHOUT A STAGE. Twenty-six
# of them, on 2026-08-30, including the entire gene surface: the index the navigator reads,
# the facet index that is the only way into 18,140 genes that is not a search box, and the
# shards the browser fetches. They were generated by someone remembering to run the script.
#
# That is not a style complaint. A tool outside the graph has no declared inputs, so nothing
# can tell that its artefact is older than the data underneath it, and `sieve run` reported a
# green pipeline while shipping whatever was last produced by hand.
OBESITY = OUT / "obesity"
OBESITY_THERMOGENESIS = OBESITY / "obesity_thermogenesis.json"
DEVICES = OUT / "devices"
CLEARED_DEVICES = DEVICES / "cleared_devices.json"
PSYCHIATRIC = OUT / "psychiatric"
PSYCHIATRIC_GWAS = PSYCHIATRIC / "psychiatric_gwas.json"
TRAIT_ATLAS = PSYCHIATRIC / "trait_atlas.json"

BIAS = RARE / "bias.json"
BARRIERS = RARE / "barriers.json"
NOMENCLATURE = RARE / "nomenclature.json"
DIMENSIONS = RARE / "dimensions.json"
DIMENSIONS_TWO = RARE / "dimensions_two.json"
GAP_PATTERNS = RARE / "gap_patterns.json"
GENE_CONSTRAINT = RARE / "gene_constraint.json"
SIGNAL_ENERGY = RARE / "signal_energy.json"
SINGLE_CELL_COVERAGE = RARE / "single_cell_coverage.json"
TROPICAL_GAP = RARE / "tropical_gap.json"

# The gene chain. Order here is the order they must run in, and until now that order lived
# only in a sentence at the bottom of each tool's docstring.
GENE_INDEX = OUT / "gene_index.json"
GENE_WORLD = OUT / "gene_world.json"
GENE_DOMAINS = OUT / "gene_domains.json"
GENE_GEOMETRY = OUT / "gene_geometry.json"
GENE_RELATED = OUT / "gene_related.json"
GENE_DATASHEET = OUT / "gene_datasheet.json"
GENE_INSIGHTS = OUT / "gene_insights.json"
GENE_ATTENTION = OUT / "gene_attention.json"

# Fetched by the browser rather than bundled, so these are the files a reader actually waits
# on. `facets.json` is the browse surface; `idx.json` is the shard map.
WEB_GENE = ROOT / "web" / "public" / "data" / "gene"
GENE_FACETS = WEB_GENE / "facets.json"
GENE_SPACE = WEB_GENE / "space.json"
GENE_SHARD_INDEX = WEB_GENE / "idx.json"

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
    for d in (OUT, FIGURES, RARE, OBESITY, DEVICES, PSYCHIATRIC, WEB_GENE,
              PAPER_NUMBERS.parent):
        d.mkdir(parents=True, exist_ok=True)


def rel(p: pathlib.Path) -> str:
    """A path as it should appear in a log line: relative to the repo, forward slashes."""
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p)
