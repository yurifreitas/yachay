# The visualisation model

> **Role:** what this project plots, why each plot exists, and how the plotting layer is
> built so that a figure cannot disagree with the text.
> **Last revised:** 2026-08-27 · **State:** the five DepMap figures are implemented and
> rendered; the pgfplots renderer is specified but ⚠️ **not built** — no TeX toolchain on
> this machine.

> Provenance of every chart form used here — who invented it, for what, and with which
> caution attached — is in [`visualization-canon.md`](visualization-canon.md).

---

## 0. Why this is a stage, not a presentation layer

The −4.09 defect lived in this repository for weeks. It was in **every table the analysis
ever printed** — the number was right there, in `out/DEPMAP_FINDINGS.md`, in the manifest,
in the paper's macros. Nobody read it as a defect, because a table asks you to *notice* a
number and then *compare it to an expectation you are holding in your head*.

Figure 3 puts the expectation on the page as a dashed curve. The defect is then not
something you notice; it is something you cannot avoid.

That is the whole argument. A plot is not how the result is communicated at the end — it is
**an instrument for finding out whether the result is real**, and it belongs next to the
assertion, not after it.

The corollary, which is the uncomfortable half: a plot that is only made at the end can only
confirm. Every figure below is specified as a *question with a failing answer*.

---

## 1. The architecture — one contract, three renderers

```
analyses/*.py  ──▶  out/*.csv + out/*.manifest.json      the measurement
                          │
            ┌─────────────┴──────────────┐
            ▼                            ▼
  web/scripts/build-data.mjs    web/scripts/build-points.mjs
  rows, for tables              columns, for dense marks
            │                            │
            └─────────────┬──────────────┘
                          ▼
                  web/ (the explorer)              paper/ (pgfplots)
                  React + SVG + canvas             the manuscript
                                                   ⚠ not built
```

Three rules make this worth the indirection:

1. **No renderer computes anything.** `figure_data.py` is the only place a number is
   derived. A chart that computes its own mean is a second implementation of the analysis,
   and it will disagree eventually.
2. **The contract is small and tidy.** Binned densities, not 726 raw values; a stratified
   sample, not 17,916 dots. The whole five-figure payload is 197 KB, which inlines into a
   page.
3. **`--check` exists.** `python tools/figure_data.py --check` fails if the figures are
   stale with respect to the analysis, the same gate `tools/paper_numbers.py --check`
   applies to the manuscript's numbers.

**Two renderers, not three.** The explorer is for interrogating a run — filter, hover,
17,916 rows; pgfplots is for a figure that must sit in a PDF at the manuscript's own type
size. Nothing else is needed, and a third rendering of the same numbers is a third chance
for them to disagree.

---

## 2. The five figures, in dependency order

The order is the argument. Each figure decides whether the next is worth reading — which is
why they are numbered on the page, and why the count distribution was moved from last to
first once that dependency was noticed.

### Fig 1 — Does the observation count vary at all?
*Form: bar chart of genes per count.* **The gate.** The correction reorders a ranking only
when counts differ. If they do not, calibration is one common monotone transform, and a
monotone transform cannot reorder anything.

> **What it said:** 19 distinct counts across 17,916 genes; **95.4 % share one value**. The
> entire count correlation rests on 830 genes.

This should open the analysis of any screen. Drawn first here, it would have said
immediately that DepMap tests the *null* well and the *ranking claim* barely at all.

### Fig 2 — What does the score read when nothing is happening?
*Form: line + ±1 sd band against a log count axis.* The null's mean and spread as a function
of n. **The slope is the bias a raw ranking inherits.**

> **What it said:** the defective null climbs **1.93× too steeply** — over-correcting exactly
> the best-measured genes. An independent algebraic decomposition had predicted 1.95× before
> this curve was drawn.

### Fig 3 — Do the controls read zero?
*Form: **normal Q-Q plot**, with the density curves demoted to a footnote.* **The one that matters.**
Genes known to do nothing must calibrate to a standard normal; anything else means the null
is wrong, whatever the shortlist looks like.

> **What it said:** −4.09 (sd 3.28) pooled, **+0.04 (sd 1.01)** blocked — and then, once
> the form changed from density to Q-Q, something the density had hidden all along: the
> blocked null is right through the body (median −0.12) and has a **heavy right tail**,
> 8.9 at the 99.95th percentile against 3.3 expected. Some genes in the "known to do
> nothing" control set are not inert. That is a new open question, and it was produced by
> changing the chart, not the analysis.

