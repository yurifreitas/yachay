"""Who was in the sample, for the disorders the psychiatric consortia have studied hardest.

WHY THIS SOURCE. Everything else in this repository is measured on curation — someone decided
what to write down, and a finding about the catalogue is partly a finding about the curator.
The GWAS Catalogue is the nearest thing here to a base that does not have that shape: findings
that cleared a genome-wide significance threshold on samples in the hundreds of thousands,
catalogued by a third party, with the composition of every sample published alongside. For the
psychiatric traits it is largely the output of the Psychiatric Genomics Consortium and its
collaborators, which is the largest coordinated human-genetics effort on these disorders that
exists.

AND THE FIRST THING IT SAYS IS ABOUT WHO IS MISSING.

Several results in this repository carry a caveat that their panels are not ancestry-neutral.
`tools/gene_constraint.py` says it in prose: gnomAD's reference population is majority
European, so constraint is estimated where the variation was sampled. That has been a
disclaimer. This file makes it a count, on the disorders where the samples are largest and the
statistical machinery is strongest — the place where the field is at its most confident.

THE JOIN WAS WRONG THE FIRST TIME, and the way it was wrong is worth keeping.

`gwas-catalog-studies.tsv` is keyed on PubMed id. Selecting psychiatric PAPERS by trait and
then taking all of their ancestry rows imports every analysis those papers contain — and one
phenome-wide paper in the ADHD set carries 1,129 study accessions, nearly all of them about
unrelated traits like transient cerebral ischemia. The result said ADHD samples were 81 % East
Asian, which contradicts everything known about a field built on Danish cohorts. The number was
surprising, and the surprise is what got it checked.

The fix is to join at the ACCESSION, which is the level the ancestry file is actually keyed
on, using `gwas-catalog-studies-accessions.txt` and selecting by MONDO id rather than by a
regular expression over free text.

THE ARITHMETIC TRAP, met and avoided. The obvious aggregation is to sum `NUMBER OF INDIVDUALS`
over the ancestry rows of every psychiatric paper. Doing that here returns 4.4 BILLION people,
which is more than half the species, because one paper carries many study accessions and the
same cohort is described once per accession. A number that large is obviously wrong; the same
error at a plausible magnitude would not have been.

So the unit here is the ACCESSION — one analysis — counted once, and the headline figures are
SHARES and MEDIANS rather than totals. Individuals are not unique people across analyses and
this file never claims they are.

NOT AN ADAPTER (.claude/skills/sieve-new-adapter): question 4 fails and question 1 is
arguable. Nothing is ranked, no entity is scored, there is no selection operator and therefore
no null. It is a tabulation with denominators.

    python tools/psychiatric_gwas.py
"""
from __future__ import annotations

import collections
import csv
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "psychiatric" / "psychiatric_gwas.json"

#: The disorders, as MONDO terms rather than as a pattern over free text. The first version
#: matched `r"attention.?deficit"` against the trait column, which pulled in a phenome-wide
#: paper because ONE of its thousand traits was ADHD. An ontology id cannot do that. Autism
#: carries two ids because the catalogue maps "Autism" and "Autism spectrum disorder"
#: separately, and both are the same disorder for this count.
DISORDERS = {
    "schizophrenia": {"MONDO_0005090"},
    "bipolar disorder": {"MONDO_0004985"},
    "major depression": {"MONDO_0002009"},
    "ADHD": {"MONDO_0007743"},
    "autism": {"MONDO_0005260", "MONDO_0005258"},
    "PTSD": {"MONDO_0005146"},
    "OCD": {"MONDO_0008114"},
    "anorexia nervosa": {"MONDO_0005351"},
    "Tourette syndrome": {"MONDO_0007661"},
}

#: Ancestry strings the catalogue uses for "we did not say". Counted as their own category
#: rather than dropped: a sixth of these analyses not stating who was in them is a result
#: about the field's reporting, not a gap in this tool.
NOT_REPORTED = {"NR", "", "Not reported"}


