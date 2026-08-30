#!/usr/bin/env python
"""Does the kind of variant predict the phenotype? Asked per gene, on individual patients.

WHY THIS IS THE THING THE PATIENT DATA WAS FOR. `tools/patient_frequencies.py` reads the
phenotype half and `tools/patient_variants.py` reads the genotype half. Neither joins them,
and the join is the only thing an aggregate catalogue cannot do at all: a disease-level
record says "this disease involves seizures" and "this gene has nonsense variants", never
"the patients with nonsense variants had seizures and the ones with missense did not".

THE COMPARISON. Within one gene, split patients by the consequence of their variant:

    loss of function   nonsense or frameshift - a truncated or absent protein
    missense           one amino acid changed - a protein that is present and different

Those are different molecular events with different therapeutic consequences, and whether
they produce different patients is a question with an answer in this data. For each HPO
feature assessed in both groups, the frequency is `observed / (observed + excluded)` on each
side, and the difference is tested with Fisher's exact test.

THREE THINGS THIS FILE DOES THAT MAKE IT THIS REPOSITORY'S RATHER THAN A SCRIPT'S.

  1. IT USES STAGE 2 BEFORE IT REPORTS A RESULT. `sieve.stages.power` says what each
     comparison could have detected at these group sizes. A test that could not have found a
     50-point difference is reported as UNDERPOWERED rather than as "no difference", because
     those are not the same statement and conflating them is how a null result becomes a
     claim.

  2. IT CORRECTS FOR MULTIPLICITY. Thousands of feature-by-gene tests are run, and picking
     the smallest p-value out of thousands is itself a selection operator - the founding
     argument of this library, one level up. Benjamini-Hochberg across every test.

  3. IT REPORTS THE DENOMINATOR ON BOTH SIDES OF EVERY ROW. A difference between 3/4 and
     1/12 is not the same object as one between 60/80 and 20/100, and a table that shows
     only percentages hides which it is looking at.

WHAT IT CANNOT SAY. phenopacket-store holds published, solved cases: every ACMG class in it
is PATHOGENIC, and patients arrive by being written up. A phenotype recorded more often in
one group may be recorded more often because that group was studied by people who looked for
it. This measures the RECORD, and the record is what every downstream computation reads.

    python tools/genotype_phenotype.py     # writes out/rare/genotype_phenotype.json

Needs scipy and statsmodels, which are already dependencies.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import zipfile
from collections import Counter, defaultdict

from scipy.stats import fisher_exact
from statsmodels.stats.multitest import multipletests

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import sieve as sv  # noqa: E402
from sieve.pipeline.sources import BY_KEY  # noqa: E402

RARE = ROOT / "out" / "rare"

# A group smaller than this is not a group. Ten per side is already generous - Stage 2 says
# a 10-vs-10 comparison cannot detect anything short of enormous - and the power column
# reports exactly how generous.
MIN_PER_GROUP = 10
# The effect a reader would care about, in percentage points, used for the power annotation.
EFFECT_OF_INTEREST = 0.5


def _consequence_fn():
    """Import the classifier rather than restating it — one definition, as everywhere else."""
    spec = importlib.util.spec_from_file_location(
        "patient_variants", ROOT / "tools" / "patient_variants.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.consequence


def main() -> int:
    path = BY_KEY["phenopackets"].dest
    if not path.exists():
        raise SystemExit("missing %s — run python tools/ingest.py" % path.name)
    consequence = _consequence_fn()

    # ---- 1. assign each patient to one gene and one group ------------------------------
    # A patient with variants in more than one gene, or with both a truncating and a
    # missense allele, is EXCLUDED rather than assigned. Forcing them into a group would put
    # the ambiguous cases exactly where the comparison is being made.
    groups: dict[tuple[str, str], list] = defaultdict(list)
    skipped = Counter()

    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not name.endswith(".json"):
                continue
            p = json.loads(z.read(name))
            genes, classes = set(), set()
            for i in p.get("interpretations", []) or []:
                for g in (i.get("diagnosis") or {}).get("genomicInterpretations", []) or []:
                    vd = (g.get("variantInterpretation") or {}).get("variationDescriptor") or {}
                    expr = {e.get("syntax"): e.get("value")
                            for e in (vd.get("expressions") or [])}
                    sym = (vd.get("geneContext") or {}).get("symbol")
                    if sym:
                        genes.add(sym)
                        classes.add(consequence(expr.get("hgvs.p"), expr.get("hgvs.c")))
            if len(genes) != 1:
                skipped["not exactly one gene"] += 1
                continue
            gene = genes.pop()
            lof = bool(classes & {"nonsense", "frameshift"})
            mis = "missense" in classes
            if lof and mis:
                skipped["both truncating and missense"] += 1
                continue
            group = "LoF" if lof else "missense" if mis else None
            if group is None:
                skipped["neither class"] += 1
                continue

            feats = {}
            for f in p.get("phenotypicFeatures", []) or []:
                term = (f.get("type") or {}).get("id")
                if term:
                    feats[term] = {"present": not f.get("excluded"),
                                   "label": (f.get("type") or {}).get("label") or term}
            groups[(gene, group)].append(feats)

    # ---- 2. one test per gene x feature -------------------------------------------------
    tests = []
    genes = sorted({g for g, _ in groups})
    for gene in genes:
        lof = groups.get((gene, "LoF"), [])
        mis = groups.get((gene, "missense"), [])
        if len(lof) < MIN_PER_GROUP or len(mis) < MIN_PER_GROUP:
            continue
        terms = {t for pats in (lof, mis) for f in pats for t in f}
        # Sorted: the tests below are collected into a list that is later stable-sorted by
        # effect size and truncated, so an unordered source reshuffles which of several
        # equal-effect terms survives the cut. Set iteration order is not stable across
        # processes in Python.
        for term in sorted(terms):
            a = sum(1 for f in lof if t_in(f, term, True))
            b = sum(1 for f in lof if t_in(f, term, False))
            c = sum(1 for f in mis if t_in(f, term, True))
            d = sum(1 for f in mis if t_in(f, term, False))
            n_lof, n_mis = a + b, c + d
            if n_lof < MIN_PER_GROUP or n_mis < MIN_PER_GROUP:
                continue
            odds, p = fisher_exact([[a, b], [c, d]])
            f_lof, f_mis = a / n_lof, c / n_mis

            # STAGE 2, before the result is read. What could this comparison have found?
            try:
                floor = sv.min_detectable_proportion_difference(
                    min(n_lof, n_mis), max(min((f_lof + f_mis) / 2, 0.99), 0.01))
                powered = floor <= EFFECT_OF_INTEREST
            except sv.PowerError:
                floor, powered = None, False

            label = next((f[term]["label"] for pats in (lof, mis) for f in pats
                          if term in f), term)
            tests.append({
                "gene": gene, "term": term, "termLabel": label,
                "lofPresent": a, "lofAssessed": n_lof, "lofFrequency": round(f_lof, 4),
                "missensePresent": c, "missenseAssessed": n_mis,
                "missenseFrequency": round(f_mis, 4),
                "difference": round(f_lof - f_mis, 4),
                "p": p,
                "detectableFloor": floor,
                "powered": powered,
            })

    if not tests:
        raise SystemExit("no gene had two groups of at least %d assessed patients"
                         % MIN_PER_GROUP)

    # ---- 3. multiplicity: picking the smallest p out of thousands is a selection --------
    pvals = [t["p"] for t in tests]
    reject, qvals, _, _ = multipletests(pvals, alpha=0.05, method="fdr_bh")
    for t, q, r in zip(tests, qvals, reject):
        t["q"] = float(q)
        t["significant"] = bool(r)

    hits = sorted((t for t in tests if t["significant"]),
                  key=lambda t: -abs(t["difference"]))
    powered = [t for t in tests if t["powered"]]
    underpowered = [t for t in tests if not t["powered"]]
    # The honest denominator for "we found nothing": tests that were BOTH powered and null.
    powered_null = [t for t in powered if not t["significant"]]

    payload = {
        "generated": "tools/genotype_phenotype.py",
        "input": str(path.relative_to(ROOT)).replace("\\", "/"),
        "premise": (
            "An aggregate catalogue can say a disease involves seizures and that a gene has "
            "nonsense variants. Only patient-level data can say whether the patients with "
            "nonsense variants had the seizures. This joins the two halves the other two "
            "patient tools read separately."
        ),
        "caveat": (
            "phenopacket-store holds published, solved cases - every ACMG class in it is "
            "PATHOGENIC and patients arrive by being written up. A feature recorded more "
            "often in one group may be recorded more often because that group was studied "
            "by people looking for it. This measures the RECORD."
        ),
        "design": {
            "groups": "loss of function (nonsense or frameshift) versus missense",
            "minimumPerGroup": MIN_PER_GROUP,
            "test": "Fisher exact, two-sided",
            "multiplicity": "Benjamini-Hochberg across every test, alpha 0.05",
            "powerModel": ("sieve.stages.power - two-proportion normal approximation, "
                           "refused where it would be anti-conservative"),
            "effectOfInterest": EFFECT_OF_INTEREST,
            "patientsSkipped": dict(skipped),
        },
        "scale": {
            "genesCompared": len({t["gene"] for t in tests}),
            "tests": len(tests),
            "powered": len(powered),
            "underpowered": len(underpowered),
            "significantAfterCorrection": len(hits),
            "poweredAndNull": len(powered_null),
        },
        "hits": hits[:60],
        "finding": (
            "%d gene-feature comparisons across %d genes. %d could detect a %d-point "
            "difference at these group sizes and %d could not - so %d of the tests are "
            "incapable of the result they are being asked for. %d survive "
            "Benjamini-Hochberg."
            % (len(tests), len({t["gene"] for t in tests}), len(powered),
               int(EFFECT_OF_INTEREST * 100), len(underpowered), len(underpowered),
               len(hits))
        ),
    }

    RARE.mkdir(parents=True, exist_ok=True)
    dest = RARE / "genotype_phenotype.json"
    dest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    s = payload["scale"]
    print("wrote %s" % dest.relative_to(ROOT))
    print("  %d genes, %s tests" % (s["genesCompared"], f"{s['tests']:,}"))
    print("  powered for a %d-point difference: %s of %s (%.0f%%)"
          % (int(EFFECT_OF_INTEREST * 100), f"{s['powered']:,}", f"{s['tests']:,}",
             100 * s["powered"] / s["tests"]))
    print("  significant after Benjamini-Hochberg: %d" % s["significantAfterCorrection"])
    print("  powered AND null (a real negative): %s" % f"{s['poweredAndNull']:,}")
    print()
    if hits:
        print("  %-9s %-34s %11s %11s %8s %8s" % ("gene", "feature", "LoF", "missense",
                                                  "diff", "q"))
        for t in hits[:12]:
            print("  %-9s %-34s %4d/%-6d %4d/%-6d %+8.2f %8.1e"
                  % (t["gene"], t["termLabel"][:34], t["lofPresent"], t["lofAssessed"],
                     t["missensePresent"], t["missenseAssessed"], t["difference"], t["q"]))
    return 0


def t_in(feats: dict, term: str, present: bool) -> bool:
    """Was this feature assessed in this patient, with this polarity?"""
    f = feats.get(term)
    return bool(f) and f["present"] is present


if __name__ == "__main__":
    raise SystemExit(main())
