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
    return {
        "observed": round(observed, 6),
        "null_mean": round(mu, 6),
        "null_sd": round(sd, 6),
        "excess_bits": round(observed - mu, 6),
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
    by_family: dict[str, list[float]] = collections.defaultdict(list)
    for r in rows:
        if r["form_minus_process"] is not None:
            by_family[r["family"]].append(r["form_minus_process"])

    family_means = {k: round(statistics.fmean(v), 6) for k, v in by_family.items() if v}
    field = family_means.get("field")
    energy = family_means.get("energy")
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
            verdict = (f"THE PREDICTION FAILED. Field families do not lean towards form more "
                       f"than energy families ({field:+.6f} against {energy:+.6f}). The "
                       f"morphogenesis result is then about alphabet size rather than about "
                       f"what the letters mean, and this file is evidence against the reading "
                       f"tools/scale_information.py gives it.")

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
        "family_means_form_minus_process": family_means,
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
    print(f"  {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
