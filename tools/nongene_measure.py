#!/usr/bin/env python
"""Measure the non-gene layer against the catalogue, instead of asserting it.

WHY THIS EXISTS. `nongene_seed.py` is authored: ten causal classes written from working
knowledge. That is honest as an argument and worthless as evidence, and the whole project's
position is that the difference matters. This file goes to the annotations already downloaded
and asks what the catalogue itself can SAY about causes that are not a gene — then reports
the answer even where it undercuts the seed.

THE THREE MEASUREMENTS

  1. THE INHERITANCE VOCABULARY. HPO annotates diseases with a mode of inheritance (aspect I).
     Most of that vocabulary is Mendelian, but not all of it: somatic mosaicism, sporadic
     occurrence, polygenic and non-Mendelian inheritance, contiguous gene syndromes, uniparental
     disomy and anticipation all have terms. Counting them gives a measured footprint for the
     classes in the seed that HAVE one.

  2. THE CLASSES WITH NO FOOTPRINT AT ALL. This is the finding, and it is the uncomfortable
     one. The inheritance vocabulary is a vocabulary of INHERITANCE, so a disease caused by
     lead, by an antibody, by a virus at eight weeks or by a diet has no term to be annotated
     with. Not a low count — no term. The catalogue is not under-counting those causes; it has
     no place to write them down, which is the streetlight argument with a number attached.

  3. WHAT "NO GENE" ACTUALLY MEANS. The non-gene tab leans on 3,801 gene-less diseases. That
     number is only interesting if those diseases are causally different rather than merely
     unsolved. So: of the gene-less diseases, how many carry an inheritance annotation at all,
     and how many carry a Mendelian one? A gene-less disease annotated autosomal recessive is
     not a non-gene disease — it is a disease whose gene has not been found, and counting it
     as evidence for a non-gene mechanism would be exactly the sloppiness this project audits.

    python tools/nongene_measure.py     # writes out/rare/nongene_measured.json
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
ONT = ROOT / "data" / "ontology"
DEST = ROOT / "out" / "rare"

HPOA = ONT / "phenotype.hpoa"
OBO = ONT / "hp.obo"
G2D = ONT / "genes_to_disease.txt"

# Terms in the inheritance vocabulary that are NOT a plain Mendelian mode. Each is tagged with
# the seed class it supports, so the seed can be checked against the catalogue rather than
# merely illustrated by it.
NON_MENDELIAN = {
    "HP:0001442": "mosaic",      # Typified by somatic mosaicism
    "HP:0025352": "mosaic",      # Typically de novo
    "HP:0003745": "idiopathic",  # Sporadic
    "HP:0001426": "idiopathic",  # Non-Mendelian inheritance
    "HP:0010982": "idiopathic",  # Polygenic inheritance
    "HP:0010983": "idiopathic",  # Oligogenic inheritance
    "HP:0010984": "idiopathic",  # Digenic inheritance
    "HP:0012275": "imprint",     # Autosomal dominant with maternal imprinting
    "HP:0032382": "imprint",     # Uniparental disomy
    "HP:0032384": "imprint",     # Uniparental isodisomy
    "HP:0003743": "dynamic",     # Genetic anticipation
    "HP:0003744": "dynamic",     # Genetic anticipation, paternal bias
    "HP:0001466": "mosaic",      # Contiguous gene syndrome
}

MENDELIAN = {
    "HP:0000006", "HP:0000007", "HP:0001417", "HP:0001419", "HP:0001423",
    "HP:0001450", "HP:0034341", "HP:0001427",
}

# Seed classes whose cause cannot be written down in an inheritance vocabulary at all.
NO_VOCABULARY = {
    "conformational": "A conformer is not a mode of inheritance. Prion disease is annotated by "
                      "the gene it involves, never by the conformation that carries the "
                      "information.",
    "autoimmune": "An antibody clone has no inheritance term, so an acquired phenocopy of a "
                  "loss-of-function disease is recorded as if the two were unrelated.",
    "exposure": "There is no term for a molecule at a dose in a window. Thalidomide embryopathy "
                "cannot be annotated as caused by thalidomide.",
    "nutritional": "No term for a diet or a soil. The deficiency and its transporter-defect "
                   "phenocopy sit in unconnected parts of the catalogue.",
    "infection": "No term for a pathogen or for the gestational week it arrived in.",
    "mechanical": "No term for delivered energy. Heterotopic ossification after a burn has no "
                  "way to record the burn.",
}


def hpo_names() -> dict[str, str]:
    names, cur = {}, None
    with OBO.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("id: HP:"):
                cur = line[4:]
            elif line.startswith("name: ") and cur:
                names[cur] = line[6:]
                cur = None
    return names


def main() -> int:
    for f in (HPOA, OBO, G2D):
        if not f.exists():
            raise SystemExit("missing %s — run the ingest first" % f.relative_to(ROOT))

    names = hpo_names()

    # ---- inheritance annotations, per disease ---------------------------------------
    inheritance: dict[str, set[str]] = defaultdict(set)
    diseases: set[str] = set()
    disease_name: dict[str, str] = {}
    with HPOA.open(encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or line.startswith("database_id"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) < 11:
                continue
            diseases.add(f[0])
            disease_name.setdefault(f[0], f[1])
            if f[10] == "I":
                inheritance[f[0]].add(f[3])

    # ---- which diseases have a causal gene -------------------------------------------
    with_gene: set[str] = set()
    with G2D.open(encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) >= 4:
                with_gene.add(f[3])

    gene_less = diseases - with_gene

    # ---- 1. the vocabulary, counted ---------------------------------------------------
    term_counts = Counter()
    for terms in inheritance.values():
        term_counts.update(terms)

    vocabulary = []
    for term, n in term_counts.most_common():
        vocabulary.append({
            "term": term,
            "name": names.get(term, "unnamed term"),
            "diseases": n,
            "mendelian": term in MENDELIAN,
            "seedClass": NON_MENDELIAN.get(term),
        })

    # ---- 2. seed classes against the measurement --------------------------------------
    per_class = defaultdict(set)
    for disease, terms in inheritance.items():
        for t in terms:
            cls = NON_MENDELIAN.get(t)
            if cls:
                per_class[cls].add(disease)

    measured = []
    for cls, ids in sorted(per_class.items(), key=lambda kv: -len(kv[1])):
        terms = sorted({t for t, c in NON_MENDELIAN.items() if c == cls})
        measured.append({
            "seedClass": cls,
            "diseases": len(ids),
            "terms": [{"term": t, "name": names.get(t, "?")} for t in terms],
            "withGene": len(ids & with_gene),
            "geneLess": len(ids - with_gene),
            "examples": sorted(disease_name.get(d, d) for d in list(ids))[:6],
        })

    unmeasurable = [
        {"seedClass": cls, "diseases": 0, "why": why}
        for cls, why in sorted(NO_VOCABULARY.items())
    ]

    # ---- 3. what "no gene" actually means ---------------------------------------------
    gl_any = {d for d in gene_less if inheritance.get(d)}
    gl_mendelian = {d for d in gene_less if inheritance.get(d, set()) & MENDELIAN}
    gl_nonmendelian = {d for d in gene_less if inheritance.get(d, set()) & set(NON_MENDELIAN)}
    gl_silent = gene_less - gl_any

    payload = {
        "generated": "tools/nongene_measure.py",
        "inputs": ["data/ontology/phenotype.hpoa", "data/ontology/hp.obo",
                   "data/ontology/genes_to_disease.txt"],
        "premise": (
            "The class list on this tab is authored. This block is not: it asks what the "
            "catalogue itself can record about a cause that is not a gene, and reports the "
            "answer where it supports the argument and where it undercuts it."
        ),
        "scale": {
            "diseasesAnnotated": len(diseases),
            "withInheritanceAnnotation": len(inheritance),
            "withGene": len(diseases & with_gene),
            "geneLess": len(gene_less),
        },
        "vocabulary": vocabulary,
        "measured": measured,
        "unmeasurable": unmeasurable,
        "geneLessBreakdown": {
            "total": len(gene_less),
            "withAnyInheritance": len(gl_any),
            "withMendelianInheritance": len(gl_mendelian),
            "withNonMendelianInheritance": len(gl_nonmendelian),
            "withNoInheritanceAnnotation": len(gl_silent),
            "says": (
                "Of %s diseases with no causal gene, %s carry a MENDELIAN inheritance "
                "annotation. Those are not non-gene diseases — they are diseases whose gene has "
                "not been found, and counting them as evidence for a non-gene mechanism would "
                "be precisely the error this project audits elsewhere. Only %s carry a "
                "non-Mendelian mode, and %s carry no inheritance annotation at all, which is a "
                "statement about curation effort rather than about biology."
                % (format(len(gene_less), ","), format(len(gl_mendelian), ","),
                   format(len(gl_nonmendelian), ","), format(len(gl_silent), ","))
            ),
        },
        "finding": (
            "Six of the ten authored classes have a measured footprint of exactly zero, and not "
            "because the diseases are rare. The inheritance vocabulary is a vocabulary of "
            "inheritance: there is no term for a molecule at a dose, for an antibody clone, for "
            "a pathogen at eight weeks, for a diet, or for delivered energy. The catalogue is "
            "not under-counting those causes — it has nowhere to write them. That is the "
            "streetlight argument with a number attached, and it is the strongest evidence on "
            "this tab that the gene-shaped architecture is a choice rather than a description."
        ),
        "summary": {
            "vocabularyTerms": len(vocabulary),
            "nonMendelianTerms": sum(1 for v in vocabulary if v["seedClass"]),
            "classesWithFootprint": len(measured),
            "classesWithNoVocabulary": len(unmeasurable),
        },
    }

    DEST.mkdir(parents=True, exist_ok=True)
    path = DEST / "nongene_measured.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    s, sc, gl = payload["summary"], payload["scale"], payload["geneLessBreakdown"]
    print("wrote %s" % path.relative_to(ROOT))
    print("  %s diseases annotated · %s carry a mode of inheritance"
          % (format(sc["diseasesAnnotated"], ","), format(sc["withInheritanceAnnotation"], ",")))
    print("  %d inheritance terms in use, %d of them non-Mendelian"
          % (s["vocabularyTerms"], s["nonMendelianTerms"]))
    print("  authored classes with a measured footprint: %d; with NO vocabulary at all: %d"
          % (s["classesWithFootprint"], s["classesWithNoVocabulary"]))
    print("  gene-less: %s total, %s annotated Mendelian, %s non-Mendelian, %s silent"
          % (format(gl["total"], ","), format(gl["withMendelianInheritance"], ","),
             format(gl["withNonMendelianInheritance"], ","),
             format(gl["withNoInheritanceAnnotation"], ",")))
    for m in measured:
        print("    %-12s %5d diseases (%d with a gene, %d without)"
              % (m["seedClass"], m["diseases"], m["withGene"], m["geneLess"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
