"""The pipeline, declared.

This file is the only place that knows what the project's stages are, what each reads and
writes, and in what order they can run. Adding a stage is adding an entry here; nothing
else needs to change.

WHY SUBPROCESS AND NOT IMPORT. The analyses under `analyses/` are scripts: they do their
work at module level, so importing one runs it. Wrapping them in `main()` functions and
importing would be cleaner, and it is the obvious next step — but it is a change to
working analysis code, and doing it in the same move as introducing the runner would mean
two things changing at once with no way to tell which broke. So the first version keeps
the scripts exactly as they are and adds only the graph around them. The declared
inputs/outputs are already correct, so the migration can happen one script at a time
without touching this file's shape.

WHAT THIS FIXES, concretely, over the previous task list:

  * `tasks.py figures` used to be runnable before `depmap` had ever written a manifest,
    producing an empty or stale artifact with no complaint. Now `figures` declares
    `needs=("depmap",)` and the runner orders them.
  * Re-running everything meant re-reading a 429 MB matrix three times even when nothing
    had changed. Now a fresh stage is skipped, with a line saying why.
  * Editing an analysis and re-running silently served the old artifact, because only the
    input data was checked. Now the analysis source is a declared dependency.
"""

from __future__ import annotations

import os
import subprocess
import sys

from . import paths
from .sources import BY_KEY
from .stage import Stage, sources

PY = sys.executable


def _run(*args: str) -> None:
    """Run a project script with `src` importable, failing loudly."""
    env = {**os.environ, "PYTHONPATH": str(paths.ROOT / "src")}
    r = subprocess.run([PY, *args], cwd=paths.ROOT, env=env)
    if r.returncode:
        raise SystemExit(r.returncode)


def _script(rel: str) -> "callable":
    return lambda: _run(str(paths.ROOT / rel))


def src(*keys: str) -> tuple:
    """The download destinations of named raw sources, as stage inputs.

    `sources.py` already knows where every raw file lands; before this, a stage that read the
    GWAS catalogue had to repeat the path, and a stage that could not be bothered declared no
    inputs at all and was therefore never stale.
    """
    return tuple(BY_KEY[k].dest for k in keys)


# --- the graph --------------------------------------------------------------------------
# Order in this dict is the order `list` prints; execution order comes from `needs`.
STAGES: dict[str, Stage] = {}


def _add(s: Stage) -> None:
    STAGES[s.name] = s


_add(Stage(
    name="depmap",
    summary="Score every gene for selective dependency and calibrate against the null.",
    inputs=(paths.CRISPR_GENE_EFFECT, paths.NONESSENTIAL, paths.COMMON_ESSENTIAL),
    outputs=(paths.DEPMAP_MANIFEST, paths.DEPMAP_GENES, paths.DEPMAP_NULL, paths.DEPMAP_FINDINGS),
    code=sources("analyses/depmap_selective_dependency.py", "src/sieve/stages/*.py",
                 "src/sieve/adapters/depmap/*.py"),
    run=_script("analyses/depmap_selective_dependency.py"),
))

_add(Stage(
    name="nf2",
    summary="Contrast NF2-null against wildtype lines, gated on a positive control.",
    inputs=(paths.CRISPR_GENE_EFFECT, paths.NONESSENTIAL, paths.MODEL, paths.DAMAGING),
    outputs=(paths.NF2_MANIFEST, paths.NF2_GENES, paths.NF2_FINDINGS),
    code=sources("analyses/nf2_subgroup.py", "src/sieve/stages/*.py",
                 "src/sieve/adapters/depmap/*.py"),
    run=_script("analyses/nf2_subgroup.py"),
))

_add(Stage(
    name="figures",
    summary="Reduce the analyses to the tidy series the explorer and the paper both read.",
    inputs=(paths.CRISPR_GENE_EFFECT, paths.NONESSENTIAL, paths.COMMON_ESSENTIAL),
    outputs=(paths.FIGURES_DEPMAP,),
    needs=("depmap",),
    code=sources("tools/figure_data.py", "src/sieve/stages/*.py"),
    run=_script("tools/figure_data.py"),
))

_add(Stage(
    name="rare",
    summary="Seed the rare-disease crosswalk, the lupus matrix, and the lupus network.",
    outputs=(paths.LEXICON, paths.LUPUS, paths.LUPUS_GRAPH),
    code=sources("tools/rare_disease_seed.py", "tools/lupus_seed.py", "tools/lupus_graph.py"),
    run=lambda: _seed(),
))

_add(Stage(
    name="capability",
    summary="Seed the instrument, cost and approach-plan layer.",
    outputs=(paths.CAPABILITY,),
    code=sources("tools/capability_seed.py"),
    run=lambda: _run_tool("capability_seed"),
))

_add(Stage(
    name="capability_math",
    summary="Derive capital per patient, the shared-facility double count, and the queue.",
    inputs=(paths.CAPABILITY, paths.DOSSIERS, paths.PREVALENCE_AUDIT),
    outputs=(paths.CAPABILITY_MATH,),
    needs=("capability", "prevalence_audit"),
    code=sources("tools/capability_math.py"),
    run=lambda: _run_tool("capability_math"),
))

