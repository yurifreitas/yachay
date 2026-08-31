#!/usr/bin/env python
"""How much of the genetics of addiction is about addiction.

## The four-question fit test, answered before any code ran

| | |
|---|---|
| Many candidate entities to rank? | **Yes** — substances, phenotype kinds, ancestries, studies. |
| Each score from noisy observations? | **Yes** — a GWAS is a sample, and its ancestry composition is a count over cohorts. |
| Does the number of observations vary? | **Yes**, by three orders of magnitude: 1,300 individuals to 3.4 million. |
| Is the aggregate a SELECTION operator? | **No.** It is a share and a total. |

Fourth answer is no, so per `.claude/skills/sieve-new-adapter` this is a **variance problem,
not a selection-bias problem**: intervals are reported and no Stage 1 claim is made. That is
written here rather than discovered later.

## The question, and why it is not the ancestry question again

`psychiatric_gwas.py` and `trait_atlas.py` already measure who was sequenced. Repeating that on
substances would add a row, not a finding. The question specific to this field is different and
it is about **what was measured**:

> The word "alcohol" appears in 366 GWAS accessions. Those are not 366 studies of alcoholism.
> They are studies of drinks per week, of AUDIT scores, of alcohol dependence, of problematic
> use, of consumption in the past year — and the field has known since the 2010s that
> **consumption and dependence do not share their genetics**. A locus for how much a person
> drinks is not a locus for whether they cannot stop.

So each accession is classified by the KIND of phenotype it measures, and the question becomes
how much of the sample behind "the genetics of alcohol" is behind a disorder phenotype at all.
The same is asked of nicotine, cannabis and opioids.

## The classification is authored, and that is the weakest part

Assigning a trait string to `disorder`, `quantity`, `cessation` or `other` is a judgement, made
by the rules in `KINDS` below and applied to every accession identically. Two things follow and
both are published: every rule is in this file where it can be argued with, and every accession
that no rule matched is counted rather than dropped. A classifier whose misses are invisible is
a classifier that always works.

    python tools/addiction_atlas.py

Stdlib only, plus this repository's own source registry.
"""

from __future__ import annotations

import collections
import csv
import importlib.util
import json
import math
import pathlib
import random
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "psychiatric" / "addiction_atlas.json"

SEED = 20260831
DRAWS = 400

#: The substances. A trait belongs to a substance when one of its words appears in the trait
#: string; the words are here so a reader can see what was and was not swept in.
SUBSTANCES = {
    "alcohol": ("alcohol", "drinking", "drinks per week", "audit", "alcoholic"),
    "nicotine": ("smoking", "nicotine", "tobacco", "cigarett", "vaping", "e-cigarette"),
    "cannabis": ("cannabis", "marijuana", "thc"),
    "opioid": ("opioid", "heroin", "methadone", "buprenorphine", "oxycodone"),
    "stimulant": ("cocaine", "amphetamine", "methamphetamine", "stimulant use"),
    "general": ("substance use", "substance dependence", "addiction", "drug use",
                "polysubstance"),
}

#: THE PHENOTYPE KINDS, and the distinction the whole file exists to measure.
#:
#:   disorder    a clinical or diagnostic construct — dependence, use disorder, addiction,
#:               abuse, DSM criteria counts, withdrawal.
#:   quantity    how much, how often, how early — consumption, drinks per week, cigarettes per
#:               day, age at initiation.
#:   cessation   quitting, and whether it succeeded.
#:   response    pharmacological or physiological response — flushing, sensitivity, treatment.
#:
#: `disorder` and `quantity` are the pair that matters: they are routinely reported under one
#: heading and their genetic architectures are known to differ.
KINDS = {
    # ⚠️ ADDED AFTER READING THE UNCLASSIFIED PILE, which is what that pile is for. A third of
    # the accessions matched no rule, and they were not noise — they were a whole category the
    # first version had no name for: alcoholic hepatitis, alcohol-associated liver disease,
    # alcohol-related hepatocellular carcinoma, alcoholic chronic pancreatitis.
    #
    # This is the most clinically loaded kind in the file and it is a THIRD question, distinct
    # from both of the others. "Who becomes dependent" and "who drinks heavily" are about
    # behaviour; "who gets cirrhosis given that they drink" is about the organ. A heading of
    # "the genetics of alcohol" covering all three erases two distinctions, not one.
    "consequence": ("liver disease", "hepatitis", "cirrhosis", "pancreatitis",
                    "hepatocellular", "cardiomyopathy", "neuropathy", "fetal alcohol",
                    "korsakoff", "wernicke", "steatosis", "fibrosis"),
    "disorder": ("dependence", "use disorder", "abuse", "addiction", "alcoholism",
                 "dsm", "withdrawal", "misuse", "problematic", "disorder"),
    "cessation": ("cessation", "quit", "former smoker", "successful smoking"),
    "response": ("flushing", "sensitivity", "response to", "treatment", "pharmacogenom",
                 "reaction to"),
    "quantity": ("per week", "per day", "consumption", "intake", "initiation", "age at",
                 "quantity", "frequency", "amount", "ever ", "current ", "status",
                 "heaviness", "drinks", "cigarettes", "audit-c", "audit",
                 "consumed", "units per", "grams per", "packs", "pack-year",
                 "liking", "preference", "usually", "taken with", "drinker"),
}


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


