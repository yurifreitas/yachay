#!/usr/bin/env python
"""How much of the phenotype survives a change of scale.

WHY THIS FILE. The thesis this repository serves is multiscale: gene -> protein -> pathway
-> cell -> tissue -> phenotype, with the evidence and the uncertainty carried along. Every
layer built so far describes ONE scale. `tools/twin_propagation.py` was the first to move
*within* a scale (a perturbation spreading on the interactome). This is the first to measure
what happens *between* two — and it measures the thing every multiscale project assumes and
none of them reports: **the coarse-graining loses information, and here is how much.**

The question, stated so it can be wrong:

    A disease is described by its causal genes. Collapse those genes onto a coarser
    alphabet - the Reactome top-level pathways they belong to, or the cell types where
    they are expressed. How much of what the gene set said about the disease's ORGAN
    SYSTEMS survives the collapse?

ADR 0007 admits this construct as the first promotion from `docs/references/theory-atlas.md`
(items "renormalisation / coarse-graining", "information bottleneck", "cross-scale fidelity").

## The method, and the reason for each choice

**Mutual information, disease-weighted.** For each of the 9,142 diseases that have both a
causal gene and an HPO annotation, the feature set F (genes, or pathways, or cell types) and
the organ-system set S are crossed, and each disease contributes total weight 1 spread evenly
over its (f, s) pairs. Without that normalisation a disease annotated to twenty systems and
forty genes would count 800 times as much as a disease with one of each, and the measurement
would be of curation effort rather than of biology - which is the ascertainment bias
`tools/atlas_bias.py` already measures at +0.2357 on this same catalogue.

**A permutation null, always, and here it is not optional.** MI rises with alphabet size for
free: 5,260 genes can memorise an organ system in a way 29 pathways cannot, so raw MI would
rank the finest scale first by construction and prove nothing. The null shuffles the
disease -> organ-system assignment, leaving every marginal and the whole feature structure
intact, and what is reported is the **excess** I - I_null. ADR 0007 makes this mandatory
rather than good practice.

**A bootstrap over diseases**, because the unit that could have been sampled differently is
the disease, not the (gene, system) pair. Every headline gets a 95% interval, which is what
`docs/references/standards.md` §4 (GUM) asks of any number this project publishes. The
bootstrap supplies the **standard error only**, and the interval is point ± 1.96 SE: mutual
information is biased in n, a resample with replacement holds ~63% of the diseases, and the
percentile interval is therefore displaced — the first version of this file printed a gene
scale point estimate of 0.2791 against a percentile interval of [0.1745, 0.2163], which is
not an interval. The failure is kept in the comment at the estimator rather than tidied away.

## What this is not

Not causal emergence. The literature's `EI` is defined over *interventions* on a dynamical
system; this is an observational mutual information over a static catalogue, and calling it
EI would be exactly the promotion ADR 0007 exists to forbid. It answers the weaker, checkable
question - is the coarse alphabet still informative about the phenotype, per category and in
total - and the artefact's `says` field states that limit rather than only this docstring.

Not a claim that pathways or cell types are the right scale. Two coarse-grainings are
measured because one would have no comparison; the ranking between them is a result, not a
design.

    python tools/scale_information.py
    python tools/scale_information.py --bootstrap 200 --null 25

Stdlib only, like the rest of the catalogue layers.
"""

from __future__ import annotations

import argparse
import collections
import csv
import gzip
import io
import json
import math
import pathlib
import random
import sys
import zipfile
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "rare" / "scale_information.json"

#: A gene is placed in a cell type when its expression there is at least this fraction of
#: its own maximum across cell types. Registered in manifests/thresholds.yaml as
#: CELL_TYPE_ENRICHMENT (conventional, chosen blind - the alternative, HPA's own enriched/
#: enhanced call, is a curated field and would make this a measurement of curation).
CELL_TYPE_ENRICHMENT = 0.5

#: Permutation draws behind the null. Registered as SCALE_PERMUTATIONS.
SCALE_PERMUTATIONS = 25

#: The root of HPO's phenotype branch. Its direct children are the organ systems.
PHENOTYPIC_ABNORMALITY = "HP:0000118"

SEED = 20260829