_add(Stage(
    name="nongene",
    summary="Seed the non-gene causal classes; reads the gene-less count live from the atlas.",
    inputs=(paths.ATLAS,),
    outputs=(paths.NONGENE,),
    code=sources("tools/nongene_seed.py"),
    run=lambda: _run_tool("nongene_seed"),
))

_add(Stage(
    name="nongene_measured",
    summary="Check the authored non-gene classes against the HPO inheritance annotations.",
    inputs=(paths.HPOA, paths.HP_OBO, paths.GENES_TO_DISEASE),
    outputs=(paths.NONGENE_MEASURED,),
    code=sources("tools/nongene_measure.py"),
    run=lambda: _run_tool("nongene_measure"),
))

_add(Stage(
    name="prevalence_audit",
    summary="Read every Orphanet prevalence record, so the cohort is one quantity and not four.",
    inputs=(paths.ORPHA_PREVALENCE,),
    outputs=(paths.PREVALENCE_AUDIT,),
    code=sources("tools/prevalence_audit.py"),
    run=lambda: _run_tool("prevalence_audit"),
))

_add(Stage(
    name="interactome_string",
    summary="Test our modularity result against an independent graph built from other evidence.",
    inputs=(paths.STRING_LINKS, paths.INTERACTOME_SPARSE),
    outputs=(paths.INTERACTOME_STRING,),
    needs=("interactome",),
    code=sources("tools/interactome_string.py"),
    run=lambda: _run_tool("interactome_string"),
))

_add(Stage(
    name="consistency",
    summary="Confront the layers with each other: where they claim the same thing, do they agree?",
    inputs=(paths.LEXICON, paths.DOSSIERS, paths.CAPABILITY, paths.CAPABILITY_MATH),
    outputs=(paths.CONSISTENCY,),
    # `dossiers.json` is an INPUT here and to capability_math, and is produced by no stage:
    # tools/dossier.py queries ClinicalTrials.gov, and the build graph deliberately excludes
    # anything that reaches the network (the same rule that keeps `fetch` out). So it is
    # depended on as a file, not as a stage - and if it is missing the stage fails with a
    # message rather than silently making a live API call mid-build.
    needs=("rare", "capability_math"),
    code=sources("tools/consistency.py"),
    run=lambda: _run_tool("consistency"),
))

_add(Stage(
    name="lexicon_check",
    summary="Resolve every identifier in the authored lexicon against the real catalogues.",
    inputs=(paths.LEXICON, paths.ORPHA_PREVALENCE, paths.HPOA, paths.GENES_TO_DISEASE),
    outputs=(paths.LEXICON_CHECK,),
    needs=("rare",),
    code=sources("tools/lexicon_check.py"),
    run=lambda: _run_tool("lexicon_check"),
))

_add(Stage(
    name="twin_propagation",
    summary="Propagate a disease's perturbation over STRING against a degree-matched null.",
    inputs=(paths.STRING_LINKS, paths.STRING_INFO, paths.DOSSIERS, paths.GENES_TO_DISEASE),
    outputs=(paths.TWIN_PROPAGATION,),
    code=sources("tools/twin_propagation.py"),
    run=lambda: _run_tool("twin_propagation"),
))

_add(Stage(
    name="intervals",
    summary="Put a 95% interval on every headline number, including the ones that may not survive.",
    inputs=(paths.EVIDENCE_ATLAS, paths.ANCESTRY_GEOGRAPHY, paths.CLINVAR_EVIDENCE,
            paths.PATIENT_FREQUENCIES, paths.GENOTYPE_PHENOTYPE),
    outputs=(paths.INTERVALS,),
    needs=("evidence_atlas", "ancestry_geography", "clinvar_evidence", "patient_frequencies",
           "genotype_phenotype"),
    code=sources("tools/intervals.py"),
    run=lambda: _run_tool("intervals"),
))

_add(Stage(
    name="clinvar_evidence",
    summary="Read all of ClinVar: the VUS share, its own evidence grade, and our corpus in it.",
    inputs=(paths.CLINVAR, paths.PHENOPACKETS),
    outputs=(paths.CLINVAR_EVIDENCE,),
    code=sources("tools/clinvar_evidence.py"),
    run=lambda: _run_tool("clinvar_evidence"),
))

_add(Stage(
    name="genotype_phenotype",
    summary="Join genotype to phenotype in the same patient, gated on Stage 2 power.",
    inputs=(paths.PHENOPACKETS,),
    outputs=(paths.GENOTYPE_PHENOTYPE,),
    needs=("patient_variants",),
    code=sources("tools/genotype_phenotype.py", "tools/patient_variants.py"),
    run=lambda: _run_tool("genotype_phenotype"),
))

