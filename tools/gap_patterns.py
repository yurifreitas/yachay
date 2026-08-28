"""Which patterns of emptiness co-occur across the whole rare-disease catalogue.

WHY THIS EXISTS. `docs/references/visualization-canon.md` §7b names three forms the project
needed and had not built, and this is the measurement behind the third of them:

    | Which combinations of gaps co-occur? | sets and intersections | a matrix of dots |
    | **UpSet plot** | Not built. The matrix shows *which* fields are empty per disease; it
    | cannot show which *patterns* of emptiness are common. |

The gap matrix on the rare-disease page shows twelve hand-seeded diseases, one row each. It
answers "what is missing for THIS disease" and cannot answer "what is missing TOGETHER", and
those are different questions with different consequences. A disease missing only its
prevalence is a curation backlog. A disease missing its gene AND its inheritance AND its
prevalence is not under-curated, it is undescribed — and if that combination is the largest
one in the catalogue, the field's problem is not a set of independent gaps to be filled but a
population of diseases about which essentially nothing is recorded.

Nobody had counted. This counts, over every disease in the HPO annotation file.

## The five fields, and why each is a fair test

Each is a field the catalogue HAS somewhere for some diseases, so its absence is a real gap
rather than a category error. Nothing here asks whether a disease has something the sources
have nowhere to record — that is `tools/nongene_measure.py`'s question, and conflating the
two is the mistake that file exists to name.

    gene          genes_to_disease.txt      is a causal gene recorded at all
    inheritance   phenotype.hpoa aspect I   is a mode of inheritance recorded
    onset         phenotype.hpoa aspect C   is an age of onset recorded
    denominator   phenotype.hpoa frequency  does any sign carry k/n rather than a word

## PREVALENCE IS NOT ONE OF THEM, AND FINDING OUT WHY WAS THE FIRST RESULT

The obvious fifth field is prevalence, and the first version of this file included it. It
came out missing for 100 % of the population, which is the shape of a join bug rather than
of a fact — so it was measured instead of assumed. Counting the annotation rows by
identifier prefix:

    OMIM    169,427 rows   9,065 inheritance   103,106 with a k/n frequency
    ORPHA   115,875 rows       0 inheritance         0 with a k/n frequency

The two catalogues annotate different things under the same file. Inheritance, onset and
sign denominators are recorded against OMIM identifiers; prevalence exists only in
Orphanet's own file, keyed by ORPHA code, and the two are not joinable here — Orphanet's
gene product carries OMIM cross-references for GENES, not for disorders.

So the population is the OMIM-coded diseases and prevalence is out. **That split is itself
a finding**: the fields a reader would assume live in one catalogue do not, and any figure
claiming to show "what is known about a rare disease" across all five is joining two
populations without saying so.

## Output

`out/rare/gap_patterns.json`, in the shape the UpSet organism reads: per-field totals, every
non-empty combination with its size, and the count of fully-recorded diseases, which is
reported as a number rather than drawn (it would otherwise be a column that flattens the
rest).

Run: `python tools/gap_patterns.py`
"""

from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from build_atlas import load_gene_disease  # noqa: E402
from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "rare"

# The five fields, in the order they will be drawn. Order is an argument: gene first because
# every later field is usually curated only once a gene is known, so the reader meets the
# fields in the sequence the curation actually happens in.
FIELDS = ["gene", "inheritance", "onset", "denominator"]


