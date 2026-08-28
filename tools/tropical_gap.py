"""How much the catalogues hold about the diseases that dominate tropical life.

WHY THIS EXISTS, AND WHAT IT IS NOT ACCUSING ANYONE OF.

Every layer of this repository — the rare-disease atlas, the gene navigator, the gap
patterns — reads three catalogues: HPO's phenotype annotations, HPO's gene-to-disease table,
and Orphanet's prevalence file. Those catalogues are, by construction and by charter,
catalogues of **Mendelian and rare disease**. Nobody promised they would describe malaria.

That is precisely the point. The tooling the entire field builds on — the ontologies, the
phenotype vocabularies, the gene-disease joins, and every dashboard downstream of them,
including this one — inherits a shape. Diseases caused by a parasite, a virus or a vector do
not fit that shape, so they arrive with no gene, no phenotype frequency and no denominator,
and every method built on the join treats them as absent rather than as out of scope.

A Brazilian clinician looking up Chagas disease in a genomics tool finds nothing. This
measures the nothing, so it stops being invisible.

## What is counted

For each disease, four things the rest of the site depends on:

    MONDO term          does the ontology name it at all
    HPO annotations     phenotype rows: signs, onset, inheritance
    gene links          entries in genes_to_disease.txt
    Orphanet prevalence a prevalence record in a real band

Matching is by MONDO name and its exact synonyms, and MONDO's cross-references carry the
OMIM and ORPHA identifiers the other two files are keyed by. Where a disease has several
MONDO terms — malaria has thirteen, one per species and severity — they are summed and the
count of terms is reported, because "thirteen ontology terms and zero phenotype rows" is a
sharper statement than either number alone.

## The comparison that makes it mean something

A raw zero proves nothing without a denominator. So the same four measures are computed for
a **reference set**: the twelve rare Mendelian diseases this repository already profiles in
depth. Those are rare by definition, several are ultra-rare, and they are exactly the kind of
disease these catalogues exist for. If a disease affecting six million people has a hundredth
of the annotation of one affecting a few thousand, that gap is the finding.

Run: `python tools/tropical_gap.py`
"""

from __future__ import annotations

import csv
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ontology"
DEST = ROOT / "out" / "rare" / "tropical_gap.json"

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from build_atlas import load_prevalence  # noqa: E402

# The diseases, grouped by how they reach a person. Names are the ones MONDO uses; the
# matcher takes a term whose name equals or begins with one of these, which is what picks up
# "malaria" plus its thirteen species- and severity-specific children.
#
# THE LIST IS AUTHORED, and that is a limitation with a name: it comes from the WHO neglected
# tropical disease list plus the major vector-borne diseases, and a disease absent from this
# list is absent from this figure. It is not derived from the data, because no field in these
# catalogues says "neglected".
GROUPS: dict[str, list[str]] = {
    "vector-borne": [
        "malaria", "dengue", "chikungunya", "zika virus disease", "yellow fever",
        "leishmaniasis", "Chagas disease", "lymphatic filariasis", "onchocerciasis",
        "African trypanosomiasis", "West Nile", "Japanese encephalitis", "Oropouche",
        "Mayaro virus disease",
    ],
    "water and soil": [
        "schistosomiasis", "soil-transmitted helminthiasis", "ascariasis", "trichuriasis",
        "hookworm disease", "dracunculiasis", "cysticercosis", "echinococcosis",
        "fascioliasis", "paragonimiasis",
    ],
    "bacterial and other": [
        "leprosy", "Buruli ulcer", "trachoma", "yaws", "noma", "mycetoma", "scabies",
        "snakebite envenoming", "rabies", "taeniasis",
    ],
    "respiratory pandemic": [
        "COVID-19", "long COVID-19", "tuberculosis",
    ],
}

# The comparison set: the twelve diseases this repository already profiles, which are the
# kind of disease these catalogues were built for.
REFERENCE = [
    "Duchenne muscular dystrophy", "cystic fibrosis", "spinal muscular atrophy",
    "neurofibromatosis type 2", "Dravet syndrome", "CDKL5 disorder",
    "Zellweger syndrome", "fibrodysplasia ossificans progressiva", "alkaptonuria",
    "systemic lupus erythematosus", "Rett syndrome", "sickle cell anemia",
]

OBSOLETE = re.compile(r"^obsolete\b", re.I)


def load_mondo() -> list[dict]:
    """Every non-obsolete MONDO term with its name, synonyms and cross-references."""
    terms: list[dict] = []
    block: list[str] = []
    text = (DATA / "mondo.obo").read_text(encoding="utf-8", errors="replace")
    for raw in text.split("[Term]"):
        block = raw.split("\n")
        cur: dict = {"xrefs": [], "synonyms": []}
        for line in block:
            if line.startswith("id: "):
                cur.setdefault("id", line[4:].strip())
            elif line.startswith("name: "):
                cur["name"] = line[6:].strip()
            elif line.startswith("xref: "):
                cur["xrefs"].append(line[6:].strip().split(" ")[0])
            elif line.startswith("synonym: "):
                m = re.search(r'"([^"]+)"', line)
                if m:
                    cur["synonyms"].append(m.group(1))
            elif line.startswith("is_obsolete: true"):
                cur["obsolete"] = True
        if cur.get("id") and cur.get("name") and not cur.get("obsolete"):
            if not OBSOLETE.match(cur["name"]):
                terms.append(cur)
    return terms