_add(Stage(
    name="patient_variants",
    summary="Extract the genotype the phenotype pass discarded: alleles, zygosity, consequence.",
    inputs=(paths.PHENOPACKETS, paths.HPOA),
    outputs=(paths.PATIENT_VARIANTS,),
    code=sources("tools/patient_variants.py"),
    run=lambda: _run_tool("patient_variants"),
))

_add(Stage(
    name="patient_frequencies",
    summary="Compute phenotype frequencies from individual patients and test the catalogue's.",
    inputs=(paths.PHENOPACKETS, paths.HPOA),
    outputs=(paths.PATIENT_FREQUENCIES,),
    code=sources("tools/patient_frequencies.py"),
    run=lambda: _run_tool("patient_frequencies"),
))

_add(Stage(
    name="cancer_subgroups",
    summary=("Selective dependency per cancer subgroup, at three nesting levels — the "
             "question DepMap was never asked here, because it had only ever been scored "
             "as one pool."),
    inputs=(paths.CRISPR_GENE_EFFECT, paths.MODEL, paths.COMMON_ESSENTIAL),
    outputs=paths.CANCER_SUBGROUPS,
    code=sources("tools/cancer_subgroups.py", "src/sieve/stages/power.py",
                 "src/sieve/adapters/depmap/__init__.py"),
    run=lambda: [_run_tool("cancer_subgroups", "--level", lv)
                 for lv in ("lineage", "disease", "subtype")],
))

_add(Stage(
    name="cancer_genotype",
    summary=("Subgroup lines by GENOTYPE rather than by catalogue label, with the lineage "
             "and mutational-burden confounds measured instead of disclaimed."),
    inputs=(paths.CRISPR_GENE_EFFECT, paths.MODEL, paths.COMMON_ESSENTIAL,
            paths.MUTATIONS_DAMAGING),
    outputs=(paths.CANCER_GENOTYPE,),
    code=sources("tools/cancer_genotype.py", "src/sieve/stages/power.py",
                 "src/sieve/adapters/depmap/__init__.py"),
    run=lambda: _run_tool("cancer_genotype"),
))

_add(Stage(
    name="evidence_atlas",
    summary="Grade every phenotype annotation in the catalogue: how much is actually measured.",
    inputs=(paths.HPOA, paths.HP_OBO),
    outputs=(paths.EVIDENCE_ATLAS,),
    code=sources("tools/evidence_atlas.py", "tools/dossier.py"),
    run=lambda: _run_tool("evidence_atlas"),
))

_add(Stage(
    name="ancestry_geography",
    summary="Read the geography field: whose populations these prevalences are about.",
    inputs=(paths.ORPHA_PREVALENCE,),
    outputs=(paths.ANCESTRY_GEOGRAPHY,),
    code=sources("tools/ancestry_geography.py"),
    run=lambda: _run_tool("ancestry_geography"),
))

_add(Stage(
    name="interactome",
    summary="Build the real gene-gene graph, measure its sparse structure against a null, ship it.",
    inputs=(paths.GENES_TO_DISEASE,),
    outputs=(paths.INTERACTOME_SPARSE, paths.GENE_NETWORK),
    code=sources("tools/interactome_sparse.py"),
    run=lambda: _run_tool("interactome_sparse"),
))

_add(Stage(
    name="scale_information",
    summary=("Measure what a change of scale costs: information about organ systems kept "
             "when genes are coarse-grained onto pathways and onto cell types."),
    inputs=(paths.GENES_TO_DISEASE, paths.HPOA, paths.HP_OBO, paths.REACTOME_PATHWAYS,
            paths.REACTOME_HIERARCHY, paths.HPA_SINGLE_CELL, paths.STRING_ALIASES,
            paths.STRING_INFO),
    outputs=(paths.SCALE_INFORMATION,),
    code=sources("tools/scale_information.py"),
    run=lambda: _run_tool("scale_information"),
))

_add(Stage(
    name="language_coverage",
    summary=("What a reader loses by not reading English: term coverage against "
             "annotation-weighted coverage, per language and per organ system."),
    inputs=(paths.HPO_TRANSLATIONS, paths.HPOA, paths.HP_OBO),
    outputs=(paths.LANGUAGE_COVERAGE,),
    code=sources("tools/language_coverage.py"),
    run=lambda: _run_tool("language_coverage"),
))

_add(Stage(
    name="evidence_conflict",
    summary=("Whether recorded disagreement travels with carrying more conditions - "
             "the sheaf question, asked of ClinVar and stratified by review depth."),
    inputs=(paths.CLINVAR,),
    outputs=(paths.EVIDENCE_CONFLICT,),
    code=sources("tools/evidence_conflict.py"),
    run=lambda: _run_tool("evidence_conflict"),
))

_add(Stage(
    name="conflict_decomposition",
    summary=("Split recorded disagreement into contradiction and context, using each "
             "submitter's classification beside the condition it was made against."),
    inputs=(paths.CLINVAR_SUBMISSIONS,),
    outputs=(paths.CONFLICT_DECOMPOSITION,),
    code=sources("tools/conflict_decomposition.py"),
    run=lambda: _run_tool("conflict_decomposition"),
))

