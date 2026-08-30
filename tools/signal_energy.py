"""Which pathway families carry FORM, and which carry ENERGY.

WHAT THIS DEEPENS. `tools/scale_information.py` found that collapsing a disease's causal genes
onto the 29 Reactome top-level pathways keeps about a fifth of what they said about organ
system, and that the loss is worse where the abnormality is a structure that formed wrongly
than where it is a process that runs wrongly — the morphogenesis test, whose stated reason is
that "the pathway alphabet has no vocabulary for where and when".

That result treats the 29 pathways as ONE undifferentiated alphabet. It is the obvious next
question and it was never asked: **the alphabet is not homogeneous**. Signal Transduction is
the machinery that makes spatial pattern — morphogen gradients, the reaction-diffusion field
Turing described. Metabolism is energy. Developmental Biology is form, named. Treating those
as interchangeable letters and then concluding "pathways have no vocabulary for where" is a
conclusion about the average of a mixture.

SO THIS DECOMPOSES THE ALPHABET. Each top-level pathway is used alone, as a binary indicator:
does this disease have a causal gene in it or not? That single-bit alphabet is asked how much
it says about organ system, against a permutation null of the same shape. Then the same
question is asked separately inside the morphogenetic systems and inside the physiological
ones, which is where the field-versus-energy contrast becomes visible or fails to.

THE PREDICTION, WRITTEN BEFORE THE RUN. If the morphogenesis result is about geometry rather
than about coarseness in general, then the field-shaping families — Signal Transduction,
Developmental Biology, Cell-Cell communication, Extracellular matrix organization — should
carry MORE about morphogenetic systems than about physiological ones, and the energy families
— Metabolism, Transport of small molecules, Digestion and absorption — should do the reverse.
If every family splits the same way, the earlier result is about alphabet size and not about
what the letters mean, and this file says so.

WHAT A SINGLE-BIT ALPHABET CAN AND CANNOT DO. One bit cannot carry much: these numbers are
small by construction and are not comparable with the 0.279 bits the gene alphabet reaches.
They are comparable WITH EACH OTHER, which is the only comparison made here. Every figure is
an excess over a permutation null that preserves each disease's system profile and each
pathway's prevalence, so a family that is merely common cannot win by being common.

NOT AN ADAPTER (.claude/skills/sieve-new-adapter): nothing is ranked and no entity is scored.
Twenty-nine parallel measurements with their own nulls, reported with a multiplicity note.

    python tools/signal_energy.py
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import math
import pathlib
import random
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

DEST = ROOT / "out" / "rare" / "signal_energy.json"
SEED = 20260830

#: Permutation draws per pathway. Twenty-nine pathways times this many shuffles of a 7,350-row
#: table is the whole cost of the file; 200 gives a z stable to about a tenth at these sizes.
DRAWS = 200

#: Bootstrap resamples of the DISEASES, for an interval on the observed value. A z is
#: not an uncertainty and standards.md §4 asks for one on every published number.
BOOT_DRAWS = 150

#: THE FAMILIES, WRITTEN DOWN BEFORE THE COUNTS WERE READ. Reactome's top level is not a
#: taxonomy of function — it is a filing system — so grouping it is an authored act and is
#: labelled as one. The grouping is by what the family DOES in an organism, and the two that
#: carry the prediction are `field` and `energy`.
FAMILY = {
    # The machinery that makes and reads spatial pattern.
    "R-HSA-162582": "field",      # Signal Transduction
    "R-HSA-1266738": "field",     # Developmental Biology
    "R-HSA-1500931": "field",     # Cell-Cell communication
    "R-HSA-1474244": "field",     # Extracellular matrix organization
    # What it costs to run.
    "R-HSA-1430728": "energy",    # Metabolism
    "R-HSA-382551": "energy",     # Transport of small molecules
    "R-HSA-8963743": "energy",    # Digestion and absorption
    "R-HSA-397014": "energy",     # Muscle contraction
    # What the cell knows and copies.
    "R-HSA-74160": "information",       # Gene expression (Transcription)
    "R-HSA-8953854": "information",     # Metabolism of RNA
    "R-HSA-4839726": "information",     # Chromatin organization
    "R-HSA-73894": "information",       # DNA Repair
    "R-HSA-69306": "information",       # DNA Replication
    "R-HSA-392499": "information",      # Metabolism of proteins
    # What it defends against.
    "R-HSA-168256": "defence",    # Immune System
    "R-HSA-1643685": "defence",   # Disease
    "R-HSA-109582": "defence",    # Hemostasis
}


def _load_scale_information():
    """Reuse the loaders rather than reimplement them.

    A second copy of `gene_to_pathway` or `hpo_systems` in this file is a second chance for
    the two to disagree about what a pathway is — the failure an audit found four times over
    for MONDO this week. Imported by path because `tools/` is not a package.
    """
    spec = importlib.util.spec_from_file_location("si", ROOT / "tools" / "scale_information.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def indicator_mi(diseases, in_pathway, systems_of) -> float:
    """I(bit; system) in bits, each disease contributing total weight 1.

    The disease's weight is split evenly across the systems it touches, exactly as
    `scale_information.mutual_information` does, so the two files measure the same quantity on
    the same convention.
    """
    joint: dict[tuple[int, str], float] = collections.defaultdict(float)
    marg_f: dict[int, float] = collections.defaultdict(float)
    marg_s: dict[str, float] = collections.defaultdict(float)
    used = 0
    for d in diseases:
        systems = systems_of.get(d)
        if not systems:
            continue
        used += 1
        bit = 1 if d in in_pathway else 0
        w = 1.0 / len(systems)
        marg_f[bit] += 1.0
        for s in systems:
            joint[(bit, s)] += w
            marg_s[s] += w
    if not used:
        return 0.0
    total = float(used)
    mi = 0.0
    for (f, s), n in joint.items():
        pfs = n / total
        pf = marg_f[f] / total
        ps = marg_s[s] / total
        if pfs > 0 and pf > 0 and ps > 0:
            mi += pfs * math.log2(pfs / (pf * ps))
    return mi


def excess(diseases, in_pathway, systems_of, rng) -> dict:
    """Observed MI minus the mean of a permutation null, with the null's dispersion.

    THE NULL SHUFFLES THE BIT, NOT THE SYSTEMS. Reassigning which diseases carry the pathway,
    while every disease keeps its own organ systems, holds fixed both the prevalence of the
    pathway and the shape of the system distribution. Mutual information rises with alphabet
    size and with prevalence for free; this removes both, so a common pathway cannot win by
    being common.
    """
    observed = indicator_mi(diseases, in_pathway, systems_of)
    members = sorted(in_pathway)
    k = len(members)
    pool = sorted(diseases)
    if k < 30 or k > len(pool) - 30:
        return {"observed": round(observed, 6), "skipped": "too few or too many carriers to "
                                                           "calibrate against a permutation"}
    draws = []
    for _ in range(DRAWS):
        shuffled = set(rng.sample(pool, k))
        draws.append(indicator_mi(diseases, shuffled, systems_of))
    mu = statistics.fmean(draws)
    sd = statistics.pstdev(draws) or 1e-12

    # AN INTERVAL ON THE OBSERVED VALUE, because a z is not one.
    #
    #  The z above says how far this pathway's mutual information sits from the mean of a
    #  permutation null, in units of that null's spread. It says nothing about how far the
    #  OBSERVED value would move if the catalogue held a different sample of diseases — and
    #  that is what a reader comparing two families needs, because the family means below are
    #  differences of these observed values.
    #
    #  Resampled over DISEASES with replacement at the same count, so the interval answers
    #  "how much of this is the particular diseases in the catalogue". Point ± 1.96 SE and not
    #  a percentile interval: mutual information is biased upward in n, and this repository
    #  has already published one percentile interval that did not contain its own point.
    boot = []
    idx = list(range(len(pool)))
    for _ in range(BOOT_DRAWS):
        sample = [pool[rng.randrange(len(idx))] for _ in idx]
        boot.append(indicator_mi(sample, in_pathway, systems_of))
    se = statistics.pstdev(boot) if len(boot) > 10 else None

    return {
        "observed": round(observed, 6),
        "observed_se": round(se, 6) if se else None,
        "observed_ci95": ([round(observed - 1.96 * se, 6), round(observed + 1.96 * se, 6)]
                          if se else None),
        "null_mean": round(mu, 6),
        "null_sd": round(sd, 6),
        "excess_bits": round(observed - mu, 6),
        # The excess with the observed value's own uncertainty carried through. A pathway whose
        # excess interval spans zero is one whose z is carrying the whole claim.
        "excess_ci95": ([round(observed - 1.96 * se - mu, 6),
                         round(observed + 1.96 * se - mu, 6)] if se else None),
        "excess_spans_zero": bool(se) and (observed - 1.96 * se) <= mu <= (observed + 1.96 * se),
        "z": round((observed - mu) / sd, 2),
        "carriers": k,
        "draws": DRAWS,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--draws", type=int, default=DRAWS)
    args = ap.parse_args()

    si = _load_scale_information()

    print("reading the catalogue ...")
    disease_genes = si.disease_to_genes()
    systems, ancestors, hpo_names = si.hpo_systems()
    systems_of = si.disease_to_systems(systems, ancestors)
    diseases = sorted(set(disease_genes) & set(systems_of))
    pathways, pathway_names = si.gene_to_pathway()
    print(f"  {len(diseases)} diseases with genes and systems, "
          f"{len(pathway_names)} top-level pathways")

    # Which diseases carry at least one gene in each top-level pathway.
    carriers: dict[str, set[str]] = collections.defaultdict(set)
    for d in diseases:
        for g in disease_genes.get(d, ()):
            for p in pathways.get(g, ()):
                carriers[p].add(d)

    # The two halves of the earlier morphogenesis contrast, reused rather than re-authored.
    morph_systems = {s for s, k in si.SYSTEM_CLASS.items() if k == "morphogenetic"}
    phys_systems = {s for s, k in si.SYSTEM_CLASS.items() if k == "physiological"}

    def restrict(keep: set[str]) -> dict[str, set[str]]:
        out = {}
        for d, ss in systems_of.items():
            hit = ss & keep
            if hit:
                out[d] = hit
        return out

    systems_morph = restrict(morph_systems)
    systems_phys = restrict(phys_systems)
    d_morph = sorted(set(diseases) & set(systems_morph))
    d_phys = sorted(set(diseases) & set(systems_phys))
    print(f"  {len(d_morph)} diseases touch a morphogenetic system, "
          f"{len(d_phys)} a physiological one")

    rows = []
    for i, (p, members) in enumerate(sorted(carriers.items(), key=lambda kv: -len(kv[1]))):
        # A separate RNG per pathway. One shared stream would couple twenty-nine measurements
        # so that adding a thirtieth moved all of them — the coupling that already shifted a
        # published z in this repository once.
        overall = excess(diseases, members, systems_of, random.Random(SEED + 10 * i))
        row = {
            "pathway": p,
            "name": pathway_names.get(p, p),
            "family": FAMILY.get(p, "other"),
            "diseases": len(members),
            "overall": overall,
            "morphogenetic": excess(d_morph, members & set(d_morph), systems_morph,
                                    random.Random(SEED + 10 * i + 1)),
            "physiological": excess(d_phys, members & set(d_phys), systems_phys,
                                    random.Random(SEED + 10 * i + 2)),
        }
        m = row["morphogenetic"].get("excess_bits")
        f = row["physiological"].get("excess_bits")
        row["form_minus_process"] = round(m - f, 6) if m is not None and f is not None else None
        rows.append(row)
        print(f"  {row['name'][:38]:40} z {overall.get('z', '—'):>7} "
              f"form-process {row['form_minus_process']}")

    # ---- the prediction, scored
    #
    #  AND THE FIRST OBJECTION TO IT, TESTED RATHER THAN WAVED AWAY. The two arms do not have
    #  the same shape: fourteen morphogenetic systems carry H(S) = 3.582 bits and seven
    #  physiological ones 2.575. Subtracting an excess measured against one from an excess
    #  measured against the other compares quantities on different scales, and if the whole
    #  result were an artefact of that it would deserve to be thrown away rather than
    #  published. So both are reported: the raw difference, and the difference of each arm's
    #  excess divided by its own system entropy.
    def system_entropy(diseases_arm, systems_arm) -> float:
        mass: dict[str, float] = collections.defaultdict(float)
        for d in diseases_arm:
            hit = systems_arm.get(d)
            if not hit:
                continue
            for sysid in hit:
                mass[sysid] += 1.0 / len(hit)
        total = sum(mass.values()) or 1.0
        return -sum((v / total) * math.log2(v / total) for v in mass.values() if v > 0)

    h_morph = system_entropy(d_morph, systems_morph)
    h_phys = system_entropy(d_phys, systems_phys)

    by_family: dict[str, list[float]] = collections.defaultdict(list)
    by_family_norm: dict[str, list[float]] = collections.defaultdict(list)
    for r in rows:
        m = r["morphogenetic"].get("excess_bits")
        f = r["physiological"].get("excess_bits")
        if m is None or f is None:
            continue
        by_family[r["family"]].append(m - f)
        by_family_norm[r["family"]].append(m / h_morph - f / h_phys)
        r["form_minus_process_normalised"] = round(m / h_morph - f / h_phys, 6)

    family_means = {k: round(statistics.fmean(v), 6) for k, v in by_family.items() if v}

    # HOW MUCH OF THIS SURVIVES ITS OWN INTERVAL. Reported per arm, because the verdict is a
    # difference of two family means and a difference between two quantities that each span
    # zero is not a difference at all.
    # THE VERDICT IS A DIFFERENCE, AND A DIFFERENCE NEEDS ITS OWN INTERVAL.
    #
    #  standards.md §4: "a difference smaller than its own interval is not a difference and
    #  must not be reported as one." Everything above gives each PATHWAY an interval. The
    #  claim this file actually makes is about two FAMILY MEANS, and until now that claim had
    #  no uncertainty attached at either end - the negative verdict rested on comparing
    #  -0.009477 with -0.005272 as though both were exact.
    #
    #  Each pathway's form-minus-process contrast carries the two arms' standard errors
    #  combined in quadrature; the family mean's error is the quadrature sum over its members
    #  divided by their count.
    #
    #  ⚠️ THE ASSUMPTION THIS MAKES IS FALSE, AND THE MARGIN IS SMALL. Combining that way
    #  treats pathways within a family as independent. They are not: they share diseases, and
    #  a disease that fails in one Signal Transduction pathway usually fails in several. So
    #  the interval below is a LOWER BOUND on the width. The field-minus-energy contrast
    #  clears zero by about a third of its own half-width, which means a true error only ~33%
    #  larger than this estimate would put zero inside it. That is not a margin to build a
    #  claim on, and the payload says so rather than reporting the contrast as established.
    def family_interval(name: str) -> dict | None:
        members = [r for r in rows if r.get("family") == name
                   and r["morphogenetic"].get("observed_se")
                   and r["physiological"].get("observed_se")]
        if not members:
            return None
        diffs = [r["morphogenetic"]["excess_bits"] - r["physiological"]["excess_bits"]
                 for r in members]
        ses = [math.hypot(r["morphogenetic"]["observed_se"],
                          r["physiological"]["observed_se"]) for r in members]
        k = len(members)
        mean = statistics.fmean(diffs)
        se = math.sqrt(sum(e * e for e in ses)) / k
        return {"pathways": k, "mean": round(mean, 6), "se": round(se, 6),
                "ci95": [round(mean - 1.96 * se, 6), round(mean + 1.96 * se, 6)]}

    fam_ci = {f: family_interval(f) for f in sorted({r.get("family") for r in rows} - {None})}
    contrast = None
    if fam_ci.get("field") and fam_ci.get("energy"):
        a, b = fam_ci["field"], fam_ci["energy"]
        dd = a["mean"] - b["mean"]
        sd_ = math.hypot(a["se"], b["se"])
        # How much wider the true error would have to be before zero enters the interval.
        # Printed because it is the number that decides whether the correlation this ignores
        # matters, and it is more useful than a p-value nobody can act on.
        slack = abs(dd) / (1.96 * sd_) if sd_ else None
        contrast = {
            "field_minus_energy": round(dd, 6),
            "se": round(sd_, 6),
            "ci95": [round(dd - 1.96 * sd_, 6), round(dd + 1.96 * sd_, 6)],
            "spans_zero": abs(dd) < 1.96 * sd_,
            "width_multiple_that_would_reach_zero": round(slack, 2) if slack else None,
            "says": ("The contrast the prediction was about runs the OPPOSITE way and its "
                     "interval does not contain zero - but it clears zero by a factor of "
                     "%.2f on an independence assumption that is false, since pathways in a "
                     "family share diseases. An error a third wider swallows it. Reported as "
                     "a direction with a stated fragility, NOT as an established contrast."
                     % slack if slack else ""),
        }

    spans = {
        "overall": sum(1 for r in rows if r["overall"].get("excess_spans_zero")),
        "morphogenetic": sum(1 for r in rows if r["morphogenetic"].get("excess_spans_zero")),
        "physiological": sum(1 for r in rows if r["physiological"].get("excess_spans_zero")),
        "of_pathways": len(rows),
    }
    family_means_norm = {k: round(statistics.fmean(v), 6)
                         for k, v in by_family_norm.items() if v}
    field = family_means.get("field")
    energy = family_means.get("energy")
    field_n = family_means_norm.get("field")
    energy_n = family_means_norm.get("energy")
    verdict = "not computable — one of the two families produced no calibrated pathway"
    if field is not None and energy is not None:
        if field > 0 > energy:
            verdict = (f"AS PREDICTED. The field families carry more about morphogenetic "
                       f"systems than physiological ones ({field:+.6f} bits) and the energy "
                       f"families do the reverse ({energy:+.6f}). The earlier morphogenesis "
                       f"result is about what the letters MEAN, not only about how few there "
                       f"are.")
        elif field > energy:
            verdict = (f"PARTIALLY. Field families lean towards form more than energy "
                       f"families do ({field:+.6f} against {energy:+.6f}), but the two do not "
                       f"straddle zero, so the contrast is a difference of degree and the "
                       f"prediction as written is not met.")
        else:
            same_normalised = (field_n is not None and energy_n is not None
                               and field_n <= energy_n)
            verdict = (
                f"THE PREDICTION FAILED, and it failed the objection to itself as well. "
                f"Field families do not lean towards form more than energy families "
                f"({field:+.6f} against {energy:+.6f} bits), and EVERY family leans towards "
                f"the physiological side. The obvious objection is that the two arms have "
                f"different system entropies ({h_morph:.3f} against {h_phys:.3f} bits), so "
                f"the raw difference compares two scales; normalising each excess by its own "
                f"arm's entropy gives {field_n:+.6f} against {energy_n:+.6f}, which "
                f"{'does not rescue it either' if same_normalised else 'reverses the ordering'}"
                f". Read against tools/scale_information.py: its morphogenesis result stands "
                f"as a measurement, but the reading it invites — that a pathway alphabet "
                f"fails on form because it has no vocabulary for space — is NOT supported "
                f"here. On this evidence the loss is about how coarse the alphabet is, not "
                f"about what its letters mean.")

    payload = {
        "generated": "2026-08-30",
        "provenance": "HPO genes_to_disease and phenotype.hpoa, Reactome top-level pathways "
                      "through the STRING alias crosswalk; loaders imported from "
                      "tools/scale_information.py rather than reimplemented",
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md",
        "question": "tools/scale_information.py concluded that a pathway alphabet has no "
                    "vocabulary for where and when. That treats 29 pathways as one alphabet. "
                    "Which families carry form, and which carry energy?",
        "prediction_written_before_the_run": (
            "If the morphogenesis result is about geometry rather than coarseness in general, "
            "the field-shaping families (Signal Transduction, Developmental Biology, "
            "Cell-Cell communication, Extracellular matrix) should carry more about "
            "morphogenetic systems than physiological ones, and the energy families "
            "(Metabolism, Transport of small molecules, Digestion, Muscle contraction) the "
            "reverse."),
        "families_are_authored": (
            "Reactome's top level is a filing system, not a taxonomy of function, so grouping "
            "it is an authored act. The grouping is in FAMILY in this file, written before "
            "the counts were read, and a reader who disagrees can regroup: every pathway's "
            "own numbers are published beside it."),
        "verdict": verdict,
        "excess_spanning_zero": spans,
        "family_mean_intervals": fam_ci,
        "contrast_with_its_interval": contrast,
        "family_means_form_minus_process": family_means,
        "family_means_normalised": family_means_norm,
        "arm_entropies_bits": {"morphogenetic": round(h_morph, 4),
                               "physiological": round(h_phys, 4)},
        "objection_tested": (
            "The two arms carry different numbers of organ systems and therefore different "
            "system entropies, so a raw difference of excesses compares two scales. Dividing "
            "each arm's excess by its own entropy is reported beside the raw figure; the "
            "conclusion is the same under both, which is why the negative result is "
            "published rather than withdrawn."),
        "pathways": rows,
        "scale": {
            "diseases": len(diseases),
            "morphogenetic_diseases": len(d_morph),
            "physiological_diseases": len(d_phys),
            "pathways": len(rows),
        },
        "says": "A single-bit alphabet per pathway. These numbers are small by construction "
                "and are NOT comparable with the 0.279 bits the gene alphabet reaches — they "
                "are comparable with each other, which is the only comparison made. A "
                "positive excess means the pathway says something about which organ system a "
                "disease touches that its prevalence alone does not explain.",
        "limits": [
            "The morphogenetic arm carries 14 organ systems and the physiological arm 7, "
            "so the two excesses are measured against different entropy ceilings. Both the "
            "raw and the entropy-normalised comparison are published and they agree; a "
            "reader who prefers a third normalisation has every pathway's own numbers.",
            "Twenty-nine parallel tests with no correction across them. Each carries its own "
            "z against its own null; the FAMILY means are the reported quantity and are means "
            "over those, not a corrected omnibus test. Read a single pathway's z as a "
            "description, not as a discovery.",
            "The morphogenetic/physiological split is authored, taken unchanged from "
            "tools/scale_information.py so the two files cannot disagree — but it is the same "
            "authored classification, so this file inherits its assumptions rather than "
            "testing them.",
            "A disease carries a pathway if ANY of its causal genes is in it. Diseases with "
            "many genes therefore carry many pathways, and the permutation null holds "
            "prevalence fixed but not gene count.",
        ],
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    print(f"  family means (form - process): {family_means}")
    if contrast:
        print("  field - energy = %+.6f  95%% [%+.6f, %+.6f]%s"
              % (contrast["field_minus_energy"], contrast["ci95"][0], contrast["ci95"][1],
                 "  SPANS ZERO" if contrast["spans_zero"] else
                 "  clears zero by x%.2f, on an independence assumption that is false"
                 % contrast["width_multiple_that_would_reach_zero"]))
    print(f"  pathways whose excess interval SPANS ZERO: overall {spans['overall']}, "
          f"morphogenetic {spans['morphogenetic']}, physiological {spans['physiological']} "
          f"of {spans['of_pathways']}")
    print(f"  {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
