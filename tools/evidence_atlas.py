#!/usr/bin/env python
"""How much of the rare-disease phenotype is actually measured — for the whole catalogue.

WHY THIS FILE EXISTS. `tools/dossier.py` grades every sign of a disease by how much is known
behind it: a fraction with a real denominator, a fraction of one patient, an unquantified
class, or nothing. Applied to Duchenne it produced the sharpest result on the dashboard —
not one of 39 recorded signs is estimated from more than a single patient.

That was computed for **twelve** diseases. The catalogue holds **12,958**. A finding that
holds on a hand-picked dozen is an anecdote with arithmetic attached, and the twelve were
picked partly because they are well studied, so the sample is biased in the direction that
makes the finding look mild. This file asks the same question of everything, so the claim
either generalises or dies.

FOUR MEASUREMENTS.

  1. THE FIELD'S EVIDENCE PROFILE. Every annotation in phenotype.hpoa, graded. How many
     diseases have even ONE sign estimated from a real series, and what the denominators
     look like when they exist.

  2. BY ORGAN SYSTEM. Signs rolled up the HPO `is_a` graph. Which systems the field
     quantifies and which it only ever describes - across the whole catalogue rather than
     one disease at a time.

  3. AGAINST RARITY. Whether quantification tracks prevalence band. The streetlight claim
     predicts the rarest diseases are the least measured; that is testable here and it is
     allowed to come back the other way, as the streetlight test itself already did.

  4. AGAINST ATTENTION. Whether a disease with more annotations is more likely to have a
     quantified one - the ascertainment axis, applied to evidence quality rather than to
     gene discovery.

WHAT THIS CANNOT SAY. Absence of a frequency in HPO is not absence of knowledge in the
world: a frequency can be published in a paper nobody curated into the ontology. So every
number below is a statement about the CURATED RECORD, which is the thing every downstream
computation in this repository actually reads. That is the honest framing and it is also the
useful one - a pipeline cannot use a number that is not in its inputs.

    python tools/evidence_atlas.py     # writes out/rare/evidence_atlas.json

Stdlib only.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import pathlib
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "rare"


def _load_dossier_module():
    """Import the grading rules rather than restating them.

    ONE DEFINITION, DELIBERATELY. The four evidence grades and the ontology walk live in
    `tools/dossier.py`. Copying them here would give the repository two definitions of what
    "quantified" means, and they would drift - which is the same failure as A11 in
    docs/audit.md, where one file read a corpus two ways and nobody compared the answers.
    """
    spec = importlib.util.spec_from_file_location("dossier", ROOT / "tools" / "dossier.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    d = _load_dossier_module()

    parents, term_names = d.hpo_graph()
    systems = d.organ_systems(parents)
    # The rollup is the expensive part: 285,603 annotations over a 20,413-term DAG. Cached
    # per term, because the same sign appears in hundreds of diseases.
    system_cache: dict[str, frozenset] = {}

    def systems_for(term: str) -> frozenset:
        hit = system_cache.get(term)
        if hit is None:
            hit = frozenset(d.systems_of(term, parents, systems))
            system_cache[term] = hit
        return hit

    # ---- 1. grade every annotation -----------------------------------------------------
    per_disease: dict[str, Counter] = defaultdict(Counter)
    denominators: dict[str, list[int]] = defaultdict(list)
    disease_names: dict[str, str] = {}
    by_system: dict[str, Counter] = defaultdict(Counter)
    annotations = 0

    path = BY_KEY["hpo_annotations"].dest
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            header = line.rstrip("\n").split("\t")
            break
        idx = {name: i for i, name in enumerate(header)}
        reader = csv.reader(fh, delimiter="\t")
        for row in reader:
            if len(row) <= idx["aspect"]:
                continue
            # Aspect P is the phenotype layer. I (inheritance), C (clinical course) and M
            # (modifier) are different statements and are not signs.
            if row[idx["aspect"]] != "P":
                continue
            disease = row[idx["database_id"]]
            term = row[idx["hpo_id"]]
            freq = d.parse_frequency(row[idx["frequency"]].strip())
            grade = d.grade_sign(freq)

            annotations += 1
            disease_names.setdefault(disease, row[idx["disease_name"]])
            per_disease[disease][grade] += 1
            if grade == "quantified" and freq and freq.get("n"):
                denominators[disease].append(freq["n"])
            for sys_id in systems_for(term):
                by_system[sys_id][grade] += 1

    # ---- 2. the field's profile --------------------------------------------------------
    diseases = len(per_disease)
    with_quantified = sum(1 for c in per_disease.values() if c["quantified"])
    with_any_fraction = sum(1 for c in per_disease.values()
                            if c["quantified"] or c["single-case"])
    only_class_or_none = sum(1 for c in per_disease.values()
                             if not c["quantified"] and not c["single-case"])
    nothing_at_all = sum(1 for c in per_disease.values()
                         if c["none"] and not (c["quantified"] or c["single-case"] or c["class"]))

    all_denominators = sorted(n for v in denominators.values() for n in v)

    def pct(v, of):
        return round(v / of, 4) if of else None

    def quantile(values, q):
        return values[min(len(values) - 1, int(len(values) * q))] if values else None

    profile = {
        "diseasesWithPhenotypeAnnotations": diseases,
        "annotations": annotations,
        "diseasesWithAQuantifiedSign": with_quantified,
        "shareWithAQuantifiedSign": pct(with_quantified, diseases),
        "diseasesWithAnyFraction": with_any_fraction,
        "diseasesWithNoFractionAtAll": only_class_or_none,
        "shareWithNoFractionAtAll": pct(only_class_or_none, diseases),
        "diseasesWithNoFrequencyAnywhere": nothing_at_all,
        "annotationsByGrade": dict(sum(per_disease.values(), Counter()).most_common()),
        "denominators": {
            "count": len(all_denominators),
            "min": all_denominators[0] if all_denominators else None,
            "p25": quantile(all_denominators, 0.25),
            "median": quantile(all_denominators, 0.5),
            "p75": quantile(all_denominators, 0.75),
            "p95": quantile(all_denominators, 0.95),
            "max": all_denominators[-1] if all_denominators else None,
            # The number that matters for Stage 2: how many quantified signs rest on a
            # series small enough that the estimate is nearly uninformative.
            "underTen": sum(1 for n in all_denominators if n < 10),
            "underThirty": sum(1 for n in all_denominators if n < 30),
        },
    }

    # ---- 3. by organ system ------------------------------------------------------------
    system_rows = []
    for sys_id, counts in by_system.items():
        total = sum(counts.values())
        system_rows.append({
            "id": sys_id,
            "name": term_names.get(sys_id, sys_id),
            "signs": total,
            "byGrade": {g: counts[g] for g in d.EVIDENCE_GRADES},
            "shareQuantified": pct(counts["quantified"], total),
        })
    system_rows.sort(key=lambda r: -r["signs"])

    # ---- 4. against rarity and against attention ---------------------------------------
    atlas_path = DEST / "atlas.json"
    by_band: dict[str, Counter] = defaultdict(Counter)
    band_note = None
    if atlas_path.exists():
        atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
        # The atlas keys prevalence by ORPHA code; the annotation file is mostly OMIM. Only
        # the intersection can be tested, and its size is reported rather than hidden.
        prevalence = {row["id"]: row.get("prevalence")
                      for row in atlas.get("diseases", [])} if atlas.get("diseases") else {}
        if not prevalence:
            band_note = ("atlas.json carries no per-disease prevalence in this release, so "
                         "the rarity cross-tabulation is not computed rather than "
                         "approximated.")
        for disease, counts in per_disease.items():
            band = prevalence.get(disease)
            if band:
                by_band[band]["diseases"] += 1
                if counts["quantified"]:
                    by_band[band]["withQuantified"] += 1

    # Attention: annotation count against whether anything is quantified. Same proxy
    # tools/atlas_bias.py uses, applied to evidence quality rather than to gene discovery.
    sizes_q, sizes_nq = [], []
    for counts in per_disease.values():
        total = sum(counts.values())
        (sizes_q if counts["quantified"] else sizes_nq).append(total)
    sizes_q.sort()
    sizes_nq.sort()

    attention = {
        "medianAnnotationsWhenQuantified": quantile(sizes_q, 0.5),
        "medianAnnotationsWhenNot": quantile(sizes_nq, 0.5),
        "says": (
            "A disease with a quantified sign carries a median of %s annotations against %s "
            "for one without. Quantification is not independent of how much a disease was "
            "looked at, which means the share above is an upper bound on how well the "
            "UNSTUDIED half of the catalogue is measured."
            % (quantile(sizes_q, 0.5), quantile(sizes_nq, 0.5))
        ),
    }

    payload = {
        "generated": "tools/evidence_atlas.py",
        "input": str(path.relative_to(ROOT)).replace("\\", "/"),
        "premise": (
            "tools/dossier.py grades the evidence behind a sign, and found that not one of "
            "Duchenne's 39 recorded signs rests on more than a single patient. That was "
            "twelve diseases. This asks the same question of all of them, so the claim "
            "either generalises or dies."
        ),
        "caveat": (
            "Absence of a frequency in HPO is not absence of knowledge in the world - a "
            "frequency can be published and never curated. Every number here is a statement "
            "about the CURATED RECORD, which is what every downstream computation in this "
            "repository actually reads."
        ),
        "grades": d.EVIDENCE_GRADES,
        "profile": profile,
        "bySystem": system_rows,
        "byPrevalenceBand": {k: dict(v) for k, v in by_band.items()},
        "byPrevalenceBandNote": band_note,
        "attention": attention,
    }

    DEST.mkdir(parents=True, exist_ok=True)
    out = DEST / "evidence_atlas.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    p = profile
    print("wrote %s" % out.relative_to(ROOT))
    print("  %s diseases, %s phenotype annotations"
          % (f"{p['diseasesWithPhenotypeAnnotations']:,}", f"{p['annotations']:,}"))
    print("  %s (%.1f%%) have at least ONE sign estimated from a real series"
          % (f"{p['diseasesWithAQuantifiedSign']:,}", 100 * p["shareWithAQuantifiedSign"]))
    print("  %s (%.1f%%) have no fraction of any kind, anywhere"
          % (f"{p['diseasesWithNoFractionAtAll']:,}", 100 * p["shareWithNoFractionAtAll"]))
    dn = p["denominators"]
    print("  denominators: median %s, p95 %s, max %s — %s of %s are under 10"
          % (dn["median"], dn["p95"], dn["max"], f"{dn['underTen']:,}", f"{dn['count']:,}"))
    print("  %s" % attention["says"])
    print("  worst-quantified systems:")
    for row in sorted(system_rows[:14], key=lambda r: r["shareQuantified"] or 0)[:5]:
        print("    %-46s %6s signs, %.1f%% quantified"
              % (row["name"][:46], f"{row['signs']:,}", 100 * (row["shareQuantified"] or 0)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