#: AUTHORED, and the single authored constant in this file. Each organ system is marked by the
#: KIND of process whose failure produces its abnormalities:
#:
#:   morphogenetic  the abnormality is a structure that formed wrongly, in a place, at a time.
#:                  Turing's 1952 morphogenesis is the mathematics of this class - a spatial
#:                  pattern arising from reaction and diffusion, not from a list of reactions.
#:   physiological  the abnormality is a process running wrongly - flux, signalling, immunity,
#:                  proliferation. A pathway IS the right vocabulary for this class.
#:
#: ⚠️ TARGET CONTACT. The per-system retentions had already been printed when this table was
#: written. That makes the test below a DESCRIPTION of a pattern with a p-value attached, not
#: a pre-registered prediction, and the p-value must be read as such - ADR 0006's distinction,
#: applied to a classification instead of to a threshold. What protects it from being circular
#: is that the assignment follows the two literatures rather than the numbers, that it was not
#: revised after the test ran, and that the two hard cases are named below rather than dropped.
#: The honest way to promote this to a real test is a second ontology: run the same split on
#: MONDO's disease classes, which nobody here has looked at yet.
#: Two systems are deliberately hard cases and both are marked morphogenetic: the nervous
#: system (patterned in development, then physiological for life) and the cardiovascular
#: system (a structure that forms, then a pump that runs).
SYSTEM_CLASS = {
    "HP:0000478": "morphogenetic",   # eye
    "HP:0040064": "morphogenetic",   # limbs
    "HP:0000152": "morphogenetic",   # head or neck
    "HP:0033127": "morphogenetic",   # musculoskeletal
    "HP:0000598": "morphogenetic",   # ear
    "HP:0001197": "morphogenetic",   # prenatal development or birth
    "HP:0001574": "morphogenetic",   # integument
    "HP:0001626": "morphogenetic",   # cardiovascular
    "HP:0002086": "morphogenetic",   # respiratory
    "HP:0025031": "morphogenetic",   # digestive
    "HP:0000119": "morphogenetic",   # genitourinary
    "HP:0001507": "morphogenetic",   # growth
    "HP:0000707": "morphogenetic",   # nervous system
    "HP:0000769": "morphogenetic",   # breast
    "HP:0001939": "physiological",   # metabolism/homeostasis
    "HP:0001871": "physiological",   # blood and blood-forming tissues
    "HP:0002715": "physiological",   # immune system
    "HP:0000818": "physiological",   # endocrine system
    "HP:0002664": "physiological",   # neoplasm
    "HP:0025354": "physiological",   # abnormal cellular phenotype
    "HP:0025142": "physiological",   # constitutional symptom
    "HP:0002715_": "physiological",
}


# --- the catalogue ----------------------------------------------------------------------

def disease_to_genes() -> dict[str, set[str]]:
    """HPO's gene-to-disease table, inverted."""
    out: dict[str, set[str]] = collections.defaultdict(set)
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            gene = (row.get("gene_symbol") or "").strip()
            disease = (row.get("disease_id") or "").strip()
            if gene and disease:
                out[disease].add(gene)
    return dict(out)


def hpo_systems() -> tuple[set[str], dict[str, set[str]], dict[str, str]]:
    """The organ systems, and every term's ancestors, from hp.obo."""
    parents: dict[str, set[str]] = collections.defaultdict(set)
    names: dict[str, str] = {}
    term: str | None = None
    for line in BY_KEY["hpo_terms"].dest.read_text(encoding="utf-8").splitlines():
        if line.startswith("["):
            term = None
        elif line.startswith("id: HP:"):
            term = line[4:].strip()
        elif term and line.startswith("name:"):
            names[term] = line[5:].strip()
        elif term and line.startswith("is_a:"):
            parents[term].add(line[5:].split("!")[0].strip())

    systems = {t for t, ps in parents.items() if PHENOTYPIC_ABNORMALITY in ps}

    ancestors: dict[str, set[str]] = {}

    def walk(t: str) -> set[str]:
        if t in ancestors:
            return ancestors[t]
        ancestors[t] = set()                     # cycle guard, and obo does contain them
        acc: set[str] = set()
        for p in parents.get(t, ()):
            acc.add(p)
            acc |= walk(p)
        ancestors[t] = acc
        return acc

    for t in list(parents):
        walk(t)
    return systems, ancestors, names


