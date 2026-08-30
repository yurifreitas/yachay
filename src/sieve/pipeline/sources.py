"""The public sources this project ingests, declared once.

WHY THIS FILE EXISTS. The rare-disease seeds in `tools/*_seed.py` were written from
working knowledge and are marked as demonstrations. That is honest at 32 genes and
dishonest at 8,000 diseases: hand-authoring a reference database is not scale, it is
fabrication with a bigger surface area. The way to cover the field is to ingest the field's
own catalogues.

All eleven are public, downloadable without credentials, and versioned by their publishers. Every URL was resolved before it was added: this repository has a finding about numbers nobody checked (docs/audit.md A11), and a registry of broken links would be the same defect wearing different clothes.
Each entry records **what it gives us**, because a source with no stated purpose is a
download nobody maintains.

LICENCE, and it is not decoration. These have different terms:

  * HPO, MONDO, Reactome, STRING and ClinVar are permissively licensed and
    redistributable (CC BY 4.0, CC0, and US public domain respectively).
  * **gnomAD** is freely available for any use, but the terms for redistributing a
    DERIVATIVE are worth re-reading before shipping one, so it is marked non-
    redistributable here — the conservative reading, deliberately.
  * **Orphanet data is CC BY-ND 4.0 — no derivatives.** We may use and cite it; we may not
    redistribute a modified version. Anything derived from it stays local and is described
    rather than shipped.
  * **Human Protein Atlas is CC BY-SA 4.0** — attribution and share-alike.

So `data/ontology/` is gitignored and the artefacts we publish carry counts and summaries
rather than copies. That is a constraint on the design, not a footnote to it.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import paths

ONTOLOGY = paths.DATA / "ontology"


@dataclass(frozen=True)
class Source:
    key: str
    name: str
    url: str
    filename: str
    approx_mb: float
    gives: str
    licence: str
    redistributable: bool

    @property
    def dest(self):
        return ONTOLOGY / self.filename


SOURCES: tuple[Source, ...] = (
    Source(
        key="hpo_genes",
        name="HPO gene-to-disease",
        url="https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/genes_to_disease.txt",
        filename="genes_to_disease.txt",
        approx_mb=1.5,
        gives="Every gene-disease association HPO curates, keyed by OMIM and ORPHA id. "
              "This is the backbone: it turns a disease list into a gene list.",
        licence="HPO licence (permissive, attribution)",
        redistributable=True,
    ),
    Source(
        key="hpo_annotations",
        name="HPO disease annotations",
        url="https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/phenotype.hpoa",
        filename="phenotype.hpoa",
        approx_mb=35.0,
        gives="Disease-to-phenotype annotations, and the authoritative count of annotated "
              "rare diseases. Its own header states the scale: 8,574 OMIM, 4,337 Orphanet.",
        licence="HPO licence (permissive, attribution)",
        redistributable=True,
    ),
    Source(
        key="hpo_terms",
        name="HPO ontology",
        url="https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/hp.obo",
        filename="hp.obo",
        approx_mb=11.0,
        gives="The phenotype vocabulary itself, so a term id can be given a name and a "
              "position in the hierarchy.",
        licence="HPO licence (permissive, attribution)",
        redistributable=True,
    ),
    Source(
        key="hpo_translations",
        name="HPO language profiles",
        url="https://codeload.github.com/obophenotype/hpo-translations/tar.gz/refs/heads/main",
        filename="hpo-translations.tar.gz",
        approx_mb=7.4,
        gives="The phenotype vocabulary in fourteen languages besides English, as Babelon "
              "TSV. Ingested because this project publishes in two languages and had no way "
              "to say what a reader loses in either.",
        licence="HPO licence (permissive, attribution)",
        redistributable=True,
    ),
    Source(
        key="clinvar_submissions",
        name="ClinVar submissions",
        url="https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/submission_summary.txt.gz",
        filename="submission_summary.txt.gz",
        approx_mb=387.0,
        gives="Each submitter's classification BESIDE the condition it was made against. The "
              "aggregate file cannot separate a contradiction from two claims about two "
              "different conditions; this one can.",
        licence="US public domain (NCBI)",
        redistributable=True,
    ),
    Source(
        key="gene2pubmed",
        name="NCBI gene2pubmed",
        url="https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2pubmed.gz",
        filename="gene2pubmed.gz",
        approx_mb=40.0,
        gives="Which papers cite which gene. The attention axis - what the field has chosen "
              "to study - set against the burden axis it is supposed to follow.",
        licence="US public domain (NCBI)",
        redistributable=True,
    ),
    Source(
        key="orpha_genes",
        name="Orphanet gene associations",
        url="https://www.orphadata.com/data/xml/en_product6.xml",
        filename="en_product6.xml",
        approx_mb=22.0,
        gives="Orphanet's own gene-disease associations, with the association type "
              "(disease-causing, modifier, candidate) that HPO's flat file loses.",
        licence="CC BY-ND 4.0 — no derivatives may be redistributed",
        redistributable=False,
    ),
    Source(
        key="orpha_prevalence",
        name="Orphanet prevalence",
        url="https://www.orphadata.com/data/xml/en_product9_prev.xml",
        filename="en_product9_prev.xml",
        approx_mb=16.0,
        gives="Prevalence class and geographic scope per disease — the only place the "
              "rare/ultra-rare boundary can be drawn from data rather than assumed.",
        licence="CC BY-ND 4.0 — no derivatives may be redistributed",
        redistributable=False,
    ),
    Source(
        key="orpha_ages",
        name="Orphanet age of onset",
        url="https://www.orphadata.com/data/xml/en_product9_ages.xml",
        filename="en_product9_ages.xml",
        approx_mb=14.0,
        gives="Average age of onset and age of death per disease — the closest thing to a "
              "human-impact axis that comes from data rather than judgement.",
        licence="CC BY-ND 4.0 — no derivatives may be redistributed",
        redistributable=False,
    ),
    Source(
        key="hpa_single_cell",
        name="Human Protein Atlas, single-cell RNA",
        url="https://www.proteinatlas.org/download/tsv/rna_single_cell_type.tsv.zip",
        filename="rna_single_cell_type.tsv.zip",
        approx_mb=16.0,
        gives="Expression of every gene across ~80 human cell types. THIS IS THE CELL AXIS: "
              "it is what turns a gene list into a gene x cell matrix, at the scale the "
              "hand-authored lupus matrix could only gesture at.",
        licence="CC BY-SA 4.0 — attribution and share-alike",
        redistributable=False,
    ),
    # -----------------------------------------------------------------------------------
    # THE SECOND WAVE, added 2026-08-27. Every one closes a question the documentation had
    # already recorded as open, and every URL was resolved before it was written down - the
    # repository has a finding (A11) about numbers nobody checked, and a registry of broken
    # links would be the same defect in a different medium. HGNC belongs in this list and is
    # absent from it because none of its published endpoints resolved on the day; a source
    # that 404s is not registered as if it worked.
    # -----------------------------------------------------------------------------------
    Source(
        key="mondo",
        name="MONDO Disease Ontology",
        url="https://purl.obolibrary.org/obo/mondo.obo",
        filename="mondo.obo",
        approx_mb=53.0,
        gives="The merged disease ontology, and the one identifier space that CROSSES the "
              "others. It is the missing column in tools/lexicon_check.py, which today "
              "reports every MONDO id as `unverifiable` because the ontology was named in "
              "the lexicon and never ingested - a whole column of the identifier matrix "
              "reading 'never checked'.",
        licence="CC BY 4.0",
        redistributable=True,
    ),
    Source(
        key="reactome_pathways",
        name="Reactome — UniProt to pathway, all levels",
        url="https://reactome.org/download/current/UniProt2Reactome_All_Levels.txt",
        filename="UniProt2Reactome_All_Levels.txt",
        approx_mb=90.0,
        gives="Pathway membership per protein. This is what turns the MODULE argument of "
              "docs/references/rare-disease-mechanisms.md from a borrowed claim into a "
              "computable one: §4 proposes that a shortlist should be diversified over "
              "signalling modules rather than genes, and nothing on disk could say which "
              "module a gene is in.",
        licence="CC0 1.0 — public domain dedication",
        redistributable=True,
    ),
    Source(
        key="reactome_hierarchy",
        name="Reactome — pathway hierarchy",
        url="https://reactome.org/download/current/ReactomePathwaysRelation.txt",
        filename="ReactomePathwaysRelation.txt",
        approx_mb=1.0,
        gives="Parent-child relations between pathways, so membership can be rolled up to a "
              "level a person recognises. The same problem the HPO `is_a` walk solved for "
              "signs, on the pathway axis.",
        licence="CC0 1.0 — public domain dedication",
        redistributable=True,
    ),
    Source(
        key="string_links",
        name="STRING — human protein interaction network",
        url="https://stringdb-downloads.org/download/protein.links.v12.0/"
            "9606.protein.links.v12.0.txt.gz",
        filename="9606.protein.links.v12.0.txt.gz",
        approx_mb=83.0,
        gives="A REAL interactome, with confidence scores. tools/interactome_sparse.py "
              "currently measures the HPO gene-disease graph and reports modularity 0.861 "
              "against a degree-matched null - and rare-disease-mechanisms.md §5.2 names the "
              "obvious objection: that graph may be measuring how HPO was curated rather "
              "than how biology is organised. STRING is the independent graph that settles "
              "it, because its edges come from an entirely different evidence base.",
        licence="CC BY 4.0",
        redistributable=True,
    ),
    # -----------------------------------------------------------------------------------
    # THE IDENTIFIER BRIDGES, added 2026-08-28 for the digital-twin work. Without them the
    # three graphs cannot be joined at all: STRING is keyed on Ensembl protein ids, Reactome
    # on UniProt accessions, and HPO on gene symbols. A twin that cannot cross those
    # namespaces is three disconnected pictures, and `docs/references/rare-layers.md` would
    # have no way to say so.
    # -----------------------------------------------------------------------------------
    Source(
        key="string_info",
        name="STRING — protein info (ENSP to gene symbol)",
        url="https://stringdb-downloads.org/download/protein.info.v12.0/"
            "9606.protein.info.v12.0.txt.gz",
        filename="9606.protein.info.v12.0.txt.gz",
        approx_mb=2.0,
        gives="The preferred gene symbol for every STRING protein id. Small, and it is the "
              "difference between an interactome we can join to the disease layer and one "
              "we can only count edges in.",
        licence="CC BY 4.0",
        redistributable=True,
    ),
    Source(
        key="string_aliases",
        name="STRING — protein aliases (UniProt and other namespaces)",
        url="https://stringdb-downloads.org/download/protein.aliases.v12.0/"
            "9606.protein.aliases.v12.0.txt.gz",
        filename="9606.protein.aliases.v12.0.txt.gz",
        approx_mb=19.8,
        gives="STRING id to every other namespace, including UniProt — which is what joins "
              "the interactome to REACTOME, whose pathway file is keyed on UniProt "
              "accessions. This is the bridge that makes the Pathway rung of the thesis "
              "ladder computable rather than named.",
        licence="CC BY 4.0",
        redistributable=True,
    ),
    Source(
        key="gnomad_constraint",
        name="gnomAD v4.1 constraint metrics",
        url="https://storage.googleapis.com/gcp-public-data--gnomad/release/4.1/constraint/"
            "gnomad.v4.1.constraint_metrics.tsv",
        filename="gnomad.v4.1.constraint_metrics.tsv",
        approx_mb=95.0,
        gives="Per-gene mutational constraint (pLI, LOEUF) over 730,947 exomes. This is the "
              "STAGE 6 PRIOR that docs/references/rare-disease-scale.md §4 argues for and "
              "docs/references/rare-disease-ancestry.md §3 warns about: the best structural "
              "prior available for a gene with no literature, and one whose panel is not "
              "ancestry-neutral. Ingesting it makes both the prior and the caveat testable "
              "instead of cited.",
        licence="Freely available for any use; verify the current gnomAD terms before "
                "redistributing a derivative",
        redistributable=False,
    ),
    Source(
        key="cellxgene_collections",
        name="CZ CELLxGENE Discover — collection and dataset index",
        url="https://api.cellxgene.cziscience.com/curation/v1/collections",
        filename="cellxgene_collections.json",
        approx_mb=3.1,
        gives="WHICH DISEASES ANYONE HAS ACTUALLY SEQUENCED AT SINGLE-CELL RESOLUTION, as "
              "MONDO terms. Every other cell-type layer in this repository describes where a "
              "gene is EXPRESSED in a healthy reference — the Human Protein Atlas measures "
              "normal tissue, so a claim that a disease sits on some cell type is a claim "
              "about healthy biology plus an inference. This index says whether cells were "
              "ever collected from a patient with that disease at all, which is the "
              "difference between an inference and an observation. It is also the first "
              "source here that reports the DENOMINATOR of the cell axis: 2,216 datasets "
              "carrying 321 distinct disease terms, of which 1,867 are annotated `normal`.",
        licence="CC-BY 4.0 (metadata); individual datasets carry their own terms",
        redistributable=True,
    ),
    Source(
        key="phenopackets",
        name="Monarch phenopacket-store (GA4GH phenopackets)",
        url="https://github.com/monarch-initiative/phenopacket-store/releases/download/"
            "0.1.27/all_phenopackets.zip",
        filename="all_phenopackets.zip",
        approx_mb=19.4,
        gives="10,377 INDIVIDUAL PATIENTS, in the GA4GH standard, each with their own HPO "
              "terms, causative variant with an ACMG class, age, sex and the PMID they came "
              "from. Every other source here is aggregate: it reports what a disease does. "
              "This reports what happened to a person, and the difference is a denominator. "
              "Crucially, a phenopacket records phenotypes that were EXPLICITLY ABSENT as "
              "well as present - 65% of the assertions in a sample were `excluded` - so a "
              "frequency can be COMPUTED as observed/(observed+excluded) for diseases where "
              "docs/references/rare-disease-scale.md §4b measured that the curated "
              "catalogue has no frequency at all.",
        licence="BSD 3-Clause",
        redistributable=True,
    ),
    Source(
        key="clinvar",
        name="ClinVar variant summary",
        url="https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz",
        filename="variant_summary.txt.gz",
        approx_mb=442.0,
        gives="The variant layer this project does not have at all. Every dossier here "
              "reports a disease's GENES and stops; a clinician's next question is which "
              "variants, of what consequence, with what interpretation - and the allelic "
              "spectrum is also the honest test of whether a 'causal gene' attribution is "
              "one variant in one family or a characterised locus.",
        licence="US Government public domain (NCBI)",
        redistributable=True,
    ),
)

BY_KEY = {s.key: s for s in SOURCES}
TOTAL_MB = sum(s.approx_mb for s in SOURCES)
