#!/usr/bin/env python
"""Frequencies computed from individual patients, against frequencies read from a catalogue.

WHY THIS IS DIFFERENT FROM EVERY OTHER TOOL HERE. All thirteen other sources are aggregate:
they report what a *disease* does. A phenopacket reports what happened to a *person*, and
the difference is a denominator.

`docs/references/rare-disease-scale.md` §4b measured how badly that denominator is missing.
Across 267,782 curated phenotype annotations covering 12,935 diseases, only **39.7%** of
diseases carry a single sign estimated from a real series; **56.1%** carry no fraction of any
kind anywhere; and where a denominator does exist the median is **five patients**. That is
the state of the field's own frequency record.

Individual patients let the frequency be COMPUTED instead of read - and the reason it works
is a detail of the GA4GH standard that aggregate catalogues have no room for: a phenopacket
records phenotypes that were **explicitly absent** as well as present. In a sample of 1,500
packets, 28,475 of 43,499 assertions were `excluded`. An excluded term is not a gap; it is a
patient who was examined for that feature and did not have it. So:

    frequency = observed / (observed + excluded)

with a denominator that is the number of patients actually assessed for that feature, which
is the quantity the curated record almost never has.

TWO QUESTIONS, and the second is the one worth running.

  1. COVERAGE. How many disease-feature pairs get a real denominator this way, and how many
     of those diseases had nothing in the curated record?

  2. AGREEMENT. Where BOTH exist, do they agree? This is the same authored-versus-measured
     confrontation the rest of this repository keeps running (docs/audit.md A13, A14),
     pointed at the world's reference phenotype ontology rather than at our own seeds.

WHAT THIS IS NOT. Phenopacket-store is built from PUBLISHED CASE REPORTS AND SERIES, so it
inherits publication bias in full: a patient reaches it by being written up, and unusual
presentations get written up. It is not a population sample and no number below should be
read as a population frequency. What it is, is a denominator that exists - and the
comparison against the curated value is meaningful even when neither side is a population
estimate, because they are two readings of the same literature.

    python tools/patient_frequencies.py     # writes out/rare/patient_frequencies.json

Needs numpy for the bootstrap; everything else is stdlib.
"""

from __future__ import annotations

import csv
import json
import pathlib
import sys
import zipfile
from collections import Counter, defaultdict

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

RARE = ROOT / "out" / "rare"

# A feature seen in too few assessed patients is not an estimate. The floor is the same one
# tools/dossier.py grades with: n=1 is a case report wearing the costume of a proportion.
MIN_ASSESSED = 2


def load_packets() -> tuple[dict, dict, dict]:
    """Per (disease, HPO term): observed and excluded counts, from individual patients."""
    obs: dict[tuple[str, str], int] = Counter()
    exc: dict[tuple[str, str], int] = Counter()
    patients: dict[str, set] = defaultdict(set)
    labels: dict[str, str] = {}
    disease_labels: dict[str, str] = {}
    publications: dict[str, set] = defaultdict(set)

    path = BY_KEY["phenopackets"].dest
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith(".json"):
                continue
            p = json.loads(z.read(name))

            # The disease is under interpretations[].diagnosis.disease, and `diseases[]`
            # is frequently absent. Reading only the latter returns nothing, quietly.
            diseases = set()
            for interp in p.get("interpretations", []) or []:
                d = (interp.get("diagnosis") or {}).get("disease") or {}
                if d.get("id"):
                    diseases.add(d["id"])
                    disease_labels.setdefault(d["id"], d.get("label") or d["id"])
            for d in p.get("diseases", []) or []:
                t = d.get("term") or d
                if t.get("id"):
                    diseases.add(t["id"])
                    disease_labels.setdefault(t["id"], t.get("label") or t["id"])
            if not diseases:
                continue

            subject = p.get("id") or name
            for ref in (p.get("metaData", {}).get("externalReferences") or []):
                if ref.get("id"):
                    for did in diseases:
                        publications[did].add(ref["id"])

            for did in diseases:
                patients[did].add(subject)
                for f in p.get("phenotypicFeatures", []) or []:
                    term = (f.get("type") or {}).get("id")
                    if not term:
                        continue
                    labels.setdefault(term, (f.get("type") or {}).get("label") or term)
                    if f.get("excluded"):
                        exc[(did, term)] += 1
                    else:
                        obs[(did, term)] += 1

    return {"observed": obs, "excluded": exc, "patients": patients,
            "termLabels": labels, "diseaseLabels": disease_labels,
            "publications": publications}, labels, disease_labels


