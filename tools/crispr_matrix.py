#!/usr/bin/env python
"""Twenty-one million CRISPR measurements, ordered so the structure is visible.

WHAT HAS NEVER BEEN DRAWN HERE. `CRISPRGeneEffect.csv` is 1,178 cell lines by 17,916 genes —
**21.1 million gene-effect values**, the largest object this repository holds. Every screen
built on it so far shows a ranked table, a scatter of a few thousand sampled points, or a
single gene's profile. The matrix itself has never appeared, so nothing on this site has ever
shown what a genome-wide dependency screen actually looks like.

A heatmap of it is not a decoration. The three things a reader wants from DepMap are all
structural and all invisible in a ranked list:

  * the **common-essential band** — genes every line needs, which is the confound Stage 3
    removes and which should appear as a solid stripe running the full width;
  * **lineage blocks** — dependencies a group of related cell lines share and others do not,
    which is the entire promise of selective targeting;
  * **how little of the matrix is either** — the vast flat majority, which a ranked table
    hides by construction because it only ever shows the top.

## The ordering is the argument (ADR 0008)

A matrix says nothing until its rows and columns are ordered, and 21 million cells cannot be
ordered by eye. Both axes are seriated here, in Python, and shipped:

    genes        by angle in the plane of the first two singular vectors of the centred
                 matrix. A "wheel" seriation: genes with similar dependency profiles across
                 all 1,178 lines land near each other, and the ordering is a deterministic
                 function of the data with no seed and no parameter.
    cell lines   the same construction on the transpose, so lines that need the same genes
                 sit together — which is what makes a lineage block a block rather than a
                 scatter of rows.

Both are compared against the file's own alphabetical order, which is the control: alphabetical
is structure-free by construction, so any block visible under it is an artefact of the eye.

## What is shipped, and what is lost

The browser gets a **byte per cell**, quantised from the gene effect, at one row per cell line
and one column per bin of genes. A bin holds the MEDIAN of its genes — not the most extreme,
which was the first version and was wrong: the most extreme of fifteen is a max over fifteen
draws, a selection operator whose distribution depends on the bin size. That is this library's
own subject, and it saturated the figure into a map of bin size.

    python tools/crispr_matrix.py
    python tools/crispr_matrix.py --bins 1400

Requires numpy, pandas and scikit-learn.
"""

from __future__ import annotations

import argparse
import base64
import json
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline import paths  # noqa: E402

DEST = ROOT / "web" / "public" / "data" / "crispr_matrix.json"

#: Gene columns in the shipped image. 17,916 genes at one pixel each is 21 MB of payload for a
#: figure nobody can see 17,916 columns of; 1,200 bins is about 15 genes per column, which is
#: finer than a screen pixel on any display this will be read on.
BINS = 1200

#: Gene effect is a CERES/Chronos score: 0 is no effect, -1 is the median of known essentials.
#: The scale is clipped here for display only, and the clip is stated in the payload.
LO, HI = -2.0, 1.0


def load() -> tuple[np.ndarray, list[str], list[str]]:
    import pandas as pd

    t0 = time.time()
    # dtype cannot be given globally: it is applied before `index_col` takes the first column
    # out, so pandas tries to read the cell-line identifiers as float32 and fails on ACH-000001.
    # Reading then casting costs one pass over 21 million values and is the version that works.
    df = pd.read_csv(paths.CRISPR_GENE_EFFECT, index_col=0, engine="c", low_memory=False)
    df = df.astype(np.float32)
    print(f"  loaded {df.shape[0]} lines x {df.shape[1]} genes "
          f"({time.time() - t0:.0f}s)")
    genes = [c.split(" (")[0] for c in df.columns]
    return df.to_numpy(dtype=np.float32), list(df.index), genes