def disease_to_systems(systems: set[str], ancestors: dict[str, set[str]]) -> dict[str, set[str]]:
    """Every annotated HPO term lifted to the organ system it sits under."""
    out: dict[str, set[str]] = collections.defaultdict(set)
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        rows = (line for line in fh if not line.startswith("#"))
        for row in csv.DictReader(rows, delimiter="\t"):
            disease = (row.get("database_id") or "").strip()
            term = (row.get("hpo_id") or "").strip()
            if not disease or not term:
                continue
            hit = ({term} | ancestors.get(term, set())) & systems
            if hit:
                out[disease] |= hit
    return dict(out)


# --- the two coarse-grainings -----------------------------------------------------------

def uniprot_to_symbol() -> dict[str, str]:
    """Reactome speaks UniProt; the catalogue speaks gene symbols. STRING joins them."""
    accession_to_string: dict[str, str] = {}
    with gzip.open(BY_KEY["string_aliases"].dest, "rt", encoding="utf-8") as fh:
        next(fh, None)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > 2 and parts[2] == "UniProt_AC":
                accession_to_string.setdefault(parts[1], parts[0])
    string_to_symbol: dict[str, str] = {}
    with gzip.open(BY_KEY["string_info"].dest, "rt", encoding="utf-8") as fh:
        next(fh, None)
        for line in fh:
            parts = line.split("\t")
            if len(parts) > 1:
                string_to_symbol[parts[0]] = parts[1]
    return {acc: string_to_symbol[sid]
            for acc, sid in accession_to_string.items() if sid in string_to_symbol}


def gene_to_pathway() -> tuple[dict[str, set[str]], dict[str, str]]:
    """Gene -> Reactome TOP-LEVEL pathway. Lower levels would not be a coarse-graining."""
    parent: dict[str, set[str]] = collections.defaultdict(set)
    for line in BY_KEY["reactome_hierarchy"].dest.read_text(encoding="utf-8").splitlines():
        if "\t" not in line:
            continue
        up, down = line.split("\t")[:2]
        parent[down].add(up)

    roots_cache: dict[str, frozenset[str]] = {}

    def roots(pathway: str) -> frozenset[str]:
        if pathway in roots_cache:
            return roots_cache[pathway]
        found: set[str] = set()
        stack, seen = [pathway], set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            up = [p for p in parent.get(node, ()) if p.startswith("R-HSA")]
            if up:
                stack.extend(up)
            else:
                found.add(node)
        roots_cache[pathway] = frozenset(found)
        return roots_cache[pathway]

    symbol_of = uniprot_to_symbol()
    mapping: dict[str, set[str]] = collections.defaultdict(set)
    names: dict[str, str] = {}
    with BY_KEY["reactome_pathways"].dest.open(encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6 or parts[5] != "Homo sapiens":
                continue
            names[parts[1]] = parts[3]
            symbol = symbol_of.get(parts[0])
            if symbol:
                mapping[symbol] |= set(roots(parts[1]))
    return dict(mapping), names


def gene_to_cell_type() -> dict[str, set[str]]:
    """Gene -> the cell types carrying at least CELL_TYPE_ENRICHMENT of its own maximum."""
    per_gene: dict[str, dict[str, float]] = collections.defaultdict(dict)
    with zipfile.ZipFile(BY_KEY["hpa_single_cell"].dest) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".tsv"))
        with zf.open(name) as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, "utf-8"), delimiter="\t"):
                try:
                    value = float(row["nCPM"])
                except (KeyError, TypeError, ValueError):
                    continue
                per_gene[row["Gene name"]][row["Cell type"]] = value
    out: dict[str, set[str]] = {}
    for gene, profile in per_gene.items():
        peak = max(profile.values(), default=0.0)
        if peak <= 0:
            continue
        hit = {c for c, v in profile.items() if v >= CELL_TYPE_ENRICHMENT * peak}
        if hit:
            out[gene] = hit
    return out


# --- the estimator ----------------------------------------------------------------------