Every screen with a control set gets this plot. It is the cheapest possible check and it is
the one that would have caught this defect on day one.

### Fig 4 — What stands out, given how well it was measured?
*Form: funnel plot — score against precision, with null limits that widen as precision
falls.* This is the form institutional statisticians settled on for exactly this problem
(Spiegelhalter 2005), which is worth borrowing **and** worth noting: their prescription is
the opposite of this library's — they conclude *do not rank at all*.

> **What it said:** pan-essential genes ride far above p99 — the metric's maximum is
> toxicity, not selectivity — and the controls sit inside the funnel.

### Fig 5 — Did the ordering actually change?
*Form: slopegraph, raw rank → calibrated rank, by class.* The library's only claim is about
ordering, so the figure that tests it must be about ordering.

> **What it said:** almost nothing moves — pan-essentials 927 → 928, controls 11,770 →
> 11,784. **The honest reading is that DepMap is a poor test of the ranking claim**, and
> fig 1 says why.

---

## 3. Scaling the plots

Two bugs in the explorer's payload, both found by trying to draw everything.

### The trim was deleting the middle

`build-data.mjs` reduced a long table with
`[...entities.slice(0, 2000), ...entities.slice(-2000)]` — the head and tail of a
z-sorted file. **That deletes the bulk of the distribution**, which is the part a funnel
plot exists to show, and nothing on screen said so.

Replaced by `build-points.mjs`: every entity in the top and bottom 1,500, plus a uniform
**stride** through the middle. The sampling rate travels with the data and the figure
prints it. A stride rather than a random draw, so the payload is byte-identical between
builds — a figure that changes when nothing changed is a figure nobody trusts.

### The ranks were computed inside the trim

`Movers` ranked entities within the 4,000 rows it had been sent. A rank computed inside a
trim is a rank within the trim, and "moved from 12 to 1" is exactly the claim that breaks.
Ranks are now computed in `analyses/*.py` over every entity and shipped as columns.

### The techniques, and what each buys

| technique | why | measured here |
|---|---|---|
| **Columnar typed arrays over base64** rather than an array of objects | ~30 bytes of JSON text per number, re-parsed on load, versus 4 bytes ready to index | bundle **2,715 KB → 1,178 KB** *while going from 4,000 trimmed points to 10,458 sampled ones* |
| **Canvas for marks, SVG for axes** | one `<circle>` per point is a DOM node, a style resolution and a layout box; 18k of them makes hover re-run style matching over the whole tree | 0 SVG circles; repaint in a single pass |
| **Uniform-grid hit index** | canvas has no hit targets; a grid bounds the search by *local density* instead of total count | 9 cells read per pointer move, independent of n |
| **`devicePixelRatio` sizing** | a 1px dot on an unscaled canvas is a blurry 2×2 smear | canvas 1760×840 backing 880×420 CSS |
| **Filter as a predicate, not a new array** | re-slicing 17,916 rows on every checkbox click | no allocation on toggle |
| **Density by alpha, not by size** | overlap must read as density; opaque dots hide it | bulk at 0.38 alpha |
| **Two-pass draw order** | marked classes must never be buried under the bulk | classes drawn last |

### The trap that cost the most

`ctx.fillStyle = "var(--series-3)"` is **invalid** and silently ignored — canvas does not
resolve CSS custom properties. Every point painted in the leftover colour, which looked
exactly like a data problem. Tokens are now resolved through `getComputedStyle` against
the live element, and a `MutationObserver` on `data-theme` repaints, because canvas pixels
have no cascade to restyle them.

## 4. Rules

Colour, forms and interaction follow the `dataviz` method; these are the additions this
project's subject demands.

1. **Every figure is a question with a failing answer.** If there is no result that would
   make the figure look wrong, it is decoration.
2. **Plot the expectation, not just the data.** The N(0,1) curve in fig 3 and the funnel
   limits in fig 4 are the reason those figures work.
3. **Never plot what was not measured.** No jitter, no smoothing, no clipping into the edge
   bin. The clip in the first draft of fig 3 drew a spike at z = +5 that is not in the data.
4. **Sample stratified, not uniformly.** A uniform sample of DepMap is 95 % one vertical
   line and throws away precisely the genes that carry the variation.
5. **Force the locale.** `toLocaleString()` with no argument rendered `11,770` as `11.770`
   on this machine — eleven-point-seven-seven. A figure must not change meaning with the
   reader's locale.
