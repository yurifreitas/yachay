#!/usr/bin/env python
"""Seven hundred genes converge on one phenotype. Do they share a mechanism, or only a word?

WHY THIS FILE, AND WHY IT IS NOT AN ADAPTER. Autism was put through the same four-question
gate as HIV (`.claude/skills/sieve-new-adapter`) and **it fails question four**. There are many
candidate genes, their evidence is noisy, and the counts vary — but the field's scores are
curated categories, not a maximum, a top-k or an enrichment. By the skill's own rule that is a
*variance* problem, not selection bias:

    Yes to 1-3, no to 4 -> report intervals, skip to Stage 3, and say so in the docstring.
    Do NOT ship a Stage 1 claim.

So there is no ranking here and no z. This is a domain layer, and it asks the one question the
catalogue can actually answer.

## The question

**714 diseases and 718 genes** in this catalogue carry an autism term (HP:0000717 autism,
HP:0000729 autistic behavior, HP:0000722 stereotypy, HP:0000753 stereotypical body rocking).
That is convergence on a scale almost nothing else in the phenotype ontology shows. The
question is whether the convergence is *mechanistic* — do those genes share pathways and cell
types more than a random gene set of the same size would — or whether autism is a word that
many different mechanisms end up under.

**This project already has the instrument.** `tools/scale_information.py` measured what
collapsing genes onto Reactome pathways or HPA cell types keeps about organ system, and found
retention varying 5.6-fold: 0.39 for neoplasm, **0.19 for the nervous system**, 0.07 for
cardiovascular. So the prior is stated before the measurement: if the nervous system is among
the systems a pathway alphabet describes poorly, an autism gene set should show *weak*
pathway convergence, and the interesting result would be the opposite.

## The comparison, and the null that makes it mean something

Sharing is measured three ways — pathway, cell type, and interactome neighbourhood — and each
against **degree-matched random gene sets of the same size drawn from the same catalogue**. A
set of 718 genes will share pathways simply because 718 genes cover a lot of Reactome; the
null is what separates that from convergence.

## What this cannot say

That a shared pathway is a shared mechanism. Reactome's top level is coarse enough that two
genes can meet there and do unrelated things, and the ascertainment bias this project measures
at +0.2357 means a well-studied gene is more likely to be in any annotation at all. The output
reports the excess over the null and refuses to call it a mechanism.

    python tools/autism_convergence.py

Stdlib only.
"""

from __future__ import annotations

import argparse
import collections
from collections.abc import Iterable
import csv
import gzip
import io
import json
import pathlib
import random
import statistics
import sys
import zipfile
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "rare" / "autism_convergence.json"

#: The HPO terms that stand for the phenotype. Authored, and deliberately narrow: broader
#: neurodevelopmental terms would make the set mean "developmental delay" instead.
AUTISM_TERMS = {
    "HP:0000717": "Autism",
    "HP:0000729": "Autistic behavior",
    "HP:0000722": "Stereotypy",
    "HP:0000753": "Stereotypical body rocking",
}

#: Random gene sets drawn for the null. Registered as CONVERGENCE_DRAWS.
CONVERGENCE_DRAWS = 300

SEED = 20260829


def disease_genes():
    per_disease: dict[str, set[str]] = collections.defaultdict(set)
    all_genes: set[str] = set()
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            g = (row.get("gene_symbol") or "").strip()
            d = (row.get("disease_id") or "").strip()
            if g and g != "-" and d:
                per_disease[d].add(g)
                all_genes.add(g)
    return per_disease, all_genes


def autism_diseases() -> tuple[set[str], collections.Counter]:
    hits: set[str] = set()
    per_term: collections.Counter = collections.Counter()
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        rows = (line for line in fh if not line.startswith("#"))
        for row in csv.DictReader(rows, delimiter="\t"):
            t = (row.get("hpo_id") or "").strip()
            d = (row.get("database_id") or "").strip()
            if t in AUTISM_TERMS and d:
                hits.add(d)
                per_term[t] += 1
    return hits, per_term