_add(Stage(
    name="knowledge_shape",
    summary=("The shape of what is known per disease across five axes - and the measured "
             "finding that the shape is mostly a registry boundary."),
    inputs=(paths.GENES_TO_DISEASE, paths.HPOA, paths.HPA_SINGLE_CELL, paths.CLINVAR,
            paths.ORPHA_PREVALENCE, paths.ORPHA_AGES),
    outputs=(paths.KNOWLEDGE_SHAPE,),
    code=sources("tools/knowledge_shape.py"),
    run=lambda: _run_tool("knowledge_shape"),
))

_add(Stage(
    name="attention_burden",
    summary=("Research attention against disease burden, with the gene-popularity confound "
             "measured in a second arm rather than disclaimed."),
    inputs=(paths.GENE2PUBMED, paths.GENES_TO_DISEASE, paths.HPOA, paths.ORPHA_PREVALENCE),
    outputs=(paths.ATTENTION_BURDEN,),
    code=sources("tools/attention_burden.py"),
    run=lambda: _run_tool("attention_burden"),
))

_add(Stage(
    name="knowledge_void",
    summary=("The shape of the occupied space and the shape of the hole: which ways of "
             "knowing a disease occur, and which absent ones the marginals expected."),
    inputs=(paths.KNOWLEDGE_SHAPE,),
    outputs=(paths.KNOWLEDGE_VOID,),
    needs=("knowledge_shape",),
    code=sources("tools/knowledge_void.py"),
    run=lambda: _run_tool("knowledge_void"),
))

_add(Stage(
    name="gap_taxonomy",
    summary=("Type every missing field by what would close it: a study, an ingestion, a "
             "join, or a cohort."),
    inputs=(paths.MONDO, paths.GENES_TO_DISEASE, paths.HPOA, paths.ORPHA_PREVALENCE,
            paths.ORPHA_AGES),
    outputs=(paths.GAP_TAXONOMY,),
    code=sources("tools/gap_taxonomy.py"),
    run=lambda: _run_tool("gap_taxonomy"),
))

_add(Stage(
    name="autism",
    summary=("Do the 717 genes converging on an autism phenotype share a mechanism or only a "
             "word? A domain layer, NOT a Stage 1 adapter - it fails question four."),
    inputs=(paths.HPOA, paths.GENES_TO_DISEASE, paths.REACTOME_PATHWAYS,
            paths.REACTOME_HIERARCHY, paths.HPA_SINGLE_CELL, paths.STRING_ALIASES,
            paths.STRING_INFO),
    outputs=(paths.AUTISM_CONVERGENCE,),
    code=sources("tools/autism_convergence.py"),
    run=lambda: _run_tool("autism_convergence"),
))

_add(Stage(
    name="hiv",
    summary=("Stage 1 on HIV drug resistance: a max over the drug panel, an n-indexed "
             "permutation null, and a positive control named before the run."),
    inputs=(paths.HIV_PI,),
    outputs=(paths.HIV_RESISTANCE,),
    code=sources("analyses/hiv_resistance.py"),
    run=_script("analyses/hiv_resistance.py"),
))

_add(Stage(
    name="gene_ladder",
    summary=("Join every scale of one gene into a single object, and state what each step "
             "between two scales costs - or that nobody measured it."),
    inputs=(paths.GENES_TO_DISEASE, paths.HPOA, paths.HP_OBO, paths.STRING_LINKS,
            paths.STRING_INFO, paths.STRING_ALIASES, paths.REACTOME_PATHWAYS,
            paths.REACTOME_HIERARCHY, paths.HPA_SINGLE_CELL),
    outputs=(paths.GENE_LADDER,),
    needs=("scale_information",),
    code=sources("tools/gene_ladder.py"),
    run=lambda: _run_tool("gene_ladder"),
))

_add(Stage(
    name="view_models",
    summary=("Solve the orderings, bins and ribbon counts the hyperdimensional views need, "
             "so the browser draws and never computes."),
    inputs=(paths.SCALE_INFORMATION, paths.LANGUAGE_COVERAGE, paths.EVIDENCE_CONFLICT,
            paths.KNOWLEDGE_SHAPE),
    outputs=(paths.VIEW_MODELS,),
    needs=("scale_information", "language_coverage", "evidence_conflict", "knowledge_void"),
    code=sources("tools/view_models.py"),
    run=lambda: _run_tool("view_models"),
))

_add(Stage(
    name="references",
    summary="Encode the reference map and compute which communities actually share a rung.",
    outputs=(paths.REFERENCES,),
    code=sources("tools/references_seed.py"),
    run=lambda: _run_tool("references_seed"),
))

_add(Stage(
    name="thesis",
    summary="Encode the research thesis and audit each claim against what is built here.",
    outputs=(paths.THESIS,),
    code=sources("tools/thesis_seed.py"),
    run=lambda: _run_tool("thesis_seed"),
))

