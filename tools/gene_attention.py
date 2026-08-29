"""How much anyone has looked at each gene — the number this site has been asserting.

WHY THIS IS THE MOST IMPORTANT FILE HERE. Every panel on this site invokes attention bias.
The ClinVar VUS share "is a measurement of attention, not of the gene". Constraint "is
measured where people sequenced". A protein with no annotated domain "is usually one nobody
has characterised". The gap patterns are "a statement about curation effort".

All of that was asserted and none of it was measured. `gene2pubmed` is the measurement: one
row per gene per paper, published by the NCBI, going back to the beginning of the indexed
literature.

## What it makes possible that was impossible before

**A residual.** Once papers-per-gene is known, the VUS share can be asked a sharper question
than "is it high": *is it high FOR A GENE THIS STUDIED?* A gene with 3,000 papers and 80 %
uncertain variants is a different scandal from one with 4 papers and the same share — the
first is a field that looked hard and still cannot read the gene; the second is a field that
has not looked. Both are 80 % on the current site, and the site cannot tell them apart.

The residual here is deliberately the simplest thing that works: bin genes by decile of
papers, take the median VUS share within the decile, and report the difference. No regression,
no smoothing, no model. A decile median is something a reader can recompute by hand from the
shipped numbers, and every fancier estimator would have to justify itself against a baseline
this cheap — which is Stage 4 of the method this repository is built on.

## The two cautions, both load-bearing

**Papers are not attention, they are INDEXED attention.** A gene studied intensely in one
country's literature, or in an era before indexing, or under an older symbol, counts low.
The measure inherits every bias of PubMed itself.

**It is cumulative and unnormalised by time.** A gene discovered in 1985 has had forty years
to accumulate; one named in 2015 has not. The count is not a rate.

Run: `python tools/gene_attention.py`
"""

from __future__ import annotations

import csv
import gzip
import json
import pathlib
import re
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "out"
DEST = OUT / "gene_attention.json"

SRC = DATA / "ontology" / "gene2pubmed.gz"
MATRIX = DATA / "depmap" / "CRISPRGeneEffect.csv"
HUMAN = "9606"

# The DepMap header is "SYMBOL (entrez)", which is a 17,916-row symbol-to-GeneID map already
# on disk — no extra download, and it covers exactly the genes this site can show.
HEADER_GENE = re.compile(r"^(.+?)\s+\((\d+)\)$")

DECILES = 10


def load_symbol_map() -> dict[str, str]:
    """GeneID -> symbol, from the matrix header and the HPO gene table."""
    out: dict[str, str] = {}
    if MATRIX.exists():
        with MATRIX.open(encoding="utf-8") as fh:
            header = next(csv.reader(fh))
        for h in header[1:]:
            m = HEADER_GENE.match(h.strip())
            if m:
                out[m.group(2)] = m.group(1)

    # The HPO table carries "NCBIGene:1234" for genes outside the screen, so a disease gene
    # never screened in a dish still gets its literature count.
    hpo = DATA / "ontology" / "genes_to_disease.txt"
    if hpo.exists():
        with hpo.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                gid = (row.get("ncbi_gene_id") or "").replace("NCBIGene:", "").strip()
                sym = (row.get("gene_symbol") or "").strip()
                if gid and sym:
                    out.setdefault(gid, sym)
    return out