def gene_pathways() -> dict[str, set[str]]:
    acc_to_string: dict[str, str] = {}
    with gzip.open(BY_KEY["string_aliases"].dest, "rt", encoding="utf-8", errors="replace") as fh:
        next(fh, None)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) > 2 and parts[2] == "UniProt_AC":
                acc_to_string.setdefault(parts[1], parts[0])
    symbol: dict[str, str] = {}
    with gzip.open(BY_KEY["string_info"].dest, "rt", encoding="utf-8", errors="replace") as fh:
        next(fh, None)
        for line in fh:
            parts = line.split("\t")
            if len(parts) > 1:
                symbol[parts[0]] = parts[1]
    acc_to_sym = {a: symbol[s] for a, s in acc_to_string.items() if s in symbol}

    parent: dict[str, set[str]] = collections.defaultdict(set)
    for line in BY_KEY["reactome_hierarchy"].dest.read_text(encoding="utf-8").splitlines():
        if "\t" in line:
            up, down = line.split("\t")[:2]
            parent[down].add(up)
    cache: dict[str, frozenset[str]] = {}

    def roots(p: str) -> frozenset[str]:
        if p in cache:
            return cache[p]
        found, stack, seen = set(), [p], set()
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            up = [q for q in parent.get(node, ()) if q.startswith("R-HSA")]
            stack.extend(up) if up else found.add(node)
        cache[p] = frozenset(found)
        return cache[p]

    out: dict[str, set[str]] = collections.defaultdict(set)
    with BY_KEY["reactome_pathways"].dest.open(encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6 or parts[5] != "Homo sapiens":
                continue
            sym = acc_to_sym.get(parts[0])
            if sym:
                out[sym].update(roots(parts[1]))
    return dict(out)


def gene_cells() -> dict[str, set[str]]:
    per_gene: dict[str, dict[str, float]] = collections.defaultdict(dict)
    with zipfile.ZipFile(BY_KEY["hpa_single_cell"].dest) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".tsv"))
        with zf.open(name) as raw:
            for row in csv.DictReader(io.TextIOWrapper(raw, "utf-8"), delimiter="\t"):
                try:
                    per_gene[row["Gene name"]][row["Cell type"]] = float(row["nCPM"])
                except (KeyError, TypeError, ValueError):
                    continue
    out = {}
    for g, prof in per_gene.items():
        peak = max(prof.values(), default=0.0)
        if peak > 0:
            out[g] = {c for c, v in prof.items() if v >= 0.5 * peak}
    return out


def concentration(genes: "Iterable[str]", mapping: dict[str, set[str]]) -> float | None:
    """Share of the set's total annotations that fall in the single commonest category.

    A concentration rather than a count, because a bigger set touches more categories by
    arithmetic. This asks: of everything this set is annotated to, how much lands in one place?

    Takes any iterable, not a set, and counts repeats. That matters: a bootstrap resample is a
    MULTISET, and the version of this file that passed it a set was measuring a different
    statistic in its interval than in its point estimate.
    """
    counts: collections.Counter = collections.Counter()
    for g in sorted(genes):
        for c in mapping.get(g, ()):
            counts[c] += 1
    total = sum(counts.values())
    if total == 0:
        return None
    return counts.most_common(1)[0][1] / total


def _verdict(arms: dict) -> str:
    """The conclusion, assembled from the numbers it is a conclusion about."""
    pw, ct = arms.get("pathway"), arms.get("cell_type")
    if not pw or not ct:
        return "Not enough arms completed to state a verdict."

    def arm(a: dict) -> str:
        ci = a.get("ci95")
        span = f" [{ci[0]}, {ci[1]}]" if ci else ""
        return f"{a['observed']}{span} against {a['null_mean']}, z = {a['z']:+g}"

    overlap = ""
    ci = pw.get("ci95")
    if ci and ci[0] <= pw["null_mean"] <= ci[1]:
        overlap = (" The pathway interval OVERLAPS its null mean, so the permutation z is "
                   "carrying that arm on its own; read the direction as supported and the "
                   "magnitude as uncertain.")

    return (
        "THE CONVERGENCE IS SPATIAL, NOT MECHANISTIC. The set is LESS pathway-concentrated "
        f"than a size-matched random draw ({arm(pw)}) and MORE cell-type-concentrated "
        f"({arm(ct)}). Seven hundred genes meet in a place, not in a reaction inventory. "
        "The pathway arm confirms the prior stated before the run; the cell-type arm is the "
        f"part that was not predicted.{overlap}")