def mutual_information(diseases, features, systems_of):
    """I(F;S) in bits, each disease contributing total weight 1.

    Returns (I, H(S), H(F), |F| observed, diseases actually used). H(F) is carried because
    the DIRECTION matters: I/H(S) and I/H(F) are the two uncertainty coefficients, and their
    inequality is the measurable shadow of the asymmetry the theory atlas files under Finsler
    geometry (theory-atlas.md B9).
    """
    joint: dict[tuple[str, str], float] = collections.defaultdict(float)
    marg_f: dict[str, float] = collections.defaultdict(float)
    marg_s: dict[str, float] = collections.defaultdict(float)
    total = 0.0
    used = 0
    for disease in diseases:
        feats = features.get(disease)
        systems = systems_of.get(disease)
        if not feats or not systems:
            continue
        used += 1
        weight = 1.0 / (len(feats) * len(systems))
        for f in feats:
            marg_f[f] += weight * len(systems)
            for s in systems:
                joint[(f, s)] += weight
        for s in systems:
            marg_s[s] += weight * len(feats)
        total += 1.0
    if total <= 0:
        return 0.0, 0.0, 0.0, 0, 0
    info = 0.0
    for (f, s), w in joint.items():
        pxy = w / total
        info += pxy * math.log2(pxy / ((marg_f[f] / total) * (marg_s[s] / total)))
    entropy_s = -sum((v / total) * math.log2(v / total) for v in marg_s.values() if v > 0)
    entropy_f = -sum((v / total) * math.log2(v / total) for v in marg_f.values() if v > 0)
    return info, entropy_s, entropy_f, len(marg_f), used


def project(diseases, disease_genes, mapper) -> dict[str, set[str]]:
    """Push each disease's gene set through a coarse-graining."""
    out: dict[str, set[str]] = {}
    for disease in diseases:
        feats: set[str] = set()
        for gene in disease_genes.get(disease, ()):
            feats |= mapper(gene)
        if feats:
            out[disease] = feats
    return out


def measure(diseases, features, systems_of, n_null, n_boot, rng):
    """Excess mutual information over a label-permutation null, with a bootstrap interval."""
    info, entropy_s, entropy_f, alphabet, used = mutual_information(diseases, features, systems_of)

    order = list(diseases)
    nulls = []
    for _ in range(n_null):
        shuffled = order[:]
        rng.shuffle(shuffled)
        permuted = {d: systems_of[t] for d, t in zip(order, shuffled) if t in systems_of}
        nulls.append(mutual_information(order, features, permuted)[0])
    null_mean = sum(nulls) / len(nulls)
    null_sd = (sum((x - null_mean) ** 2 for x in nulls) / max(len(nulls) - 1, 1)) ** 0.5

    # The bootstrap resamples with replacement, which duplicates diseases, which SHARPENS
    # the joint and inflates MI - badly at the gene scale, where the alphabet is large
    # enough to memorise a duplicated label. A fixed null cannot absorb that: the first
    # version of this function returned an interval that did not contain its own point
    # estimate (0.2788 against [0.3614, 0.4033]). So each resample is compared against a
    # null permuted INSIDE that same resample, and the duplication bias cancels.
    boots = []
    for _ in range(n_boot):
        sample = [order[rng.randrange(len(order))] for _ in range(len(order))]
        inner = sample[:]
        rng.shuffle(inner)
        permuted = {d: systems_of[t] for d, t in zip(sample, inner) if t in systems_of}
        boots.append(mutual_information(sample, features, systems_of)[0]
                     - mutual_information(sample, features, permuted)[0])
    excess = info - null_mean

    # And the percentile interval is STILL displaced at the gene scale, because mutual
    # information is biased in n and a resample with replacement holds only ~63% of the
    # diseases: the inner null does not cancel a bias that moves with the effective sample
    # size. Two honest responses were available - report a displaced interval, or use the
    # bootstrap for the DISPERSION only. The second is taken: the interval below is
    # point +- 1.96 * bootstrap SE, and the artefact says so. Reporting the raw percentiles
    # would put the point estimate outside its own interval, which is not an interval.
    mean_b = sum(boots) / len(boots) if boots else float("nan")
    se = ((sum((x - mean_b) ** 2 for x in boots) / max(len(boots) - 1, 1)) ** 0.5
          if boots else float("nan"))
    lo, hi = excess - 1.96 * se, excess + 1.96 * se
    return {
        "diseases": used,
        "alphabet": alphabet,
        "mutual_information_bits": round(info, 5),
        "null_mean_bits": round(null_mean, 5),
        "null_sd_bits": round(null_sd, 5),
        "excess_bits": round(excess, 5),
        "excess_se": round(se, 5),
        "excess_ci95": [round(lo, 5), round(hi, 5)],
        "system_entropy_bits": round(entropy_s, 4),
        "feature_entropy_bits": round(entropy_f, 4),
        "fraction_of_system_entropy": round(excess / entropy_s, 5) if entropy_s else None,
        "bits_per_category": round(excess / alphabet, 8) if alphabet else None,
        # The two directions. U(S|F) is how much of the organ system the features pin down;
        # U(F|S) is how much of the feature identity the organ system pins down. They are
        # the same numerator over different denominators, and their ratio is the asymmetry.
        "u_system_given_features": round(info / entropy_s, 5) if entropy_s else None,
        "u_features_given_system": round(info / entropy_f, 5) if entropy_f else None,
        "asymmetry_ratio": (round((info / entropy_s) / (info / entropy_f), 3)
                            if entropy_s and entropy_f and info else None),
    }


