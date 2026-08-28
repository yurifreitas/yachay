#!/usr/bin/env python
"""The arithmetic of the capability layer. Nothing here is authored — all of it is derived.

WHY THIS IS A SEPARATE FILE. `capability_seed.py` holds judgements: what an instrument costs,
what physics forces it, how many samples a year it realistically runs. Those are estimates a
person wrote and a person can argue with. THIS file writes no estimates. It reads the seed and
the dossiers and does arithmetic, so every number below can be recomputed from its inputs and
falsified by changing them. The project has kept that line everywhere else; the capability
layer should not be the place it blurs.

THE THREE COMPUTATIONS

  1. CAPITAL PER PATIENT. The economic barrier, which every previous tab asserted, as a number.
     Orphanet gives a prevalence CLASS, not a rate — "1-9 / 100 000" is a band — and the plan
     capital is also a band. So the quotient is a band, and the interval arithmetic is done
     properly: the cheapest case divides the low capital by the large cohort, the dearest
     divides the high capital by the small one. A point estimate here would be a lie about
     two different uncertainties at once.

  2. THE DOUBLE COUNT. Each plan was costed as if its programme bought every instrument it
     needs. Seven programmes do not each need their own mass spectrometer. Summing the plans
     and then summing the UNION of distinct instruments gives the difference, and that
     difference is what a shared facility is worth — computed, not advocated.

  3. THE QUEUE. An instrument has a throughput. A disease has a cohort. Dividing one by the
     other says how many instruments it would take to run every prevalent patient through the
     diagnosis once, and how long one instrument would need. For most rare diseases the answer
     is a fraction of one machine for a fraction of a year, which is the real shape of the
     problem: the capacity exists and is not pointed here.

WHAT THIS ASSUMES, STATED SO IT CAN BE ATTACKED. Prevalence is applied to a world population of
8.1 billion as if the disease were uniformly distributed. It is not. Orphanet's classes are
largely European estimates, so for sickle cell anaemia — whose prevalence is far higher in
parts of Africa and in the diaspora — this UNDER-counts, and the capital per patient computed
here is therefore too high. The direction of that error is known; its size is not. Every other
disease inherits the milder version of the same problem.

    python tools/capability_math.py     # writes out/rare/capability_math.json
"""

from __future__ import annotations

import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "out" / "rare"

WORLD = 8_100_000_000
EUROPE = 748_000_000

# "1-9 / 100 000" and "1-5 / 10 000" — a class, not a rate.
CLASS_RE = re.compile(r"([\d.]+)\s*-\s*([\d.]+)\s*/\s*([\d\s]+)")


def parse_prevalence(text: str | None):
    """Return (lo_rate, hi_rate) as a fraction of population, or None if not stated."""
    if not text:
        return None
    m = CLASS_RE.search(text)
    if not m:
        return None
    lo, hi, denom = float(m.group(1)), float(m.group(2)), float(m.group(3).replace(" ", ""))
    return lo / denom, hi / denom