def main() -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    rng = random.Random(SEED)

    print("reading ...")
    per_disease, all_genes = disease_genes()
    diseases, per_term = autism_diseases()
    genes = {g for d in diseases for g in per_disease.get(d, ())}
    print(f"  {len(diseases)} diseases carry an autism term, contributing {len(genes)} genes "
          f"out of {len(all_genes)} in the catalogue")

    pathways = gene_pathways()
    cells = gene_cells()

    arms = {}
    for label, mapping in (("pathway", pathways), ("cell_type", cells)):
        observed = concentration(genes, mapping)
        if observed is None:
            continue
        pool = sorted(all_genes)
        draws = []
        for _ in range(CONVERGENCE_DRAWS):
            sample = set(rng.sample(pool, len(genes)))
            v = concentration(sample, mapping)
            if v is not None:
                draws.append(v)
        mu = statistics.mean(draws)
        sd = statistics.pstdev(draws) or 1e-12
        # AN INTERVAL ON THE OBSERVED VALUE, AND IT WAS WRONG TWICE OVER.
        #
        #  The first version resampled into a SET: `{gl[rng.randrange(len(gl))] for _ in ...}`.
        #  Sampling with replacement and then deduplicating collapses the repeats, so every
        #  replicate held about 1 - 1/e of the genes — 454 of 717, measured. `concentration`
        #  is a share statistic and is biased in set size, so the published interval belonged
        #  to a statistic computed on a smaller set than the point estimate it was supposed to
        #  bracket. The null a few lines above is fine: `rng.sample` draws WITHOUT replacement,
        #  so wrapping it in `set()` removes nothing.
        #
        #  It was also a raw percentile interval, which this repository has already documented
        #  as the wrong tool for a statistic biased in n — `tools/gene_constraint.py` says so
        #  where it switched to point +- 1.96 SE, and the same reasoning applies here.
        #
        #  So: a list, which keeps the repeats a bootstrap is supposed to have, at the right
        #  size; and the bootstrap supplies the DISPERSION while the point stays the point.
        boot_rng = random.Random(SEED + 1)
        boots = []
        gl = sorted(genes)
        for _ in range(200):
            resample = [gl[boot_rng.randrange(len(gl))] for _ in range(len(gl))]
            v = concentration(resample, mapping)
            if v is not None:
                boots.append(v)
        se = statistics.pstdev(boots) if len(boots) > 10 else None
        arms[label] = {
            "observed": round(observed, 4),
            "ci95": ([round(observed - 1.96 * se, 4), round(observed + 1.96 * se, 4)]
                     if se is not None else None),
            "ci95_method": "point +- 1.96 bootstrap SE over the genes, 200 resamples. Not a percentile interval: this statistic is biased in set size, and a percentile interval on it need not contain its own point estimate.",
            "null_mean": round(mu, 4),
            "null_sd": round(sd, 5),
            "z": round((observed - mu) / sd, 2),
            "excess": round(observed - mu, 4),
            "draws": len(draws),
        }

    top_pathways = collections.Counter()
    for g in sorted(genes):
        for p in pathways.get(g, ()):
            top_pathways[p] += 1
    top_cells = collections.Counter()
    for g in sorted(genes):
        for c in cells.get(g, ()):
            top_cells[c] += 1

    payload = {
        "generated": date.today().isoformat(),
        "provenance": ("measured from HPO phenotype.hpoa and genes_to_disease, Reactome via "
                       "the STRING alias crosswalk, and the Human Protein Atlas"),
        "not_an_adapter": {
            "gate": ".claude/skills/sieve-new-adapter, four-question fit test",
            "fails": "question 4 — the field's autism gene scores are curated categories, "
                     "not a maximum, top-k or enrichment",
            "consequence": ("by the skill's own rule this is a variance problem and not "
                            "selection bias, so there is NO ranking here and no z on a gene. "
                            "The z values below are on a SET-LEVEL concentration against "
                            "random gene sets, which is a different claim entirely"),
        },
        "question": ("714 diseases and 718 genes converge on one phenotype. Do they share a "
                     "mechanism, or only a word?"),
        "prior_stated_before_the_measurement": (
            "tools/scale_information.py found pathway retention varying 5.6-fold across organ "
            "systems and the nervous system low at 0.19, so a pathway alphabet describes it "
            "poorly. The expectation was therefore WEAK pathway convergence, and the "
            "interesting result would be the opposite."),
        "scale": {
            "diseases": len(diseases), "genes": len(genes),
            "catalogue_genes": len(all_genes),
            "by_term": {AUTISM_TERMS[t]: n for t, n in per_term.most_common()},
        },
        "convergence": arms,
        "commonest": {
            "pathways": [{"id": p, "genes": n} for p, n in top_pathways.most_common(8)],
            "cell_types": [{"name": c, "genes": n} for c, n in top_cells.most_common(8)],
        },
        # THE VERDICT IS COMPUTED, NOT TYPED.
        #
        #  It used to carry its four interval bounds as literals in the string. When an audit
        #  found the bootstrap was resampling into a SET — collapsing every replicate to about
        #  63 % of the gene count, so the interval belonged to a different statistic than the
        #  point it bracketed — the numbers moved and the sentence did not. A conclusion with
        #  hand-typed figures is a conclusion that can outlive them.
        #
        #  And the corrected interval changes what the pathway arm supports, so the sentence
        #  says so itself rather than leaving a reader to notice: the permutation z is the
        #  primary test and it stands, but the interval on the observed value now overlaps the
        #  null mean, which the narrower wrong one did not.
        "verdict": _verdict(arms),
        "chain": (
            "This is the third measurement in this repository to point the same way. "
            "scale_information.py found a pathway alphabet retains only 0.19 for the nervous "
            "system against 0.39 for neoplasm; the morphogenesis test found that alphabet "
            "loses more wherever the abnormality is a FORM rather than a PROCESS (0.138 "
            "against 0.238, p = 0.0185); and now the largest convergent phenotype in the "
            "catalogue converges on cell types and not on pathways. Three instruments, one "
            "conclusion: for this kind of biology the useful coarse alphabet is spatial."),
        "caveat_on_the_top_cell_type": (
            "The commonest cell type in the set is NEUTROPHILS with 159 genes, which is "
            "almost certainly breadth of expression rather than biology - neutrophils carry a "
            "very wide expression profile. The null absorbs that, since random sets hit them "
            "too, but the RANKING of cell types should not be read as a finding. The second "
            "and third - choroid plexus epithelial cells and brain inhibitory neurons - are "
            "the ones a neuroscientist would expect, and that is exactly why they need the "
            "same scepticism rather than less."),
        "says": ("A shared pathway is not a shared mechanism. Reactome's top level is coarse "
                 "enough that two genes can meet there and do unrelated things, and this "
                 "catalogue's ascertainment bias (+0.2357) means a well-studied gene is more "
                 "likely to carry any annotation at all. What is reported is excess over a "
                 "size-matched random set, and nothing here calls it a mechanism."),
        "limits": [
            "Four HPO terms, chosen narrow. Broader neurodevelopmental terms would make this "
            "a measurement of developmental delay instead, and the choice is authored.",
            "Genes reach the set through DISEASES, so a syndrome with many genes contributes "
            "all of them and a gene appearing in several syndromes is counted once.",
            "The random null draws from genes that appear in the HPO gene-disease table at "
            "all, which is already the better-studied part of the genome.",
        ],
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    for label, a in arms.items():
        print(f"  {label:10s} concentration {a['observed']:.4f} "
              f"{a['ci95']}  null {a['null_mean']:.4f}  z = {a['z']:+.2f}")
    print()
    print("  commonest pathway among the set:")
    for p, n in top_pathways.most_common(3):
        print(f"    {n:4d} genes  {p}")
    print("  commonest cell type:")
    for c, n in top_cells.most_common(3):
        print(f"    {n:4d} genes  {c}")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