def per_system(diseases, scales, systems_of, names, n_null, rng):
    """Which organ systems SURVIVE a coarse-graining, and which are destroyed by it.

    The pooled number in `measure` averages over 23 organ systems and can only say that a
    fifth of the information survives. It cannot say whether that fifth is spread evenly or
    concentrated - and those are different worlds. If retention is even, the coarse alphabet
    is a uniformly lossy summary; if it is concentrated, the pathway scale is the RIGHT scale
    for some systems and the wrong one for others, which is the observational shadow of the
    "cross-scale invariant" the theory atlas lists as research problem 10.

    One-vs-rest: each system becomes a binary label, so the alphabets are identical across
    systems and the retentions are comparable. Systems are reported only when the gene-scale
    excess clears 5 null standard deviations, because a ratio whose denominator is noise is
    noise with a decimal point.
    """
    rows = []
    for system in sorted({s for v in systems_of.values() for s in v}):
        binary = {d: ({"in"} if system in systems_of.get(d, ()) else {"out"}) for d in diseases}
        at = {}
        for scale, features in scales.items():
            info = mutual_information(diseases, features, binary)[0]
            nulls = []
            for _ in range(n_null):
                shuffled = list(diseases)
                rng.shuffle(shuffled)
                permuted = {d: binary[t] for d, t in zip(diseases, shuffled)}
                nulls.append(mutual_information(diseases, features, permuted)[0])
            mu = sum(nulls) / len(nulls)
            sd = (sum((x - mu) ** 2 for x in nulls) / max(len(nulls) - 1, 1)) ** 0.5
            at[scale] = {"excess_bits": round(info - mu, 6),
                         "z_vs_null": round((info - mu) / sd, 2) if sd else None}
        base = at["gene"]["excess_bits"]
        if not base or (at["gene"]["z_vs_null"] or 0) < 5:
            continue
        rows.append({
            "system": system,
            "name": names.get(system, system),
            "diseases": sum(1 for d in diseases if system in systems_of.get(d, ())),
            "gene_excess_bits": base,
            "pathway_retention": round(at["pathway"]["excess_bits"] / base, 3),
            "cell_type_retention": round(at["cell_type"]["excess_bits"] / base, 3),
        })
    rows.sort(key=lambda r: r["pathway_retention"], reverse=True)
    return rows