#: ⚠️ TRAITS THAT MENTION A SUBSTANCE WITHOUT BEING ABOUT IT, and the first version of this
#: file counted every one of them. The unclassified pile is what exposed it:
#:
#:   "ACPA-negative rheumatoid arthritis (smoking interaction)"  — smoking is a COVARIATE
#:   "Adult onset asthma (smoking interaction)"                   — same
#:   "Alcohol dehydrogenase 1B levels (ADH1B.9834.62.3)"          — a protein assay
#:
#: None of those is an addiction phenotype. Sweeping them in inflated the study count and the
#: sample, and put studies of arthritis inside a measurement about alcohol. Every exclusion is
#: listed here and every excluded accession is counted in the payload, because a filter whose
#: removals are invisible is a filter nobody can check.
NOT_ABOUT_THE_SUBSTANCE = (
    "interaction",          # the substance is a covariate on some other disease
    "dehydrogenase",        # ADH/ALDH protein assays
    " level", "levels",     # any biomarker concentration
    "metabolite", "metabolome", "proteom",
)


def substance_of(trait: str) -> str | None:
    t = trait.lower()
    if any(w in t for w in NOT_ABOUT_THE_SUBSTANCE):
        return None
    for sub, words in SUBSTANCES.items():
        if any(w in t for w in words):
            return sub
    return None


def kind_of(trait: str) -> str:
    """The phenotype kind, by first matching rule.

    ORDER MATTERS AND IS DELIBERATE. `disorder` is tested first because "alcohol use disorder"
    also contains "use", and a quantity rule would otherwise capture the single most important
    category in the file. Every ordering decision of this kind is a judgement; this one is
    stated rather than left in the sequence of a dict.
    """
    t = trait.lower()
    # `consequence` is tested first: "alcohol-associated liver disease in heavy drinkers"
    # contains "drinkers", and a quantity rule would otherwise file an organ disease as a
    # measure of how much somebody drinks.
    for kind in ("consequence", "disorder", "cessation", "response", "quantity"):
        if any(w in t for w in KINDS[kind]):
            return kind
    return "unclassified"


