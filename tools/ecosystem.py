#!/usr/bin/env python
"""What is installed, what is used, and what is sitting on the machine unopened.

WHY NOT A SHOPPING LIST. A page listing libraries one could adopt is worth nothing — anyone can
write it and nothing about it is checkable. This file imports each candidate, records the
version it actually finds, and greps the repository for whether the project imports it. The
interesting column is neither "installed" nor "would be nice": it is INSTALLED AND UNUSED,
because that is capability already paid for and not spent.

The result is uncomfortable and worth publishing: this project declares numpy and pandas as its
dependencies and runs on a machine carrying scipy, statsmodels, scikit-learn, networkx, numba
and torch. Until `tools/multiplicity.py`, every statistic here was hand-rolled from numpy while
scipy sat installed — which for a project whose argument is about statistical care is close to
the worst place to be self-reliant.

EACH ENTRY IS TIED TO A RUNG. The thesis ladder runs genotype → structure → dynamics →
interactome → pathway → cell → tissue → patient, and several rungs are marked "named, not
built". A library is only interesting here if it would move one of those, so every row names
which, and rows that would move nothing are omitted rather than padded.

RESOURCES ARE THE OTHER HALF. Public datasets carry licences that decide whether a derivative
may be shipped, and this project has already been shaped by that — Orphanet is CC BY-ND, so
its derivatives stay local. Anything proposed for ingestion is listed with its licence, its
size and whether it is already downloaded.

    python tools/ecosystem.py     # writes out/ecosystem.json
"""

from __future__ import annotations

import importlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "out" / "ecosystem.json"

SEARCH_DIRS = ("src", "tools", "analyses", "tests")


def lib(module, name, rung, would, note, status_hint=None):
    return dict(module=module, name=name, rung=rung, would=would, note=note,
                statusHint=status_hint)


# --- the candidates, each tied to a rung it would actually move -----------------------
LIBS = [
    lib("numpy", "NumPy", "all", "The array. Everything else is built on it.",
        "Declared, used everywhere. Nothing to argue about."),
    lib("pandas", "pandas", "all", "Tabular joins and the CSV boundary between stages.",
        "Declared and used. The atlas joins are pandas."),

    lib("scipy", "SciPy", "pathway",
        "Distributions, goodness-of-fit, sparse matrices, optimisation.",
        "The one that stings. Every statistic in this repository was hand-rolled from numpy "
        "while scipy sat installed, in a project whose entire argument is statistical care. "
        "tools/multiplicity.py is the first file to import it, and the first thing it found "
        "was that the calibrated z fails a normality test its mean and variance pass."),
    lib("statsmodels", "statsmodels", "pathway",
        "Multiple-testing correction, regression, and the diagnostics that go with it.",
        "Benjamini-Hochberg is four lines to write and the reason not to write it is that the "
        "four lines are where the off-by-one lives. Now used for the FDR layer."),
    lib("sklearn", "scikit-learn", "cell",
        "Dimensionality reduction, clustering, and the metrics for both.",
        "Available and unused. It is the obvious tool for the cell-state rung, which is "
        "currently one expression value per cell type rather than a cell-by-gene matrix."),
    lib("networkx", "NetworkX", "interactome",
        "Graph construction, propagation, community detection, centrality.",
        "Available and unused. The lupus graph is hand-built and its propagation is written by "
        "hand; random walk with restart and heat diffusion are both one call here."),
    lib("scipy.sparse", "scipy.sparse", "interactome",
        "CSR/CSC matrices and the sparse linear algebra the thesis is about.",
        "The computational thesis in this project is about sparse workloads on biological "
        "topology, and no sparse matrix has been constructed yet. This is the gap between the "
        "second thesis and the repository, stated as an import."),
    lib("numba", "Numba", "dynamics",
        "JIT compilation of numeric loops, including parallel ones.",
        "Available and unused. The null resampling is the only hot loop here and it is small "
        "enough not to need it — worth saying, because reaching for a JIT before measuring is "
        "how projects acquire complexity they cannot justify."),
    lib("torch", "PyTorch", "structure",
        "Tensors on the GPU; the substrate every structure and language model runs on.",
        "Installed with CUDA and unused. It is the entry point to the structure rung — ESMFold "
        "and the protein language models run on it — and that rung is currently named and not "
        "built."),
    lib("pyarrow", "PyArrow", "all",
        "Columnar storage; Parquet instead of CSV at the stage boundary.",
        "Declared as an optional extra. The stage boundary is CSV, which is fine at 17,916 "
        "rows and stops being fine at the single-cell rung."),
    lib("sympy", "SymPy", "pathway", "Symbolic algebra.",
        "Available and unused, and likely to stay that way: nothing here needs a closed form."),
    lib("joblib", "joblib", "all", "Parallel map and on-disk memoisation.",
        "Available and unused. The pipeline's staleness tracking does the caching job at a "
        "coarser grain, which is the right grain for stages that take minutes."),
    lib("matplotlib", "Matplotlib", "all", "Static figures for the manuscript.",
        "Not installed, and deliberately so: figures are data files rendered by the web app, "
        "so there is no second implementation of a chart to disagree with the first."),
    lib("anndata", "AnnData", "cell",
        "The standard container for single-cell matrices with per-cell and per-gene annotation.",
        "Not installed. It is the format the cell rung would arrive in, and the reason that "
        "rung is 'partial' rather than 'built'."),
    lib("scanpy", "Scanpy", "cell",
        "The single-cell analysis stack built on AnnData.",
        "Not installed. Named in the thesis, absent from the machine."),
    lib("squidpy", "Squidpy", "tissue",
        "Spatial single-cell: neighbourhood graphs, spatial statistics.",
        "Not installed. The tissue rung is the largest hole in the ladder and this is the "
        "library that would fill it."),
    lib("Bio", "Biopython", "structure",
        "Sequence and structure file handling, alignment.",
        "Not installed. It is the mundane plumbing under any structural work."),
    lib("mdtraj", "MDTraj", "dynamics",
        "Trajectory analysis for molecular dynamics.",
        "Not installed. The dynamics rung needs a sampling engine before it needs an analyser, "
        "so this is downstream of a decision not yet made."),
    lib("openmm", "OpenMM", "dynamics",
        "GPU molecular dynamics.",
        "Not installed. The rung is about the sampling bottleneck, and this is where that "
        "bottleneck would actually be met."),
    lib("pyhpo", "PyHPO", "patient",
        "Semantic similarity over the Human Phenotype Ontology.",
        "Not installed. The dossiers parse HPO by hand; phenotype-to-phenotype distance is the "
        "obvious next measurement and needs an ontology-aware library."),
    lib("hypothesis", "Hypothesis", "all",
        "Property-based testing: generate inputs rather than enumerate them.",
        "Not installed. For a null-calibration library the properties almost write themselves "
        "— calibrating a constant column must not change a ranking — and that is a stronger "
        "test than any fixed example."),
]