def accessions() -> list[dict[str, str]]:
    """One row per STUDY ACCESSION with its mapped ontology terms.

    This is the level the ancestry file is keyed on, and the level at which a disorder can
    be selected without importing the rest of a phenome-wide paper along with it.
    """
    with BY_KEY["gwas_accessions"].dest.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="	"))


def ancestry() -> list[dict[str, str]]:
    with BY_KEY["gwas_ancestry"].dest.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def as_int(value: str) -> int:
    try:
        return int((value or "").strip() or 0)
    except ValueError:
        return 0


def compose(rows: list[dict[str, str]]) -> dict:
    """Ancestry composition over a set of ancestry rows, counted per ACCESSION once.

    Each analysis contributes weight 1, split across the ancestries it reports. Summing people
    instead would count the same cohort once per accession — the error that returns four
    billion individuals when it is done over every psychiatric paper at once.
    """
    per_acc: dict[str, dict[str, int]] = collections.defaultdict(dict)
    for r in rows:
        acc = r["STUDY ACCESSION"]
        cat = (r.get("BROAD ANCESTRAL CATEGORY") or "NR").strip() or "NR"
        # max, not sum: the same ancestry can be listed twice for one accession across
        # sub-cohorts, and taking the larger avoids double counting inside an accession too.
        per_acc[acc][cat] = max(per_acc[acc].get(cat, 0), as_int(r.get("NUMBER OF INDIVDUALS")))

    weight: collections.Counter = collections.Counter()
    majority: collections.Counter = collections.Counter()
    sizes: list[int] = []
    for parts in per_acc.values():
        total = sum(parts.values())
        if total <= 0:
            # No sample size published. The analysis still exists, so it is counted in the
            # majority tally by its single listed ancestry, and excluded from the sizes.
            for cat in parts:
                majority[cat] += 1 / len(parts)
            continue
        sizes.append(total)
        for cat, n in parts.items():
            weight[cat] += n / total
        majority[max(parts, key=parts.get)] += 1

    w = sum(weight.values()) or 1
    m = sum(majority.values()) or 1
    return {
        "analyses": len(per_acc),
        "median_individuals": int(statistics.median(sizes)) if sizes else None,
        "largest_analysis": max(sizes) if sizes else None,
        "by_weight": [{"ancestry": k, "share": round(v / w, 4)}
                      for k, v in weight.most_common(10)],
        "by_majority": [{"ancestry": k, "analyses": round(v, 1), "share": round(v / m, 4)}
                        for k, v in majority.most_common(10)],
        "european_share": round(sum(v for k, v in weight.items()
                                    if k.strip() == "European") / w, 4),
        "unstated_share": round(sum(v for k, v in weight.items()
                                    if k.strip() in NOT_REPORTED) / w, 4),
        "african_majority_analyses": round(sum(
            v for k, v in majority.items() if "African" in k), 1),
    }