_add(Stage(
    name="numbers",
    summary="Regenerate the manuscript's macros, so no number is typed into the LaTeX.",
    outputs=(paths.PAPER_NUMBERS,),
    needs=("depmap",),
    code=sources("tools/paper_numbers.py"),
    run=_script("tools/paper_numbers.py"),
))

_add(Stage(
    name="multiplicity",
    summary="Turn calibrated z into p, test the normality it assumes, and control the FDR.",
    inputs=(paths.DEPMAP_GENES,),
    outputs=(paths.MULTIPLICITY,),
    needs=("depmap",),
    code=sources("tools/multiplicity.py"),
    run=lambda: _run_tool("multiplicity"),
))

_add(Stage(
    name="tail_calibration",
    summary="Measure how far the calibrated z departs from normal, and what a fitted tail costs.",
    inputs=(paths.DEPMAP_GENES,),
    outputs=(paths.TAIL_CALIBRATION,),
    needs=("depmap",),
    code=sources("tools/tail_calibration.py"),
    run=lambda: _run_tool("tail_calibration"),
))

_add(Stage(
    name="ecosystem",
    summary="Survey which libraries are installed, which are used, and which resources are not.",
    outputs=(paths.ECOSYSTEM,),
    always=True,
    code=sources("tools/ecosystem.py"),
    run=lambda: _run_tool("ecosystem"),
))


# --- the twenty-six that were run by hand ------------------------------------------------
#
#  Everything below this line already existed and already produced a published artefact. What
#  it did not have was a stage - so `sieve run` could report every stage fresh while the gene
#  index the navigator reads was older than the DepMap matrix it summarises, and nothing in
#  the system could say so. A tool outside the graph is a tool whose output nobody can date.
#
#  The gene chain is the sharpest case: eleven tools that must run in one order, and that
#  order was written only in prose at the bottom of each docstring. It is declared here now,
#  once, in `needs`.

_add(Stage(
    name="atlas",
    summary="The disease atlas: gene-disease, phenotype, prevalence and expression, joined.",
    inputs=src("hpo_genes", "hpo_annotations", "orpha_prevalence", "hpa_single_cell"),
    outputs=(paths.ATLAS,),
    code=sources("tools/build_atlas.py"),
    run=lambda: _run_tool("build_atlas"),
))

_add(Stage(
    name="atlas_bias",
    summary="What the atlas over- and under-represents, measured against its own sources.",
    inputs=src("hpo_genes", "hpo_annotations", "orpha_prevalence", "hpa_single_cell"),
    outputs=(paths.BIAS,),
    needs=("atlas",),
    code=sources("tools/atlas_bias.py"),
    run=lambda: _run_tool("atlas_bias"),
))

_add(Stage(
    name="gap_patterns",
    summary="The shapes a missing annotation takes, counted rather than described.",
    inputs=src("hpo_annotations", "hpo_genes"),
    outputs=(paths.GAP_PATTERNS,),
    needs=("atlas",),
    code=sources("tools/gap_patterns.py", "tools/build_atlas.py"),
    run=lambda: _run_tool("gap_patterns"),
))

_add(Stage(
    name="barriers",
    summary="What stands between a rare-disease finding and a patient, encoded.",
    outputs=(paths.BARRIERS,),
    code=sources("tools/barriers_seed.py"),
    run=lambda: _run_tool("barriers_seed"),
))

_add(Stage(
    name="nomenclature",
    summary="The naming layer: which identifiers agree, and where they silently do not.",
    outputs=(paths.NOMENCLATURE,),
    code=sources("tools/nomenclature_seed.py"),
    run=lambda: _run_tool("nomenclature_seed"),
))

_add(Stage(
    name="dimensions",
    summary="The first hyperdimensional view model, solved in Python so the browser draws.",
    outputs=(paths.DIMENSIONS,),
    needs=("rare", "nomenclature", "atlas"),
    code=sources("tools/dimensions.py"),
    run=lambda: _run_tool("dimensions"),
))

_add(Stage(
    name="dimensions_two",
    summary="The second view model: the orderings the first one could not carry.",
    outputs=(paths.DIMENSIONS_TWO,),
    needs=("rare", "atlas"),
    code=sources("tools/dimensions_two.py"),
    run=lambda: _run_tool("dimensions_two"),
))

_add(Stage(
    name="tropical_gap",
    summary="Which neglected tropical diseases the ontologies carry, and how thinly.",
    inputs=(paths.MONDO, paths.HPOA, paths.GENES_TO_DISEASE),
    outputs=(paths.TROPICAL_GAP,),
    code=sources("tools/tropical_gap.py"),
    run=lambda: _run_tool("tropical_gap"),
))

_add(Stage(
    name="gene_constraint",
    summary=("gnomAD LOEUF against disease genes, with a length-matched control - two "
             "thirds of the shift is coding length."),
    inputs=src("gnomad_constraint", "hpo_genes"),
    outputs=(paths.GENE_CONSTRAINT,),
    code=sources("tools/gene_constraint.py"),
    run=lambda: _run_tool("gene_constraint"),
))