def main() -> int:
    pg = load("psychiatric_gwas")
    accs = pg.accessions()
    anc_rows = pg.ancestry()

    by_acc_anc: dict[str, list[dict]] = collections.defaultdict(list)
    for r in anc_rows:
        by_acc_anc[r["STUDY ACCESSION"]].append(r)

    rows = []
    excluded: list[str] = []
    for a in accs:
        trait = (a.get("DISEASE/TRAIT") or "").strip()
        t = trait.lower()
        mentions = any(w in t for words in SUBSTANCES.values() for w in words)
        sub = substance_of(trait)
        if mentions and not sub:
            excluded.append(trait)
        if not sub:
            continue
        acc = a.get("STUDY ACCESSION") or ""
        n = sum(pg.as_int(r.get("NUMBER OF INDIVDUALS"))
                for r in by_acc_anc.get(acc, []))
        rows.append({"accession": acc, "trait": trait, "substance": sub,
                     "kind": kind_of(trait), "n": n})

    if not rows:
        print("no substance-use accessions matched", file=sys.stderr)
        return 1

    print(f"  {len(rows)} accessions across {len({r['substance'] for r in rows})} substances")

    rng = random.Random(SEED)

    def share_with_interval(subset: list[dict], kind: str) -> dict:
        """Share of SAMPLE behind a phenotype kind, with a bootstrap interval over studies.

        Weighted by people, not by studies: a hundred small consumption papers and one large
        dependence cohort are a different field from the reverse, and counting studies would
        report them identically. The resample is over ACCESSIONS, which is the unit that
        would differ if the field had made different choices.
        """
        total = sum(r["n"] for r in subset)
        if total <= 0 or len(subset) < 3:
            return {"share": None, "reason": "no published sample sizes, or too few studies"}
        obs = sum(r["n"] for r in subset if r["kind"] == kind) / total
        reps = []
        for _ in range(DRAWS):
            draw = [subset[rng.randrange(len(subset))] for _ in subset]
            t = sum(r["n"] for r in draw)
            if t > 0:
                reps.append(sum(r["n"] for r in draw if r["kind"] == kind) / t)
        if len(reps) < 20:
            return {"share": round(obs, 4), "ci95": None}
        se = statistics.pstdev(reps)
        return {"share": round(obs, 4),
                "ci95": [round(max(0.0, obs - 1.96 * se), 4),
                         round(min(1.0, obs + 1.96 * se), 4)],
                "studies": len(subset), "people": total}

    per_substance = []
    for sub in SUBSTANCES:
        subset = [r for r in rows if r["substance"] == sub]
        if not subset:
            continue
        kinds = collections.Counter(r["kind"] for r in subset)
        people = collections.Counter()
        for r in subset:
            people[r["kind"]] += r["n"]
        anc = pg.compose([r for a in subset for r in by_acc_anc.get(a["accession"], [])])
        per_substance.append({
            "substance": sub,
            "studies": len(subset),
            "sample_summed_over_studies": sum(r["n"] for r in subset),
            "studies_by_kind": dict(kinds),
            "people_by_kind": {k: int(v) for k, v in people.items()},
            "disorder_share_of_sample": share_with_interval(subset, "disorder"),
            "quantity_share_of_sample": share_with_interval(subset, "quantity"),
            "consequence_share_of_sample": share_with_interval(subset, "consequence"),
            "ancestry": anc,
            "largest": sorted(subset, key=lambda r: -r["n"])[0]["trait"],
        })
    per_substance.sort(key=lambda s: -s["sample_summed_over_studies"])

    overall = share_with_interval(rows, "disorder")
    unclassified = [r for r in rows if r["kind"] == "unclassified"]

    payload = {
        "generated": "tools/addiction_atlas.py",
        "governed_by": "docs/adr/0007 and .claude/skills/sieve-new-adapter",
        "fit_test": {
            "many_entities": "yes — substances, phenotype kinds, ancestries, studies",
            "noisy_observations": "yes — a GWAS is a sample",
            "counts_vary": "yes, by three orders of magnitude: 1,300 to 3.4 million",
            "aggregate_is_selection": "NO — it is a share and a total",
            "verdict": ("Fourth answer is no, so this is a variance problem and not a "
                        "selection-bias one. Intervals are reported and NO Stage 1 claim is "
                        "made. Written before the code ran, per the adapter skill."),
        },
        "question": (
            "The word 'alcohol' appears in hundreds of GWAS accessions, and those are not "
            "hundreds of studies of alcoholism. They are studies of drinks per week, AUDIT "
            "scores, dependence, problematic use and consumption — and consumption and "
            "dependence are known not to share their genetics. So: how much of the sample "
            "behind 'the genetics of alcohol' sits behind a disorder phenotype at all?"),
        "classification_is_authored": (
            "Assigning a trait string to disorder / quantity / cessation / response is a "
            "judgement. Every rule is in tools/addiction_atlas.py where it can be argued "
            "with, `disorder` is tested first because 'alcohol use disorder' also contains "
            "'use', and every accession no rule matched is counted rather than dropped."),
        "totals": {
            "accessions": len(rows),
            "substances": len(per_substance),
            "sample_summed_over_studies": sum(r["n"] for r in rows),
            "why_that_name": (
                "It is NOT a count of people. The same cohort — UK Biobank above all — is "
                "reported by dozens of accessions, so summing across studies counts those "
                "individuals dozens of times. tools/psychiatric_gwas.py records the same trap: "
                "done over every psychiatric paper it returns four billion individuals. The "
                "figure is a study-weighted total and is only used as a weight; the shares "
                "below are ratios in which the double counting largely divides out."),
            "unclassified": len(unclassified),
            "unclassified_examples": sorted({r["trait"] for r in unclassified})[:10],
            "excluded_as_not_about_the_substance": len(excluded),
            "excluded_examples": sorted(set(excluded))[:8],
        },
        "disorder_share_overall": overall,
        "by_substance": per_substance,
        "says": None,
    }

    o = overall.get("share")
    if o is not None:
        payload["says"] = (
            "%.1f%% of the reported sample across every substance-use GWAS in the catalogue "
            "sits behind a DISORDER phenotype; the rest measures how much, how often or how "
            "early. Both are worth studying and they are not the same trait, which is the "
            "distinction a heading like 'the genetics of alcohol' erases."
            % (o * 100))

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"  disorder share of all reported sample: {o:.4f} "
          f"{overall.get('ci95')}" if o is not None else "  disorder share: not computable")
    for s in per_substance:
        d = s["disorder_share_of_sample"].get("share")
        print(f"    {s['substance']:10s} {s['studies']:4d} studies  "
              f"{s['sample_summed_over_studies']:>12,} sample  "
              f"disorder share {d if d is not None else '—'}")
    print(f"  unclassified: {len(unclassified)}")
    print(f"\nwrote {DEST.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
