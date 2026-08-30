#!/usr/bin/env python
"""HIV drug resistance: which mutations does the metric's maximum actually reward?

THE FIT TEST, answered before any code was written, per `.claude/skills/sieve-new-adapter`.

| question | answer |
|---|---|
| 1. Many candidate entities to rank? | **Yes** — every amino-acid substitution observed at every protease or RT position: 1,000+ distinct mutations. |
| 2. Is each entity's score estimated from noisy observations? | **Yes** — the fold-resistance of each isolate carrying it, measured in a phenotype assay with real assay error. |
| 3. Does the observation count VARY across entities? | **Yes, by three orders of magnitude.** A major resistance mutation appears in hundreds of isolates; a rare polymorphism in two. |
| 4. Is the aggregate a SELECTION operator? | **Yes.** The natural score is the maximum fold-resistance across the drug panel — "this mutation confers resistance to at least one drug" is a max over eight drugs, which is exactly the operator Stage 1 exists for. |

Four yeses, so it is built.

| element | what it is here |
|---|---|
| entity | one amino-acid substitution at one position, e.g. protease L90M |
| observation | one isolate carrying that substitution, with its measured fold-resistance |
| aggregate | **max over the drug panel** of the median fold-resistance among carriers |
| counts vary | 2 to 800+ isolates per mutation |

## The control pool, named rather than assumed

The skill ranks three options. There are **no designed controls** in this dataset and no
published inert-position list on disk, so this uses **option 3, label permutation**: the
isolate-to-resistance assignment is shuffled while each mutation keeps its exact carrier
count. That gives an n-indexed null by construction, which is what Stage 1 needs.

**It is the weakest of the three and the reason is stated out loud**: a real resistance effect
contaminates the pool, so the null is slightly inflated and every z here is slightly
conservative. Conservative in the safe direction, but not free.

## WHAT THIS DOMAIN DOES THAT THE CORE ASSUMES AWAY

The skill asks for this explicitly, and here it is not a technicality:

**The observations are not exchangeable.** DepMap's cell lines are treated as independent
draws; HIV isolates are tips of a phylogeny, and resistance mutations arrive in *linked
pathways* — an isolate with M184V very often carries K65R or the TAM cluster, because
selection under a drug regime produced them together. So a mutation's carriers are not a
random sample of isolates, and two mutations' carrier sets overlap heavily.

The consequence is measurable and is reported below: the top of this ranking is not a set of
independent findings but a **correlated block**, and the permutation null cannot see that,
because it preserves each mutation's count while destroying exactly the co-occurrence
structure that makes the observations dependent. The library's `null_blocks` argument exists
for this shape and this adapter is the second domain to need it.

    python analyses/hiv_resistance.py

Stdlib only. Reads data/hiv/*_DataSet.txt from Stanford HIVdb.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import pathlib
import random
import statistics
import sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

DATA = ROOT / "data" / "hiv"
DEST = ROOT / "out" / "hiv_resistance.json"

#: Carriers a mutation needs before it is scored at all. Below this the median fold-change is
#: one or two assays and the interval swamps the estimate.
MIN_CARRIERS = 3

#: Permutation draws behind the null.
HIV_PERMUTATIONS = 200

#: Bootstrap resamples of the ISOLATES, behind the interval on each observed score.
#:
#: The resample has to be over isolates and not over each mutation's carriers separately,
#: because the carrier sets overlap heavily - resistance mutations are selected together
#: under a drug regime, so two mutations often ride on largely the same isolates. Resampling
#: isolates once and rescoring every mutation on that resample keeps that dependence intact,
#: which is the only version of the interval that means anything for a SHORTLIST: the
#: question is not "would this mutation survive resequencing" one at a time, but "would this
#: list".
HIV_BOOTSTRAP = 200

SEED = 20260829

#: THE POSITIVE CONTROL, named before the run. ADR 0003: a failed positive control blocks the
#: shortlist, so the gate has to be written down before the numbers arrive. These are the
#: textbook major resistance mutations for each panel, from the literature and NOT from this
#: dataset. If the ranking does not recover them near the top, the adapter is wrong and its
#: output may not be used.
POSITIVE_CONTROLS = {
    "PI": {"84V", "90M", "82A", "46I", "54V", "48V", "30N"},
    "NRTI": {"184V", "215Y", "41L", "67N", "70R", "219Q", "65R"},
    "NNRTI": {"103N", "181C", "190A", "100I", "188L"},
}

#: The panels, and the drug columns each carries. The amino-acid columns are everything
#: starting with P (protease) or with the RT prefix, and are detected rather than listed.
PANELS = {
    "PI": "protease inhibitors",
    "NRTI": "nucleoside RT inhibitors",
    "NNRTI": "non-nucleoside RT inhibitors",
}


def load_panel(name: str):
    """Isolates as (mutations, {drug: fold}) — sign already normalised."""
    path = DATA / f"{name}_DataSet.txt"
    if not path.exists() or path.stat().st_size == 0:
        return [], []
    with path.open(encoding="utf-8", errors="replace") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if not rows:
        return [], []

    header = list(rows[0].keys())
    pos_cols = [c for c in header if c[:1] == "P" and c[1:].isdigit()]
    drug_cols = [c for c in header
                 if c not in pos_cols and c not in ("SeqID", "PtID", "Method", "RefID",
                                                    "Type", "IsolateName", "Subtype")]

    isolates = []
    for row in rows:
        folds = {}
        for d in drug_cols:
            v = (row.get(d) or "").strip()
            try:
                f = float(v)
            except ValueError:
                continue
            if f > 0:
                # LARGER IS BETTER, once, at the boundary: fold-resistance is already
                # "bigger means more resistant", so a log keeps it additive and comparable
                # across drugs whose dynamic ranges differ by an order of magnitude.
                folds[d] = math.log10(f)
        if not folds:
            continue
        muts = set()
        for c in pos_cols:
            aa = (row.get(c) or "").strip()
            # A dash is wild type; a dot is missing; a multi-letter cell is a mixture, and a
            # mixture is not one observation of one mutation, so it is dropped rather than
            # split. Dropping is the conservative choice and it is stated in the artefact.
            if aa and aa not in ("-", ".", "~") and len(aa) == 1 and aa.isalpha():
                muts.add(f"{c[1:]}{aa}")
        isolates.append((muts, folds))
    return isolates, drug_cols


def score_mutations(isolates, drugs):
    """max over drugs of the median log fold-change among carriers."""
    carriers: dict[str, list[int]] = collections.defaultdict(list)
    for i, (muts, _) in enumerate(isolates):
        for m in muts:
            carriers[m].append(i)

    scored = {}
    for m, idx in carriers.items():
        if len(idx) < MIN_CARRIERS:
            continue
        best, best_drug = None, None
        for d in drugs:
            vals = [isolates[i][1][d] for i in idx if d in isolates[i][1]]
            if len(vals) < MIN_CARRIERS:
                continue
            med = statistics.median(vals)
            if best is None or med > best:
                best, best_drug = med, d
        if best is not None:
            scored[m] = {"score": best, "drug": best_drug, "n": len(idx)}
    return scored, carriers


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--permutations", type=int, default=HIV_PERMUTATIONS)
    args = ap.parse_args()
    rng = random.Random(SEED)

    panels = {}
    for name in PANELS:
        isolates, drugs = load_panel(name)
        if not isolates:
            print(f"  {name}: no data on disk")
            continue
        print(f"  {name}: {len(isolates)} isolates, {len(drugs)} drugs")

        scored, carriers = score_mutations(isolates, drugs)

        # THE NULL. Each mutation keeps its exact carrier count; the isolate-to-resistance
        # assignment is shuffled. So the null is indexed by n by construction, which is the
        # whole point of Stage 1 — and it is label permutation, the weakest control pool the
        # adapter skill ranks, because a real effect contaminates it.
        by_n: dict[int, list[float]] = collections.defaultdict(list)
        order = list(range(len(isolates)))
        for _ in range(args.permutations):
            shuffled = order[:]
            rng.shuffle(shuffled)
            remap = {a: b for a, b in zip(order, shuffled)}
            for m, rec in scored.items():
                idx = [remap[i] for i in carriers[m]]
                d = rec["drug"]
                vals = [isolates[i][1][d] for i in idx if d in isolates[i][1]]
                if len(vals) >= MIN_CARRIERS:
                    by_n[rec["n"]].append(statistics.median(vals))

        # ---- the interval on the observed score ------------------------------------------
        #
        #  A Z IS NOT AN UNCERTAINTY. Everything above measures how far each mutation's
        #  fold-resistance sits from a label-permutation null. None of it says how far the
        #  OBSERVED fold-resistance itself would move on a different sample of isolates - and
        #  for a shortlist that is the operative question, because a clinician acting on this
        #  list acts on the observed effect, not on its distance from a shuffle.
        #
        #  THE DRUG IS HELD AT THE ONE THE FULL DATA CHOSE. The score is a max over the drug
        #  panel, so re-taking the max inside every resample would let each draw pick its own
        #  best drug and inflate the interval with a selection this repository's own Stage 1
        #  exists to remove. Fixing the drug makes the interval one about the fold-resistance,
        #  which is what it claims to be.
        boot_rng = random.Random(SEED + 11)
        boot_scores: dict[str, list[float]] = collections.defaultdict(list)
        n_iso = len(isolates)
        for _ in range(HIV_BOOTSTRAP):
            pick = [boot_rng.randrange(n_iso) for _ in range(n_iso)]
            # Carriers of each mutation IN THIS RESAMPLE. Rebuilt rather than reweighted,
            # because an isolate drawn twice must count twice in the median.
            b_car: dict[str, list[int]] = collections.defaultdict(list)
            for i in pick:
                for m in isolates[i][0]:
                    if m in scored:
                        b_car[m].append(i)
            for m, rec in scored.items():
                d = rec["drug"]
                vals = [isolates[i][1][d] for i in b_car.get(m, []) if d in isolates[i][1]]
                if len(vals) >= MIN_CARRIERS:
                    boot_scores[m].append(statistics.median(vals))

        rows = []
        for m, rec in scored.items():
            draws = by_n.get(rec["n"], [])
            if len(draws) < 20:
                continue
            mu = sum(draws) / len(draws)
            sd = (sum((x - mu) ** 2 for x in draws) / (len(draws) - 1)) ** 0.5
            reps = boot_scores.get(m, [])
            # ---- the ceiling, found by the interval -------------------------------------
            #
            #  THE BOOTSTRAP RETURNED A WIDTH OF EXACTLY ZERO for several of the highest-
            #  ranked mutations, which is not a mutation measured with perfect precision.
            #  It is the assay's upper limit: `100` is the single most common value in this
            #  dataset - 8.6% of every fold-resistance in the PI panel - because the
            #  phenotype assay reports ">100-fold" as 100. Taking its log10 gives exactly
            #  2.0, and every carrier of a strong mutation sits on that value, so every
            #  resample returns the same median.
            #
            #  This matters for the SHORTLIST and not only for the interval. Among the
            #  censored mutations the score is identical by construction, so their ORDER in
            #  the ranking is not coming from the resistance data at all - it comes from
            #  whatever the permutation null happened to give each carrier count. A reader
            #  ranking 184V above 41L above 215Y is reading the null, not the assay.
            #
            #  So a censored score is published as censored rather than given a zero-width
            #  interval, which would claim certainty the assay explicitly refuses to provide.
            ceiling = max(v for iso in isolates for v in iso[1].values())
            at_ceiling = sum(1 for i in carriers[m]
                             for d in [rec["drug"]]
                             if d in isolates[i][1] and isolates[i][1][d] >= ceiling - 1e-9)
            censored = bool(reps) and statistics.pstdev(reps) == 0.0 \
                and abs(rec["score"] - ceiling) < 1e-9
            # A draw in which the mutation fell below MIN_CARRIERS produces no replicate, so
            # the count is reported: an interval from 140 of 200 draws is a different object
            # from one from 200, and a rare mutation is exactly where that happens.
            se = statistics.pstdev(reps) if len(reps) >= 20 else None
            if not se:
                se = None
            z_val = round((rec["score"] - mu) / sd, 3) if sd else None
            rows.append({
                "mutation": m, "drug": rec["drug"], "n": rec["n"],
                "score": round(rec["score"], 4),
                "null_mean": round(mu, 4), "null_sd": round(sd, 4),
                "z": z_val,
                "score_se": round(se, 4) if se else None,
                "score_ci95": ([round(rec["score"] - 1.96 * se, 4),
                                round(rec["score"] + 1.96 * se, 4)] if se else None),
                "resamples": len(reps),
                # The z with the observed score's own uncertainty carried through, and the
                # honest version of "beats the null": the LOWER end of the interval does.
                "z_ci95": ([round((rec["score"] - 1.96 * se - mu) / sd, 3),
                            round((rec["score"] + 1.96 * se - mu) / sd, 3)]
                           if se and sd else None),
                "interval_clears_null": bool(se and sd and (rec["score"] - 1.96 * se) > mu),
                # Why there is no interval, when there is none. An empty reason means the
                # resample simply produced too few replicates.
                "censored_at_assay_ceiling": censored,
                "carriers_at_ceiling": at_ceiling,
                "no_interval_because": (
                    "every carrier sits at the assay's reporting ceiling (fold >= %g, "
                    "log10 = %.1f), so the score is a lower bound and the resample cannot "
                    "move it. Its rank among the other censored mutations is set by the "
                    "null, not by the assay." % (10 ** ceiling, ceiling)
                    if censored else (None if se else
                                      "fewer than 20 resamples kept this mutation above the "
                                      "minimum carrier count")),
            })
        rows.sort(key=lambda r: -(r["z"] or 0))

        # THE DEPENDENCE THE CORE ASSUMES AWAY, measured. How much do the carrier sets of the
        # top mutations overlap? If the top of the list is one correlated block, it is not
        # twenty findings.
        top = rows[:20]
        cens = [r for r in top if r["censored_at_assay_ceiling"]]
        with_ci = [r for r in top if r["score_ci95"]]
        clears = [r for r in with_ci if r["interval_clears_null"]]
        overlaps = []
        for i, a in enumerate(top):
            for b in top[i + 1:]:
                ca, cb = set(carriers[a["mutation"]]), set(carriers[b["mutation"]])
                if ca and cb:
                    overlaps.append(len(ca & cb) / len(ca | cb))
        # THE GATE. How many of the named controls land in the top twenty?
        controls = POSITIVE_CONTROLS.get(name, set())
        top20 = {r["mutation"] for r in rows[:20]}
        recovered = sorted(controls & top20)
        # And the other half of the same question: what is in the top twenty that is NOT a
        # known resistance mutation? Under the dependence this adapter predicts, those are
        # passengers on a resistance haplotype rather than findings.
        passengers = sorted(m for m in top20 if m not in controls)

        panels[name] = {
            "description": PANELS[name],
            "positive_control": {
                "named_before_the_run": sorted(controls),
                "recovered_in_top20": recovered,
                "recovered": len(recovered),
                "of": len(controls),
                "passes": len(recovered) >= max(2, len(controls) // 2),
                "says": ("ADR 0003: a failed positive control blocks the shortlist. The list "
                         "was written from the literature before the run, not read off the "
                         "result."),
            },
            "passengers_in_top20": {
                "mutations": passengers,
                "says": ("Top-twenty entries that are not known resistance mutations. This "
                         "adapter PREDICTED them: carrier sets overlap because resistance "
                         "mutations arrive in linked pathways, so a passenger on a "
                         "resistance haplotype scores like a driver and the permutation null "
                         "cannot tell them apart."),
            },
            "isolates": len(isolates), "drugs": drugs,
            "mutations_scored": len(rows),
            "top": top,
            # WHAT SURVIVES ITS OWN INTERVAL, and what has no interval to survive. The three
            # numbers are reported together because they partition the published twenty and
            # a reader has to see which bucket a mutation is in before acting on its rank.
            "uncertainty": {
                "method": ("bootstrap over ISOLATES with replacement at the same count, "
                           "%d draws, rescoring every mutation on each resample so the "
                           "overlap between carrier sets is preserved; the drug is held at "
                           "the one the full data chose, so the interval is on the "
                           "fold-resistance and not on the max over the panel"
                           % HIV_BOOTSTRAP),
                "published": len(top),
                "with_an_interval": len(with_ci),
                "clearing_the_null_on_the_lower_end": len(clears),
                "censored_at_the_assay_ceiling": len(cens),
                "censored_mutations": [r["mutation"] for r in cens],
                "says": ("%d of the published %d carry an interval and %d of those keep the "
                         "observed score above the null at its lower end. The remaining %d "
                         "are CENSORED: every carrier sits at the assay's reporting ceiling, "
                         "so their scores are identical by construction and their order in "
                         "this table comes from the permutation null rather than from the "
                         "resistance data. That is a limit of the assay, and it is stated "
                         "here rather than hidden behind a zero-width interval."
                         % (len(with_ci), len(top), len(clears), len(cens))),
            },
            "carrier_overlap": {
                "median_jaccard_top20": round(statistics.median(overlaps), 4) if overlaps else None,
                "pairs": len(overlaps),
                "says": ("Jaccard overlap between the carrier sets of the top twenty. DepMap "
                         "treats its observations as exchangeable; these are tips of a "
                         "phylogeny and resistance mutations arrive in linked pathways, so a "
                         "high overlap means the top of this ranking is one correlated block "
                         "rather than twenty independent findings. The permutation null "
                         "cannot see it: it preserves each count and destroys exactly the "
                         "co-occurrence that makes the observations dependent."),
            },
        }

    payload = {
        "generated": date.today().isoformat(),
        "provenance": "Stanford HIV Drug Resistance Database, genotype-phenotype datasets",
        "governed_by": ".claude/skills/sieve-new-adapter — the four-question fit test",
        "fit_test": {
            "many_entities": True, "noisy_observations": True,
            "counts_vary": True, "selection_operator": True,
            "verdict": "four yeses; Stage 1 applies",
        },
        "elements": {
            "entity": "one amino-acid substitution at one position",
            "observation": "one isolate carrying it, with its measured fold-resistance",
            "aggregate": "max over the drug panel of the median log10 fold-change",
            "counts_vary": "3 to 800+ isolates per mutation",
        },
        "control_pool": {
            "used": "label permutation",
            "rank": "option 3 of 3, the weakest",
            "why": ("no designed controls exist in this dataset and no inert-position list is "
                    "on disk. Permutation preserves each mutation's carrier count exactly, so "
                    "the null is n-indexed by construction"),
            "cost": ("a real resistance effect contaminates the pool, so the null is slightly "
                     "inflated and every z here is conservative"),
        },
        "panels": panels,
        "what_this_domain_breaks": (
            "Exchangeability. DepMap's cell lines are treated as independent draws; HIV "
            "isolates are tips of a phylogeny and resistance mutations arrive in linked "
            "pathways, so carrier sets overlap heavily and the top of a ranking is a "
            "correlated block. sieve's null_blocks argument exists for this shape and this is "
            "the second domain to need it."),
        "limits": [
            "Mixtures — cells holding more than one amino acid — are dropped rather than "
            "split, which is conservative and removes real observations.",
            "Fold-resistance is assay-derived and the panels use different assays; the log "
            "keeps them additive but does not make them the same measurement.",
            "Subtype is not modelled at all. The dataset is B-heavy, so a mutation common "
            "outside subtype B is under-observed here — which is the ancestry axis this "
            "project already measures for rare disease, in a new domain.",
        ],
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    for name, p in panels.items():
        pc = p["positive_control"]
        gate = "PASS" if pc["passes"] else "FAIL"
        print(f"  {name} — {p['mutations_scored']} mutations scored · positive control "
              f"{gate} ({pc['recovered']}/{pc['of']}: {', '.join(pc['recovered_in_top20'])}) · "
              f"top-20 carrier overlap {p['carrier_overlap']['median_jaccard_top20']}")
        print(f"    passengers in top 20: {', '.join(p['passengers_in_top20']['mutations'])}")
        for r in p["top"][:6]:
            print(f"    {r['mutation']:8s} z={r['z']:7.2f}  n={r['n']:4d}  "
                  f"{r['drug']:6s} score={r['score']:.2f}")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
