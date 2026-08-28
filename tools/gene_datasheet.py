"""A gene, written the way a transistor is written.

THE FRAMING, AND WHY IT IS NOT A METAPHOR. A transistor datasheet does not print "gain: 100".
It prints a parameter, a symbol, a minimum, a typical and a maximum, the unit, and the TEST
CONDITIONS under which those three numbers were obtained — Vce = 5 V, Ic = 2 mA, Ta = 25 °C.
Every number carries the circumstances that produced it, and a number without them is not
publishable.

That discipline is exactly what this repository argues for and had not yet applied to itself.
Every other panel here reports a gene's dependency as one number. But a gene has 1,178
dependency measurements, one per cell line, and the spread between them is the whole question
a target programme is asking: a gene needed at −1.8 in forty lines and at 0.0 in the rest is a
selective target; a gene at −1.0 in every line is a poison. Both report a mean near −1.

So this builds the characteristics table. Every row is a parameter with min, typical and max
where a distribution exists, the unit, the condition it was measured under, and the file it
came from. Where only one number exists, the min and max columns are empty rather than filled
with the typical — a datasheet that repeats the typical in all three columns is lying about
what was measured.

## The blocks, and their electrical equivalents

    Physical            length, domains, membrane passes        package and pinout
    Absolute maximum    LoF tolerance, essentiality             absolute maximum ratings
    Dependency          gene effect across 1,178 lines          DC characteristics
    Expression          nCPM across 154 cell types              operating conditions
    Variants            ClinVar classifications                 quality and reliability

## What the dependency block costs

`CRISPRGeneEffect.csv` is 409 MB and 1,178 rows of 17,916 columns. It is read once, in
chunks, accumulating per-column order statistics — a few minutes, and the only step here that
touches the raw matrix. Everything else is already summarised on disk.

Run: `python tools/gene_datasheet.py`
"""

from __future__ import annotations

import csv
import json
import pathlib
import re
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "out"
DEST = OUT / "gene_datasheet.json"

MATRIX = DATA / "depmap" / "CRISPRGeneEffect.csv"

# DepMap's own conventions, and they are thresholds rather than truths — printed with the
# number so a reader can move them.
DEPENDENT = -0.5      # the cut DepMap uses for "this line depends on this gene"
STRONG = -1.0         # around the median of the common-essential distribution

HEADER_GENE = re.compile(r"^(.+?)\s+\(\d+\)$")


