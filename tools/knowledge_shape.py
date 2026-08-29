#!/usr/bin/env python
"""Knowledge has a shape, and for most rare diseases it is a spike.

THE IDEA, AND WHY IT IS UNUSUAL. Every rare-disease resource answers "how much is known about
this disease?" with a quantity - papers, genes, annotations. The design work behind this atlas
proposes something else: that what matters is the **anisotropy** of what is known. A disease
with a thousand genetics papers and two on natural history is not well studied; it is studied
along one axis and dark along the others, and a clinician standing on a dark axis gets nothing
from the thousand.

So the object is not a score but a vector, and the question is its shape:

    K_D = [ genetics, phenotype, cellular, natural history, population ]

and then, across the catalogue: **is knowledge distributed or concentrated?** If concentrated,
on which axis, and does the answer differ between the diseases the field has studied a lot and
the ones it has barely touched?

## The five axes, and what each is counted from

Every axis is a count over an ingested public source, normalised to its own catalogue-wide
distribution (a rank, so that "many genes" and "many annotations" are commensurable at all):

    genetics          causal genes (HPO) + ClinVar submissions for those genes
    phenotype         HPO annotations, weighted by how many carry a real evidence code
    cellular          distinct HPA cell types reachable from the disease's genes
    natural history   annotations carrying an ONSET, plus Orphanet age-of-onset records
    population        Orphanet prevalence records for the disorder

**These are proxies and the artefact says so.** "Cellular knowledge" here is expression
reachability, not cell biology; a disease can have deep cellular literature and score zero
because its genes are not in the HPA table. What the measurement supports is a statement about
the SHAPE of the catalogue's coverage, which is the thing a reader of the atlas actually faces.

## The statistic

Normalised entropy over the five ranks, so 1.0 is a disease known equally along every axis and
0.0 is everything on one axis:

    H(D) = -sum p_i log p_i / log 5,   p_i = axis_i / sum(axis)

reported as **anisotropy = 1 - H**, against a null that shuffles each axis independently
across diseases. The null matters: five heavy-tailed counts will look concentrated even when
independent, so raw anisotropy would measure the marginals.

    python tools/knowledge_shape.py

Stdlib only.
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
from xml.etree import ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "rare" / "knowledge_shape.json"

AXES = ["genetics", "phenotype", "cellular", "natural_history", "population"]

#: A disease needs a non-zero count on at least this many axes to have a shape at all. Below
#: it the entropy is an artefact of the zeros. Registered as MIN_AXES.
MIN_AXES = 2

#: Permutation draws behind the null. Registered as SHAPE_PERMUTATIONS.
SHAPE_PERMUTATIONS = 200

SEED = 20260829

#: HPO evidence codes that stand for an actual observation rather than an inference.
REAL_EVIDENCE = {"PCS", "ICE"}


def disease_genes() -> dict[str, set[str]]:
    out: dict[str, set[str]] = collections.defaultdict(set)
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            g, d = (row.get("gene_symbol") or "").strip(), (row.get("disease_id") or "").strip()
            if g and d:
                out[d].add(g)
    return dict(out)


def annotations() -> tuple[collections.Counter, collections.Counter, collections.Counter]:
    """Per disease: all annotations, those with a real evidence code, those with an onset."""
    total: collections.Counter = collections.Counter()
    solid: collections.Counter = collections.Counter()
    onset: collections.Counter = collections.Counter()
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        rows = (line for line in fh if not line.startswith("#"))
        for row in csv.DictReader(rows, delimiter="\t"):
            d = (row.get("database_id") or "").strip()
            if not d:
                continue
            total[d] += 1
            if (row.get("evidence") or "").strip() in REAL_EVIDENCE:
                solid[d] += 1
            if (row.get("onset") or "").strip():
                onset[d] += 1
    return total, solid, onset


def gene_cell_types() -> dict[str, set[str]]:
    per_gene: dict[str, dict[str, float]] = collections.defaultdict(dict)
    with zipfile.ZipFile(BY_KEY["hpa_single_cell"].dest) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".tsv"))
        with zf.open(name) as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, "utf-8"), delimiter="\t"):
                try:
                    per_gene[row["Gene name"]][row["Cell type"]] = float(row["nCPM"])
                except (KeyError, TypeError, ValueError):
                    continue
    out: dict[str, set[str]] = {}
    for gene, profile in per_gene.items():
        peak = max(profile.values(), default=0.0)
        if peak > 0:
            out[gene] = {c for c, v in profile.items() if v >= 0.5 * peak}
    return out


def clinvar_by_gene() -> collections.Counter:
    counts: collections.Counter = collections.Counter()
    with gzip.open(BY_KEY["clinvar"].dest, "rt", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row.get("Assembly") != "GRCh38":
                continue
            sym = (row.get("GeneSymbol") or "").strip()
            if sym and sym != "-":
                counts[sym] += 1
    return counts


def orphanet_counts(key: str, tag: str) -> collections.Counter:
    """Records per ORPHA disorder in one of Orphanet's product files."""
    counts: collections.Counter = collections.Counter()
    try:
        root = ET.parse(BY_KEY[key].dest).getroot()
    except (OSError, ET.ParseError):
        return counts
    for disorder in root.iter("Disorder"):
        code = disorder.findtext("OrphaCode")
        if not code:
            continue
        n = sum(1 for _ in disorder.iter(tag))
        if n:
            counts[f"ORPHA:{code}"] += n
    return counts


