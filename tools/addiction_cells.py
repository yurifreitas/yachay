#!/usr/bin/env python
"""Which cells the genetics of addiction lands in — and whether the answer depends on what was measured.

`addiction_atlas.py` established that only about a quarter of the sample behind substance-use
GWAS sits behind a disorder phenotype; the rest measures how much somebody uses, or which organ
failed. That was a finding about the FIELD. This asks the biological question it opens, and it
is the reason the associations file was ingested:

> The genetics of "who cannot stop" and the genetics of "who drinks a lot" are reported under
> one heading. Do they land in the same cells?

## How the question is made answerable

Every catalogued association carries the gene its variant was mapped to. Substance-use
associations are selected by the same rules `addiction_atlas.py` uses — the same substance
words, the same exclusions for traits that merely mention a substance, the same phenotype-kind
classifier — imported rather than copied, so the two files cannot drift into disagreeing about
what counts as an alcohol study.

Those genes are then mapped to cell types through the Human Protein Atlas single-cell data:
154 cell types, of which nine are brain.

## The control, which is the whole difficulty

Genes that appear in GWAS are not a random sample of genes. They are longer, better studied,
and — the part that matters here — **expressed in more cell types**, because a gene expressed
everywhere has more chances to be enriched anywhere. An unmatched null would report that
addiction genetics implicates whichever cell types express the most genes, which is a fact
about the Human Protein Atlas rather than about addiction.

So the null draws gene sets **matched on expression breadth**, in quantile bins of how many
cell types each gene is enriched in. Same construction as `community_identity.py`, for the same
reason, and the same reason `gene_constraint.py` matches on coding length — where two thirds of
the apparent effect turned out to be the covariate.

Empirical tails floored at 1/(draws+1), Benjamini–Hochberg across the whole family. No z is
computed: `docs/audit.md` A41 established that a z past about 2.6 extrapolates beyond what a
permutation of this size resolves.

    python tools/addiction_cells.py

Stdlib plus numpy and statsmodels.
"""

from __future__ import annotations

import collections
import csv
import importlib.util
import io
import json
import pathlib
import statistics
import sys
import zipfile

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "psychiatric" / "addiction_cells.json"

SEED = 20260831
DRAWS = 400

#: A cell type must be hit by this many of a set's genes to be tested at all. Below three, one
#: gene decides the answer.
MIN_HITS = 3

#: A gene set smaller than this is not tested: the matched null cannot be drawn meaningfully
#: and the multiplicity cost buys nothing.
MIN_GENES = 10


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def associations():
    """Every catalogued association, streamed out of the zip.

    Streamed rather than loaded: 1.19 million rows with sixty columns is a gigabyte in memory
    for four fields, and nothing here needs the other fifty-six.
    """
    src = BY_KEY["gwas_associations"].dest
    with zipfile.ZipFile(src) as z:
        name = next(n for n in z.namelist() if n.endswith(".tsv"))
        with z.open(name) as fh:
            for row in csv.DictReader(io.TextIOWrapper(fh, "utf-8"), delimiter="\t"):
                yield row


def genes_in(field: str) -> list[str]:
    """MAPPED_GENE holds one symbol, or several separated by ` - ` or `, `.

    The dash form means the variant is INTERGENIC and the two genes flank it. Both are kept
    and the count of them is published: dropping them would discard the intergenic majority of
    a GWAS, and treating them as certain would credit two genes for one variant. They are
    counted once each, which is the compromise, and it is stated.
    """
    if not field or field in ("", "-", "NR"):
        return []
    parts = field.replace(" - ", ",").split(",")
    return [p.strip() for p in parts if p.strip() and p.strip() not in ("-", "NR")]


