"""DepMap CRISPR adapter — the reference application, and the scale test.

## Why this dataset

It is the same problem class as the screen this library came from, roughly four orders
of magnitude larger, and it carries the *same two confounds* natively:

| the small screen                        | DepMap                                        |
|-----------------------------------------|-----------------------------------------------|
| 307 perturbations                        | ~18,000 genes x ~1,100 cell lines             |
| score = top-3 of 12 signature z-scores   | score = top-k of the gene's most dependent lines |
| control = NC (non-targeting) cells       | control = the Achilles NONESSENTIAL gene set  |
| KIF11 killed cells and topped the metric | pan-essential genes top the metric for the same reason |
| cells per perturbation varied 1 -> 4,494 | lines screened per gene varies                |

So every stage can be exercised with real statistical power, and the answers can be
checked against biology that is independently known.

## The question this adapter asks

**Selective dependency.** A useful drug target is a gene whose knockout kills *some*
cell lines and spares the rest. A gene that kills everything is a toxic liability, not a
target — the DepMap version of the KIF11 lesson. So the score is deliberately a top-k
statistic (how strong is this dependency in the contexts where it matters), which is
exactly the operator that needs Stage 1 before it can be ranked.

## Data

Public release files, from the DepMap figshare mirror (the portal itself sits behind a
bot check, so this adapter never scrapes it):

    CRISPRGeneEffect.csv                  ~429 MB   lines x genes, Chronos gene effect
    AchillesNonessentialControls.csv                the control pool for Stage 1
    AchillesCommonEssentialControls.csv             the known pan-essential confound

Gene effect is scaled so that 0 = no effect and -1 = the median common-essential gene.
Dependency is therefore NEGATIVE, which is why :func:`load_matrix` flips the sign: every
stage in this library assumes larger is better.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

__all__ = ["DepMap", "load_matrix", "load_gene_set", "score_genes"]

GENE_EFFECT = "CRISPRGeneEffect.csv"
NONESSENTIAL = "AchillesNonessentialControls.csv"
COMMON_ESSENTIAL = "AchillesCommonEssentialControls.csv"

_SYMBOL = re.compile(r"^([^\s(]+)")


def _symbol(col: str) -> str:
    """DepMap columns are 'SYMBOL (ENTREZID)'. Keep the symbol."""
    m = _SYMBOL.match(col.strip())
    return m.group(1) if m else col.strip()


@dataclass
class DepMap:
    """Gene-effect matrix with dependency oriented so that LARGER IS BETTER."""

    values: np.ndarray          # (n_lines, n_genes) float32, sign-flipped, NaN preserved
    lines: pd.Index
    genes: pd.Index
    flipped: bool = True

    @property
    def shape(self) -> tuple[int, int]:
        return self.values.shape

    def gene_block(self, genes: list[str]) -> np.ndarray:
        """Rows = observations for those genes, NaNs dropped. Used as the control pool."""
        idx = [self.genes.get_loc(g) for g in genes if g in self.genes]
        if not idx:
            raise KeyError("none of the requested genes are in the matrix")
        block = self.values[:, idx]
        return block[np.isfinite(block).all(axis=1)]


def load_matrix(
    data_dir: str,
    *,
    chunksize: int = 128,
    max_lines: int | None = None,
    flip_sign: bool = True,
) -> DepMap:
    """Read CRISPRGeneEffect.csv in row chunks and return a float32 matrix.

    The file is ~429 MB of text for ~20 million numbers. Read in chunks and stored as
    float32 it is ~80 MB in memory, which is the difference between this running on a
    laptop and not.
    """
    path = os.path.join(data_dir, GENE_EFFECT)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Fetch the DepMap release files first "
            f"(python tasks.py fetch)."
        )

    blocks: list[np.ndarray] = []
    line_ids: list[str] = []
    genes: pd.Index | None = None

    for chunk in pd.read_csv(path, chunksize=chunksize, index_col=0):
        if genes is None:
            genes = pd.Index([_symbol(c) for c in chunk.columns], name="gene")
        line_ids.extend(chunk.index.astype(str).tolist())
        blocks.append(chunk.to_numpy(dtype="float32"))
        if max_lines is not None and len(line_ids) >= max_lines:
            break

    values = np.vstack(blocks)
    if max_lines is not None:
        values = values[:max_lines]
        line_ids = line_ids[:max_lines]
    if flip_sign:
        values = -values          # dependency is negative in DepMap; sieve wants larger-is-better

    assert genes is not None
    return DepMap(values=values, lines=pd.Index(line_ids, name="cell_line"),
                  genes=genes, flipped=flip_sign)


def load_gene_set(data_dir: str, filename: str) -> list[str]:
    """Read one of the Achilles control gene lists into plain symbols."""
    path = os.path.join(data_dir, filename)
    df = pd.read_csv(path)
    col = df.columns[0]
    return sorted({_symbol(str(g)) for g in df[col].dropna()})


def score_genes(dm: DepMap, statistic, *, min_lines: int = 1) -> pd.DataFrame:
    """One row per gene: the screen's aggregate plus the observation count behind it.

    This is the frame every sieve stage consumes — it satisfies
    :func:`sieve.contracts.entity_scores`. `n` is the number of cell lines actually
    screened for that gene, and it varies, which is the entire reason Stage 1 exists.
    """
    vals = dm.values
    finite = np.isfinite(vals)
    counts = finite.sum(axis=0)

    scores = np.full(vals.shape[1], np.nan, dtype="float64")
    for j in range(vals.shape[1]):
        col = vals[finite[:, j], j]
        if col.size:
            scores[j] = statistic(col[None, :])[0]

    out = pd.DataFrame({
        "entity": dm.genes.astype(str),
        "score": scores,
        "n": counts.astype("int64"),
    })
    out = out[(out["n"] >= min_lines) & np.isfinite(out["score"])].reset_index(drop=True)
    return out