def curated_frequencies() -> dict[tuple[str, str], dict]:
    """The catalogue's own frequency, per (disease, term), where it states one."""
    out: dict[tuple[str, str], dict] = {}
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            header = line.rstrip("\n").split("\t")
            break
        idx = {n: i for i, n in enumerate(header)}
        for row in csv.reader(fh, delimiter="\t"):
            if len(row) <= idx["aspect"] or row[idx["aspect"]] != "P":
                continue
            raw = row[idx["frequency"]].strip()
            if not raw:
                continue
            key = (row[idx["database_id"]], row[idx["hpo_id"]])
            k = n = None
            if "/" in raw:
                a, b = raw.split("/", 1)
                if a.isdigit() and b.isdigit():
                    k, n = int(a), int(b)
            out[key] = {"raw": raw, "k": k, "n": n,
                        "point": (k / n if k is not None and n else None)}
    return out


def main() -> int:
    path = BY_KEY["phenopackets"].dest
    if not path.exists():
        raise SystemExit("missing %s — run python tools/ingest.py" % path.name)

    store, term_labels, disease_labels = load_packets()
    obs, exc = store["observed"], store["excluded"]
    curated = curated_frequencies()

    # ---- 1. what the patients give us ---------------------------------------------------
    rows = []
    # Sorted: these rows are stable-sorted and truncated below, and a seeded bootstrap later
    # indexes this same sequence — so an unordered source feeds a different sample into a
    # deliberately reproducible interval.
    for key in sorted(set(obs) | set(exc)):
        o, e = obs.get(key, 0), exc.get(key, 0)
        assessed = o + e
        if assessed < MIN_ASSESSED:
            continue
        did, term = key
        rows.append({
            "disease": did,
            "diseaseLabel": disease_labels.get(did, did),
            "term": term,
            "termLabel": term_labels.get(term, term),
            "observed": o,
            "excluded": e,
            "assessed": assessed,
            "frequency": round(o / assessed, 4),
        })
    rows.sort(key=lambda r: -r["assessed"])

    diseases_with_denominator = {r["disease"] for r in rows}
    assessed_values = sorted(r["assessed"] for r in rows)

    def q(v, p):
        return v[min(len(v) - 1, int(len(v) * p))] if v else None

    # ---- 2. where both exist, do they agree? -------------------------------------------
    compared = []
    for r in rows:
        c = curated.get((r["disease"], r["term"]))
        if not c or c["point"] is None:
            continue
        compared.append({
            **r,
            "curatedRaw": c["raw"],
            "curatedK": c["k"], "curatedN": c["n"], "curatedPoint": round(c["point"], 4),
            "difference": round(r["frequency"] - c["point"], 4),
            # A curated value from a bigger series than ours is not "disagreeing with the
            # patients" - it may be the better number. Which denominator is larger is the
            # first thing a reader needs.
            "biggerDenominator": "curated" if (c["n"] or 0) > r["assessed"] else "patients",
        })
    compared.sort(key=lambda r: -abs(r["difference"]))

    big_gaps = [r for r in compared if abs(r["difference"]) >= 0.5]
    agree = [r for r in compared if abs(r["difference"]) < 0.2]

    # Diseases where the patients give a denominator and the catalogue gives nothing at all.
    curated_diseases = {d for d, _ in curated}
    new_denominators = sorted(diseases_with_denominator - curated_diseases)

    # ---- 3. THE SINGLE-CASE BIAS, which is Stage 1 in miniature -------------------------
    # A curated frequency of 1/1 says "100%": one patient was written up and had the
    # feature. That is a selected observation - the first patient reported is not a random
    # patient - and this library exists because selecting on the largest of a few noisy
    # estimates is positively biased. Here the bias can be MEASURED, because the patient set
    # says what happened when more people were assessed for the same feature.
    by_curated_n = defaultdict(list)
    for r in compared:
        n = r["curatedN"] or 0
        bucket = "n=1" if n == 1 else "n=2-4" if n <= 4 else "n=5-19" if n <= 19 else "n>=20"
        by_curated_n[bucket].append(r)

    single_case_bias = {}
    for bucket, rs in by_curated_n.items():
        diffs = [r["difference"] for r in rs]
        single_case_bias[bucket] = {
            "pairs": len(rs),
            "meanCuratedPoint": round(sum(r["curatedPoint"] for r in rs) / len(rs), 4),
            "meanPatientFrequency": round(sum(r["frequency"] for r in rs) / len(rs), 4),
            # Negative means the curated value is HIGHER than what the patients show.
            "meanDifference": round(sum(diffs) / len(diffs), 4),
            "curatedOverstatesBy20OrMore": sum(1 for d in diffs if d <= -0.2),
            "share": round(sum(1 for d in diffs if d <= -0.2) / len(rs), 4),
        }
    # ---- THE INTERVAL ON THE STRONGEST CLAIM THIS PROJECT MAKES -------------------------
    # `tools/intervals.py` could not compute this from the artefact, because the artefact
    # ships only the worst-disagreement head - and bootstrapping a head that was selected
    # for large differences returns a large difference, which is a tautology wearing an
    # interval. So it is computed HERE, where the full 16,276 comparisons exist.
    #
    # THE RESAMPLING UNIT IS THE DISEASE, not the pair. Two features of one disease share
    # patients, a curator and usually a publication; treating them as independent narrows
    # the interval in exactly the direction that flatters the claim. This library exists
    # because a null fitted on the wrong resampling unit produced a z of -4.09 for two
    # months (lineage.md §8a), and repeating that here would be unforgivable.
    rng = np.random.default_rng(20260827)
    RESAMPLES = 4000

    for bucket, rs in by_curated_n.items():
        by_disease: dict[str, list] = defaultdict(list)
        for r in rs:
            by_disease[r["disease"]].append(r)
        keys = list(by_disease)
        if len(keys) < 2:
            single_case_bias[bucket]["interval"] = {
                "method": "not computed", "says": "fewer than two diseases to resample"}
            continue
        draws_diff, draws_cur, draws_pat = [], [], []
        for _ in range(RESAMPLES):
            picked = rng.integers(0, len(keys), len(keys))
            pool = [r for i in picked for r in by_disease[keys[i]]]
            if not pool:
                continue
            draws_diff.append(sum(r["difference"] for r in pool) / len(pool))
            draws_cur.append(sum(r["curatedPoint"] for r in pool) / len(pool))
            draws_pat.append(sum(r["frequency"] for r in pool) / len(pool))
        q = lambda a, p: float(np.percentile(np.asarray(a, dtype=float), p))
        single_case_bias[bucket]["interval"] = {
            "method": f"cluster bootstrap over {len(keys)} diseases, {RESAMPLES} resamples",
            "diseases": len(keys),
            "meanDifference": [round(q(draws_diff, 2.5), 4), round(q(draws_diff, 97.5), 4)],
            "meanCuratedPoint": [round(q(draws_cur, 2.5), 4), round(q(draws_cur, 97.5), 4)],
            "meanPatientFrequency": [round(q(draws_pat, 2.5), 4), round(q(draws_pat, 97.5), 4)],
            "excludesZero": q(draws_diff, 97.5) < 0 or q(draws_diff, 2.5) > 0,
        }

    order = ["n=1", "n=2-4", "n=5-19", "n>=20"]
    payload_bias = {
        "byCuratedDenominator": {k: single_case_bias[k] for k in order if k in single_case_bias},
        "says": (
            "A curated frequency of 1/1 reads as 100%, and it is a SELECTED observation: the "
            "first patient written up is not a random patient. This library exists because "
            "selecting the largest of a few noisy estimates is positively biased, and here "
            "the bias is measurable - the patient set says what happened when more people "
            "were assessed for the same feature."
        ),
    }

    payload = {
        "generated": "tools/patient_frequencies.py",
        "input": str(path.relative_to(ROOT)).replace("\\", "/"),
        "premise": (
            "Every other source here is aggregate and reports what a disease does. A "
            "phenopacket reports what happened to a person, and the difference is a "
            "denominator. An EXCLUDED phenotype is a patient examined for a feature who did "
            "not have it, which is what makes observed/(observed+excluded) a real rate."
        ),
        "caveat": (
            "phenopacket-store is built from published case reports and series, so it "
            "carries publication bias in full: a patient reaches it by being written up. "
            "Nothing here is a population frequency, and the comparison against the curated "
            "value is meaningful only as two readings of the same literature."
        ),
        "scale": {
            "patients": sum(len(v) for v in store["patients"].values()),
            "distinctDiseases": len(store["patients"]),
            "publications": len({p for v in store["publications"].values() for p in v}),
            "featurePairs": len(rows),
            "diseasesWithAComputedDenominator": len(diseases_with_denominator),
            "minAssessed": MIN_ASSESSED,
        },
        "denominators": {
            "median": q(assessed_values, 0.5),
            "p75": q(assessed_values, 0.75),
            "p95": q(assessed_values, 0.95),
            "max": assessed_values[-1] if assessed_values else None,
            "atLeastTen": sum(1 for v in assessed_values if v >= 10),
            "atLeastThirty": sum(1 for v in assessed_values if v >= 30),
        },
        "agreement": {
            "comparable": len(compared),
            "within20points": len(agree),
            "differBy50PointsOrMore": len(big_gaps),
            "biggerDenominator": dict(Counter(r["biggerDenominator"] for r in compared)),
            "worst": compared[:25],
        },
        "singleCaseBias": payload_bias,
        "diseasesWithNoCuratedFrequencyAtAll": len(new_denominators),
        "rows": rows[:400],
        "finding": "",
    }

    if compared:
        payload["finding"] = (
            "%d disease-feature pairs can be compared. %d agree within 20 percentage points "
            "and %d differ by 50 or more. In %d of the comparable pairs the PATIENT set has "
            "the larger denominator, which is the case where the curated value is the one "
            "that should move."
            % (len(compared), len(agree), len(big_gaps),
               payload["agreement"]["biggerDenominator"].get("patients", 0))
        )

    RARE.mkdir(parents=True, exist_ok=True)
    dest = RARE / "patient_frequencies.json"
    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    s, d = payload["scale"], payload["denominators"]
    print("wrote %s" % dest.relative_to(ROOT))
    print("  %s patients across %s diseases, from %s publications"
          % (f"{s['patients']:,}", f"{s['distinctDiseases']:,}", f"{s['publications']:,}"))
    print("  %s disease-feature pairs with a computed denominator (>= %d assessed)"
          % (f"{s['featurePairs']:,}", MIN_ASSESSED))
    print("  denominators: median %s, p95 %s, max %s — %s pairs at 10+, %s at 30+"
          % (d["median"], d["p95"], d["max"], f"{d['atLeastTen']:,}",
             f"{d['atLeastThirty']:,}"))
    print("  %s diseases get a denominator the curated record never gave them"
          % f"{payload['diseasesWithNoCuratedFrequencyAtAll']:,}")
    print()
    print("  %s" % payload["finding"])
    print()
    print("  THE SINGLE-CASE BIAS, by the denominator the CATALOGUE used:")
    print("  %-8s %7s %14s %14s %12s   %s" % ("curated", "pairs", "curated mean",
                                              "patient mean", "overstated", "interval"))
    for bucket, v in payload_bias["byCuratedDenominator"].items():
        iv = v.get("interval", {})
        ci = iv.get("meanDifference")
        print("  %-8s %7s %14.3f %14.3f %11.1f%%   %s"
              % (bucket, f"{v['pairs']:,}", v["meanCuratedPoint"],
                 v["meanPatientFrequency"], 100 * v["share"],
                 (f"diff 95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]"
                  f"{'  EXCLUDES 0' if iv.get('excludesZero') else '  INCLUDES 0'}")
                 if ci else "no interval"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
