# The visualisation canon — what each discipline contributed, and where it is used here

> **Role:** the interdisciplinary reference layer behind the dashboard. Every chart form
> in `web/` was invented by someone, for a problem, with a caution attached. This records
> which one, so a form is chosen rather than reached for.
> **Last revised:** 2026-08-28 · **State:** §7b's three open rows are now **all built**, and
> §7d adds the three forms that arrived with them. ⚠️ **written from working knowledge, not
> from consultation** — authors, years and venues must be checked against the source before any
> of this appears in a manuscript. What is verified is the right-hand column: what we
> actually built and what it measured.
>
> Companion files: [`visualization.md`](visualization.md) is the model and the scaling
> work; this is the provenance.

---

## 0. Why an interdisciplinary layer at all

Every field that ranks noisy things has independently invented a chart for it, and each
one carries a different half of the problem:

| the problem | who solved it | the form |
|---|---|---|
| is this process in control? | manufacturing QC, 1920s | control chart |
| is this unit an outlier, given its size? | institutional / medical statistics, 2000s | funnel plot |
| does this distribution match the one claimed? | statistical graphics, 1960s | Q-Q plot |
| did the ordering change? | information design, 1980s | slopegraph |
| is this count an artefact of sampling effort? | ecology, 1970s | rarefaction curve |
| what does the raw data look like? | statistics education, 1970s | Anscombe's quartet |

`sieve` sits at the intersection of all six. **Borrowing the form is cheap; borrowing the
caution attached to it is the part that pays.** Spiegelhalter invented the funnel plot and
concluded *do not rank at all* — a conclusion this library disagrees with, and had better
disagree with explicitly rather than by not noticing.

---

## 1. Statistical process control — the null band is a control chart

**Shewhart, *Economic Control of Quality of Manufactured Product* (1931).** ⚠️
Distinguishes *common-cause* variation, which is the process, from *special-cause*
variation, which is a signal. The chart draws limits at ±3σ of the in-control process and
declares anything outside a signal.

**What we use:** this is exactly `NoiseFloor` — the band is common-cause variation,
estimated from real control observations rather than from a formula, and the entities
above p99 are the special-cause candidates.

**The direct lineage worth naming:** Shewhart taught Deming; Deming took it to Japan in
1950; the Japanese quality tradition that `standards.md` §2 already draws on is downstream
of the same idea. **This repository's central statistic and its documentation practice
have the same ancestor**, which is not something we noticed until this file was written.

**The caution:** Shewhart's limits assume a *stable* process with *constant* subgroup size.
Ours vary — which is the entire subject of the library, and the reason the band is a
function of n rather than a pair of horizontal lines.

## 2. Institutional comparison — the funnel plot

**Spiegelhalter, "Funnel plots for comparing institutional performance", *Statistics in
Medicine* 24(8), 2005.** ⚠️ Plot the estimate against its precision, with control limits
that widen as precision falls.

**What we use:** the `NoiseFloor` scatter is a funnel plot with a resampled rather than
parametric limit.

**The caution, and it is aimed at us:** the paper's own conclusion is that funnel plots
*"avoid spurious ranking of institutions into league tables"* — the recommendation is not
to rank. `sieve` ranks anyway, on a standardised score. That disagreement is a real
position and it belongs in the manuscript, not in a footnote.

**The companion demonstration:** Marshall & Spiegelhalter, *BMJ* 316, 1998 ⚠️ — IVF clinic
league tables, where a clinic ranked sixth from the top on 82 treatments cannot be placed
in the top half with any confidence. It is the same figure as our count-variation chart,
made twenty-eight years earlier.

## 3. Distributional agreement — the Q-Q plot

**Wilk & Gnanadesikan, "Probability plotting methods for the analysis of data",
*Biometrika* 55(1), 1968.** ⚠️ Plot the sample quantiles against the theoretical ones; a
match is a straight line.

**What we use:** `ControlCalibration`, and it is the single biggest methodological upgrade
in the dashboard. The density overlay it replaced showed *that* the controls were
displaced. The Q-Q decomposes the disagreement into three separately readable parts —
offset is bias, slope is spread, curvature at the ends is tail misfit — and immediately
produced a finding the density version had hidden for the whole project:

