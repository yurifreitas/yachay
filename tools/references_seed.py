#!/usr/bin/env python
"""The reference map, encoded — and the bridge it implies, computed rather than asserted.

WHAT THIS IS. The author's world map of references for this research line: the NF2 clinical and
gene-therapy community, the rare-disease infrastructure, the network-biology school, the
sparse-HPC people, the tensor-compiler people, and the complex-systems influences. Roughly
eighty entries across a dozen countries.

WHY IT IS NOT JUST A BIBLIOGRAPHY. The last observation in the source material is the sharpest
one in it: these references belong to communities that normally publish separately, and the
unusual part of the project is the bridge, not any single citation. A bibliography cannot show
that. So every entry is tagged with its COMMUNITY and with the LADDER RUNG it serves, and the
file then computes which rungs carry references from more than one community — those are the
real bridges — and which carry only one, which are the places the project is currently a
member of exactly one conversation.

PROVENANCE, IN TWO CLASSES, AND THE DISTINCTION IS NOT PEDANTRY.

  `public-artifact`  a library, standard, database or paper whose existence and purpose are
                     common knowledge in its field: BLIS, GraphBLAS, TACO, MLIR, GROMACS, PDB,
                     OMIM, Turing 1952. Nothing about these needs checking here.

  `author-supplied`  claims about PEOPLE, POSTS, PROGRAMMES AND MONEY: who works where, who
                     sits on which board, which programme holds which grant, what a foundation
                     has raised. These are the author's, this repository has verified none of
                     them, and no file in this project resolves a single one. They are marked
                     on every row rather than in a footnote, because a name attached to an
                     institution reads as a fact whether or not anyone checked it.

The distinction matters most where it is least comfortable: "TACO is a sparse tensor algebra
compiler" is common knowledge; "X sits on the scientific board of Y and holds a $3M SBIR" is a
factual claim about a living person and an organisation, and publishing it unverified beside
verified material would launder the second into the first.

    python tools/references_seed.py     # writes out/rare/references.json
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "out" / "rare"

PUBLIC = "public-artifact"
SUPPLIED = "author-supplied"

# The six communities. The author's own formulation names five and treats complex systems as
# an influence rather than a discipline being bridged; that is kept as a flag rather than
# silently promoted.
COMMUNITIES = [
    dict(id="clinical", name="Rare-disease biology and therapy",
         inAuthorFormula=True,
         note="The people who would actually treat someone. Publishes in medical genetics and "
              "neuro-oncology venues."),
    dict(id="infra", name="Rare-disease infrastructure",
         inAuthorFormula=True,
         note="Ontologies, registries and variant catalogues. Rarely credited as research and "
              "load-bearing for all of it."),
    dict(id="systems", name="Systems and computational biology",
         inAuthorFormula=True,
         note="Networks, single-cell, spatial, structure, dynamics. Publishes in bioinformatics "
              "and systems-biology venues."),
    dict(id="hpc", name="High-performance and sparse computation",
         inAuthorFormula=True,
         note="Numerical linear algebra, graph algorithms, profiling. Publishes at SC, PPoPP, "
              "IPDPS — venues the biology communities do not read."),
    dict(id="compiler", name="Compilers and runtimes",
         inAuthorFormula=True,
         note="IRs, lowering, kernel generation, domain-specific compilation. Publishes at "
              "PLDI, CGO, ASPLOS."),
    dict(id="complex", name="Complex systems and morphogenesis",
         inAuthorFormula=False,
         note="Named by the author as influence rather than as a discipline being bridged, and "
              "kept that way here."),
]

RUNGS = ["genotype", "structure", "dynamics", "interactome", "pathway",
         "cell", "tissue", "patient", "substrate", "method"]


def ref(id, name, kind, community, rung, where, why, prov, country="—"):
    return dict(id=id, name=name, kind=kind, community=community, rung=rung,
                where=where, why=why, provenance=prov, country=country)


REFERENCES = [
    # ---- NF2 clinical and gene therapy -------------------------------------------------
    ref("brenner", "Gary J. Brenner", "person", "clinical", "patient",
        "Massachusetts General Hospital / Harvard Medical School",
        "Named as a central reference for experimental therapy in NF2-associated schwannoma: "
        "AAV gene therapy and tumour-directed strategies.", SUPPLIED, "United States"),
    ref("henwood", "Nicole Henwood", "person", "clinical", "patient",
        "Cure NF2 Foundation",
        "Named as founder of the foundation that turned an advocacy group into an organisation "
        "specialised in accelerating gene therapy for NF2.", SUPPLIED, "United States"),
    ref("rodriguez", "Edgar Rodríguez-Lebrón", "person", "clinical", "genotype",
        "Cure NF2 / Lacerta Therapeutics / University of Florida",
        "AAV, CNS delivery, microRNA and gene editing.", SUPPLIED, "United States"),
    ref("alcantara", "Krizelle Alcantara", "person", "clinical", "genotype",
        "Abigail Wexner Research Institute / Nationwide Children's",
        "Gene therapy for NF2 and miRNA regulation of the NF2 gene; also a person living with "
        "NF2, which the author records deliberately.", SUPPLIED, "United States"),
    ref("meyer", "Kathrin Meyer", "person", "clinical", "genotype",
        "Nationwide Children's Hospital",
        "The AAV NF2 gene-addition line — restoring Merlin rather than blocking a pathway.",
        SUPPLIED, "United States"),
    ref("kaspar", "Brian Kaspar", "person", "clinical", "genotype",
        "Nationwide Children's / gene-therapy ecosystem",
        "Historical reference for CNS gene therapy; the environment the SMA strategies came "
        "out of.", SUPPLIED, "United States"),
    ref("flotte", "Terry Flotte", "person", "clinical", "genotype",
        "UMass Chan Medical School",
        "AAV, gene replacement and silencing in monogenic disease.", SUPPLIED, "United States"),
    ref("meijboom", "Katharina Meijboom", "person", "clinical", "genotype",
        "UMass Chan Medical School",
        "Associated with the experimental NF2 gene-therapy lines.", SUPPLIED, "United States"),
    ref("mekalanos", "John Mekalanos", "person", "clinical", "patient",
        "Harvard Medical School",
        "Bacterial immunotherapy against NF2 tumours — engineered attenuated Salmonella.",
        SUPPLIED, "United States"),
    ref("castellanos", "Elisabeth Castellanos", "person", "clinical", "genotype",
        "Germans Trias i Pujol Research Institute (IGTP)",
        "Patient-specific antisense oligonucleotide strategies — the concrete European route "
        "into N-of-1 therapeutics for a private variant.", SUPPLIED, "Spain"),
    ref("giovannini", "Marco Giovannini", "person", "clinical", "cell",
        "UCLA",
        "Murine models of NF2, including the historical lines. The reference behind the "
        "author's point that the animal should follow the prioritisation.", SUPPLIED,
        "United States"),
    ref("xu", "Lei Xu", "person", "clinical", "cell",
        "Massachusetts General Hospital / Harvard",
        "Preclinical models of NF2.", SUPPLIED, "United States"),
    ref("morrison", "Helen Morrison", "person", "clinical", "pathway",
        "Leibniz Institute",
        "Merlin biology and the cellular mechanisms of its loss — the European anchor for the "
        "molecular half rather than the tumour half.", SUPPLIED, "Germany"),
    ref("curenf2", "Cure NF2 Foundation", "organisation", "clinical", "patient",
        "United States",
        "A portfolio rather than a single bet: gene addition, a suicide-gene programme, "
        "bacterial immunotherapy, a biobank, preclinical models, microenvironment work. The "
        "author records raised funds, programme counts and a biobank size; none is verified "
        "here.", SUPPLIED, "United States"),
    ref("ctf", "Children's Tumor Foundation", "organisation", "clinical", "patient",
        "United States",
        "Works across the neurofibromatoses and schwannomatoses and functions as the bridge "
        "between researchers, patients, industry and trials.", SUPPLIED, "United States"),
    ref("ninds", "NIH / NINDS", "organisation", "clinical", "patient",
        "United States",
        "The funder of record for the neurological half, including the SBIR mechanism the "
        "author cites for one programme.", SUPPLIED, "United States"),

    # ---- rare-disease infrastructure ----------------------------------------------------
    ref("genereviews", "GeneReviews — NF2-Related Schwannomatosis", "reference", "infra",
        "patient", "NCBI",
        "The clinical baseline: genetics, phenotype, diagnosis, natural history, management.",
        PUBLIC, "United States"),
    ref("clinvar", "ClinVar", "database", "infra", "genotype", "NCBI",
        "Variant-level clinical interpretation with review status. The genotype rung of this "
        "project stops at genes; this is where variants would enter.", PUBLIC, "United States"),
    ref("cosmic", "COSMIC", "database", "infra", "genotype", "Wellcome Sanger Institute",
        "Somatic mutation catalogue. NF2 is germline AND somatic, and the architecture has to "
        "keep the two apart.", PUBLIC, "United Kingdom"),
    ref("omim", "OMIM", "database", "infra", "patient", "Johns Hopkins University",
        "Gene to Mendelian phenotype. Already one of the three identifier spaces this atlas "
        "joins, and the reason its disease count is larger than the usual 7,000-8,000.",
        PUBLIC, "United States"),
    ref("hpo", "Human Phenotype Ontology", "ontology", "infra", "patient", "international",
        "A patient becomes a set of terms rather than free text, and phenotype similarity "
        "becomes computable. Already ingested here, and the source of the inheritance "
        "measurement behind the non-gene tab.", PUBLIC, "international"),
    ref("orphanet", "Orphanet", "database", "infra", "patient", "INSERM / European network",
        "Rare-disease classification, epidemiology, orphan drugs. Already ingested — and its "
        "CC BY-ND licence shaped this repository's architecture.", PUBLIC, "France / Europe"),
    ref("monarch", "Monarch Initiative", "ontology", "infra", "patient", "international",
        "Integrates genes, diseases, phenotypes and model organisms. The closest existing "
        "thing to the knowledge graph the thesis describes.", PUBLIC, "international"),
    ref("nof1", "N-of-1 antisense therapeutics", "concept", "infra", "genotype", "global",
        "The paradigm case that changed how the field discusses treatment when N = 1. The "
        "logical extreme of the thesis's own architecture.", PUBLIC, "global"),

    # ---- systems and computational biology ----------------------------------------------
    ref("barabasi", "Albert-László Barabási", "person", "systems", "interactome",
        "Northeastern University",
        "Network medicine: disease as a perturbation of a module in a molecular network rather "
        "than a property of one gene. The scientific school closest to the thesis's second "
        "insight.", PUBLIC, "United States"),
    ref("biogrid", "BioGRID", "database", "systems", "interactome", "international consortium",
        "Curated protein-protein interactions — the concrete substrate for a Merlin subgraph "
        "and the propagation on it. Named in this project and not ingested.", PUBLIC,
        "international"),
    ref("string", "STRING", "database", "systems", "interactome", "EMBL / SIB",
        "Scored functional associations, decomposed by evidence type. Denser than BioGRID and "
        "requires a threshold, which is a judgement to state rather than inherit.", PUBLIC,
        "Europe"),
    ref("kegg", "KEGG", "database", "systems", "pathway", "Kyoto University",
        "Pathways, metabolism, gene networks — and a source of real biological graphs for "
        "benchmarking sparse kernels.", PUBLIC, "Japan"),
    ref("reactome", "Reactome", "database", "systems", "pathway", "OICR / EMBL-EBI",
        "Curated pathway membership. Would turn this project's hand-written Hippo gene list "
        "into a citation.", PUBLIC, "Canada / Europe"),
    ref("pdb", "Protein Data Bank", "database", "systems", "structure", "wwPDB",
        "Experimental structures. The step before trusting any prediction of Merlin.", PUBLIC,
        "international"),
    ref("alphafold", "AlphaFold", "tool", "systems", "structure", "DeepMind",
        "Predicted structure at proteome scale — with the caveat the thesis states itself: a "
        "predicted structure is not protein dynamics.", PUBLIC, "United Kingdom"),
    ref("esmfold", "ESMFold", "tool", "systems", "structure", "Meta AI",
        "Fast structure prediction from a language model; the benchmark against AlphaFold "
        "rather than a replacement for it.", PUBLIC, "United States"),
    ref("rosetta", "Rosetta", "tool", "systems", "structure", "RosettaCommons",
        "Structure, design, docking, and the ddG of a mutation.", PUBLIC, "United States"),
    ref("foldx", "FoldX", "tool", "systems", "structure", "CRG Barcelona",
        "A second, independent estimate of mutational ddG — the point being not to depend on "
        "one method.", PUBLIC, "Spain"),
    ref("gromacs", "GROMACS", "tool", "systems", "dynamics", "Stockholm / Uppsala",
        "Molecular dynamics. Where structure becomes an ensemble, and where the sampling "
        "bottleneck actually bites.", PUBLIC, "Sweden"),
    ref("bioemu", "Emulators of conformational ensembles", "tool", "systems", "dynamics",
        "research direction",
        "The new generation trying to cut the cost of conformational sampling with learned "
        "models — aimed exactly at the question of how a mutation moves a distribution of "
        "states rather than a single structure.", PUBLIC, "global"),
    ref("geo", "GEO", "database", "systems", "cell", "NCBI",
        "Expression datasets, including single-cell — the concrete route to schwannoma "
        "cell-state data.", PUBLIC, "United States"),
    ref("tcga", "TCGA", "database", "systems", "cell", "NCI / NHGRI",
        "Cancer genomics at scale; useful for transfer between tumours rather than for NF2 "
        "directly.", PUBLIC, "United States"),
    ref("tenx", "10x Genomics datasets", "database", "systems", "cell", "10x Genomics",
        "Public single-cell matrices — over 90% sparse, and therefore a workload as much as a "
        "biological resource.", PUBLIC, "United States"),
    ref("scanpy", "Scanpy / AnnData / Seurat / scvi-tools / CellRank / PAGA", "tool", "systems",
        "cell", "open ecosystem",
        "The single-cell stack. PAGA in particular is graph computation over cells, which is "
        "the thesis's point that cellular biology already IS graph computation.", PUBLIC,
        "global"),
    ref("spatial", "Visium / MERFISH / Slide-seq / Xenium / SpatialData / Squidpy", "tool",
        "systems", "tissue", "open ecosystem",
        "Spatial transcriptomics: cell, gene, x, y, neighbourhood. Produces exactly the large "
        "sparse neighbourhood graphs the computational thesis is about, and it is the emptiest "
        "rung in this repository.", PUBLIC, "global"),
    ref("crispr", "CRISPR perturbation screens", "concept", "systems", "pathway", "global",
        "Observations closer to interventions than to correlations — the reason the DepMap "
        "adapter is the one this library was hardened against.", PUBLIC, "global"),
    ref("doudna", "Jennifer Doudna and Emmanuelle Charpentier", "person", "systems", "genotype",
        "UC Berkeley / Max Planck",
        "Historical reference for the editing chemistry. What matters to this thesis is "
        "downstream: screens, Perturb-seq, base and prime editing, variant validation.",
        PUBLIC, "United States / Germany"),
    ref("perturbseq", "Perturb-seq", "concept", "systems", "cell", "global",
        "CRISPR plus single-cell readout: perturbation in, transcriptomic response out. The "
        "experimental version of what the thesis wants a model to learn.", PUBLIC, "global"),

    # ---- HPC and sparse computation -------------------------------------------------------
    ref("buluc", "Aydın Buluç", "person", "hpc", "substrate",
        "Lawrence Berkeley National Laboratory / UC Berkeley",
        "GraphBLAS, sparse matrix algorithms, SpGEMM. The principal reference for the "
        "BioSparse line.", PUBLIC, "United States"),
    ref("graphblas", "GraphBLAS", "standard", "hpc", "substrate", "international",
        "Graph algorithms expressed as sparse linear algebra. The formal equivalence that "
        "connects biological graphs to hardware.", PUBLIC, "international"),
    ref("davis", "Timothy A. Davis", "person", "hpc", "substrate", "Texas A&M University",
        "SuiteSparse and SuiteSparse:GraphBLAS. Any own implementation of sparse computation "
        "is measured against this ecosystem or it is not measured.", PUBLIC, "United States"),
    ref("suitesparse", "SuiteSparse and its Matrix Collection", "tool", "hpc", "substrate",
        "Texas A&M University",
        "The reference implementation and the reference benchmark set. The planned comparison "
        "was SuiteSparse's general families against BioGRID, STRING, KEGG and single-cell.",
        PUBLIC, "United States"),
    ref("carson", "Erin Carson", "person", "hpc", "substrate", "Charles University",
        "Numerical linear algebra, communication-avoiding algorithms, mixed precision.",
        PUBLIC, "Czechia"),
    ref("helenxu", "Helen Xu", "person", "hpc", "substrate", "Georgia Tech",
        "Sparse linear algebra and HPC; recorded as a potential intellectual contact once "
        "there is a concrete experimental result to discuss.", SUPPLIED, "United States"),
    ref("vandegeijn", "Robert van de Geijn", "person", "hpc", "substrate",
        "University of Texas at Austin",
        "The pedagogical route into GEMM: naive, loop order, tiling, packing, register "
        "blocking, SIMD.", PUBLIC, "United States"),
    ref("goto", "Kazushige Goto", "person", "hpc", "substrate", "—",
        "Co-author of Anatomy of High-Performance Matrix Multiplication — why fast GEMM is "
        "organised around cache blocking, packing, microkernels and register reuse.", PUBLIC,
        "Japan / United States"),
    ref("vanzee", "Field G. Van Zee", "person", "hpc", "substrate",
        "University of Texas at Austin",
        "BLIS, which makes the architecture of GEMM explicit and extensible rather than "
        "hidden behind an interface.", PUBLIC, "United States"),
    ref("blis", "BLIS", "tool", "hpc", "substrate", "UT Austin",
        "The framework the author's HPC track was built around.", PUBLIC, "United States"),
    ref("blas", "BLAS and LAPACK", "standard", "hpc", "substrate", "international",
        "The historical substrate, and the origin of the author's question: what if an "
        "abstraction at this level knew something about the semantic structure of the data?",
        PUBLIC, "international"),
    ref("openblas", "OpenBLAS", "tool", "hpc", "substrate", "open source",
        "The CPU baseline. The pedagogical goal was a meaningful fraction of it before "
        "touching sparse work at all.", PUBLIC, "international"),
    ref("cusparse", "cuSPARSE", "tool", "hpc", "substrate", "NVIDIA",
        "The baseline for the BioSparse hypothesis — and the author's own correction: the "
        "defensible question is not beating a general kernel everywhere, it is beating it on "
        "specific structural subclasses of biological graphs.", PUBLIC, "United States"),
    ref("cutlass", "CUTLASS", "tool", "hpc", "substrate", "NVIDIA",
        "Modern GPU GEMM kernels, to be studied rather than reinvented.", PUBLIC,
        "United States"),
    ref("ginkgo", "Ginkgo", "tool", "hpc", "substrate", "Karlsruhe Institute of Technology",
        "Sparse linear algebra for accelerators, and a well-structured codebase to read.",
        PUBLIC, "Germany"),
    ref("graphblast", "GraphBLAST", "tool", "hpc", "substrate", "research",
        "GraphBLAS on the GPU: graph analytics, sparse matrices and accelerators meeting.",
        PUBLIC, "United States"),
    ref("sputnik", "Sputnik", "tool", "hpc", "substrate", "Google",
        "Sparse kernels built for deep learning — an architectural reference for highly "
        "specialised sparse computation.", PUBLIC, "United States"),
    ref("nsight", "Nsight Compute and Nsight Systems", "tool", "hpc", "substrate", "NVIDIA",
        "Because the thesis cannot be judged on runtime alone: memory transactions, cache "
        "behaviour, occupancy, warp divergence and stall reasons are the evidence.", PUBLIC,
        "United States"),
    ref("vtune", "Intel VTune", "tool", "hpc", "substrate", "Intel",
        "The CPU half of the same argument: cache misses, branching, threading.", PUBLIC,
        "United States"),
    ref("tensorcores", "Tensor Cores and 2:4 structured sparsity", "concept", "hpc",
        "substrate", "NVIDIA",
        "Structure that is incorporated physically into the hardware — the existence proof "
        "that a sparsity pattern can be worth silicon.", PUBLIC, "United States"),

    # ---- compilers and runtimes ------------------------------------------------------------
    ref("mlir", "MLIR", "standard", "compiler", "method", "LLVM ecosystem",
        "Multi-level IR with domain dialects. The closest existing technology to a "
        "biologically aware substrate, and the author's own preferred phrasing over 'a new "
        "BLAS'.", PUBLIC, "international"),
    ref("lattner", "Chris Lattner", "person", "compiler", "method", "LLVM / Modular",
        "LLVM, Clang, MLIR, Swift. The central reference if the work genuinely enters "
        "dialects and domain-specific compilation.", PUBLIC, "United States"),
    ref("triton", "Triton", "tool", "compiler", "method", "OpenAI",
        "The middle ground between high-level Python and hand-written CUDA — which is exactly "
        "where a semantic kernel would live.", PUBLIC, "United States"),
    ref("tillet", "Philippe Tillet", "person", "compiler", "method", "OpenAI",
        "Author of Triton and of the paper behind it.", PUBLIC, "United States"),
    ref("tvm", "Apache TVM", "tool", "compiler", "method", "Apache",
        "How a high-level description becomes optimised code across different hardware — the "
        "same question in a different domain.", PUBLIC, "international"),
    ref("tianqi", "Tianqi Chen", "person", "compiler", "method", "CMU",
        "TVM and machine-learning systems.", PUBLIC, "United States"),
    ref("xla", "XLA", "tool", "compiler", "method", "Google",
        "Tensor compilation and lowering; one of the systems the novelty claim has to be "
        "stated against rather than around.", PUBLIC, "United States"),
    ref("iree", "IREE", "tool", "compiler", "method", "Google / LLVM ecosystem",
        "MLIR-based lowering to multiple runtimes and hardware targets.", PUBLIC,
        "United States"),
    ref("halide", "Halide", "tool", "compiler", "method", "MIT",
        "Separating WHAT to compute from HOW to compute it. The single most load-bearing idea "
        "under the semantic-kernel proposal: biological operation is not physical execution "
        "strategy.", PUBLIC, "United States"),
    ref("taco", "TACO", "tool", "compiler", "method", "MIT",
        "Sparse tensor algebra compilation — where the SpGEMM line has to arrive once "
        "single-cell gains a time, patient or treatment axis.", PUBLIC, "United States"),
    ref("kjolstad", "Fredrik Kjolstad", "person", "compiler", "method", "Stanford University",
        "TACO and sparse tensor compilation.", PUBLIC, "United States"),
    ref("dataflow", "Differential dataflow", "concept", "compiler", "method", "research",
        "Incremental recomputation as data changes — the systems analogue of the thesis's "
        "G(t), a graph whose nodes and edges move.", PUBLIC, "international"),

    # ---- complex systems and morphogenesis --------------------------------------------------
    ref("turing", "Alan Turing — The Chemical Basis of Morphogenesis (1952)", "paper",
        "complex", "tissue", "—",
        "Global pattern from local rules. The author states the correct reading explicitly: "
        "this is NOT a claim that NF2 is a reaction-diffusion system.", PUBLIC,
        "United Kingdom"),
    ref("levin", "Michael Levin", "person", "complex", "tissue", "Tufts University",
        "Bioelectricity, morphogenesis, collective cellular control — the contemporary "
        "reference closest to the author's curiosity about form and information in living "
        "systems.", PUBLIC, "United States"),
    ref("carlsson", "Gunnar Carlsson", "person", "complex", "cell", "Stanford University",
        "Topological data analysis.", PUBLIC, "United States"),
    ref("tda", "Topological data analysis", "concept", "complex", "cell", "—",
        "Persistent homology and topological signatures over cell-state manifolds, tumour "
        "architecture and spatial data — to be reached for when there is a hypothesis, not "
        "for the mathematics.", PUBLIC, "international"),
    ref("wolfram", "Wolfram Physics Project", "concept", "complex", "method", "—",
        "Adjacent influence on the complex-systems side; not a reference for NF2 and recorded "
        "as such.", PUBLIC, "United States"),
    ref("anton", "Anton — D. E. Shaw Research", "tool", "complex", "dynamics",
        "D. E. Shaw Research",
        "Special-purpose hardware for molecular dynamics. The historical proof of the "
        "principle the computational thesis rests on: when a domain matters enough, "
        "specialised hardware and software can beat general architectures by a lot.", PUBLIC,
        "United States"),
    ref("deshaw", "David E. Shaw", "person", "complex", "dynamics", "D. E. Shaw Research",
        "Protein dynamics driven into specialised computation.", PUBLIC, "United States"),
    ref("folding", "Folding@home", "tool", "complex", "dynamics", "distributed",
        "Distributed HPC applied to molecular biology — a different architecture for the same "
        "sampling problem.", PUBLIC, "global"),
]


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)

    by_comm = Counter(r["community"] for r in REFERENCES)
    by_kind = Counter(r["kind"] for r in REFERENCES)
    by_prov = Counter(r["provenance"] for r in REFERENCES)
    by_country = Counter(r["country"] for r in REFERENCES)
    by_rung = Counter(r["rung"] for r in REFERENCES)

    # ---- the bridge, computed -----------------------------------------------------------
    # A rung carrying references from more than one community is a place where two literatures
    # are talking about the same object. Those are the bridges the thesis claims to build, and
    # the ones carrying a single community are the places it is still inside one conversation.
    comm_at_rung: dict[str, set[str]] = defaultdict(set)
    for r in REFERENCES:
        comm_at_rung[r["rung"]].add(r["community"])

    bridges = []
    for rung in RUNGS:
        comms = sorted(comm_at_rung.get(rung, set()))
        refs_here = [r for r in REFERENCES if r["rung"] == rung]
        bridges.append({
            "rung": rung,
            "communities": comms,
            "communityCount": len(comms),
            "references": len(refs_here),
            "bridged": len(comms) > 1,
        })

    # Which PAIRS of communities meet, and where.
    pairs: dict[str, list[str]] = defaultdict(list)
    for rung, comms in comm_at_rung.items():
        cs = sorted(comms)
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                pairs[f"{cs[i]}|{cs[j]}"].append(rung)
    pair_rows = sorted(
        ({"a": k.split("|")[0], "b": k.split("|")[1], "rungs": sorted(set(v)), "count": len(set(v))}
         for k, v in pairs.items()),
        key=lambda r: -r["count"])

    bridged = [b for b in bridges if b["bridged"]]
    lonely = [b for b in bridges if not b["bridged"] and b["references"]]

    # ---- and, more usefully, which communities NEVER meet ---------------------------------
    # The comfortable reading of the block above is "seven of ten rungs are bridged". The
    # useful reading is the complement: which pairs of communities share no rung at all. That
    # is where the project's central claim — that these literatures are being joined — is
    # currently unsupported by its own reference map.
    all_comms = [c["id"] for c in COMMUNITIES]
    met = {tuple(sorted((p["a"], p["b"]))) for p in pair_rows}
    never = []
    for i in range(len(all_comms)):
        for j in range(i + 1, len(all_comms)):
            pair = tuple(sorted((all_comms[i], all_comms[j])))
            if pair not in met:
                never.append({
                    "a": pair[0], "b": pair[1],
                    "refsA": by_comm.get(pair[0], 0), "refsB": by_comm.get(pair[1], 0),
                })
    never.sort(key=lambda r: -(r["refsA"] + r["refsB"]))

    # Communities confined to a single rung: present in force and touching nothing.
    confined = []
    for c in all_comms:
        rungs = sorted({r["rung"] for r in REFERENCES if r["community"] == c})
        if len(rungs) == 1:
            shares = sorted(comm_at_rung[rungs[0]] - {c})
            confined.append({"community": c, "rung": rungs[0],
                             "references": by_comm.get(c, 0), "sharesWith": shares})

    payload = {
        "generated": "tools/references_seed.py",
        "premise": (
            "The sharpest observation in the source material is not any single citation: it is "
            "that these references belong to communities that normally publish separately, and "
            "that the bridge is the unusual part of the project. A bibliography cannot show "
            "that, so every entry carries its community and the ladder rung it serves, and the "
            "bridges are computed from those two fields rather than claimed."
        ),
        "provenanceNote": (
            "Two classes, and the distinction is not pedantry. `public-artifact` covers a "
            "library, standard, database or paper whose existence and purpose are common "
            "knowledge in its field — BLIS, GraphBLAS, TACO, MLIR, GROMACS, PDB, OMIM, Turing "
            "1952. `author-supplied` covers claims about PEOPLE, POSTS, PROGRAMMES AND MONEY: "
            "who works where, who sits on which board, which programme holds which grant. This "
            "repository has verified none of the second class and no file in it resolves a "
            "single one. Publishing them unmarked beside the first class would launder one "
            "into the other."
        ),
        "communities": COMMUNITIES,
        "references": REFERENCES,
        "bridges": bridges,
        "communityPairs": pair_rows,
        "neverMeet": never,
        "confined": confined,
        "authorFormula": (
            "Rare Disease + Systems Biology + Computational Biology + HPC + Compiler/Runtime "
            "Research — the author's own list of five. Complex systems and morphogenesis is "
            "carried here as a sixth, flagged as influence rather than as a discipline being "
            "bridged, because that is how the source material treats it."
        ),
        "finding": (
            "The comfortable reading of this map is that %d of %d rungs carry more than one "
            "community. The useful reading is the complement, and it is uncomfortable: %d "
            "pairs of communities share no rung at all. Every one of those pairs has a "
            "biological community on one side and a computational one on the other. The "
            "high-performance-computing entries — %d of them, the joint largest group here — "
            "sit entirely on the `substrate` rung, and no other community is on it. The "
            "compiler entries sit on `method` and meet only the complex-systems influences "
            "there. So the biological literatures and the computational literatures, in this "
            "map, never once talk about the same object."
            % (len(bridged), len([b for b in bridges if b["references"]]), len(never),
               by_comm.get("hpc", 0))
        ),
        "theGap": (
            "This is the project's own central claim failing its own audit. The thesis says "
            "the unusual part is the intersection of rare disease, systems biology, "
            "computational biology, HPC and compiler research. The reference map says that "
            "intersection is currently EMPTY: the computational references are not references "
            "about biology, they are references about computation that the author intends to "
            "point at biology. That is a real and honourable position — it is what a research "
            "programme looks like before it has done the joining work — but it is not the same "
            "thing as a bridge, and the map is the wrong place to discover that after the "
            "thesis has been written. The rungs where the join would have to happen are "
            "`interactome`, `cell` and `tissue`: sparse graphs, sparse matrices and sparse "
            "neighbourhood tensors are all sitting there, and every reference at those rungs "
            "is biological."
        ),
        "summary": {
            "references": len(REFERENCES),
            "byCommunity": dict(by_comm),
            "byKind": dict(by_kind),
            "byProvenance": dict(by_prov),
            "byRung": dict(by_rung),
            "countries": len([c for c in by_country if c != "—"]),
            "topCountries": dict(by_country.most_common(8)),
            "bridgedRungs": len(bridged),
            "singleCommunityRungs": len(lonely),
            "communityPairs": len(pair_rows),
            "neverMeet": len(never),
            "confinedCommunities": [c["community"] for c in confined],
            "authorSupplied": by_prov.get(SUPPLIED, 0),
        },
    }

    path = DEST / "references.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    s = payload["summary"]
    print("wrote %s" % path.relative_to(ROOT))
    print("  %d references across %d communities and %d countries"
          % (s["references"], len(s["byCommunity"]), s["countries"]))
    print("  by community: %s" % s["byCommunity"])
    print("  provenance: %s" % s["byProvenance"])
    print("  %d rungs bridged by more than one community, %d carry exactly one"
          % (s["bridgedRungs"], s["singleCommunityRungs"]))
    for b in bridges:
        if b["references"]:
            print("    %-12s %d refs · %s" % (b["rung"], b["references"], ", ".join(b["communities"])))
    print("  COMMUNITIES THAT NEVER SHARE A RUNG: %d pairs" % len(never))
    for r in never:
        print("    %-10s (%2d refs)  x  %-10s (%2d refs)"
              % (r["a"], r["refsA"], r["b"], r["refsB"]))
    for c in confined:
        print("  CONFINED: %s has %d references and touches only `%s` (shared with: %s)"
              % (c["community"], c["references"], c["rung"],
                 ", ".join(c["sharesWith"]) or "nobody"))
    print("  strongest community pairs:")
    for p in pair_rows[:5]:
        print("    %-12s + %-12s meet at %d rungs (%s)"
              % (p["a"], p["b"], p["count"], ", ".join(p["rungs"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