# --- public resources, with the licence that decides what may be shipped ---------------
RESOURCES = [
    dict(id="depmap", name="DepMap CRISPR (Chronos)", rung="pathway",
         gives="Gene effect across ~1,178 cell lines: the perturbation screen this whole "
               "library was hardened against.",
         licence="CC BY 4.0", ingested=True,
         note="Already the primary adapter."),
    dict(id="hpo", name="Human Phenotype Ontology", rung="patient",
         gives="Disease-to-phenotype annotations, inheritance modes, the vocabulary itself.",
         licence="permissive, attribution", ingested=True,
         note="Carries the inheritance measurement behind the non-gene tab."),
    dict(id="orphanet", name="Orphanet", rung="patient",
         gives="Prevalence records with type and geography, gene associations, ages of onset.",
         licence="CC BY-ND 4.0 — no derivatives may be redistributed", ingested=True,
         note="The licence is why derived material stays local and is described rather than "
              "shipped. It shaped the architecture."),
    dict(id="hpa", name="Human Protein Atlas, single-cell", rung="cell",
         gives="Expression across 154 cell types.", licence="CC BY-SA 4.0", ingested=True,
         note="The cell axis. Per cell TYPE, not per cell."),
    dict(id="ctgov", name="ClinicalTrials.gov API v2", rung="patient",
         gives="What is being tried right now, by disease and by intervention.",
         licence="public domain", ingested=True,
         note="Queried live and cached so the artefact stays reproducible."),
    dict(id="biogrid", name="BioGRID", rung="interactome",
         gives="Curated protein-protein interactions — the subgraph a Merlin propagation "
               "would run on.",
         licence="MIT", ingested=False,
         note="Named in the thesis as the concrete next step and not downloaded. The lupus "
              "graph is hand-built in its place."),
    dict(id="string", name="STRING", rung="interactome",
         gives="Scored functional associations, with the score decomposed by evidence type.",
         licence="CC BY 4.0", ingested=False,
         note="Denser than BioGRID and needs a threshold, which is a judgement this project "
              "would have to state rather than inherit."),
    dict(id="reactome", name="Reactome", rung="pathway",
         gives="Curated pathway membership and hierarchy.",
         licence="CC0", ingested=False,
         note="The Hippo axis is currently a hand-written gene list; this would make it a "
              "citation."),
    dict(id="clinvar", name="ClinVar", rung="genotype",
         gives="Variant-level clinical interpretation, with the review status attached.",
         licence="public domain", ingested=False,
         note="The genotype rung stops at genes. Variants are where the thesis actually "
              "starts."),
    dict(id="gnomad", name="gnomAD", rung="genotype",
         gives="Population allele frequency, and per-gene constraint.",
         licence="ODbL / free for any use", ingested=False,
         note="Constraint is the cheapest evidence that a gene tolerates no loss, and it is "
              "one file away."),
    dict(id="alphafold", name="AlphaFold DB", rung="structure",
         gives="Predicted structures for essentially every human protein, with per-residue "
               "confidence.",
         licence="CC BY 4.0", ingested=False,
         note="The structure rung would begin here rather than with a folding run, which is "
              "the difference between a download and a GPU budget."),
    dict(id="uniprot", name="UniProt", rung="structure",
         gives="Domains, sites, isoforms, and the residue numbering everything else keys on.",
         licence="CC BY 4.0", ingested=False,
         note="Without it a residue position is a number with no meaning."),
    dict(id="mondo", name="MONDO", rung="patient",
         gives="A disease ontology that merges OMIM, Orphanet and DECIPHER identifiers.",
         licence="CC BY 4.0", ingested=False,
         note="Would replace the exact-name matching the dossiers currently do — which is the "
              "same fragility that put five wrong ORPHA codes on this site once already."),
]