> the blocked null is correct through the body (median z −0.12) and has a **heavy right
> tail**: the 99.95th percentile of the control set sits at **8.9** where a standard normal
> gives 3.3.

That is a statement about **control-set purity** — some genes in the "known to do nothing"
set behave like real dependencies — and a density curve compresses exactly that region into
an invisible sliver near zero. The tails are where a shortlist is drawn from, so the form
that renders the tails legibly is not a stylistic preference.

**The caution:** a Q-Q plot of 726 points invites over-reading of the extreme ends, where a
handful of observations set the shape. Ours has no confidence band, which is the honest
gap — see `standards.md` §7 item 1.

## 4. Change in ordering — the slopegraph

**Tufte, *The Visual Display of Quantitative Information* (1983).** ⚠️ Two ranked columns
and a line between them; the reader decodes change as slope.

**What we use:** `RankShift`. It beats a grouped bar chart, which forces two separate
position comparisons, and a rank-versus-rank scatter, which shows the joint distribution
but buries the direction of individual moves.

**The deliberate loss:** we plot class medians, not 17,916 lines. A slopegraph of every
entity is a hairball. The question being asked is not "where did each gene go" — the table
answers that — but "did the classes we can check move as the method predicts". Choosing the
task before the encoding is Munzner's abstraction step (below).

## 5. Sampling effort — rarefaction, and the road not taken

**Hurlbert, *Ecology* 52(4), 1971; Gotelli & Colwell, *Ecology Letters* 4(4), 2001; Chao et
al., *Ecological Monographs* 84(1), 2014.** ⚠️ Species richness rises with sampling effort,
so richness measured at different efforts is not comparable. The standard fix is to
subsample every unit down to a **common** n.

**Why it matters here:** ecology chose *equalise-n*; `sieve` chose *standardise-against-n*.
They solve the same problem and a reviewer will ask why. The honest answer is that
equalising throws away data from the best-measured entities, and that the choice should be
driven by the distribution in the count-variation chart — **when 95 % of entities share one
count, rarefaction is nearly free and calibration is nearly pointless**, which is precisely
the DepMap situation.

This is currently the strongest argument *against* the library's approach on this dataset,
and it came out of writing this file.

## 6. Perception — why these encodings and not others

**Cleveland & McGill, "Graphical perception", *JASA* 79(387), 1984.** ⚠️ Ranks elementary
perceptual tasks by accuracy: position on a common scale beats length, which beats angle,
which beats area, which beats colour saturation.

**What we use:** every quantitative comparison in the dashboard is position on a common
scale. The count distribution is bars, not a pie or a treemap — the same data on area is
decoded far worse and cannot show the log-spaced axis the variable lives on.

**Bertin, *Sémiologie graphique* (1967)** ⚠️ — the visual variables, and the rule that
identity should never rest on colour alone. Applied as: every series is direct-labelled,
and the two-series slopegraph carries no legend at all.

**Munzner, *Visualization Analysis and Design* (2014)** ⚠️ — what/why/how: abstract the task
before choosing the encoding. Applied as the class-median decision in §4.

**Few, *Information Dashboard Design* (2006)** ⚠️ — no gauges, no pie charts, no decorative
chrome; a dashboard is scanned, so the summary precedes the detail. Applied as the stat
tiles above each chart.

## 7. Why plot at all — the argument this whole layer rests on