_add(Stage(
    name="single_cell_coverage",
    summary="How much of the disease catalogue single-cell atlases have ever measured.",
    inputs=src("cellxgene_collections", "hpo_genes", "hpo_annotations"),
    outputs=(paths.SINGLE_CELL_COVERAGE,),
    code=sources("tools/single_cell_coverage.py"),
    run=lambda: _run_tool("single_cell_coverage"),
))

_add(Stage(
    name="cleared_devices",
    summary="The FDA's own list of authorised AI devices, counted by panel.",
    inputs=src("fda_ai_devices"),
    outputs=(paths.CLEARED_DEVICES,),
    code=sources("tools/cleared_devices.py"),
    run=lambda: _run_tool("cleared_devices"),
))

_add(Stage(
    name="psychiatric_gwas",
    summary="Who was sequenced in psychiatric genetics, by ancestry, per disorder.",
    inputs=src("gwas_accessions", "gwas_ancestry", "gwas_studies"),
    outputs=(paths.PSYCHIATRIC_GWAS,),
    code=sources("tools/psychiatric_gwas.py"),
    run=lambda: _run_tool("psychiatric_gwas"),
))

_add(Stage(
    name="trait_atlas",
    summary="The same ancestry question across eight disease areas, seriated both ways.",
    inputs=src("gwas_accessions", "gwas_ancestry", "gwas_studies", "gwas_efo"),
    outputs=(paths.TRAIT_ATLAS,),
    needs=("psychiatric_gwas",),
    code=sources("tools/trait_atlas.py"),
    run=lambda: _run_tool("trait_atlas"),
))

_add(Stage(
    name="signal_energy",
    summary=("Whether form-giving pathways carry more information about which organ fails "
             "than energy pathways do - the prediction failed, and the artefact says so."),
    outputs=(paths.SIGNAL_ENERGY,),
    needs=("scale_information",),
    code=sources("tools/signal_energy.py", "tools/scale_information.py"),
    run=lambda: _run_tool("signal_energy"),
))

_add(Stage(
    name="obesity",
    summary=("Stage 1 on a thermogenesis screen with a DESIGNED control pool - 41 clear the "
             "null on the point, 16 on the lower end of their own interval."),
    inputs=src("obesity_thermo_cells", "obesity_thermo_perturbation"),
    outputs=(paths.OBESITY_THERMOGENESIS,),
    code=sources("analyses/obesity_thermogenesis.py"),
    run=_script("analyses/obesity_thermogenesis.py"),
))

# --- the gene chain, in the order it has to run ------------------------------------------

_add(Stage(
    name="gene_index",
    summary="Symbol to record for 18,140 genes: the spine every other gene tool reads.",
    inputs=(paths.DEPMAP_GENES, paths.CANCER_GENOTYPE, paths.GENE_NETWORK),
    outputs=(paths.GENE_INDEX,),
    needs=("depmap", "cancer_genotype", "interactome"),
    code=sources("tools/gene_index.py"),
    run=lambda: _run_tool("gene_index"),
))

_add(Stage(
    name="gene_world",
    summary="Where each gene sits in the world: expression breadth, lineage, and scope.",
    inputs=(paths.GENE_INDEX,),
    outputs=(paths.GENE_WORLD,),
    needs=("gene_index",),
    code=sources("tools/gene_world.py"),
    run=lambda: _run_tool("gene_world"),
))

_add(Stage(
    name="gene_domains",
    summary="UniProt domain families, normalised - the molecular part you can browse by.",
    inputs=(paths.GENE_INDEX,),
    outputs=(paths.GENE_DOMAINS,),
    needs=("gene_index",),
    code=sources("tools/gene_domains.py"),
    run=lambda: _run_tool("gene_domains"),
))

_add(Stage(
    name="gene_geometry",
    summary="The shape of a gene's neighbourhood, calibrated - clustering fell 95% to 36%.",
    inputs=(paths.GENE_INDEX, paths.GENE_WORLD),
    outputs=(paths.GENE_GEOMETRY,),
    needs=("gene_world",),
    code=sources("tools/gene_geometry.py"),
    run=lambda: _run_tool("gene_geometry"),
))

_add(Stage(
    name="gene_related",
    summary="What to read next from a gene page, and why that gene and not another.",
    inputs=(paths.GENE_INDEX, paths.GENE_DOMAINS, paths.GENE_NETWORK),
    outputs=(paths.GENE_RELATED,),
    needs=("gene_domains",),
    code=sources("tools/gene_related.py"),
    run=lambda: _run_tool("gene_related"),
))

_add(Stage(
    name="gene_datasheet",
    summary="The gene as a datasheet: every measured field with its null and its interval.",
    inputs=(paths.GENE_INDEX,),
    outputs=(paths.GENE_DATASHEET,),
    needs=("gene_index",),
    code=sources("tools/gene_datasheet.py"),
    run=lambda: _run_tool("gene_datasheet"),
))

