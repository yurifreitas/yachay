# paper/ — the manuscript standard

> **Role:** how an article is written and built in this repository. The rules, the
> toolchain, and the one thing that makes it different from a normal LaTeX project.
> **Last revised:** 2026-08-26 · **State:** scaffold complete and number generation
> verified; ⚠️ **the LaTeX build has never been run** — no TeX toolchain is installed on
> this machine (checked 2026-08-26: no `latexmk`, `lualatex`, `tectonic`, or `biber`).
> Expect first-build fixes.

## The one rule that matters

**No number is ever typed into a `.tex` file.**

Every reported value is a macro in `generated/numbers.tex`, written by
`tools/paper_numbers.py` from `out/*.manifest.json`. A number therefore cannot drift
between the code that measured it and the paper that reports it — and if a macro is
missing, LaTeX fails with an undefined control sequence rather than printing something
plausible. That is Stage 8 ("no claim without an executable assertion behind it") and
*jidoka* ("stop the line, do not pass the defect downstream") in the same mechanism.

```
python tasks.py depmap            # measure       -> out/depmap.manifest.json
python tools/paper_numbers.py     # generate      -> paper/generated/numbers.tex
make -C paper                     # typeset
make -C paper check               # fail if stale, or if refs are unverified
```

If you are about to type a digit into `sections/*.tex`: stop, add it to the analysis
manifest, regenerate.

## Layout

| path | what |
|---|---|
| `main.tex` | the document: title, authors, section order. Nothing else. |
| `sieve.sty` | **the whole preamble**, once. Typography, siunitx, biblatex, semantic macros. A manuscript that redefines this is a fork, not a paper. |
| `sections/*.tex` | one file per section, numbered so the order is visible in the directory |
| `refs.bib` | the canonical bibliography — see conventions at the top of the file |
| `generated/numbers.tex` | **generated, never edited** |
| `figures/` | figures that are not drawn from data by pgfplots |
| `Makefile` | `all` · `final` · `check` · `watch` · `clean` |

## Conventions the preamble enforces

- **Units and numbers through `siunitx` only.** `\num{}`, `\qty{}`, `S` table columns.
- **Uncertainty is not optional** (GUM). `\val{0.845}{0.045}` renders value ± half-width.
  A value that still has no interval uses `\nointerval{}`, which renders **visibly
  flagged in draft mode** so it cannot quietly reach a submission.
- **`\Measured` / `\Pending`** on every claim, the `knee` convention. `[P]` is red in
  draft.
- **`booktabs` only** — no vertical rules, no `\hline`.
- **`cleveref`** for every cross-reference: `\cref{tab:classes}`, never "Table 2".
- **Semantic macros** for the method's notation (`\entity`, `\nobs`, `\stat`,
  `\nullmean{}`, `\zof{}`, `\neff`) so notation cannot drift between papers. The
  calibration itself is one macro, `\calibration`, defined once.
- **`sorting=none`** in biblatex: citations appear in the order the argument needs them,
  because a reader follows the argument and not the alphabet.

## Bibliography rules

Two fields are mandatory on every entry, and `make check` enforces the second:

- `annotation` — **the claim in this repository that the reference supports**. An entry
  with no stated purpose is decoration and gets deleted. Mirrors the `notes:` convention
  in `CITATION.cff`.
- `verified` — `{yes, <date>}` once year, venue, authors and DOI have been checked
  against the source; `{no}` otherwise. **Every entry is currently `{no}`**: they were
  written from working knowledge, and `make check` will refuse to build a submission
  until they are checked.

`refs.bib` is the single source of truth for citations. `CITATION.cff` describes how to
cite *the software* and mirrors the annotations; it does not compete.

## Toolchain

LuaLaTeX + biber, driven by `latexmk`. LuaLaTeX because `unicode-math` and `fontspec` give
one consistent font stack; `-shell-escape` because `minted` and TikZ externalisation need
it.

**None of it is installed here.** Options, cheapest first:

```bash
# 1. TeX Live via a container (no local install)
docker run --rm -v "$PWD":/work -w /work/paper texlive/texlive make

# 2. Tectonic — single binary, downloads what it needs
tectonic -X compile main.tex        # note: minted/shell-escape needs extra setup

# 3. Full TeX Live locally
```

Fonts: Libertinus if present, otherwise the preamble falls back silently. Typography is a
decision, not a build dependency.

## Writing standard

Beyond the mechanics — the parts a reviewer notices:

1. **Every claim about prior work says what our measurement does to it** — confirms,
   extends, quantifies, or contradicts. The long form is `docs/lineage.md`; the paper
   cites it rather than restating it.
2. **Anomalies go in Results, not in a footnote.** `sections/03-results.tex` §2 exists
   because two measured numbers are unexplained. A paper that reports only confirmations
   is advertising.
3. **Limitations are constraints on use, not hedges.** "Requires a control pool" tells a
   reader whether they can use this. "Results may vary" tells them nothing.
4. **Every `\Pending` is a promise.** It marks a number not yet measured — not a number
   we hope holds.