def main() -> int:
    if not SRC.exists():
        print(f"{SRC.relative_to(ROOT)} absent. Fetch it with:\n"
              "  curl -L -o data/ontology/gene2pubmed.gz \\\n"
              "    https://ftp.ncbi.nlm.nih.gov/gene/DATA/gene2pubmed.gz")
        return 1

    symbols = load_symbol_map()
    print(f"{len(symbols):,} GeneID to symbol pairs on disk", flush=True)

    print("counting papers per gene…", flush=True)
    papers: Counter = Counter()
    rows = 0
    try:
        with gzip.open(SRC, "rt", encoding="utf-8", errors="replace") as fh:
            fh.readline()
            for line in fh:
                p = line.rstrip("\n").split("\t")
                if len(p) < 3 or p[0] != HUMAN:
                    continue
                sym = symbols.get(p[1])
                if sym:
                    papers[sym] += 1
                rows += 1
    except EOFError as exc:
        # A truncated download would silently under-count every gene, which is worse than
        # failing: the whole point of this file is a denominator.
        print(f"  the archive is incomplete ({exc}). Re-download before trusting this.")
        return 1

    if not papers:
        print("no human rows matched a known symbol — check the symbol map")
        return 1

    # ------------------------------------------------------------------ residual
    world_path = OUT / "gene_world.json"
    world = json.loads(world_path.read_text(encoding="utf-8")) if world_path.exists() \
        else {"genes": {}}

    # Genes with enough variants for a share to mean anything, and a paper count.
    pairs = []
    for sym, rec in world["genes"].items():
        clin = rec.get("clin") or {}
        if clin.get("total", 0) >= 20 and sym in papers:
            pairs.append((papers[sym], clin["vusShare"], sym))
    pairs.sort()

    # Deciles by paper count. A reader can recompute this from the shipped numbers, which no
    # regression would allow — and Stage 4 of this method says the baseline comes first.
    bands: list[dict] = []
    residual: dict[str, float] = {}
    if pairs:
        size = max(1, len(pairs) // DECILES)
        for d in range(DECILES):
            lo = d * size
            hi = len(pairs) if d == DECILES - 1 else min(len(pairs), (d + 1) * size)
            chunk = pairs[lo:hi]
            if not chunk:
                continue
            shares = sorted(c[1] for c in chunk)
            med = shares[len(shares) // 2]
            bands.append({
                "decile": d + 1,
                "papersFrom": chunk[0][0],
                "papersTo": chunk[-1][0],
                "genes": len(chunk),
                "medianVus": round(med, 4),
            })
            for _, share, sym in chunk:
                residual[sym] = round(share - med, 4)

    genes = {
        sym: {"papers": n, **({"vusResidual": residual[sym]} if sym in residual else {})}
        for sym, n in papers.items()
    }

    counts = sorted(papers.values())
    top = papers.most_common(15)
    payload = {
        "generated": "tools/gene_attention.py",
        "premise": (
            "Every panel on this site invokes attention bias and none of them measured it. "
            "gene2pubmed is the measurement: one row per gene per indexed paper. It turns "
            "'the VUS share is a measurement of attention' from an assertion into a residual "
            "— is the share high FOR A GENE THIS STUDIED?"
        ),
        "caution": (
            "Papers are INDEXED attention, not attention: a gene studied intensely in one "
            "country's literature, before indexing, or under an older symbol counts low. And "
            "the count is cumulative and not a rate — a gene named in 1985 has had forty "
            "years to accumulate one named in 2015 has not."
        ),
        "baseline": (
            "The residual is the gene's VUS share minus the median share of its paper decile. "
            "No regression and no smoothing: a decile median is something a reader can "
            "recompute by hand from the numbers below, and any fancier estimator has to "
            "justify itself against a baseline this cheap."
        ),
        "scope": {
            "genes": len(papers),
            "rowsRead": rows,
            "median": counts[len(counts) // 2],
            "p90": counts[int(len(counts) * 0.9)],
            "max": counts[-1],
            "withResidual": len(residual),
            "source": "NCBI gene2pubmed, taxon 9606",
        },
        "deciles": bands,
        "mostStudied": [{"gene": g, "papers": n} for g, n in top],
        "genes": genes,
    }

    DEST.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    print(f"\n{len(papers):,} genes with at least one paper "
          f"({DEST.stat().st_size / 1024:,.0f} kB)")
    print(f"  median {counts[len(counts) // 2]:,} papers · "
          f"90th pct {counts[int(len(counts) * 0.9)]:,} · max {counts[-1]:,}")
    print("\n  most studied: " + ", ".join(f"{g} ({n:,})" for g, n in top[:6]))
    if bands:
        print("\n  VUS share by decile of papers studied:")
        for b in bands:
            print(f"    {b['decile']:>2}  {b['papersFrom']:>5}–{b['papersTo']:<6} papers   "
                  f"{b['genes']:>5} genes   median VUS {b['medianVus']:.1%}")
    print(f"\nwrote {DEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