def load_matrix_stats() -> tuple[dict[str, dict], dict]:
    """Per-gene order statistics over every cell line, in one pass.

    Columns are genes and rows are cell lines, so a per-gene statistic needs the whole file
    in memory or a transpose. 1,178 x 17,916 float32 is 84 MB — small enough to hold, and
    holding it is what makes the quantiles exact rather than approximated from a sample.
    """
    if not MATRIX.exists():
        return {}, {"lines": 0, "note": "CRISPRGeneEffect.csv absent"}

    print("reading the CRISPR matrix (409 MB, one pass)…", flush=True)
    with MATRIX.open(encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    genes = []
    for h in header[1:]:
        m = HEADER_GENE.match(h.strip())
        genes.append(m.group(1) if m else h.strip())

    # PANDAS, NOT loadtxt. The matrix writes a missing measurement as an EMPTY CELL, not as
    # NaN, and loadtxt refuses it — "could not convert string '' to float32 at row 0, column
    # 193". A gene not screened in a line is exactly the case this file has to handle
    # correctly, so the reader has to be one that understands absence.
    import pandas as pd

    # No global dtype: the low-memory parser applies it before the index column is set
    # aside, so float32 tries to parse the cell-line identifier "ACH-000001" as a number.
    # Inferred on read, narrowed on conversion.
    frame = pd.read_csv(MATRIX, index_col=0)
    values = frame.to_numpy(dtype=np.float32)
    genes = [HEADER_GENE.match(c.strip()).group(1) if HEADER_GENE.match(c.strip())
             else c.strip() for c in frame.columns]
    lines = values.shape[0]
    print(f"  {lines:,} cell lines x {values.shape[1]:,} genes", flush=True)

    out: dict[str, dict] = {}
    # NaN is a gene not screened in that line. Order statistics must ignore them, and the
    # count of real measurements is itself a parameter — it is the `n` every other panel
    # calibrates against.
    for i, gene in enumerate(genes):
        col = values[:, i]
        good = col[~np.isnan(col)]
        if good.size == 0:
            continue
        q = np.quantile(good, [0.0, 0.25, 0.5, 0.75, 1.0])
        out[gene] = {
            "n": int(good.size),
            "min": round(float(q[0]), 3),
            "q1": round(float(q[1]), 3),
            "median": round(float(q[2]), 3),
            "q3": round(float(q[3]), 3),
            "max": round(float(q[4]), 3),
            "mean": round(float(good.mean()), 3),
            "sd": round(float(good.std(ddof=1)), 3) if good.size > 1 else None,
            "dependent": int((good < DEPENDENT).sum()),
            "strong": int((good < STRONG).sum()),
        }
    return out, {"lines": lines, "genes": len(out), "source": "DepMap CRISPRGeneEffect.csv",
                 "dependentCut": DEPENDENT, "strongCut": STRONG}


def load_expression_stats() -> tuple[dict[str, dict], dict]:
    """nCPM order statistics across every HPA cell type, not only the top eight.

    The existing world layer keeps the eight highest, which answers "where is it loudest".
    A datasheet needs the range: the minimum is what a therapy has to tolerate everywhere,
    and the maximum alone cannot say whether the gene is silent in the other 150 types.
    """
    import zipfile

    path = DATA / "ontology" / "rna_single_cell_type.tsv.zip"
    if not path.exists():
        return {}, {"cellTypes": 0}

    per: dict[str, list[float]] = {}
    types: set[str] = set()
    with zipfile.ZipFile(path) as z:
        name = z.namelist()[0]
        with z.open(name) as raw:
            head = raw.readline().decode("utf-8").rstrip("\r\n").split("\t")
            i_sym, i_cell, i_val = (head.index(c) for c in ("Gene name", "Cell type", "nCPM"))
            for line in raw:
                p = line.decode("utf-8", "replace").rstrip("\r\n").split("\t")
                if len(p) <= i_val:
                    continue
                try:
                    v = float(p[i_val])
                except ValueError:
                    continue
                types.add(p[i_cell])
                per.setdefault(p[i_sym], []).append(v)

    out: dict[str, dict] = {}
    for sym, vals in per.items():
        a = np.array(vals, dtype=np.float32)
        q = np.quantile(a, [0.0, 0.5, 1.0])
        out[sym] = {
            "types": int(a.size),
            "min": round(float(q[0]), 1),
            "median": round(float(q[1]), 1),
            "max": round(float(q[2]), 1),
            # Where the gene is loudest carries the units; the ratio says whether it is
            # focused or flat, which is the question a target programme asks first.
            "ratio": round(float(q[2] / q[1]), 1) if q[1] > 0 else None,
        }
    return out, {"cellTypes": len(types), "genes": len(out),
                 "source": "Human Protein Atlas single-cell RNA"}


def main() -> int:
    index_path = OUT / "gene_index.json"
    if not index_path.exists():
        print("out/gene_index.json absent — run tools/gene_index.py first")
        return 1
    reachable = set(json.loads(index_path.read_text(encoding="utf-8"))["genes"])

    dep, dep_scope = load_matrix_stats()
    print("reading expression…", flush=True)
    exp, exp_scope = load_expression_stats()

    genes: dict[str, dict] = {}
    for sym in sorted(reachable):
        rec: dict[str, object] = {}
        if sym in dep:
            rec["dep"] = dep[sym]
        if sym in exp:
            rec["exp"] = exp[sym]
        if rec:
            genes[sym] = rec

    payload = {
        "generated": "tools/gene_datasheet.py",
        "premise": (
            "A transistor datasheet does not print 'gain: 100'. It prints a minimum, a "
            "typical and a maximum, and the conditions under which those were obtained. "
            "Every other panel here reports a gene's dependency as one number, but a gene "
            "has 1,178 dependency measurements and the spread between them is the question a "
            "target programme is asking: needed at -1.8 in forty lines and at 0.0 in the "
            "rest is a selective target; -1.0 in every line is a poison. Both report a mean "
            "near -1."
        ),
        "convention": (
            "Where only one number was measured, min and max are empty rather than filled "
            "with the typical. A datasheet that repeats the typical in all three columns is "
            "lying about what was measured."
        ),
        "scope": {"dependency": dep_scope, "expression": exp_scope, "genes": len(genes)},
        "genes": genes,
    }

    DEST.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    size = DEST.stat().st_size / 1024
    print(f"\n{len(genes):,} genes  ({size:,.0f} kB)")
    print(f"  dependency  {len(dep):>6,} over {dep_scope.get('lines', 0):,} cell lines")
    print(f"  expression  {len(exp):>6,} over {exp_scope.get('cellTypes', 0)} cell types")

    # A worked example, because the whole point is that one number hides two genes.
    for probe in ("NF2", "SNRPD3", "KRAS"):
        d = dep.get(probe)
        if d:
            print(f"\n  {probe}: gene effect {d['min']} … {d['median']} … {d['max']}"
                  f"   dependent in {d['dependent']}/{d['n']} lines")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