def load_hpo_counts() -> tuple[Counter, Counter]:
    """Phenotype rows per disease id, and how many carry a k/n frequency."""
    rows: Counter = Counter()
    withDenom: Counter = Counter()
    path = DATA / "phenotype.hpoa"
    with path.open(encoding="utf-8", errors="replace") as fh:
        idx: dict[str, int] = {}
        for line in fh:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if not idx:
                if p and p[0] == "database_id":
                    idx = {n: i for i, n in enumerate(p)}
                continue
            if len(p) <= max(idx.values()):
                continue
            did = p[idx["database_id"]]
            rows[did] += 1
            if "/" in p[idx["frequency"]]:
                withDenom[did] += 1
    return rows, withDenom


def load_gene_links() -> Counter:
    counts: Counter = Counter()
    with (DATA / "genes_to_disease.txt").open(encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            did = (row.get("disease_id") or "").strip()
            if did:
                counts[did] += 1
    return counts


def profile(names: list[str], terms: list[dict], hpo: Counter, denom: Counter,
            genes: Counter, prev: dict) -> list[dict]:
    """One record per named disease, summing over every MONDO term that matches it."""
    out: list[dict] = []
    for want in names:
        low = want.lower()
        matched = [
            t for t in terms
            if t["name"].lower() == low
            or t["name"].lower().startswith(low + " ")
            or low in [s.lower() for s in t["synonyms"]]
            or (low in t["name"].lower() and len(low) > 6)
        ]
        ids: set[str] = set()
        for t in matched:
            for x in t["xrefs"]:
                if x.startswith(("OMIM:", "ORPHA:", "Orphanet:", "DECIPHER:")):
                    ids.add(x.replace("Orphanet:", "ORPHA:"))

        annotations = sum(hpo.get(i, 0) for i in ids)
        with_denom = sum(denom.get(i, 0) for i in ids)
        gene_links = sum(genes.get(i, 0) for i in ids)
        prevalence = any(
            (prev.get(i, {}).get("prevalence") or "").strip()
            not in ("", "Unknown", "Not yet documented")
            for i in ids
        )

        out.append({
            "name": want,
            "mondoTerms": len(matched),
            "xrefIds": len(ids),
            "annotations": annotations,
            "signsWithDenominator": with_denom,
            "geneLinks": gene_links,
            "prevalence": prevalence,
        })
    return out


def main() -> int:
    print("reading MONDO…", flush=True)
    terms = load_mondo()
    print("reading HPO annotations…", flush=True)
    hpo, denom = load_hpo_counts()
    genes = load_gene_links()
    prev = load_prevalence()

    groups = {
        key: profile(names, terms, hpo, denom, genes, prev)
        for key, names in GROUPS.items()
    }
    reference = profile(REFERENCE, terms, hpo, denom, genes, prev)

    tropical = [d for rows in groups.values() for d in rows]
    named = [d for d in tropical if d["mondoTerms"] > 0]
    silent = [d for d in named if d["annotations"] == 0]

    def _median(v: list[int]) -> float:
        s = sorted(v)
        return s[len(s) // 2] if s else 0

    payload = {
        "generated": "tools/tropical_gap.py",
        "premise": (
            "HPO and Orphanet are catalogues of Mendelian and rare disease, by charter. "
            "Nobody promised they would describe malaria. That is the point: the ontologies "
            "and gene-disease joins the whole field builds on inherit a shape, and diseases "
            "caused by a parasite, a virus or a vector do not fit it — so they arrive as "
            "absent rather than as out of scope, and every method downstream treats them the "
            "same way."
        ),
        "listIsAuthored": (
            "The disease list comes from the WHO neglected tropical disease list plus the "
            "major vector-borne diseases. No field in these catalogues says 'neglected', so "
            "the list could not be derived from the data. A disease missing from the list is "
            "missing from this figure."
        ),
        "measures": ["mondoTerms", "annotations", "signsWithDenominator", "geneLinks",
                     "prevalence"],
        "groups": groups,
        "reference": reference,
        "summary": {
            "diseases": len(tropical),
            "namedByMondo": len(named),
            "withNoAnnotation": len(silent),
            "silentNames": [d["name"] for d in silent],
            "medianAnnotationsTropical": _median([d["annotations"] for d in named]),
            "medianAnnotationsReference": _median([d["annotations"] for d in reference]),
            "medianGeneLinksTropical": _median([d["geneLinks"] for d in named]),
            "medianGeneLinksReference": _median([d["geneLinks"] for d in reference]),
        },
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    s = payload["summary"]
    print(f"\n{s['diseases']} diseases on the list; {s['namedByMondo']} named by MONDO")
    print(f"{s['withNoAnnotation']} have NO phenotype annotation at all:")
    for n in s["silentNames"]:
        print(f"    {n}")
    print(f"\nmedian phenotype rows   tropical {s['medianAnnotationsTropical']:>6}"
          f"   reference {s['medianAnnotationsReference']:>6}")
    print(f"median gene links       tropical {s['medianGeneLinksTropical']:>6}"
          f"   reference {s['medianGeneLinksReference']:>6}")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