def wheel_order(x: np.ndarray) -> np.ndarray:
    """Seriate the rows of `x` by angle in the plane of its first two singular vectors.

    WHY THIS AND NOT HIERARCHICAL CLUSTERING. A dendrogram over 17,916 genes is an O(n²)
    distance matrix — 1.3 billion pairs — and its leaf order still depends on a linkage choice
    and a tie-breaking rule. The angle in the top-2 SVD plane is a deterministic function of
    the data alone: no seed, no linkage, no cut. It is the standard "wheel" seriation, and it
    is exactly right for this matrix because the dominant structure IS low-rank — a common-
    essential axis and a lineage axis.

    WHAT IT CANNOT DO, stated because a seriation that oversells itself is a figure that lies:
    it orders by position on a circle, so it recovers gradients and large blocks and will not
    resolve two small clusters that happen to sit at the same angle.
    """
    from sklearn.decomposition import TruncatedSVD

    centred = np.nan_to_num(x - np.nanmean(x, axis=0, keepdims=True), nan=0.0)
    svd = TruncatedSVD(n_components=2, random_state=0)
    emb = svd.fit_transform(centred)
    ang = np.arctan2(emb[:, 1], emb[:, 0])
    return np.argsort(ang, kind="stable")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bins", type=int, default=BINS)
    args = ap.parse_args()

    if not paths.CRISPR_GENE_EFFECT.exists():
        print(f"missing {paths.CRISPR_GENE_EFFECT}", file=sys.stderr)
        return 1

    t0 = time.time()
    mat, lines, genes = load()          # lines x genes
    n_lines, n_genes = mat.shape

    # ---- the two orderings ---------------------------------------------------------------
    gene_order = wheel_order(mat.T)     # genes by their profile across lines
    line_order = wheel_order(mat)       # lines by which genes they need

    # ---- rotate the seam out of the band --------------------------------------------------
    #
    #  A wheel seriation orders by ANGLE, and an angle is circular: cutting it at -pi is
    #  arbitrary, and the first render cut straight through the common-essential band, which
    #  then appeared as two bright stripes at opposite edges of the figure with the flat
    #  majority between them. That is one band drawn as two, which is the most misleading
    #  thing a heatmap can do to a block.
    #
    #  The cut is moved to the FLATTEST place on the circle: the window of columns whose
    #  median absolute effect is smallest. Nothing is reordered — the sequence is rolled — so
    #  the seriation is untouched and only the arbitrary starting point changes.
    def rotate_to_flattest(order: np.ndarray, m: np.ndarray, window: int = 200) -> np.ndarray:
        strength = np.abs(np.nan_to_num(np.nanmedian(m, axis=0), nan=0.0))[order]
        kernel = np.ones(window) / window
        smooth = np.convolve(np.concatenate([strength, strength[:window]]), kernel, "valid")
        return np.roll(order, -int(np.argmin(smooth)))

    gene_order = rotate_to_flattest(gene_order, mat)
    print(f"  seriated both axes ({time.time() - t0:.0f}s)")

    # ---- the controls that make the seriation checkable -----------------------------------
    #
    #  Alphabetical is structure-free by construction. If a block is visible under it, the
    #  block is in the reader's eye rather than in the matrix — the same argument the gene
    #  graph's `degree` ordering makes, and the reason both are shipped.
    alpha_gene = np.argsort(np.array(genes), kind="stable")
    alpha_line = np.arange(n_lines)

    # ---- how much structure each ordering actually shows ----------------------------------
    #
    #  Measured, not asserted: the mean absolute difference between neighbouring columns. A
    #  good seriation puts similar profiles side by side, so that number falls.
    def roughness(order: np.ndarray, axis_matrix: np.ndarray) -> float:
        m = np.nan_to_num(axis_matrix[:, order], nan=0.0)
        return float(np.abs(np.diff(m, axis=1)).mean())

    rough = {
        "seriated": round(roughness(gene_order, mat), 5),
        "alphabetical": round(roughness(alpha_gene, mat), 5),
    }
    rng = np.random.default_rng(20260831)
    rough["shuffled"] = round(
        float(np.mean([roughness(rng.permutation(n_genes), mat) for _ in range(3)])), 5)
    print(f"  column roughness: seriated {rough['seriated']}, "
          f"alphabetical {rough['alphabetical']}, shuffled {rough['shuffled']}")

    # ---- the image ------------------------------------------------------------------------
    #
    #  One row per cell line, one column per bin of genes, one byte per cell.
    #
    #  ⚠️ THE FIRST VERSION TOOK THE MOST EXTREME VALUE IN EACH BIN, and that is this
    #  repository's own subject committed in its own figure. The most extreme of fifteen genes
    #  is a MAX OF FIFTEEN DRAWS — a selection operator whose distribution depends on how many
    #  genes are in the bin, which is exactly the winner's curse every stage of this library
    #  exists to calibrate. Almost every bin of fifteen contains one gene with a real
    #  dependency, so almost every column came out saturated: the picture became a map of bin
    #  size, and the flat majority the caption promised to show simply vanished.
    #
    #  The median has no such dependence. It shows the typical dependency of the genes in a
    #  column, the flat majority stays flat, and a lethal gene sitting alone in a bin of
    #  fifteen is correctly NOT drawn as if the whole column were lethal.
    def image_for(g_order: np.ndarray, l_order: np.ndarray) -> np.ndarray:
        m = mat[np.ix_(l_order, g_order)]
        edges = np.linspace(0, n_genes, args.bins + 1).astype(int)
        out = np.zeros((n_lines, args.bins), dtype=np.uint8)
        for b in range(args.bins):
            chunk = m[:, edges[b]:edges[b + 1]]
            if chunk.size == 0:
                continue
            filled = np.nan_to_num(chunk, nan=0.0)
            out[:, b] = ((np.clip(np.median(filled, axis=1), LO, HI) - LO)
                         / (HI - LO) * 255).astype(np.uint8)
        return out

    img = image_for(gene_order, line_order)
    img_alpha = image_for(alpha_gene, alpha_line)
    print(f"  images built ({time.time() - t0:.0f}s)")

    # ---- annotation ------------------------------------------------------------------------
    lineage = {}
    if paths.MODEL.exists():
        import pandas as pd
        mod = pd.read_csv(paths.MODEL, index_col=0, low_memory=False)
        col = next((c for c in ("OncotreeLineage", "lineage", "Lineage")
                    if c in mod.columns), None)
        if col:
            lineage = {str(k): (str(v) if isinstance(v, str) else "unknown")
                       for k, v in mod[col].items()}

    def essentials() -> set[str]:
        if not paths.COMMON_ESSENTIAL.exists():
            return set()
        import pandas as pd
        ce = pd.read_csv(paths.COMMON_ESSENTIAL)
        col = ce.columns[0]
        return {str(v).split(" (")[0] for v in ce[col]}

    common = essentials()
    # Per bin, under the seriated ordering: what share of it is common-essential. This is the
    # margin that lets a reader tell the essential band from a lineage block without guessing.
    edges = np.linspace(0, n_genes, args.bins + 1).astype(int)
    ordered_genes = [genes[i] for i in gene_order]
    ess_share = [
        round(float(np.mean([g in common for g in ordered_genes[edges[b]:edges[b + 1]]])), 3)
        if edges[b + 1] > edges[b] else 0.0
        for b in range(args.bins)
    ]
    # A name per bin: the gene with the most extreme median effect in it, which is the one a
    # reader pointing at that column is most likely to be asking about.
    med = np.nan_to_num(np.nanmedian(mat, axis=0), nan=0.0)[gene_order]
    bin_names = []
    for b in range(args.bins):
        seg = med[edges[b]:edges[b + 1]]
        if seg.size == 0:
            bin_names.append("")
            continue
        bin_names.append(ordered_genes[edges[b] + int(np.argmin(seg))])

    payload = {
        "generated": "tools/crispr_matrix.py",
        "governed_by": "docs/adr/0008 — the ordering is solved in Python, and it is an argument",
        "says": (
            "1,178 cell lines by 17,916 genes — 21.1 million gene-effect values, the whole "
            "screen. Every previous view of this data on this site was a ranked table or a "
            "sample; a ranked table cannot show the common-essential band, the lineage blocks, "
            "or how little of the matrix is either."),
        "shape": {"lines": n_lines, "genes": n_genes, "values": n_lines * n_genes,
                  "bins": args.bins, "genes_per_bin": round(n_genes / args.bins, 1)},
        "scale": {"low": LO, "high": HI,
                  "says": ("Chronos gene effect: 0 is no effect and -1 is the median of known "
                           "essential genes. Clipped to [%g, %g] for display only." % (LO, HI))},
        "binning": (
            "A bin holds the MEDIAN of its genes. The first version took the most extreme "
            "value, which is a max over fifteen draws — a selection operator whose "
            "distribution depends on the bin size, and the exact bias this library exists to "
            "calibrate. It saturated almost every column and turned the figure into a map of "
            "how many genes each bin holds."),
        "orderings": {
            "seriated": {
                "says": ("Both axes by angle in the plane of the first two singular vectors — "
                         "a deterministic function of the data with no seed, no linkage and "
                         "no cut."),
                "cannot": ("It orders by position on a circle, so it recovers gradients and "
                           "large blocks and will not separate two small clusters that sit at "
                           "the same angle."),
            },
            "alphabetical": {
                "says": ("The control. Alphabetical is structure-free by construction, so a "
                         "block visible under it is in the reader's eye rather than in the "
                         "matrix."),
            },
        },
        "roughness": {
            **rough,
            "says": ("Mean absolute difference between neighbouring columns. A seriation that "
                     "puts similar profiles side by side lowers it; the shuffled figure is "
                     "what no ordering at all looks like."),
        },
        "lines": [{"id": l, "lineage": lineage.get(l, "unknown")} for l in
                  [lines[i] for i in line_order]],
        "bin_names": bin_names,
        "essential_share": ess_share,
        "image": base64.b64encode(img.tobytes()).decode("ascii"),
        "image_alphabetical": base64.b64encode(img_alpha.tobytes()).decode("ascii"),
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    mb = DEST.stat().st_size / 1e6
    print(f"\nwrote {DEST.relative_to(ROOT).as_posix()}  ({mb:.1f} MB, "
          f"{time.time() - t0:.0f}s total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