def ranks(values: dict[str, float]) -> dict[str, float]:
    """Fractional rank in [0,1]. Ranks, not raw counts: five heavy-tailed counts on different
    units cannot be added, and normalising by the maximum would let one outlier set the scale."""
    ordered = sorted(values.items(), key=lambda kv: kv[1])
    n = len(ordered)
    out: dict[str, float] = {}
    for i, (k, _) in enumerate(ordered):
        out[k] = (i + 1) / n
    return out


def anisotropy(vec: list[float]) -> float | None:
    total = sum(vec)
    if total <= 0:
        return None
    entropy = 0.0
    for v in vec:
        if v > 0:
            p = v / total
            entropy -= p * math.log(p)
    return 1.0 - entropy / math.log(len(vec))


def main() -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    rng = random.Random(SEED)

    print("reading ...")
    genes = disease_genes()
    total, solid, onset = annotations()
    cells = gene_cell_types()
    clinvar = clinvar_by_gene()
    prevalence = orphanet_counts("orpha_prevalence", "Prevalence")
    ages = orphanet_counts("orpha_ages", "AverageAgeOfOnset")
    print(f"  {len(genes)} diseases with a gene, {len(total)} with an annotation, "
          f"{len(prevalence)} with a prevalence record, {len(ages)} with an age of onset")

    diseases = sorted(set(genes) | set(total))
    raw: dict[str, dict[str, float]] = {}
    for d in diseases:
        gs = genes.get(d, set())
        raw[d] = {
            "genetics": len(gs) + sum(clinvar.get(g, 0) for g in gs) / 100.0,
            "phenotype": total.get(d, 0) + 2 * solid.get(d, 0),
            "cellular": len({c for g in gs for c in cells.get(g, ())}),
            "natural_history": onset.get(d, 0) + ages.get(d, 0),
            "population": prevalence.get(d, 0),
        }

    ranked = {axis: ranks({d: raw[d][axis] for d in diseases}) for axis in AXES}
    # A zero count must stay zero: a fractional rank would give an unmeasured axis a floor.
    for axis in AXES:
        for d in diseases:
            if raw[d][axis] <= 0:
                ranked[axis][d] = 0.0

    rows = []
    for d in diseases:
        vec = [ranked[a][d] for a in AXES]
        live = sum(1 for v in vec if v > 0)
        if live < MIN_AXES:
            continue
        a = anisotropy(vec)
        if a is None:
            continue
        dominant = AXES[max(range(len(vec)), key=lambda i: vec[i])]
        rows.append({"disease": d, "axes_present": live, "anisotropy": round(a, 4),
                     "dominant_axis": dominant,
                     "vector": {ax: round(v, 4) for ax, v in zip(AXES, vec)}})

    observed = sum(r["anisotropy"] for r in rows) / len(rows)

    # An interval on the headline. standards.md 4 asks for one on any published number and
    # the first version of this file shipped the mean with a z and no dispersion of its own.
    # A mean is unbiased under resampling, so the percentile interval is used directly.
    #
    # ITS OWN GENERATOR, AND THAT IS THE POINT. Drawing these from `rng` consumed numbers
    # ahead of the permutation null below and moved a PUBLISHED figure: z went from -19.0 to
    # -20.37 without a single line of the null's own code changing. tools/verify_claims.py
    # caught it on the next run. A stream shared between an added statistic and an existing
    # one couples them, so every statistic here takes a generator seeded for itself.
    boot_rng = random.Random(SEED + 1)
    boot_means = []
    for _ in range(400):
        boot_means.append(sum(rows[boot_rng.randrange(len(rows))]["anisotropy"]
                              for _ in range(len(rows))) / len(rows))
    boot_means.sort()
    mean_ci = [round(boot_means[9], 5), round(boot_means[-10], 5)]

    # Null: shuffle each axis independently across diseases, preserving every marginal. What
    # survives is the CO-OCCURRENCE structure - whether the axes rise and fall together.
    nulls = []
    keys = [r["disease"] for r in rows]
    columns = {a: [ranked[a][d] for d in keys] for a in AXES}
    for _ in range(SHAPE_PERMUTATIONS):
        shuffled = {}
        for a in AXES:
            col = columns[a][:]
            rng.shuffle(col)
            shuffled[a] = col
        acc = 0.0
        for i in range(len(keys)):
            v = anisotropy([shuffled[a][i] for a in AXES])
            acc += v if v is not None else 0.0
        nulls.append(acc / len(keys))
    null_mean = sum(nulls) / len(nulls)
    null_sd = (sum((x - null_mean) ** 2 for x in nulls) / max(len(nulls) - 1, 1)) ** 0.5
    z = (observed - null_mean) / null_sd if null_sd else None

    dominant = collections.Counter(r["dominant_axis"] for r in rows)
    by_axes_present = collections.defaultdict(list)
    for r in rows:
        by_axes_present[r["axes_present"]].append(r["anisotropy"])
    depth = {str(k): {"diseases": len(v), "mean_anisotropy": round(sum(v) / len(v), 4)}
             for k, v in sorted(by_axes_present.items())}

    spikes = [r for r in rows if r["anisotropy"] >= 0.5]

    # ANISOTROPY TURNED OUT TO BE MOSTLY A COUNT. The by_axes_present table below shows it
    # falling monotonically from 0.590 at two live axes to 0.021 at five, which is close to
    # arithmetic: with fractional ranks, more non-zero entries is a flatter vector. So the
    # statistic answers "how broad is the coverage", not "what shape is the knowledge", and
    # the shape question needs the CO-OCCURRENCE structure instead - which axes rise and fall
    # together across the catalogue. Spearman, because the inputs are already ranks.
    def spearman(a: str, b: str) -> float:
        xs = [ranked[a][d] for d in keys_all]
        ys = [ranked[b][d] for d in keys_all]
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
        dy = math.sqrt(sum((y - my) ** 2 for y in ys))
        return num / (dx * dy) if dx and dy else 0.0

    keys_all = [r["disease"] for r in rows]
    pairs = {}
    for i, a in enumerate(AXES):
        for b in AXES[i + 1:]:
            pairs[f"{a}~{b}"] = round(spearman(a, b), 4)
    loneliest = min(
        AXES,
        key=lambda a: sum(v for k, v in pairs.items() if a in k.split("~"))
        / max(sum(1 for k in pairs if a in k.split("~")), 1))

    payload = {
        "generated": date.today().isoformat(),
        "provenance": ("measured from HPO genes_to_disease + phenotype.hpoa, ClinVar "
                       "variant_summary, Human Protein Atlas single-cell, Orphanet "
                       "prevalence and age-of-onset"),
        "question": ("Is what is known about a rare disease spread across the axes a reader "
                     "needs, or concentrated on one? The object is a vector, not a score."),
        "verdict": ("THE PREDICTION FAILS, TWICE. Knowledge is LESS concentrated than "
                    "independence would give (mean anisotropy 0.2633 against a null of "
                    "0.2723, z = -19.0), not more - the axes rise and fall together. And the "
                    "anisotropy statistic turns out to track the NUMBER of populated axes "
                    "almost arithmetically (0.590 at two live axes, 0.021 at five), so it "
                    "answers 'how broad is the coverage' rather than 'what shape is the "
                    "knowledge'. The replacement question - which axes co-occur - then finds "
                    "that the strongest couplings are artefacts of how the axes were built, "
                    "and that the residual structure is a registry boundary. Recorded in "
                    "full because a catalogue of ideas where every idea works is a catalogue "
                    "nobody tested."),
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md",
        "axes": {
            "genetics": "causal genes, plus ClinVar submissions on those genes / 100",
            "phenotype": "HPO annotations, double-weighted when the evidence code is PCS or ICE",
            "cellular": "distinct HPA cell types reachable from the genes",
            "natural_history": "annotations carrying an onset, plus Orphanet age-of-onset records",
            "population": "Orphanet prevalence records",
        },
        "statistic": {
            "value": "anisotropy = 1 - normalised entropy over five fractional ranks",
            "null": (f"{SHAPE_PERMUTATIONS} permutations, each axis shuffled INDEPENDENTLY "
                     "across diseases so every marginal is preserved and only the "
                     "co-occurrence between axes is destroyed"),
            "why_ranks": ("five heavy-tailed counts on different units cannot be added; "
                          "normalising by the maximum would let one outlier set the scale"),
        },
        "scale": {"diseases_with_a_shape": len(rows),
                  "diseases_considered": len(diseases),
                  "min_axes": MIN_AXES},
        "headline": {
            "mean_anisotropy": round(observed, 4),
            "mean_ci95": mean_ci,
            "null_mean": round(null_mean, 4),
            "null_sd": round(null_sd, 5),
            "z_vs_null": round(z, 2) if z is not None else None,
            "diseases_at_or_above_half": len(spikes),
            "share_at_or_above_half": round(len(spikes) / len(rows), 4),
        },
        # The per-disease vectors. They stay in the LOCAL artefact and are dropped by
        # web/scripts/build-data.mjs, because 12,994 five-dimensional rows are what
        # tools/view_models.py needs to bin and what a browser has no use for.
        "diseases": rows,
        "dominant_axis": dict(dominant.most_common()),
        "axis_correlation": {
            "asks": ("Which axes rise and fall together? This is the shape question the "
                     "anisotropy statistic could not answer, because that statistic turned "
                     "out to track the NUMBER of populated axes almost arithmetically."),
            "spearman": pairs,
            "least_coupled_axis": loneliest,
            "says": ("READ THE TOP TWO PAIRS AS DEFECTS OF THIS MEASUREMENT, NOT AS FINDINGS. "
                     "natural_history~population (+0.759) is high because both axes are "
                     "counted from Orphanet, and genetics~cellular (+0.640) is high because "
                     "the cellular axis is DERIVED from the genetics axis - cell types are "
                     "reached through the disease's genes. Neither says anything about "
                     "knowledge. What is left after removing them is the finding: "
                     "genetics~phenotype is +0.012, so knowing a disease's genes predicts "
                     "nothing about how well its phenotype is annotated; and every "
                     "cross-catalogue pair is NEGATIVE, with phenotype~population at -0.332. "
                     "That is the OMIM/ORPHA fault line - HPO annotation is OMIM-heavy and "
                     "prevalence exists only under ORPHA codes - appearing as if it were a "
                     "shape of knowledge. At catalogue scale this vector largely measures "
                     "WHICH REGISTRY a disease lives in."),
        },
        "by_axes_present": depth,
        "says": ("A statement about the shape of the CATALOGUE's coverage, not about the "
                 "literature. Every axis is a proxy over an ingested source and a disease can "
                 "be deeply studied on an axis that scores zero here because its evidence "
                 "does not reach these files."),
        "limits": [
            "Five axes, chosen because they are the five this project can count. Treatment "
            "and mechanism are missing and are exactly where the catalogue is thinnest.",
            "A rank is relative to this catalogue, so anisotropy cannot be compared across "
            "releases without recomputing both.",
            "Diseases scoring on fewer than two axes are excluded rather than called maximally "
            "anisotropic, which would confuse absence with concentration.",
        ],
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"  {len(rows)} diseases have a shape at all (>= {MIN_AXES} axes)")
    print(f"  mean anisotropy {observed:.4f} against a null of {null_mean:.4f} "
          f"(z = {z:.1f})" if z is not None else "")
    print(f"  {len(spikes)} ({100*len(spikes)/len(rows):.1f} %) sit at 0.5 or above — "
          f"more than half their knowledge on one axis")
    print()
    print("  dominant axis")
    for axis, n in dominant.most_common():
        print(f"    {axis:16s} {n:6d}  {100*n/len(rows):5.1f} %")
    print()
    print("  by how many axes carry anything")
    for k, v in depth.items():
        print(f"    {k} axes  {v['diseases']:6d} diseases   mean anisotropy "
              f"{v['mean_anisotropy']:.3f}")
    print()
    print("  how the axes move together (Spearman over ranks)")
    for k, v in sorted(pairs.items(), key=lambda kv: -kv[1]):
        flag = "   <- artefact of construction, not a finding" if v > 0.5 else ""
        print(f"    {k:34s} {v:+.3f}{flag}")
    print(f"    least coupled axis: {loneliest}")
    print()
    print("  VERDICT: the prediction fails. Knowledge is LESS concentrated than independence")
    print("  gives, the anisotropy statistic tracks how many axes are populated rather than")
    print("  their shape, and what survives is a registry boundary wearing a shape.")

    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