_add(Stage(
    name="gene_insights",
    summary="What two layers say when read together, per gene, or that they disagree.",
    inputs=(paths.GENE_INDEX, paths.GENE_WORLD, paths.GENE_GEOMETRY, paths.GENE_DOMAINS,
            paths.GENE_DATASHEET),
    outputs=(paths.GENE_INSIGHTS,),
    needs=("gene_geometry", "gene_datasheet", "gene_domains"),
    code=sources("tools/gene_insights.py"),
    run=lambda: _run_tool("gene_insights"),
))

_add(Stage(
    name="gene_attention",
    summary="How much has ever been written about each gene, against what it constrains.",
    inputs=(paths.GENE_WORLD,),
    outputs=(paths.GENE_ATTENTION,),
    needs=("gene_world",),
    code=sources("tools/gene_attention.py"),
    run=lambda: _run_tool("gene_attention"),
))

_add(Stage(
    name="gene_facets",
    summary=("PROPERTY to symbols: the browse index for people who do not already know the "
             "gene they need. Six facets, every one of them a measurement on disk."),
    inputs=(paths.GENE_INDEX, paths.GENE_WORLD, paths.GENE_GEOMETRY, paths.GENE_DOMAINS),
    outputs=(paths.GENE_FACETS,),
    needs=("gene_geometry", "gene_domains"),
    code=sources("tools/gene_facets.py"),
    run=lambda: _run_tool("gene_facets"),
))

_add(Stage(
    name="gene_space",
    summary="The gene projection the navigator plots, solved once here rather than per view.",
    inputs=(paths.GENE_INDEX, paths.GENE_WORLD, paths.GENE_DATASHEET, paths.GENE_INSIGHTS,
            paths.GENE_ATTENTION),
    outputs=(paths.GENE_SPACE,),
    needs=("gene_insights", "gene_attention"),
    code=sources("tools/gene_space.py"),
    run=lambda: _run_tool("gene_space"),
))

_add(Stage(
    name="gene_shards",
    summary="Split the gene surface into fetchable shards, so a page loads one and not all.",
    inputs=(paths.GENE_INDEX, paths.GENE_WORLD, paths.GENE_GEOMETRY, paths.GENE_DOMAINS,
            paths.GENE_RELATED, paths.GENE_DATASHEET, paths.GENE_INSIGHTS,
            paths.GENE_ATTENTION),
    outputs=(paths.GENE_SHARD_INDEX,),
    needs=("gene_related", "gene_insights", "gene_attention", "gene_facets", "gene_space"),
    code=sources("tools/gene_shards.py"),
    run=lambda: _run_tool("gene_shards"),
))

_add(Stage(
    name="community_stability",
    summary=("Is the published partition in the graph or in the algorithm? Twelve seeds, "
             "three algorithms, a resolution sweep and a per-gene consensus confidence."),
    inputs=(paths.GENE_NETWORK,),
    outputs=(paths.COMMUNITY_STABILITY,),
    needs=("rare",),
    code=sources("tools/community_stability.py"),
    run=lambda: _run_tool("community_stability"),
))

_add(Stage(
    name="community_identity",
    summary=("Name each community from Reactome - the one annotation the graph's own "
             "construction never consulted - against an annotation-matched null."),
    inputs=(paths.COMMUNITY_STABILITY,),
    outputs=(paths.COMMUNITY_IDENTITY,),
    needs=("community_stability",),
    code=sources("tools/community_identity.py", "tools/scale_information.py"),
    run=lambda: _run_tool("community_identity"),
))

_add(Stage(
    name="relational_primacy",
    summary=("Are entities better predicted by their relations than by their attributes? The "
             "author's most central construct, in the only form that can be falsified."),
    inputs=src("hpo_genes"),
    outputs=(paths.RELATIONAL_PRIMACY,),
    needs=("gene_embedding",),
    code=sources("tools/relational_primacy.py", "tools/gene_embedding.py"),
    run=lambda: _run_tool("relational_primacy"),
))

_add(Stage(
    name="methods",
    summary=("The five constructs, each with its falsifier and whether that falsifier has "
             "been computed. Two measured, two specified, one untestable in public data."),
    outputs=(paths.METHODS,),
    code=sources("tools/methods_seed.py"),
    run=lambda: _run_tool("methods_seed"),
))

_add(Stage(
    name="nonreciprocal",
    summary=("Does asymmetry carry information its symmetric projection loses? The author's "
             "own hypothesis, run against the falsifier he wrote before any number existed."),
    inputs=src("hpo_genes"),
    outputs=(paths.NONRECIPROCAL,),
    code=sources("tools/nonreciprocal.py"),
    run=lambda: _run_tool("nonreciprocal"),
))