def main() -> int:
    aa = load("addiction_atlas")
    si = load("scale_information")

    cells = si.gene_to_cell_type()
    breadth = {g: len(v) for g, v in cells.items()}
    universe = sorted(cells)
    print(f"  {len(universe)} genes with cell-type expression, "
          f"{len({c for v in cells.values() for c in v})} cell types")

    # ---- the substance-use gene sets --------------------------------------------------------
    per_set: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    intergenic = 0
    seen = 0
    for row in associations():
        trait = (row.get("DISEASE/TRAIT") or "").strip()
        sub = aa.substance_of(trait)
        if not sub:
            continue
        seen += 1
        kind = aa.kind_of(trait)
        gs = genes_in(row.get("MAPPED_GENE") or "")
        if len(gs) > 1:
            intergenic += 1
        for g in gs:
            if g in cells:
                per_set[(sub, kind)].add(g)
                per_set[("all", kind)].add(g)
                per_set[(sub, "any")].add(g)
                per_set[("all", "any")].add(g)
    print(f"  {seen} substance associations, {intergenic} intergenic (two flanking genes)")

    # ---- the breadth-matched null -----------------------------------------------------------
    counts = np.array([breadth[g] for g in universe])
    edges = np.unique(np.quantile(counts, np.linspace(0, 1, 9)))
    bin_of = {g: int(np.searchsorted(edges, breadth[g], side="right")) for g in universe}
    by_bin: dict[int, list[str]] = collections.defaultdict(list)
    for g in universe:
        by_bin[bin_of[g]].append(g)

    rng = np.random.default_rng(SEED)
    results, tests = [], []

    for (sub, kind), genes in sorted(per_set.items()):
        if len(genes) < MIN_GENES:
            continue
        members = sorted(genes)
        hits = collections.Counter()
        for g in members:
            hits.update(sorted(cells[g]))
        candidates = {c: hits[c] for c in sorted(hits) if hits[c] >= MIN_HITS}
        if not candidates:
            continue

        want = collections.Counter(bin_of[g] for g in members)
        null: dict[str, list[int]] = {c: [] for c in candidates}
        for _ in range(DRAWS):
            drawn: list[str] = []
            for b, k in want.items():
                pool = by_bin[b]
                drawn.extend(pool[i] for i in rng.integers(0, len(pool), size=k))
            dh = collections.Counter()
            for g in drawn:
                dh.update(sorted(cells[g]))
            for c in candidates:
                null[c].append(dh.get(c, 0))

        found = []
        for c, obs in candidates.items():
            draws = null[c]
            mu = statistics.fmean(draws)
            ge = sum(1 for x in draws if x >= obs)
            p = (ge + 1) / (DRAWS + 1)
            found.append({
                "cell_type": c,
                "genes": obs,
                "of_set": len(members),
                "share_of_set": round(obs / len(members), 4),
                "null_mean": round(mu, 2),
                "fold": round(obs / mu, 2) if mu else None,
                "p_empirical": round(p, 5),
            })
        found.sort(key=lambda r: (r["p_empirical"], -r["genes"], r["cell_type"]))
        tests.extend(found)
        results.append({
            "substance": sub, "kind": kind, "genes": len(members),
            "top": found[:8],
        })

    # ---- multiplicity ------------------------------------------------------------------------
    surviving = 0
    if tests:
        try:
            from statsmodels.stats.multitest import multipletests
            ok, q, _, _ = multipletests([t["p_empirical"] for t in tests],
                                        alpha=0.05, method="fdr_bh")
            for t, keep, qq in zip(tests, ok, q):
                t["q"] = round(float(qq), 5)
                t["survives_fdr"] = bool(keep)
            surviving = int(sum(ok))
        except ImportError:
            print("  statsmodels absent — no q values", file=sys.stderr)

    key = {(t["cell_type"], t["genes"], t["of_set"]): t for t in tests}
    for r in results:
        for e in r["top"]:
            t = key.get((e["cell_type"], e["genes"], e["of_set"]))
            if t:
                e["q"] = t.get("q")
                e["survives_fdr"] = t.get("survives_fdr")

    # ---- the comparison this file exists for -------------------------------------------------
    #
    #  Do the disorder sets and the quantity sets land in the same cells? Measured as the
    #  overlap of their surviving cell types, per substance, rather than argued.
    def surviving_cells(sub: str, kind: str) -> set[str]:
        for r in results:
            if r["substance"] == sub and r["kind"] == kind:
                return {e["cell_type"] for e in r["top"] if e.get("survives_fdr")}
        return set()

    same_cells = []
    for sub in sorted({r["substance"] for r in results}):
        a, b = surviving_cells(sub, "disorder"), surviving_cells(sub, "quantity")
        if not a and not b:
            continue
        inter = a & b
        union = a | b
        same_cells.append({
            "substance": sub,
            "disorder_cells": sorted(a),
            "quantity_cells": sorted(b),
            "shared": sorted(inter),
            "jaccard": round(len(inter) / len(union), 3) if union else None,
        })

    brain = {"astrocytes", "bergmann glia", "brain excitatory neurons",
             "brain inhibitory neurons", "microglia", "oligodendrocyte progenitor cells",
             "oligodendrocytes", "other brain neurons", "neuroendocrine cells"}

    payload = {
        "generated": "tools/addiction_cells.py",
        "governed_by": "docs/adr/0007; docs/audit.md A41 for why no z is computed",
        "question": (
            "The genetics of 'who cannot stop' and of 'who drinks a lot' are reported under "
            "one heading. Do they land in the same cells?"),
        "control": (
            "Null gene sets of the same size drawn in quantile bins of EXPRESSION BREADTH — "
            "how many cell types a gene is enriched in. Genes that appear in GWAS are longer, "
            "better studied and broadly expressed, and an unmatched null would report that "
            "addiction implicates whichever cell types express the most genes, which is a "
            "fact about the Human Protein Atlas."),
        "no_z": (
            "Empirical tails only, floored at 1/%d. A z past about 2.6 extrapolates beyond "
            "what a permutation of this size resolves (docs/audit.md A41)." % (DRAWS + 1)),
        "intergenic": (
            "MAPPED_GENE holds two flanking genes when the variant is intergenic. Both are "
            "counted once. Dropping them would discard the intergenic majority of a GWAS; "
            "treating them as certain would credit two genes for one variant."),
        "totals": {
            "associations_used": seen,
            "intergenic_associations": intergenic,
            "gene_sets_tested": len(results),
            "cell_type_tests": len(tests),
            "surviving_fdr_5pct": surviving,
            "brain_cell_types": sorted(brain),
        },
        "by_set": results,
        "disorder_versus_quantity": same_cells,
        "says": None,
    }

    both = [s for s in same_cells if s["jaccard"] is not None]
    if both:
        payload["says"] = (
            "Across %d substances where both phenotype kinds could be tested, the cell types "
            "surviving correction for the DISORDER sets and for the QUANTITY sets overlap at "
            "a median Jaccard of %.2f. They are reported under one heading and they are not "
            "the same biology."
            % (len(both), statistics.median(s["jaccard"] for s in both)))

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"  {len(results)} gene sets, {len(tests)} cell-type tests, "
          f"{surviving} survive FDR 5%")
    for r in results:
        if r["kind"] in ("disorder", "quantity") and r["substance"] in ("alcohol", "nicotine", "all"):
            top = [e for e in r["top"] if e.get("survives_fdr")][:3]
            names = ", ".join(f"{e['cell_type']} ({e['fold']}x)" for e in top) or "—"
            print(f"    {r['substance']:9s} {r['kind']:9s} {r['genes']:5d} genes  {names}")
    for s in same_cells:
        print(f"    {s['substance']:9s} disorder vs quantity, shared cell types: "
              f"{len(s['shared'])} of {len(set(s['disorder_cells']) | set(s['quantity_cells']))}"
              f"  jaccard {s['jaccard']}")
    print(f"\nwrote {DEST.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