def repo_imports() -> set[str]:
    """Which modules the repository actually imports. Grep, because that is the ground truth."""
    found: set[str] = set()
    pat = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][\w.]*)", re.M)
    for d in SEARCH_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for f in base.rglob("*.py"):
            try:
                for m in pat.findall(f.read_text(encoding="utf-8", errors="ignore")):
                    found.add(m.split(".")[0])
                    found.add(m)
            except OSError:
                continue
    return found


def main() -> int:
    used = repo_imports()
    rows = []
    for entry in LIBS:
        mod = entry["module"]
        top = mod.split(".")[0]
        try:
            m = importlib.import_module(mod)
            version = getattr(m, "__version__", None) or getattr(
                importlib.import_module(top), "__version__", "installed")
            installed = True
        except Exception:
            version, installed = None, False
        in_use = mod in used or top in used
        rows.append({**entry, "installed": installed, "version": version,
                     "inUse": bool(in_use),
                     "status": ("in use" if installed and in_use
                                else "installed, unused" if installed
                                else "not installed")})

    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1

    unused = [r["name"] for r in rows if r["status"] == "installed, unused"]
    ingested = sum(1 for r in RESOURCES if r["ingested"])

    payload = {
        "generated": "tools/ecosystem.py",
        "premise": (
            "Not a list of libraries one could adopt — anyone can write that and none of it is "
            "checkable. Each row below was imported to get its version and grepped for across "
            "src, tools, analyses and tests to see whether this project actually uses it. The "
            "interesting column is INSTALLED AND UNUSED: capability already paid for and not "
            "spent."
        ),
        "confession": (
            "This project declares numpy and pandas as its dependencies and runs on a machine "
            "carrying scipy, statsmodels, scikit-learn, NetworkX, Numba and PyTorch. Until "
            "tools/multiplicity.py every statistic here was hand-rolled from numpy while scipy "
            "sat installed — and the first thing scipy found, on its first run, was that the "
            "calibrated z fails a normality test whose mean and variance it passes."
        ),
        "libraries": rows,
        "resources": RESOURCES,
        "summary": {
            "libraries": len(rows),
            "byStatus": by_status,
            "installedUnused": unused,
            "resources": len(RESOURCES),
            "resourcesIngested": ingested,
            "resourcesNamed": len(RESOURCES) - ingested,
        },
    }

    DEST.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    s = payload["summary"]
    print("wrote %s" % DEST.relative_to(ROOT))
    print("  %d libraries: %s" % (s["libraries"], s["byStatus"]))
    print("  installed and unused: %s" % ", ".join(unused))
    print("  %d public resources, %d ingested, %d named and not"
          % (s["resources"], s["resourcesIngested"], s["resourcesNamed"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