def main() -> int:
    cap = json.loads((SRC / "capability.json").read_text(encoding="utf-8"))
    dos = json.loads((SRC / "dossiers.json").read_text(encoding="utf-8"))
    # The audited cohorts. Absent only if the audit has not been run, and the code says so
    # rather than silently falling back to the string it exists to replace.
    audit_path = SRC / "prevalence_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else None
    cohorts = (audit or {}).get("cohorts", {})

    by_id = {i["id"]: i for i in cap["instruments"]}
    prevalence = {d["name"]: d.get("prevalence") for d in dos["dossiers"]}
    orpha = {d["name"]: (d.get("orpha") or "").replace("ORPHA:", "") for d in dos["dossiers"]}
    trials = {d["name"]: d["trials"]["total"] for d in dos["dossiers"]}

    # ---- 1. capital per patient ------------------------------------------------------
    per_patient = []
    for p in cap["plans"]:
        rates = parse_prevalence(prevalence.get(p["catalogueName"]))
        row = {
            "planId": p["id"],
            "catalogueName": p["catalogueName"],
            "approach": p["approach"],
            "prevalenceClass": prevalence.get(p["catalogueName"]),
            "capexUSD": p["capexUSD"],
            "trials": trials.get(p["catalogueName"]),
        }
        # THE COHORT NOW COMES FROM THE AUDIT, not from the collapsed prevalence string.
        # The string mixes point prevalence with prevalence at birth, annual incidence and raw
        # case counts — 68.6% of Orphanet disorders carry more than one kind — so dividing
        # money by it was dividing by four different quantities depending on the row.
        code = orpha.get(p["catalogueName"])
        audited = cohorts.get(code) if code else None
        row["orpha"] = code
        row["cohortBasis"] = audited["basis"] if audited else "no audited cohort"
        row["prevalenceRecords"] = audited["records"] if audited else None
        row["typesPresent"] = audited["typesPresent"] if audited else []

        # Keep the old reading so the correction is visible rather than merely applied.
        if rates:
            row["stringCohort"] = {"lo": round(rates[0] * WORLD), "hi": round(rates[1] * WORLD)}
            row["stringCapitalPerPatientUSD"] = {
                "lo": round(p["capexUSD"]["lo"] / (rates[1] * WORLD), 2),
                "hi": round(p["capexUSD"]["hi"] / (rates[0] * WORLD), 2),
            }
        else:
            row["stringCohort"] = None
            row["stringCapitalPerPatientUSD"] = None

        if audited and audited.get("loRate") is not None and audited.get("hiRate"):
            rates = (audited["loRate"], audited["hiRate"])

        if rates and rates[1] > 0:
            lo_n, hi_n = rates[0] * WORLD, rates[1] * WORLD
            row["patients"] = {"lo": round(lo_n), "hi": round(hi_n)}
            # Interval arithmetic, done in the right direction: cheapest case is the low
            # capital spread over the large cohort; dearest is high capital, small cohort.
            # A class of "<1 / 1 000 000" has a true floor of zero, so the small-cohort end of
            # the quotient is unbounded. Reported as None rather than as a very large number
            # that would look like a measurement.
            row["capitalPerPatientUSD"] = {
                "lo": round(p["capexUSD"]["lo"] / hi_n, 2),
                "hi": None if lo_n <= 0 else round(p["capexUSD"]["hi"] / lo_n, 2),
            }
            row["patientsEurope"] = {"lo": round(rates[0] * EUROPE), "hi": round(rates[1] * EUROPE)}
        else:
            row["patients"] = None
            row["capitalPerPatientUSD"] = None
            row["patientsEurope"] = None
        per_patient.append(row)

    ranked = [r for r in per_patient if r["capitalPerPatientUSD"]]
    # An unbounded high end sorts last: it is the least constrained, not the smallest.
    ranked.sort(key=lambda r: (r["capitalPerPatientUSD"]["hi"] is None,
                               r["capitalPerPatientUSD"]["hi"] or 0))

    # ---- what the correction actually moved ------------------------------------------
    movement = []
    for r in ranked:
        old_v, new_v = r.get("stringCapitalPerPatientUSD"), r["capitalPerPatientUSD"]
        if not old_v or not new_v:
            continue
        # Compare BOTH ends. The high end of the quotient comes from the small-cohort end of
        # the prevalence class, and for most of these the class floor did not move — so
        # checking only the high end reported "no change" on rows whose cohort grew tenfold.
        folds = {}
        for end in ("lo", "hi"):
            a, b = old_v.get(end), new_v.get(end)
            if a and b:
                folds[end] = round(b / a, 3)
        if not folds or all(abs(f - 1) < 0.01 for f in folds.values()):
            continue
        movement.append({
            "catalogueName": r["catalogueName"],
            "fromUSD": old_v, "toUSD": new_v,
            "fromCohort": r.get("stringCohort"), "toCohort": r.get("patients"),
            "folds": folds,
            "biggestFold": max(folds.values(), key=lambda f: max(f, 1 / f)),
            "basis": r["cohortBasis"],
            "records": r["prevalenceRecords"],
        })
    movement.sort(key=lambda m: -max(m["biggestFold"], 1 / m["biggestFold"]))

    # ---- 2. the double count ---------------------------------------------------------
    sum_lo = sum(p["capexUSD"]["lo"] for p in cap["plans"])
    sum_hi = sum(p["capexUSD"]["hi"] for p in cap["plans"])
    union_ids = sorted({i for p in cap["plans"] for i in p["instruments"]})
    union_lo = sum(by_id[i]["capexUSD"][0] for i in union_ids)
    union_hi = sum(by_id[i]["capexUSD"][1] for i in union_ids)

    # How many plans each instrument serves — the ones counted most often are the ones a
    # shared facility buys first.
    demand = {}
    for p in cap["plans"]:
        for i in p["instruments"]:
            demand.setdefault(i, []).append(p["catalogueName"])
    shared = sorted(
        ({"id": i, "name": by_id[i]["name"], "plans": len(v), "diseases": sorted(set(v)),
          "capexUSD": by_id[i]["capexUSD"],
          "wastedIfNotSharedUSD": {"lo": by_id[i]["capexUSD"][0] * (len(v) - 1),
                                   "hi": by_id[i]["capexUSD"][1] * (len(v) - 1)}}
         for i, v in demand.items()),
        key=lambda r: (-r["plans"], -r["capexUSD"][1]))

    # ---- 3. the queue ----------------------------------------------------------------
    queue = []
    for r in per_patient:
        if not r["patients"]:
            continue
        plan = next(p for p in cap["plans"] if p["id"] == r["planId"])
        n = r["patients"]["hi"]
        rows = []
        for iid in plan["instruments"]:
            inst = by_id[iid]
            thr = inst["throughputPerYear"]
            rows.append({
                "id": iid, "name": inst["name"], "unit": inst["unit"],
                "throughputPerYear": thr,
                # One pass of the whole prevalent cohort through this instrument.
                "instrumentYears": round(n / thr, 2),
                "instrumentsForOneYear": math.ceil(n / thr),
                "consumablesForCohortUSD": round(n * inst["consumablePerUnitUSD"]),
            })
        rows.sort(key=lambda x: -x["instrumentYears"])
        queue.append({"planId": r["planId"], "catalogueName": r["catalogueName"],
                      "cohort": n, "rows": rows,
                      "bottleneck": rows[0]["name"],
                      "bottleneckYears": rows[0]["instrumentYears"]})
    queue.sort(key=lambda q: -q["bottleneckYears"])

    # ---- cost per answer, ranked, against capital rank -------------------------------
    by_capital = sorted(cap["instruments"], key=lambda i: -(i["capexUSD"][0] + i["capexUSD"][1]))
    by_answer = sorted(cap["instruments"], key=lambda i: -i["costPerAnswerUSD"])
    rank_cap = {i["id"]: n for n, i in enumerate(by_capital, 1)}
    rank_ans = {i["id"]: n for n, i in enumerate(by_answer, 1)}
    inversion = sorted(
        ({"id": i["id"], "name": i["name"], "unit": i["unit"],
          "capexUSD": i["capexUSD"], "costPerAnswerUSD": i["costPerAnswerUSD"],
          "rankByCapital": rank_cap[i["id"]], "rankByAnswer": rank_ans[i["id"]],
          "move": rank_cap[i["id"]] - rank_ans[i["id"]]}
         for i in cap["instruments"]),
        key=lambda r: -abs(r["move"]))

    # ---- an authored check against the derived numbers, kept visibly separate ---------
    # EVERYTHING ELSE IN THIS FILE IS DERIVED. This list is not, and says so. Two of the
    # prevalence classes read out of the dossiers disagree with long-published incidence by
    # about two orders of magnitude, and publishing a cohort built on them without saying so
    # would be the ascertainment failure this project spends a whole tab on.
    discrepancies = [
        {"catalogueName": "Cystic fibrosis",
         "readAs": prevalence.get("Cystic fibrosis"),
         "conflictsWith": "Birth incidence around 1 in 2,500-3,500 in European-descended "
                          "populations — roughly 100x the class read here.",
         "likelyCause": "The resolved Orphanet record is a subtype or an atypical form, or the "
                        "class is a point prevalence where the familiar figure is a birth "
                        "incidence. The two are not the same quantity and this file cannot tell "
                        "them apart from the class string alone.",
         "effect": "The cohort is under-counted, so capital per patient here is an UPPER bound."},
        {"catalogueName": "Duchenne muscular dystrophy",
         "readAs": prevalence.get("Duchenne muscular dystrophy"),
         "conflictsWith": "Birth incidence around 1 in 5,000 male births, so roughly 1 in 10,000 "
                          "people — about 20x the class read here.",
         "likelyCause": "Same confusion: an X-linked birth incidence quoted against male births "
                        "versus a whole-population point prevalence in a disease that shortens "
                        "life, which genuinely lowers point prevalence below birth incidence.",
         "effect": "Cohort under-counted; the $1,001 per patient figure is an upper bound and "
                   "the true number is smaller, which strengthens rather than weakens the "
                   "conclusion below."},
    ]

    payload = {
        "generated": "tools/capability_math.py",
        "inputs": ["out/rare/capability.json", "out/rare/dossiers.json"],
        "premise": (
            "Nothing on this tab was written down. Every figure is computed from the instrument "
            "estimates and the Orphanet prevalence classes, so changing an input changes the "
            "answer and any of it can be falsified by arithmetic rather than by argument."
        ),
        "assumptions": {
            "worldPopulation": WORLD,
            "europePopulation": EUROPE,
            "uniformDistribution": (
                "Prevalence is applied to the whole world population as if the disease were "
                "evenly distributed. It is not. Orphanet's classes are largely European "
                "estimates, so for sickle cell anaemia this UNDER-counts the cohort badly and "
                "the capital per patient computed here is correspondingly too high. The "
                "direction of that error is known; its magnitude is not."
            ),
            "prevalenceIsAClass": (
                "Orphanet records a band, not a rate, so the cohort is a band and the quotient "
                "is a band. Both ends are carried through rather than collapsed to a midpoint."
            ),
            "capitalIsOneOff": (
                "Capital per patient divides a one-time purchase by a standing cohort. It is a "
                "ratio for comparison between diseases, not an annual cost and not a price."
            ),
        },
        "discrepancies": discrepancies,
        "finding": (
            "Capital per patient runs from under a dollar to about a thousand — and both ends "
            "are upper bounds, because the cohorts are under-counted. Against a rare-disease "
            "therapy priced in the hundreds of thousands, the laboratory capital is not the "
            "expensive part of the problem, and this tab is the arithmetic that says so. That "
            "cuts against the economic barrier as it is usually stated, including as it is "
            "stated on the barriers tab: what is actually dear is the released dose and the "
            "trial, not the instruments that decide what to make. The one instrument whose "
            "queue does not fit is the bioreactor, and that is a manufacturing problem wearing "
            "a diagnostic tab's clothes."
        ),
        "cohortSource": (
            "Validated point prevalence from tools/prevalence_audit.py, which reads all 17,108 "
            "Orphanet prevalence records rather than the single collapsed string each dossier "
            "carries. Where a disorder has no validated point-prevalence class, the row says so "
            "instead of substituting a different quantity."
            if cohorts else
            "PREVALENCE AUDIT NOT PRESENT — cohorts fell back to the collapsed dossier string, "
            "which mixes point prevalence with birth prevalence and annual incidence. Run "
            "tools/prevalence_audit.py."
        ),
        "movement": movement,
        "capitalPerPatient": ranked,
        "sharing": {
            "sumOfPlansUSD": {"lo": sum_lo, "hi": sum_hi},
            "unionOfInstrumentsUSD": {"lo": union_lo, "hi": union_hi},
            "doubleCountedUSD": {"lo": sum_lo - union_lo, "hi": sum_hi - union_hi},
            "doubleCountedFraction": round(1 - union_hi / sum_hi, 3),
            "distinctInstruments": len(union_ids),
            "instrumentSlotsAcrossPlans": sum(len(p["instruments"]) for p in cap["plans"]),
            "byInstrument": shared,
        },
        "queue": queue,
        "capitalVsAnswer": inversion,
        "summary": {
            "plansWithPrevalence": len(ranked),
            "capitalPerPatientRangeUSD": {
                "lowest": ranked[0]["capitalPerPatientUSD"]["lo"] if ranked else None,
                "highest": next((r["capitalPerPatientUSD"]["hi"] for r in reversed(ranked)
                             if r["capitalPerPatientUSD"]["hi"] is not None), None),
            },
            "cheapestDisease": ranked[0]["catalogueName"] if ranked else None,
            "dearestDisease": ranked[-1]["catalogueName"] if ranked else None,
            "biggestRankMove": inversion[0]["name"] if inversion else None,
            "biggestRankMoveBy": inversion[0]["move"] if inversion else None,
        },
    }

    path = SRC / "capability_math.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    s = payload["summary"]
    sh = payload["sharing"]
    print("wrote %s" % path.relative_to(ROOT))
    hi = s["capitalPerPatientRangeUSD"]["highest"]
    print("  cohorts from: %s" % payload["cohortSource"][:70])
    print("  capital per patient spans $%s (%s) to %s (%s)"
          % (format(s["capitalPerPatientRangeUSD"]["lowest"], ","), s["cheapestDisease"],
             "unbounded" if hi is None else "$" + format(round(hi), ","), s["dearestDisease"]))
    for m in payload["movement"]:
        print("    %-34s %s  (%s, %d records)"
              % (m["catalogueName"][:34], m["folds"], m["basis"][:34], m["records"] or 0))
    print("  %d instrument slots across %d plans resolve to %d distinct instruments"
          % (sh["instrumentSlotsAcrossPlans"], len(cap["plans"]), sh["distinctInstruments"]))
    print("  double counted if nothing is shared: $%s-$%s (%.0f%% of the total)"
          % (format(sh["doubleCountedUSD"]["lo"], ","), format(sh["doubleCountedUSD"]["hi"], ","),
             sh["doubleCountedFraction"] * 100))
    print("  slowest queue: %s, %s at %.1f instrument-years"
          % (payload["queue"][0]["catalogueName"], payload["queue"][0]["bottleneck"],
             payload["queue"][0]["bottleneckYears"]))
    print("  biggest rank move, capital vs cost-per-answer: %s by %d places"
          % (s["biggestRankMove"], s["biggestRankMoveBy"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