def morphogenesis_test(rows, rng, n_perm=20000):
    """Does a pathway alphabet lose more where the abnormality is a FORM than a PROCESS?

    Turing's 1952 account of morphogenesis says a spatial pattern can arise from reaction and
    diffusion - the explanatory object is a field with a geometry and a time, not a list of
    reactions. If that is the right frame for structural birth defects, then collapsing a
    disease's genes onto Reactome top-level pathways should destroy more of what they said
    about the eye or the limbs than about metabolism or immunity, because the pathway alphabet
    has no vocabulary for where and when.

    Ashby's law of requisite variety (1956) says the same thing from the controller's side:
    only variety can absorb variety, and one alphabet cannot represent two populations whose
    variety differs. The measurement below is the same claim as the retention spread already
    reported - this asks whether the spread lines up with the predicted classes.

    A permutation test on the difference of mean retention, because 20 systems is far too few
    for an asymptotic test and the retentions are neither normal nor independent of system size.
    """
    marked = [(r, SYSTEM_CLASS[r["system"]]) for r in rows if r["system"] in SYSTEM_CLASS]
    morph = [r["pathway_retention"] for r, k in marked if k == "morphogenetic"]
    phys = [r["pathway_retention"] for r, k in marked if k == "physiological"]
    if len(morph) < 3 or len(phys) < 3:
        return None
    observed = sum(phys) / len(phys) - sum(morph) / len(morph)

    pool = morph + phys
    n_phys = len(phys)
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        diff = (sum(pool[:n_phys]) / n_phys
                - sum(pool[n_phys:]) / (len(pool) - n_phys))
        if diff >= observed:
            hits += 1
    p_value = (hits + 1) / (n_perm + 1)

    return {
        "asks": ("Does a pathway coarse-graining retain less about systems whose "
                 "abnormalities are FORMS than about systems whose abnormalities are "
                 "PROCESSES? Turing 1952 for the mechanism, Ashby 1956 for the "
                 "representation argument."),
        "classification": ("AUTHORED, and ⚠️ with target contact - the retentions were visible "
                           "when the classes were written. A description with a p-value, not a "
                           "pre-registered test. See SYSTEM_CLASS."),
        "morphogenetic": {"n": len(morph), "mean_pathway_retention": round(sum(morph) / len(morph), 4),
                          "systems": sorted(r["name"] for r, k in marked if k == "morphogenetic")},
        "physiological": {"n": len(phys), "mean_pathway_retention": round(sum(phys) / len(phys), 4),
                          "systems": sorted(r["name"] for r, k in marked if k == "physiological")},
        "difference": round(observed, 4),
        "permutation_p_one_sided": round(p_value, 5),
        "permutations": n_perm,
        "says": ("One-sided permutation test on a classification taken from theory rather than "
                 "fitted, but written with the numbers in view. It cannot show that Turing's "
                 "mechanism operates in these diseases, and it is not evidence at the strength "
                 "a pre-registered test would carry. It can show whether the alphabet that "
                 "describes processes loses more signal in the systems where the theory says "
                 "form is what fails."),
    }