**Anscombe, "Graphs in statistical analysis", *The American Statistician* 27(1), 1973** ⚠️ —
four datasets with identical means, variances, correlation and regression line, and
completely different shapes. **Matejka & Fitzmaurice, CHI 2017** ⚠️ ("Same Stats, Different
Graphs" / the Datasaurus) generalised it: any target statistic can be held fixed while the
shape is moved anywhere.

**What it means here, concretely:** the −4.09 was in every table this repository printed —
in the findings file, in the manifest, in the manuscript's macros — and it was read as a
number rather than as a defect for weeks. Anscombe is the reason that is predictable rather
than embarrassing: a summary is not the data, and a table asks the reader to hold the
expected shape in their head. The Q-Q plot puts the expectation on the page.

---

## 7b. The less obvious forms, and why each earns its place

Added 2026-08-27, when the conventional forms stopped answering. **A rare form is only
justified when it answers better than the common one** — novelty is not a reason, and a
form that needs a manual to be read either gets annotated in the piece itself or gets
replaced by a bar chart.

| Question | Data structure | What I had | What it needed | Verdict |
|---|---|---|---|---|
| What does the score read when nothing happens, at each n? | distribution × many ordered series | line of mean ± sd | **ridgeline (joyplot)** | **Built.** The band reported two moments of a distribution whose *shape* is the subject: a top-k operator is skewed by construction, and skew is what decides where a cutoff lands. |
| What stands out, given the precision behind it? | 2-variable distribution, 17,916 points | overplotted scatter | **hexbin** or contour | **Built 2026-08-28.** `HexbinPlot` on the selectivity plane, hybrid: cells above two genes are drawn as density, cells at or below give their points back as marks, so the crowded core reads as density and the sparse corner stays nameable. Both axes became non-linear at the same time — see §7d. |
| Which combinations of gaps co-occur? | sets and intersections | a matrix of dots | **UpSet plot** | **Built 2026-08-28.** Twice, from one organism: `FlagOverlap` on the run dashboard and `GapPatterns` on the rare page. The second needed a new measurement — `tools/gap_patterns.py` — because nothing on disk had ever counted co-occurring gaps. |

**Ridgeline — the trade, stated.** Overlapping ridges swap a little positional precision
(Cleveland–McGill's most accurate channel) for seeing seven distributions at once. That is
the right trade here because the question is comparative — "how does the null change with
n" — not a lookup. It is the wrong trade the moment someone needs to read a value off it,
which is why the table view carries the numbers.

**What it showed that the band could not:** every ridge is right-skewed, the whole
distribution slides right as n grows, and the 99th percentile moves from 0.743 to 0.869
across the range. A gene screened in more lines must clear a higher bar to mean the same
thing — visible as a shape, invisible as two numbers.

### The colour system this required

Three scales, three jobs, because using one where another belongs is the most common
charting error there is:

| Scale | Job | Construction | Where |
|---|---|---|---|
| categorical | identity, no order | 6 hues, staggered lightness, OKLCH | classes, systems |
| sequential | magnitude, one direction | one hue, monotone lightness | the ridgeline, prevalence |
| diverging | polarity around a midpoint | two hues, **neutral** middle | a calibrated z, which is genuinely diverging around zero |

All in `web/src/lib/palette.ts`, defined in OKLCH and converted to hex on demand because
chart libraries take literal colours and cannot read CSS custom properties. **Two drafts
of the categorical scale failed the validator before one passed** — the first put yellow
next to orange (normal-vision ΔE 13.7, below the floor of 15), the second stepped the dark
variants outside the 0.48–0.67 lightness band. Neither was visible by eye, which is the
argument for running the validator rather than reasoning about it.

---

### What the two built forms said that the old ones could not

**Hexbin.** The linear scatter of 800 genes showed one blob. On a symlog x and a log y with
density binning, the plane resolves into **two separated clouds** — a low-selectivity group
at negative dependency and a high-selectivity group at positive dependency. The bimodality
was in the file the whole time; the encoding was hiding it.

**UpSet, on the run.** Of the shipped sample, **64 genes are in the raw top 100, in the
calibrated top 100, and flagged common-essential** — one column, one number, the argument
for calibrating. The single-class colouring used everywhere else on the site cannot express
that a gene is two things at once, and this is the only figure in which the overlap is
visible at all.

**UpSet, on the catalogue.** `tools/gap_patterns.py`, over 8,574 OMIM-coded diseases:
**4,565 (53 %) record all four fields** (gene, inheritance, onset, sign denominators), and
among those with any gap the largest single pattern is **1,326 diseases missing gene, onset
and denominator together**. Emptiness is concentrated, not scattered — which changes the
problem from a curation backlog into a population nobody has described.

**And a join failure, found by trying to draw it.** Prevalence was meant to be a fifth field.
It came back missing for 100 % of the population — the shape of a broken join, not of a
fact. Counting the HPO annotation rows by identifier prefix:

| prefix | rows | inheritance annotations | signs with a `k/n` frequency |
|---|---:|---:|---:|
| OMIM | 169,427 | 9,065 | 103,106 |
| ORPHA | 115,875 | **0** | **0** |

The two catalogues annotate different things in the same file, and prevalence exists only
under ORPHA codes. Any figure showing gene, inheritance, onset, signs *and* prevalence
together is joining two populations. **This belongs in §8: the defect was found by a chart,
and by nothing else.**

---

## 7c. Sonification — the one channel where the ear beats the eye

Added 2026-08-27. Sound is not in the atlas of forms, so it enters under the same rule as
any exotic form: **only if it answers better, and only with the mapping printed beside it.**

There is a narrow, real case, and it is not novelty.

**The ear resolves a beat frequency far below the threshold at which the eye separates two
nearly coincident points.** Two tones a fraction of a semitone apart produce an audible
throb whose rate *is* the difference. A Q-Q plot near its reference line is exactly that
situation — the departure that matters most is the one hardest to see, because the points
sit on top of the diagonal.

So the mapping is: **a correct null sounds like one note.**

Two voices sweep the quantiles together, one at the pitch a correct null would give, one
at the pitch observed. Perfect calibration is a **unison**; any departure opens an
interval, and the beating in the tails arrives before the dots visibly leave the line. A
cursor tracks the sweep on the plot, so sound and sight stay locked and neither has to be
trusted alone.

The second mapping is deliberately literal rather than clever: **uncertainty sounds
uncertain.** In the ultra-rare evidence panel the estimate is a pitch and the interval
around it is *bandwidth* — a narrow interval is a clean tone, a wide one a band of hiss you
can locate but not pin down. It needs no training to read, which is the usual and fair
objection to sonification.

**The rules the engine enforces**, because a sonification that breaks them is worse than
none:

- **Never autoplay.** The `AudioContext` is created inside the first gesture — which is
  what browsers require and what anyone who has opened a page that made noise at them
  requires too.
- **Always a visual equivalent.** Sound is added to a chart, never instead of one. The
  exception is the reader who cannot see the chart, and for them it is the only channel —
  which is the strongest argument for building it at all.
- **The key is printed.** A mapping nobody can read is a novelty, not a channel.
- **Enveloped amplitude.** Square-edged gain changes click, and a click reads as data.
- Pitch is mapped **logarithmically**, because pitch perception is: equal ratios sound like
  equal steps, equal differences do not.

**What it is not.** It is not a substitute for the Q-Q plot, and it does not make an
unclear finding clear. It makes one specific comparison — deviation from a reference —
available to a faster and more sensitive channel, and it makes the whole figure available
to a reader who had nothing.

---

## 7d. Forms added 2026-08-28, and what each replaced

**A rare form is only justified when it answers better than the common one** — the §7b rule,
applied again.

| Form | Anchor | Replaced | Why the replacement was forced |
|---|---|---|---|
| **Hexagonal binning** | Carr, Littlefield, Nicholson & Littlefield, *JASA* 82(398), 1987 ⚠️ | an 800-point overplotted scatter | Alpha blending fails in both directions: low alpha loses the sparse corner, high alpha saturates the core and every count above saturation looks identical. Hexagons rather than squares because a hexagon's centre is equidistant from all six neighbours, so bin assignment does not depend on which axis a point drifted along — square bins band visibly in exactly the dense regions the plot exists to show. |
| **Raincloud** | Allen, Poggiali, Whitaker, Marshall & Kievit, *Wellcome Open Research* 4:63, 2019 ⚠️ | a five-number box plot of the three populations | A box is five numbers, and two distributions with the same five can be unimodal and bimodal — Matejka & Fitzmaurice's Datasaurus point ⚠️. The populations panel exists to show whether the controls sit at the null and the candidates separate from it, and a second mode is the most interesting thing that could happen there. It duly appeared: the candidate row has mass at z ≈ −1.3 **and** at z ≈ +15. The box drew that as a wide box. |
| **UpSet** | Lex, Gehlenborg, Vuillemot, Streit & Pfister, *IEEE TVCG* 20(12), 2014 ⚠️ | nothing — the overlap had no figure | A Venn is readable to three sets and encodes count by **area**, near the bottom of Cleveland–McGill. At four sets a proportional Venn is usually geometrically impossible, so the drawing stops being proportional without saying so. UpSet puts intersections on a common baseline and reads as a bar chart. |

**The dodge, and why it is not jitter.** The raincloud's rain uses a one-dimensional
beeswarm: a point moves only on the axis that carries no units. Jitter, the usual shortcut,
displaces on both and therefore moves every point away from the value it represents. The
swarm is then scaled — not clipped — to its row: local density sets a swarm's height, five
hundred genes at one z pile into a column that walks through the neighbouring rows, and
compressing an axis with no units removes no information while clipping would delete
observations.

**Non-linear axes became a first-class object at the same time**, because the forms above
were not enough on their own:

| Scale | Where | Why not linear |
|---|---|---|
| `symlog` | median dependency, −0.48 to +4.37 | Crosses zero, so log is unavailable; middle half inside [−0.17, 1.83], so a linear axis spends three quarters of its width on a tail holding a handful of genes. Linear within ±0.25, logarithmic outside, and the threshold is an argument rather than a default because it is a claim about which differences stop mattering. |
| `log` | selectivity, strictly positive and right-skewed | The standard case. |
| `quantile` | available, unused so far | Position by rank rather than by magnitude — the honest axis when the question is "who is where" and not "how much". Its axis must print percentiles, since the units are no longer linear in position. |

**Everything under them is checked.** `web/scripts/check-viz.mjs` runs in `npm run check`,
beside the contrast and palette gates, and imports the same TypeScript modules the app does:
KDE integrates to 1 and peaks at the normal's 0.399, quantiles match `numpy.percentile`'s
type 7, every hexbin point lands in its nearest lattice centre, the beeswarm leaves no
collisions, and UpSet partitions its items. **Two of the twenty-eight checks failed on the
first run and both were the assertion, not the code** — one asserted that symlog compresses
decades near the threshold, which is backwards; the other compared bandwidths between a
sample and its own left tail rather than a subsample.

---

---

## 8. What each form would have caught, and when

The retrospective test — for each defect this project actually found, which chart would
have surfaced it first:

| defect | found by | which form would have shown it immediately |
|---|---|---|
| control genes at z = −4.09 | an adversarial code audit, weeks later | **Q-Q or control chart**, day one |
| null slope 1.93× too steep | algebraic decomposition | **null curve**, two series overlaid |
| ranking claim untestable on DepMap | writing a figure caption | **count distribution**, before any modelling |
| control set not fully inert | **the Q-Q plot, today** | — |
| prevalence and inheritance live under different identifier systems | **the UpSet, 2026-08-28** — the field came back 100 % missing, which is the shape of a broken join | — (no earlier form was drawing the two together, so nothing could have shown it) |
| explorer deleting the distribution's middle | trying to draw all points | any density-preserving scatter |
| ranks computed inside a trim | reading the payload | — (no chart shows this; only the code does) |

Two of six were found by a chart and one *only* by a chart. That is the return on treating
plotting as a stage, and it is also the limit: the last row is a reminder that a figure
cannot show a defect in the pipeline that feeds it.

---

## 9. To verify before citing

Every entry above is ⚠️ from working knowledge. In priority order, because these carry
argumentative weight rather than decoration:

1. **Spiegelhalter 2005** — the exact wording of the anti-ranking conclusion, since we
   disagree with it in print.
2. **Wilk & Gnanadesikan 1968** — that this is the correct primary citation for the Q-Q
   plot rather than a later popularisation.
3. **Hurlbert 1971 / Chao 2014** — the current recommended rarefaction practice, since §5
   is the strongest objection to our approach.
4. **Cleveland & McGill 1984** — the exact ordering of the perceptual task ranking.
5. **Shewhart → Deming → Japan** — the lineage claim in §1, which ties this file to
   `standards.md` §2 and should not rest on folklore.