def main() -> int:
    for key in ("gwas_accessions", "gwas_ancestry"):
        if not BY_KEY[key].dest.exists():
            print(f"missing {BY_KEY[key].dest}", file=sys.stderr)
            return 1

    st = accessions()
    anc = ancestry()

    # ACCESSION-LEVEL SELECTION. An accession may carry several mapped terms — a pleiotropy
    # study lists every trait it covers — so one accession can belong to more than one
    # disorder here. That is real and is counted; what it can no longer do is drag in the
    # thousand unrelated analyses that shared its paper.
    terms_of: dict[str, set[str]] = {}
    for r in st:
        acc = (r.get("STUDY ACCESSION") or "").strip()
        if not acc:
            continue
        ids = {u.strip().rsplit("/", 1)[-1]
               for u in (r.get("MAPPED_TRAIT_URI") or "").split(",") if u.strip()}
        terms_of[acc] = ids

    # Initial stage only. A replication cohort is a different sample and mixing the two would
    # count the well-studied populations twice, in the direction that flatters the field.
    initial = [r for r in anc if (r.get("STAGE") or "").strip().lower() == "initial"]
    by_acc: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for r in initial:
        by_acc[(r.get("STUDY ACCESSION") or "").strip()].append(r)

    per_disorder = {}
    all_accs: set[str] = set()
    for name, ids in DISORDERS.items():
        accs = {a for a, t in terms_of.items() if t & ids}
        rows = [r for a in accs for r in by_acc.get(a, ())]
        if not rows:
            continue
        all_accs |= accs
        multi = sum(1 for a in accs if len(terms_of[a]) > 1)
        per_disorder[name] = {
            "accessions": len(accs),
            "accessions_with_ancestry": len({r["STUDY ACCESSION"] for r in rows}),
            "multi_trait_accessions": multi,
            **compose(rows),
        }

    overall = compose([r for a in all_accs for r in by_acc.get(a, ())])

    countries: collections.Counter = collections.Counter()
    for a in all_accs:
        for r in by_acc.get(a, ()):
            for c in (r.get("COUNTRY OF RECRUITMENT") or "").split(","):
                c = c.strip()
                if c and c != "NR":
                    countries[c] += 1

    payload = {
        "generated": "2026-08-30",
        "provenance": "GWAS Catalog (EMBL-EBI) studies and ancestry releases; the "
                      "psychiatric traits are largely Psychiatric Genomics Consortium output",
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md",
        "question": "On the disorders where human genetics is at its most confident — the "
                    "largest samples, the strongest statistical machinery — who was actually "
                    "in the sample?",
        "not_an_adapter": {
            "gate": ".claude/skills/sieve-new-adapter",
            "fails": "nothing is ranked and no entity is scored, so there is no selection "
                     "operator and no null. A tabulation with denominators.",
        },
        "unit": {
            "counted": "one STUDY ACCESSION — one analysis — weighted once",
            "why": "Summing NUMBER OF INDIVDUALS across the ancestry rows of every "
                   "psychiatric paper returns 4.4 billion people, more than half the "
                   "species, because one paper carries many accessions and the same cohort "
                   "is described once per accession. That number is obviously wrong; the "
                   "same error at a plausible magnitude would not have been. Shares and "
                   "medians are reported instead of totals, and individuals are not unique "
                   "people across analyses.",
            "stage": "initial only — a replication cohort is a different sample, and mixing "
                     "them counts the well-studied populations twice",
        },
        "scale": {
            "catalogue_accessions": len(terms_of),
            "psychiatric_accessions": len(all_accs),
            "analyses": overall["analyses"],
            "median_individuals_per_analysis": overall["median_individuals"],
            "largest_analysis": overall["largest_analysis"],
        },
        "overall": overall,
        "by_disorder": per_disorder,
        "commonest_countries_of_recruitment": [
            {"country": c, "analyses": n} for c, n in countries.most_common(20)
        ],
        "says": "Composition of the samples, not quality of the findings. A genome-wide "
                "significant association from a European cohort is not wrong; it is "
                "established in that population, and its transferability to another is a "
                "separate question this file does not touch. Nothing here says a result is "
                "false — it says who it was established in.",
        "limits": [
            "Broad ancestral category is what the authors reported, in the catalogue's own "
            "vocabulary. It is a coarse and contested grouping, and a sixth of these "
            "analyses do not state it at all — which is counted as its own category rather "
            "than distributed across the others.",
            "The trait selection is a regular expression over a free-text field, registered "
            "in DISORDERS above so a reader can see the boundary and disagree with it. A "
            "study of a symptom dimension rather than a diagnosis may fall either side.",
            "An analysis is not a person and not a study. Papers carry many accessions, and "
            "a paper with more analyses contributes more weight here than one with fewer, "
            "which is a property of the catalogue's structure rather than of the science.",
        ],
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {DEST.relative_to(ROOT)}")
    print(f"  {len(all_accs):,} psychiatric accessions, {overall['analyses']:,} with "
          f"ancestry, "
          f"median n={overall['median_individuals']:,}")
    print(f"  European {100 * overall['european_share']:.1f} % of analysis weight · "
          f"unstated {100 * overall['unstated_share']:.1f} %")
    print(f"  analyses with an African-ancestry majority: "
          f"{overall['african_majority_analyses']:.0f} of {overall['analyses']:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