# --- main -------------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--null", type=int, default=SCALE_PERMUTATIONS, help="permutation draws per scale")
    ap.add_argument("--bootstrap", type=int, default=200, help="bootstrap resamples per scale")
    args = ap.parse_args()

    rng = random.Random(SEED)

    print("reading the catalogue ...")
    disease_genes = disease_to_genes()
    systems, ancestors, hpo_names = hpo_systems()
    systems_of = disease_to_systems(systems, ancestors)
    diseases = sorted(set(disease_genes) & set(systems_of))
    print(f"  {len(disease_genes)} diseases with a gene, {len(systems_of)} with a phenotype, "
          f"{len(diseases)} with both; {len(systems)} organ systems")

    print("building the coarse-grainings ...")
    pathways, pathway_names = gene_to_pathway()
    cells = gene_to_cell_type()
    print(f"  {len(pathways)} genes carry a top-level pathway, {len(cells)} a cell type")

    scales = {
        "gene": (project(diseases, disease_genes, lambda g: {g}), "the finest scale on disk"),
        "pathway": (project(diseases, disease_genes, lambda g: pathways.get(g, set())),
                    "Reactome top-level pathways"),
        "cell_type": (project(diseases, disease_genes, lambda g: cells.get(g, set())),
                      "Human Protein Atlas single-cell types"),
    }

    results = {}
    for name, (features, note) in scales.items():
        print(f"measuring {name} ...")
        results[name] = measure(diseases, features, systems_of, args.null, args.bootstrap, rng)
        results[name]["scale"] = note

    print("measuring retention per organ system ...")
    feature_sets = {k: v[0] for k, v in scales.items()}
    systems_table = per_system(diseases, feature_sets, systems_of, hpo_names,
                               max(args.null // 5, 5), rng)

    print("testing the morphogenesis prediction ...")
    morphogenesis = morphogenesis_test(systems_table, rng)

    base = results["gene"]["excess_bits"]
    for name, row in results.items():
        row["retained_vs_gene"] = round(row["excess_bits"] / base, 4) if base else None
        row["compression_vs_gene"] = (round(results["gene"]["alphabet"] / row["alphabet"], 2)
                                      if row["alphabet"] else None)

    payload = {
        "generated": date.today().isoformat(),
        "provenance": ("measured from HPO genes_to_disease + phenotype.hpoa + hp.obo, "
                       "Reactome UniProt2Reactome_All_Levels + PathwaysRelation, "
                       "Human Protein Atlas rna_single_cell_type, STRING v12 aliases/info"),
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md",
        "question": ("How much of what a disease's causal genes say about its organ systems "
                     "survives a coarse-graining onto pathways or onto cell types?"),
        "estimator": {
            "statistic": "mutual information I(F;S) in bits, each disease weighted 1",
            "null": (f"{args.null} permutations of the disease -> organ-system assignment; "
                     "every headline is the EXCESS over that null, because MI rises with "
                     "alphabet size for free"),
            "interval": (f"point +- 1.96 SE, the SE from a {args.bootstrap}-resample bootstrap "
                         "over diseases, each resample carrying its own permuted null. The "
                         "bootstrap gives the DISPERSION only: mutual information is biased "
                         "in n, so a percentile interval on a resample holding ~63% of the "
                         "diseases sits away from the point estimate"),
            "thresholds": {"CELL_TYPE_ENRICHMENT": CELL_TYPE_ENRICHMENT,
                           "SCALE_PERMUTATIONS": args.null},
            "seed": SEED,
        },
        "scales": results,
        "per_organ_system": systems_table,
        "morphogenesis_prediction": morphogenesis,
        "says": ("Observational mutual information over a static catalogue. NOT effective "
                 "information and NOT causal emergence: there is no intervention here and no "
                 "dynamics. It answers whether a coarser alphabet is still informative about "
                 "the phenotype, not whether it is the causally correct scale."),
        "limits": [
            "Organ systems come from HPO annotation, which is curated unevenly - the same "
            "ascertainment bias tools/atlas_bias.py measures at +0.2357 on this catalogue.",
            "Genes without a Reactome or HPA mapping drop out of that scale, so the three "
            "rows do not stand on identical disease sets; each row reports its own n.",
            "One coarse-graining per scale. A different pathway level or a different "
            "enrichment fraction is a different measurement, not a robustness check.",
        ],
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"{'scale':10s} {'n':>6s} {'|F|':>6s} {'I':>8s} {'null':>8s} {'excess':>8s} "
          f"{'95% CI':>18s} {'kept':>6s}")
    for name, row in results.items():
        ci = f"[{row['excess_ci95'][0]:.4f}, {row['excess_ci95'][1]:.4f}]"
        print(f"{name:10s} {row['diseases']:6d} {row['alphabet']:6d} "
              f"{row['mutual_information_bits']:8.4f} {row['null_mean_bits']:8.4f} "
              f"{row['excess_bits']:8.4f} {ci:>18s} {row['retained_vs_gene']:6.2f}")

    print()
    print("direction: U(system|features) against U(features|system)")
    for name, row in results.items():
        print(f"  {name:10s} {row['u_system_given_features']:.4f} vs "
              f"{row['u_features_given_system']:.4f}   ratio {row['asymmetry_ratio']}")

    print()
    print("retention by organ system, one-vs-rest, gene-scale z >= 5")
    print(f"  {'organ system':46s} {'n':>5s} {'pathway':>8s} {'cell':>7s}")
    for row in systems_table[:5]:
        print(f"  {row['name'][:46]:46s} {row['diseases']:5d} "
              f"{row['pathway_retention']:8.2f} {row['cell_type_retention']:7.2f}")
    if len(systems_table) > 5:
        last = systems_table[-1]
        print(f"  ... {len(systems_table)} systems in the artefact; the lowest is "
              f"{last['name'][:34]} at {last['pathway_retention']:.2f}")
    if morphogenesis:
        m, ph = morphogenesis["morphogenetic"], morphogenesis["physiological"]
        print()
        print("  the morphogenesis prediction (Turing 1952; Ashby 1956)")
        print(f"    physiological systems (n={ph['n']:2d}) keep "
              f"{ph['mean_pathway_retention']:.3f} of the gene-scale signal")
        print(f"    morphogenetic systems (n={m['n']:2d}) keep "
              f"{m['mean_pathway_retention']:.3f}")
        print(f"    difference {morphogenesis['difference']:+.3f}, "
              f"permutation p = {morphogenesis['permutation_p_one_sided']:.4f} "
              f"({morphogenesis['permutations']} draws, one-sided)")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