_add(Stage(
    name="clusterability",
    summary=("Is there anything to cluster? Hopkins, HDBSCAN noise and the k-means silhouette "
             "against a null that shuffles each feature independently."),
    inputs=(paths.GENE_WORLD, paths.GENE_ATTENTION, paths.GENE_GEOMETRY),
    outputs=(paths.CLUSTERABILITY,),
    needs=("gene_embedding",),
    code=sources("tools/clusterability.py", "tools/gene_embedding.py"),
    run=lambda: _run_tool("clusterability"),
))

_add(Stage(
    name="gene_embedding",
    summary=("A UMAP of eleven per-gene measurements, published with the three numbers that "
             "say what it is worth: trustworthiness, seed agreement, and clustering the "
             "picture against clustering the data."),
    inputs=(paths.GENE_WORLD, paths.GENE_ATTENTION, paths.GENE_GEOMETRY),
    outputs=(paths.GENE_EMBEDDING,),
    needs=("gene_attention", "gene_geometry"),
    code=sources("tools/gene_embedding.py"),
    run=lambda: _run_tool("gene_embedding"),
))

_add(Stage(
    name="partition_flow",
    summary=("Which genes move between the three algorithms' communities, matched by an "
             "exact assignment solution and ordered to cut ribbon crossings."),
    inputs=(paths.GENE_NETWORK, paths.COMMUNITY_IDENTITY),
    outputs=(paths.PARTITION_FLOW,),
    needs=("community_identity",),
    code=sources("tools/partition_flow.py", "tools/community_stability.py"),
    run=lambda: _run_tool("partition_flow"),
))

_add(Stage(
    name="network_layout",
    summary=("Three orderings of the gene graph, solved in Python so the browser draws "
             "38,746 edges and never seriates them."),
    inputs=(paths.GENE_NETWORK, paths.COMMUNITY_STABILITY),
    outputs=(paths.NETWORK_LAYOUT,),
    needs=("community_stability",),
    code=sources("tools/network_layout.py"),
    run=lambda: _run_tool("network_layout"),
))

_add(Stage(
    name="pipeline_state",
    summary="Publish which stages are fresh or stale, so freshness is not terminal-only.",
    outputs=(paths.PIPELINE_STATE,),
    always=True,
    code=sources("tools/pipeline_state.py", "src/sieve/pipeline/*.py"),
    run=lambda: _run_tool("pipeline_state"),
))

_add(Stage(
    name="check",
    summary="Verify the manuscript is submittable: numbers current, references verified.",
    needs=("numbers", "figures"),
    always=True,
    run=lambda: _check(),
))


def _run_tool(module: str, *args: str) -> None:
    """Run a tools/ script in-process so a failure is a traceback, not a silent exit code.

    `args` are forwarded as argv. Before they were, this function silently discarded any
    flag a caller passed — a stage that ran one tool three times with different `--level`
    values would have produced the same level three times and overwritten nothing, which is
    a wrong artefact rather than an error.
    """
    import runpy
    import sys

    path = paths.ROOT / "tools" / (module + ".py")
    argv = sys.argv
    sys.argv = [str(path), *args]
    try:
        runpy.run_path(str(path), run_name="__main__")
    except SystemExit as exit_:
        if exit_.code not in (0, None):
            raise
    finally:
        sys.argv = argv


def _seed() -> None:
    """The three seeds are one stage: they share a vocabulary and drift if run apart."""
    for script in ("rare_disease_seed.py", "lupus_seed.py", "lupus_graph.py"):
        _run(str(paths.TOOLS / script))


def _check() -> None:
    """The submission gate. A verification stage, so it is never cached.

    `verify_claims.py` joined this gate on 2026-08-28. It is F1 of docs/audit.md: the
    manuscript's numbers were already generated from manifests and could not drift, while
    the MARKDOWN quoted them by hand and drifted twice (A1, A11). A submission gate that
    checks the paper and not the documentation was checking the smaller half.

    `status.py --check` joined it the same day and closes the remaining half again.
    `verify_claims.py` checks that quoted NUMBERS still match their artefacts; it cannot see
    a citation to a file that does not exist, or a sentence asserting that a dataset was
    never fetched while 1.39 GB of it sits on disk. Both of those were present when the
    check was written.
    """
    _run(str(paths.TOOLS / "paper_numbers.py"), "--check")
    _run(str(paths.TOOLS / "figure_data.py"), "--check")
    _run(str(paths.TOOLS / "verify_claims.py"))
    _run(str(paths.TOOLS / "status.py"), "--check")
    _run(str(paths.TOOLS / "index_check.py"))
    _run(str(paths.TOOLS / "z_audit.py"), "--check")
    bib = paths.REFS_BIB.read_text(encoding="utf-8")
    unverified = sum(
        1
        for line in bib.splitlines()
        if not line.lstrip().startswith("%") and "verified" in line and "{no}" in line
    )
    if unverified:
        print(f"  {unverified} reference(s) still unverified — not submittable")
        raise SystemExit(1)
    print("  manuscript numbers current, references verified")


#: Everything, in declaration order. `all` is a target, not a stage.
DEFAULT_TARGETS = ("depmap", "figures", "rare", "numbers")
