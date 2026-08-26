"""Data contracts — declare the shape of every frame that crosses a stage boundary.

Adopted from day one because its absence was a named finding in the predecessor: a
15-column, order-sensitive output schema was defended by a single `assert` and by hope,
and a *silently* wrong column order would have passed.

Deliberately tiny. This is not pandera; it is the 5% of pandera that catches the bugs
that actually happen in a screening pipeline: a missing column, a column that became
object dtype, an all-NaN column, a count column with zeros in it, duplicate entity keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import pandas as pd

__all__ = ["Column", "Schema", "ContractError"]


class ContractError(AssertionError):
    """Raised when a frame violates its declared contract."""


@dataclass(frozen=True)
class Column:
    name: str
    kind: str = "float"                 # "float" | "int" | "str" | "any"
    required: bool = True
    unique: bool = False
    allow_nan: bool = True
    min: float | None = None
    max: float | None = None
    note: str = ""

    def check(self, s: pd.Series) -> list[str]:
        bad: list[str] = []
        if self.kind == "float" and not pd.api.types.is_numeric_dtype(s):
            bad.append(f"{self.name}: expected numeric, got {s.dtype}")
        elif self.kind == "int" and not pd.api.types.is_integer_dtype(s):
            bad.append(f"{self.name}: expected integer, got {s.dtype}")
        elif self.kind == "str" and not (
            pd.api.types.is_string_dtype(s) or pd.api.types.is_object_dtype(s)
        ):
            bad.append(f"{self.name}: expected string, got {s.dtype}")

        if self.unique and s.duplicated().any():
            dupes = s[s.duplicated()].unique()[:3]
            bad.append(f"{self.name}: must be unique, {s.duplicated().sum()} duplicates e.g. {list(dupes)}")

        if pd.api.types.is_numeric_dtype(s):
            n_nan = int(s.isna().sum())
            if n_nan == len(s) and len(s):
                bad.append(f"{self.name}: every value is NaN")
            elif not self.allow_nan and n_nan:
                bad.append(f"{self.name}: {n_nan} NaN not allowed")
            finite = s.to_numpy(dtype=float)
            finite = finite[np.isfinite(finite)]
            if finite.size:
                if self.min is not None and finite.min() < self.min:
                    bad.append(f"{self.name}: min {finite.min():.4g} below allowed {self.min}")
                if self.max is not None and finite.max() > self.max:
                    bad.append(f"{self.name}: max {finite.max():.4g} above allowed {self.max}")
        return bad


@dataclass(frozen=True)
class Schema:
    """A named set of columns, optionally order-sensitive."""

    name: str
    columns: tuple[Column, ...]
    ordered: bool = False               # True when downstream consumers index by position
    extra_ok: bool = True

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        problems: list[str] = []
        present = list(df.columns)

        for col in self.columns:
            if col.name not in present:
                if col.required:
                    problems.append(f"missing required column {col.name!r}"
                                    + (f" ({col.note})" if col.note else ""))
                continue
            problems.extend(col.check(df[col.name]))

        if self.ordered:
            expected = [c.name for c in self.columns if c.name in present]
            actual = [c for c in present if c in {x.name for x in self.columns}]
            if expected != actual:
                problems.append(
                    "column ORDER differs from the contract; downstream code indexes by "
                    f"position.\n  expected: {expected}\n  actual:   {actual}"
                )

        if not self.extra_ok:
            known = {c.name for c in self.columns}
            unexpected = [c for c in present if c not in known]
            if unexpected:
                problems.append(f"unexpected columns: {unexpected}")

        if problems:
            raise ContractError(
                f"frame does not satisfy contract {self.name!r}:\n  - "
                + "\n  - ".join(problems)
            )
        return df

    def describe(self) -> str:
        lines = [f"{self.name}" + (" (ordered)" if self.ordered else "")]
        for c in self.columns:
            flags = ", ".join(
                f for f in (
                    c.kind,
                    "required" if c.required else "optional",
                    "unique" if c.unique else "",
                    "no-nan" if not c.allow_nan else "",
                ) if f
            )
            lines.append(f"  {c.name:<20} {flags}" + (f"  # {c.note}" if c.note else ""))
        return "\n".join(lines)


def entity_scores(
    entity: str = "entity",
    score: str = "score",
    count: str = "n",
    extra: Iterable[Column] = (),
) -> Schema:
    """The frame every stage in this library consumes: one row per candidate entity.

    `count` is the number of observations the score was estimated from. It is required
    and must be >= 1 because the null-calibration stage cannot be honest without it —
    and a pipeline that does not know its own observation counts is precisely the one
    that ranks noise.
    """
    return Schema(
        name="entity_scores",
        columns=(
            Column(entity, kind="str", unique=True, allow_nan=False),
            Column(score, kind="float", note="the screen's aggregate, uncalibrated"),
            Column(count, kind="int", allow_nan=False, min=1,
                   note="observations behind the score; required by Stage 1"),
            *extra,
        ),
    )
