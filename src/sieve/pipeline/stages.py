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