6. **Look at it.** The validator checks colour, not layout. Rendering the page found the
   clipped labels, the mojibake, the locale bug and the misordered figures — none of which
   any check would have caught.

---

## 5. What is not built

- **The pgfplots renderer.** Specified in `paper/sieve.sty`; no TeX toolchain here, so it
  has never run.
- **Figures 1, 3 and 5 in the explorer.** The count distribution, the control-calibration
  check and the rank slopegraph exist as data in `out/figures/depmap.json` but are not yet
  components; `web/src/features/{overview,nullfloor,ranking}` are their homes.
- **The explorer's three empty feature directories** (`web/src/features/nullfloor`,
  `overview`, `ranking`) are the natural homes for figures 3, 1 and 5.
- **No figure for the NF2 run.** It needs the two-group contrast resolved first — see
  `../lineage.md` §9.
- **No uncertainty on any figure.** The bands in fig 2 are the null's spread, not a
  confidence interval on the estimate. That is the same GUM gap recorded in
  `standards.md` §7, and it is visible here as an absence.


---

## The ADR 0007 layer, and the three things its panels do differently

Added 2026-08-29. Four results carry a governing decision record, a null and an interval, and
until this section they were rendered nowhere — the failure `web/scripts/build-data.mjs`
already names in a comment, committed again on newer work.

**1. Provenance is a disclosure, not a tooltip.** Every artefact under ADR 0007 carries
`provenance` (which files were read), a method block, `says` (the limit of the claim, written
by the *analysis* rather than by the interface) and `limits`. `Provenance.tsx` renders all
four, collapsed by default so a reader meets the finding first and a sceptic never has to open
a JSON file. It is deliberately not a tooltip: provenance that vanishes when the pointer moves
cannot be read on a phone, and this is the half of the page an argument needs.

**2. A failed result is drawn in the neutral.** The accent on this site means *measured and
standing*. The knowledge-shape panel is measured and did **not** stand, so its headline number
— a z of −19.0, pointing the wrong way — is drawn in `--r-text-3`, and the two correlations
that are artefacts of construction are labelled as artefacts on the axis itself. Giving a
failed prediction the accent would have flattered it, and the site would have been arguing for
something the analysis disowned.

**3. The table is the chart.** These payloads are dense — a five-by-five stratified table with
intervals, twenty organ systems on two retention scales, fourteen languages on six columns. A
bar chart of any one column would have hidden the other five, so the form is a table with the
value drawn *behind* the number (`BarCell`), which lets a column read as a distribution while
every figure stays legible and copyable. Cleveland & McGill's ordering is respected in the one
place it matters: the comparison the reader is asked to make — the split between context and
contradiction — is a single length on a common baseline.

**Interaction is reordering, never recomputation.** Sorting the organ systems and picking a
language change what is drawn and nothing else; no statistic is computed in the browser. That
is what keeps `tools/verify_claims.py` able to fail the build when prose and artefact drift.


---

## The run dashboard, and the dimension each view puts back

Added 2026-08-29. The DepMap sections had the numbers and drew them one dimension at a time,
which is how a claim about *comparability across n* ends up rendered as a bar chart of scores.
Three views, each restoring the axis that carries the argument.

**The calibration field.** z over (raw score, observation count). On the usual
score-against-z scatter, n is a colour nobody reads; here it is an axis, and the shape bends —
which is the entire reason the library exists. Pan-essential density is drawn as a **ring**
rather than a second fill, because it is a warning about what the metric rewards and not a
second quantity of the same kind.

**The bump.** Raw rank against calibrated rank for the raw top sixty. A reordering cannot be
shown by a bar chart of either ranking — only by the lines between them. Of those sixty,
**35 are pan-essential, 55 fell, and 33 of the 55 that fell are pan-essential**: the claim
that the raw maximum is toxicity, drawn rather than asserted. Pan-essential lines carry the
accent because they are the finding.

**The lineage matrix.** 23 lineages against the 44 genes they nominated, ordered so the genes
several lineages share sit left. A per-lineage bar chart answers *what did Lung find* and
hides the only question worth asking — whether anything Lung found was found anywhere else.
**27 of the 44 were nominated by more than one lineage**, which is the single-point-of-failure
risk Stage 7 exists to catch, made visible.

All three read `out/rare/view_models.json` — the same solved layouts the rare group fetches,
so a reader who has visited either pays the 53 kB once.