def load_annotation_facts() -> tuple[dict[str, set[str]], set[str]]:
    """Per disease: which of the hpoa-derived fields it has, and every disease id seen.

    One pass over a 35 MB file, because three passes for three fields is three chances for
    the three answers to be drawn from different row sets.
    """
    path = BY_KEY["hpo_annotations"].dest
    has: dict[str, set[str]] = defaultdict(set)
    seen: set[str] = set()

    with path.open(encoding="utf-8") as fh:
        idx: dict[str, int] = {}
        for line in fh:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if not idx:
                if parts and parts[0] == "database_id":
                    idx = {name: i for i, name in enumerate(parts)}
                continue
            if len(parts) <= max(idx.values()):
                continue

            did = parts[idx["database_id"]]
            if not did:
                continue
            seen.add(did)

            aspect = parts[idx["aspect"]]
            # HPO's own aspect codes: I is a mode of inheritance, C a clinical course
            # (which is where onset lives). Reading the aspect rather than pattern-matching
            # the term id means a new inheritance term is picked up the day HPO adds it.
            if aspect == "I":
                has[did].add("inheritance")
            if aspect == "C" or parts[idx["onset"]].strip():
                has[did].add("onset")

            freq = parts[idx["frequency"]].strip()
            # A frequency is only evidence if it carries its denominator. "Frequent"
            # (HP:0040282) is a word; "7/12" is a measurement, and the difference is the
            # whole subject of the rare-disease page.
            if "/" in freq:
                has[did].add("denominator")

    return has, seen


def main() -> int:
    _, disease_to_gene, _ = load_gene_disease()
    hpoa, diseases = load_annotation_facts()

    # Per disease, the set of fields it is MISSING. The plot is about emptiness, so the sets
    # are the gaps themselves rather than their complement — a reader should not have to
    # invert every bar in their head.
    # THE POPULATION IS THE OMIM-CODED DISEASES, AND THAT IS NOT A CONVENIENCE.
    # ORPHA-coded rows in this same file carry zero inheritance annotations and zero
    # fractional frequencies (see the module docstring). Including them would put every one
    # of them in the "missing inheritance" and "missing denominator" bars, and the largest
    # pattern in the figure would be an artefact of which catalogue assigned the identifier
    # rather than a statement about how much is known. The excluded count is reported.
    population = sorted(d for d in diseases if d.startswith("OMIM:"))
    unjoinable = len(diseases) - len(population)

    combos: Counter[tuple[str, ...]] = Counter()
    totals: Counter[str] = Counter()
    complete = 0

    for did in population:
        present = set(hpoa.get(did, set()))
        if disease_to_gene.get(did):
            present.add("gene")

        missing = tuple(f for f in FIELDS if f not in present)
        for f in missing:
            totals[f] += 1
        if not missing:
            complete += 1
        else:
            combos[missing] += 1

    ordered = sorted(combos.items(), key=lambda kv: (-kv[1], len(kv[0])))
    payload = {
        "generated": "tools/gap_patterns.py",
        "inputs": [
            "data/ontology/phenotype.hpoa",
            "data/ontology/genes_to_disease.txt",
        ],
        "question": (
            "Not which field is missing, but which fields are missing TOGETHER. A disease "
            "missing one field is a curation backlog; a disease missing four is not "
            "under-described, it is undescribed."
        ),
        "fields": FIELDS,
        "total": len(population),
        "unjoinable": unjoinable,
        "population": (
            "OMIM-coded diseases in the HPO annotation file. ORPHA- and DECIPHER-coded "
            "diseases are excluded: their rows in the same file carry no inheritance "
            "annotations and no fractional sign frequencies at all, so for them these "
            "fields are unjoinable rather than empty."
        ),
        "complete": complete,
        "totals": [{"field": f, "missing": totals[f]} for f in FIELDS],
        "combinations": [
            {"missing": list(k), "size": v} for k, v in ordered
        ],
        "caveat": (
            "Absence here is absence FROM THESE SOURCES, not absence from the world. A "
            "disease with no recorded gene may have a known cause that HPO has not curated; "
            "what is counted is the catalogue's silence, which is the only thing a "
            "catalogue can be measured on."
        ),
    }

    DEST.mkdir(parents=True, exist_ok=True)
    out = DEST / "gap_patterns.json"
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")

    print(f"{len(population):,} OMIM-coded diseases "
          f"({unjoinable:,} excluded as unjoinable); {complete:,} record all four fields")
    for f in FIELDS:
        print(f"  {f:<12} missing in {totals[f]:>6,} ({totals[f] / len(population):.1%})")
    print("\nlargest patterns of emptiness:")
    for k, v in ordered[:10]:
        print(f"  {v:>6,}  missing: {', '.join(k)}")
    print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
