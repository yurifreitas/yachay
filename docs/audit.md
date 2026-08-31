# Repository audit — the project against its own standard

> **Role:** a standing audit of this repository against the rules it publishes for itself
> (`references/standards.md`, the documentation standard, the ten stages). One dated
> section per pass. It records what is *out of conformance*, not what works.
> **Last revised:** 2026-08-29 · **State:** nine sweeps in one day. Five went deeper into the
> rare-disease layers, the sixth measured the repository itself, the seventh widened the
> reference base, the eighth used it to attack this project's own weakest published claim,
> the ninth brought in patient-level data for the first time, the tenth read the two thirds
> of it the ninth had discarded, the eleventh joined the halves, the twelfth read all nine
> million rows of ClinVar, the thirteenth turned the result into a stage other people can
> run, the fourteenth verified every published number against the artefact that produced it,
> the fifteenth put an interval on every headline — closing **A6**, the oldest open finding
> here — the sixteenth surveyed the author's own prior projects and found the ancestor this
> repository never credited, and the seventeenth transferred two practices from them.
> **37 findings**, 29 closed. **A27 is the one to read first**: it restates A15 and it is an
> attribution debt, not a bug. **A28 is the one that stings**: five of this project's nineteen
> thresholds were chosen after looking at the data they gate. The backlog is ordered in
> [`roadmap.md`](roadmap.md).
> **A18 is the strongest result here**: the library's founding claim, measured on 10,377
> real patients, in a domain it was never aimed at. **A11 is the most serious defect found** — a wrong number, on
> screen, for months. **A14 is the most uncomfortable** — it falsified a generalisation this
> audit had published two entries earlier. **A15 is the most important**, and it is not a
> defect at all: the periphery is 6.5× the core, nothing in the periphery uses the core, and
> eight of the ten headline stages have no implementation. Every other finding here is
> inside something; that one is about the shape of the whole.
>
> This file is **explanation-mode** (Diátaxis): it argues about the state of the project.
> It is not a how-to and must not accumulate instructions.

The five-lane adversarial review of 2026-08-26 (`references/deep/README.md`) asked whether
the *science* is right. This asks a smaller and more boring question: does the repository
still say what it does? A project whose documentation lags its code by one fix is a project
that will be cited for a number it has already retracted.

Method: the whole tree was read (11,816 lines of Python across `src/`, `tools/`,
`analyses/`, `tests/`; 4,572 lines of Markdown under `docs/`; the manuscript sources), the
test suite was run, and every headline number in the prose was checked against the manifest
that generated it. Commands are quoted where a finding rests on one.

---

## 1. What the pass confirmed

Stated first and briefly, so that the findings below are not read as a verdict on the whole.

- `python -m pytest -q` → **29 passed** in 21 s. No skips, no xfails.
- The defect the internal-audit lane called fatal — *"every z the library has published is
  on the wrong scale"* — **is fixed in the shipped artefact.** `out/depmap.manifest.json`
  now carries `null_blocks: "gene"` and `nonessential_mean_z: 0.036` (sd 1.013) where the
  published number was −4.09. The positive control passes: `common_essential_mean_z: 9.452`.
- The fix carries a *poka-yoke*, not just a parameter: `fit_null` warns when called on
  pooled rows with no `blocks=`, and `tests/test_block_nulls.py` asserts the failure mode
  the warning describes. That is the right shape — the old behaviour is reachable but no
  longer silent.
- ADR 0004 was written **before** the work and scored the same day. *Nemawashi* is being
  practised, not merely documented.

---

## 2. Findings

Ordered by what a reader of this repository would be misled by first.

### A1 — `CITATION.cff` advertises two anomalies that are resolved · **closed in this pass**

The header block of `CITATION.cff` — the machine-readable claim list, the thing a citing
author copies — still read:

> `TWO OPEN ANOMALIES, stated because they are not yet explained: the nonessential control
> pool calibrates to a mean z of -4.09 rather than ~0 …`

Both were explained on 2026-08-26 and one was fixed; `docs/lineage.md` §8 says so, and the
manifest agrees with the fix. The citation file was the only place still carrying the old
state, and it is the place with the longest half-life.

This is exactly the failure the repository's own §4 rule exists to prevent (*"the claim and
its number cannot drift apart"*), landing on the file that rule names. **Fixed in this
pass**, with the resolution and the new numbers in place of the old claim.

*Root cause (five whys, one level deep enough to act on):* the fix updated the manifest and
the lineage file because those were open in the editor; nothing links the manifest's
`headline` keys to the prose that quotes them. See F1.

### A2 — `README.md` under-declares the repository by roughly half · **partly closed**

The README's documentation table lists 9 files. The tree holds a `tools/` directory of
**7,000+ lines** producing eleven distinct analytical layers under `out/rare/` — the world
atlas (14,831 diseases), the bias audit, the prevalence audit over 17,108 Orphanet records,
the non-gene layer, the capability arithmetic, the nomenclature layer, the barriers layer,
the thesis audit — none of which the README mentions. A reader is told this is a
statistics library with a DepMap case study. It is that plus a rare-disease evidence
platform, and the second half is undocumented in the entry point.

**Partly closed:** the three documents written alongside this audit
(`references/rare-disease-mechanisms.md`, `-scale.md`, `-equity.md`) document the *claims*
of that layer and are now indexed. The `tools/` scripts themselves still have no reference
page; each carries an excellent module docstring, and nothing collects them. **Open.**

### A3 — the `docs/` tree has no map of `out/rare/` · **closed**

Related to A2 but distinct, and the more dangerous of the two. Eleven JSON artefacts are
consumed by the web explorer and cited in prose, and no document states, per artefact: what
produced it, what its provenance field says, and — the load-bearing one — **whether its
content is measured or authored.**

The scripts themselves are scrupulous about this. `nongene_seed.py` says its classes are
authored; `nongene_measure.py` exists precisely to test them against the catalogue and
reports that six of the ten have a measured footprint of exactly zero. `barriers.json` and
`nomenclature.json` carry explicit `provenance: "Written from working knowledge"` fields.
That discipline is invisible to anyone who reads the dashboard instead of the source.

**Closed by [`references/rare-layers.md`](references/rare-layers.md)**, which does exactly
what this finding asked for: every artefact with its producer, its grade
(measured / derived / authored), and the number it exists to support — with the provenance
strings quoted from the payloads rather than paraphrased.

Writing it produced a count nobody had: **eight of the twenty layers are measured, three
derived and nine authored.** The ratio is not a complaint, but it had never been visible,
and it exposes A13.

### A9 — a field in the primary source had never been read · **closed, by measuring it**

Found by the second sweep, and it is the most productive finding in this audit.

`tools/prevalence_audit.py` opened Orphanet's prevalence records, established that a
prevalence is a *list* of measurements rather than a number, and reported geography as a
by-product — "65 % carry no named place". Nothing then read the field. Eleven analytical
layers, a manuscript and a dashboard were built on a corpus whose **population** column had
never been opened.

`tools/ancestry_geography.py` (new, registered as a pipeline stage so it goes stale like
every other) reads it. The results are in
[`references/rare-disease-ancestry.md`](references/rare-disease-ancestry.md) §1; the two
that change what this project may claim:

- **386 of 525 (73.5 %)** disorders with records in more than one country fall into
  **different prevalence classes** by country. Every other tab collapses each to one band,
  so a cohort denominator computed anywhere in this repository is a world average over
  populations that disagree.
- Representation against population: **Europe 8.10, Africa 0.07**. The `capability_math`
  arithmetic, the dossiers and the atlas all inherit that skew and none of them says so.

The finding is also **in the interface**, not only in prose: a new explorer section
(`#rare?s=population`) renders all three results, and two defects were caught by building
it that the documents alone would not have surfaced — a stat tile that coloured Europe
green where the chart beneath it coloured Europe orange (a valence smuggled into an
encoding that carries only a direction), and a layout ratchet where an ECharts canvas
measured pre-layout grew its own grid track until the page overflowed by 110px and clipped
a tile. Both are recorded in the source with the measurement that found them.

*Root cause:* the audit rule this repository applies to its own **statistics**
(`tools/atlas_bias.py` turns the library on its own reference data) had never been applied
to its own **schema**. Auditing what a number says is not the same as auditing what its
source could have said and did not.

### A10 — FAIR is in the standards, CARE is not · **open, ADR written**

`references/standards.md` names FAIR among the canons this project answers to. The CARE
Principles for Indigenous Data Governance (Carroll et al., 2020) — which govern who data is
*about*, where FAIR governs how data *moves* — appear nowhere in the repository.

No obligation is currently breached: every input here is a public aggregate. The design gap
is real regardless, and it is the same gap as A9 seen from the ethical side — the
architecture has **one untyped string** for a population and no field for
provenance-of-consent.

Not fixed in this pass, deliberately. Editing a standards file is a decision, and decisions
get an ADR first: [0005](adr/0005-population-as-a-typed-field.md), written before the work,
proposing both the typed population field and the CARE row, with the risk that a population
field invites the ancestry inference this project must not make.

### A11 — an XML entity was never decoded, and the largest band in the catalogue was invisible · **closed**

The worst defect in this audit, found by looking at a rendered panel and asking why one row
read `&lt;1 / 1 000 000` instead of `<1 / 1 000 000`.

**The mechanism.** `tools/build_atlas.py`, `tools/dossier.py` and `tools/atlas_bias.py` read
the Orphanet prevalence XML with **regular expressions rather than a parser**, so nothing
decoded `&lt;`. Orphanet writes the rarest prevalence class as `&lt;1 / 1 000 000`, and the
corpus contains **4,998 such records — the single largest class there is**. Every one
arrived as a literal entity string that matched no entry in the rank table, with two
consequences that both shipped:

1. `min(classes, key=lambda c: RANK.get(c, 99))` sent the rarest class to rank 99, so a
   **more common band was selected and displayed as "the rarest on record"**.
2. `if v["prevalence"] in ("<1 / 1 000 000", "1-9 / 1 000 000")` — the membership test
   defining the ultra-rare set — was **dead code that could never fire**.

**What it cost, measured before and after the one-line fix:**

| | before | after |
|---|---|---|
| ultra-rare diseases | 770 | **4,586** |
| …with a known gene | 390 | **2,663** |
| ultra-rare gene coverage | 50.7 % | **58.1 %** |
| diseases in the `< 1 / 1 000 000` band | **absent from every output** | **3,987** |
| streetlight rank correlation | −0.0847 | **−0.113** |

The hero counter on the rare-disease dashboard read *"380 of 770 ultra-rare, and no gene"*.
The true figure is 4,586 ultra-rare, 1,923 of them with no gene. Every downstream artefact
was regenerated and every document quoting the old numbers was corrected — see
`references/rare-disease-scale.md` §2, which carries the correction in place rather than
silently restating the new value.

**Why the other two readers were never affected, and what that argues.**
`tools/prevalence_audit.py` and `tools/ancestry_geography.py` use `ElementTree`, which
unescapes. The same corpus, read two ways, gave two answers for months. *The defect is the
argument for the parser* — and the deeper point is that the regex readers were **older**,
so the newer, more careful code was silently disagreeing with the code the dashboard
actually rendered.

*Root cause, five whys, stopping where it becomes actionable:* the numbers were never
cross-checked between the two parsing paths, because nothing in the repository asserts that
two tools reading one file agree. That is F3.

### A12 — the disease panel rendered fourteen identical bars as if they were evidence · **closed**

Found by the user looking at the rendered page, which is worth recording: three automated
sweeps did not catch it.

The "One disease" panel drew one bar per sign with its Wilson interval. For Duchenne
muscular dystrophy it drew **fourteen identical bars**, every one reading `1/1 · 21%–100%`,
because **not one of the 39 recorded signs of Duchenne in HPO is estimated from more than a
single patient**. A 100 % point estimate on n=1, with an interval covering four fifths of
the scale, is not a measurement — and the panel rendered it exactly like the 106/111 series
it draws for cystic fibrosis.

Three compounding defects, all now fixed in `tools/dossier.py`:

1. **No evidence grade.** A fraction with a real denominator, a fraction of one patient, an
   unquantified class and nothing at all are four different amounts of knowledge. They are
   now graded at the source and the grade travels on the record, so no renderer can flatten
   them back into one bar chart.
2. **The sort inverted the evidence.** The key was `(kind != "fraction", -point)`, which
   ranks a 1/1 case report — point estimate 1.0 — **above** a 106/111 series. The weakest
   evidence in the corpus sorted to the top of the panel.
3. **Truncation hid the ignorance.** `signs[:24]` combined with that sort meant the signs
   with *no frequency at all* were never rendered. The panel displayed the noise and
   dropped the silence, which inverts this project's argument.

Measured across the twelve dossiers: five diseases — spinal muscular atrophy, NF2, Dravet,
CDKL5 deficiency, Zellweger, sickle cell anaemia — have **zero** signs with a denominator
of any size. Cystic fibrosis, with 21 quantified signs and a median series of 27, is the
exception rather than the standard.

*Root cause:* the repository audits the statistics it computes and had never audited the
statistics it **displays**. A9 was the schema equivalent of this; this is the rendering one.

### A13 — only two of the nine authored layers have ever been tested · **open**

Exposed by writing A3's map, which is the argument for writing such maps.

`nongene_seed.py` is authored, and `nongene_measure.py` exists to check it against the
catalogue. That check came back hard: **six of its ten authored causal classes have a
measured footprint of exactly zero**, and the result is published beside the seed rather
than used to quietly revise it. That is the pattern this repository claims for itself.

It has been done **once**. `barriers.json`, `capability.json`, `nomenclature.json`,
`lupus.json`, `lupus_graph.json`, `lexicon.json`, `references.json` and `thesis.json` are
authored and untested — and the first three are the ones the dashboard renders most
confidently, as tables of facts, with their provenance strings sitting unread in the
payload.

*Fix, in the order the value falls:* the lexicon is mechanically checkable (resolve every
identifier against Orphanet, OMIM, MONDO and HPO — the file already says this must be done
before use); nomenclature's rename cases are checkable against the source that renamed them;
barriers and capability are judgement layers where the honest move is not a test but
**surfacing the confidence mark in the interface**, which is a rendering change and cheap.

#### The first of those is done, and it found something · `tools/lexicon_check.py`

**Two of nine authored layers are now tested.** The check resolves every identifier in
`lexicon.json` against the ingested catalogues — 6,728 Orphanet disorders, 12,956 annotated
diseases, 5,524 gene symbols — and reports `unverifiable` rather than `pass` for MONDO,
which is not ingested. Eight of twelve diseases come back clean. The four that do not:

| disease | field | what the catalogue says |
|---|---|---|
| **CDKL5 deficiency disorder** | ORPHA + prevalence | its code **`ORPHA:3095` is *Atypical Rett syndrome*** — the superseded classification. The correct code, **`ORPHA:505652`**, is the one our own *measured* dossier already uses. The prevalence disagreement (`1-9 / 1 000 000` claimed, `1-9 / 100 000` recorded) is a **symptom of the wrong code**, not a separate error. |
| **Zellweger spectrum disorder** | ORPHA | `ORPHA:79205` resolves in nothing ingested. The corpus carries the entity only as OMIM peroxisome-biogenesis entries. |
| **NF2-related schwannomatosis** | ORPHA name | code resolves; Orphanet calls it *Full NF2-related schwannomatosis* |
| **Spinal muscular atrophy** | ORPHA name | code resolves; Orphanet calls it *Proximal spinal muscular atrophy* |

**The finding under the finding.** In all four cases the *measured* layer — `dossiers.json`,
built from the catalogues — already had it right; the *authored* crosswalk is the one that
is wrong. Two layers of this repository disagreed about the identity of the same disease,
and nothing compared them until now. That is A11's failure mode (one corpus read two ways,
never cross-checked) recurring in a different medium, which is why F3 was generalised beyond
XML parsing.

**And the checker's own first draft was wrong, in the way it exists to catch.** It authored
a token map (`P_LT_1_1M`) instead of reading the one the lexicon ships (`P_LT_1M`), and
flagged four diseases for an unreadable prevalence token when the token was fine. Worse, it
read `UNKNOWN_GENE` and `UNKNOWN_PREVALENCE` as failures — the *declared unknowns* that are
the entire design decision the lexicon is named for. Both are fixed by reading the
vocabularies from the artefact, and the mistake is recorded at the top of the file rather
than quietly corrected: a verifier that authors its own constants is a verifier with the
defect it checks for.

**Still open:** nomenclature, capability, barriers, lupus, lupus_graph, references and
thesis — seven authored layers, untested.

### A12b — the evidence claim was made on twelve diseases and is now made on all of them · **closed**

Recorded because the fix is a strengthening rather than a correction, and because the
generalisation was not guaranteed to hold.

A12 found the disease panel drawing single-patient case reports as measurements, and the
Duchenne headline — not one of 39 signs estimated from more than one patient — came from a
**hand-picked dozen** chosen partly for being well studied. That is a sample biased toward
making the finding look mild. `tools/evidence_atlas.py` asks the same question of all
**12,935** annotated diseases, importing the grading rules from `tools/dossier.py` rather
than restating them, so the two cannot drift.

The claim did not merely survive; it got worse. Only **39.7 %** of diseases have a single
sign estimated from a real series, **56.1 %** have no fraction of any kind anywhere, and the
median denominator where one exists is **5 patients** — with **72 %** of all quantified signs
resting on fewer than ten. Across 23 organ systems the quantified share runs 7.9 % to 35.5 %:
there is no well-measured system. Full account in
[`references/rare-disease-scale.md`](references/rare-disease-scale.md) §4b.

### A14 — nothing had ever checked the layers against each other · **closed, and it falsified one of this audit's own claims**

The same defect had now appeared three times in three costumes — A11 (two readers of one
corpus, never compared), A13 (an authored crosswalk and a measured dossier disagreeing about
a disease's identity, never compared), and F3 (the fix for A11, implemented for exactly one
file). At that point the pattern is not three bugs; it is one missing **kind** of check.

Every layer here is careful about itself: each states its provenance, marks its confidence
and says what it cannot do. Nothing checked whether they **contradict each other**.
`tools/consistency.py` does, and it is a different class of test — not "is this number
right", which usually needs a source we do not have, but "do our own artefacts disagree",
which needs nothing external and is therefore always answerable. **A contradiction proves at
least one layer is wrong without requiring us to know which.**

Six layers indexed, 23 disease keys, **3 contradictions**:

| disease | field | authored says | measured says | verdict |
|---|---|---|---|---|
| CDKL5-deficiency disorder | ORPHA | `ORPHA:3095` | `ORPHA:505652` | **identity** — the codes name different diseases |
| Cystic fibrosis | prevalence | `1-5 / 10 000` | `1-9 / 1 000 000` | which band to quote |
| Duchenne muscular dystrophy | prevalence | `1-9 / 100 000` | `1-9 / 1 000 000` | which band to quote |

**And the join was the first thing that had to be audited.** The initial version deleted
punctuation instead of replacing it, so `CDKL5-deficiency disorder` and `CDKL5 deficiency
disorder` normalised differently and never met — and the ORPHA contradiction the file was
written to find went unreported. A weak join does not raise a false alarm; it produces
**silence**, and silence reads as agreement. Fixed, and the reason is in the function's
docstring.

**The finding that matters most is the one against this audit.** Two rounds earlier,
`references/rare-layers.md` recorded a pattern: *"in every case so far, where an authored
layer and a measured layer disagree, the measured layer is right."* The cystic fibrosis row
above falsifies it. Orphanet records four bands for CF; the authored lexicon quotes
`1-5 / 10 000`, which is what the disease is actually known at, and the measured dossier
quotes `1-9 / 1 000 000` because it exposes the **rarest** band — a single outlying report.
The measured layer is not wrong about the data. It leads with the wrong summary, and it does
so despite this repository having spent an entire sweep (A9) establishing that collapsing a
prevalence spread to one number is a category error.

The claim has been struck through rather than deleted, with the correction beside it. The
narrower version that survives: **where the disagreement is about a fact, measured has won
every time; where it is about which summary to expose, being measured buys nothing.**

*Consequence, still open:* the dossier's headline prevalence tile leads with `rarestBand`.
It is honestly labelled — "Prevalence, rarest band on record" — but a tile is read before
its label, and the spread beneath it is the better headline. Changing which band leads is a
judgement about what a reader should see first, so it belongs in an ADR rather than in a
commit.

### A15 — the periphery is 6.5× the core, and none of it uses the core · **open, and it is the structural finding of this audit**

Every previous entry is a defect inside something. This one is about the shape of the whole
repository, and it was found by asking the dullest possible question — *how much of this is
the library?*

| | lines |
|---|---|
| `src/sieve/` — the library the project is named after | **1,627** |
| `analyses/` — the two runs that use it | 571 |
| `tools/` — the rare-disease layers | **10,506** |

**Of 29 files in `tools/`, not one calls the statistics.** Nine import from `sieve`, and
every one of those imports `sieve.pipeline.sources.BY_KEY` — the download registry. They use
the package as a module of file paths. `fit_null` and `calibrate` are called from exactly
three places: the two analyses, and `figure_data.py`, which re-implements the resampling
inline and says so in a comment.

**And the ten stages are two.** `src/sieve/stages/` holds `null.py` (Stage 1, 310 lines) and
`design.py` (Stage 10, 334 lines). Stages 0, 2, 3, 4, 5, 6, 7, 8 and 9 — Objective, Power,
Confound, Baseline, Validation, Prior, Shortlist, Report, Repro — have **no
implementation**. They are a table in the README, a section in `methodology.md` and a
subsection in the manuscript. The README's Status paragraph does say Stage 1 and the
contracts are what is implemented, so nothing here is *undeclared*; what is undeclared is
the **ratio**, and the ratio is the finding.

**Why this is the honest answer to "it's still shallow."** This audit ran five sweeps in one
day and every one of them deepened the periphery: the population axis, the disease panel,
the evidence atlas, the layer map, the cross-layer check. All real, all measured, all
documented — and **none of it touches the argument the project exists to make.** A reader
who came for "turn a large, noisy, confounded screen into a defensible shortlist" finds one
stage of ten implemented and ten thousand lines of rare-disease cataloguing beside it. The
depth went somewhere; it did not go into the claim.

**Two readings, and the repository has to pick one.**

1. *The library is the project* and the rare-disease work is an application of it. Then the
   application should **use** it — the evidence grades, the prevalence spread and the trial
   power layer are all Stage 2 and Stage 6 arguments made in `tools/` with hand-rolled
   arithmetic rather than through the stages, and the eight missing stages are the backlog.
2. *There are two projects here.* A calibration library, and a rare-disease evidence atlas
   that shares its download registry and its documentation discipline. Both defensible; the
   atlas is arguably the more finished of the two. But then the README, which presents one
   project, is misdescribing the repository — and `docs/expansion-map.md`'s scope rule
   ("an entry that does not fit gets deleted, not stretched") is being applied to references
   and diseases while the repository itself is exempt from it.

This is a decision, not a defect, so it goes to an ADR rather than a commit. It is recorded
here first because the decision cannot be taken by someone who has not seen the ratio.

*What would resolve it:* one of the eight missing stages, implemented and used by a
rare-disease layer that currently hand-rolls the same reasoning. Stage 2 (Power) is the
obvious candidate — `tools/dossier.py` already computes minimum detectable effects inline
(A12b), which is Stage 2 written twice: once as prose in `methodology.md` and once as
arithmetic in a tool, with nothing in the library between them.

#### Done, for one stage · `src/sieve/stages/power.py`

**Stages implemented: 2 of 10 → 3 of 10**, and for the first time a `tools/` layer calls the
library for something other than a file path. The extraction gained the part a script did
not need and a stage does — the **per-entity form**, `underpowered(counts, effect)`, because
a screen has one sample size per entity and that is the premise the whole library rests on.

Three things came out of it that the inline version could not have produced:

1. **A published number moved, for a stated reason.** Duchenne's under-powered trial count
   went 96 → 90. The inline code treated any trial below n=4 as under-powered; the stage
   separates *under-powered* (90) from *too small to assess* (6 — enrolments of two and
   three). Merging them let a count of rumours pass as a count of weak studies. The floors
   themselves are unchanged, and `tests/test_power.py` now pins them.
2. **A boundary case that rounding had hidden.** The first version rounded the floor inside
   the model, so `min_detectable_effect(49)` returned exactly `0.800` when the true value is
   `0.80045` — on the wrong side of the large-effect line. Rounding is now presentation
   (`.at()`), not arithmetic.
3. **The stage refuses rather than approximates.** An unlisted `alpha`, a sample below four,
   a proportion below five expected events: each raises `PowerError` instead of returning a
   plausible number. A power calculation quietly done at the wrong alpha is the class of
   error this stage exists to catch, so the stage must not be able to commit it.

**Still open:** stages 0, 3, 4, 5, 6, 7, 8 and 9, and the choice A15 poses about what this
repository is. One stage does not settle that — but it does mean the answer is now being
argued with code rather than only with prose.

### A16 — the reference bases were too weak to catch what they were meant to catch · **closed for one source, and it immediately paid**

Raised by the user, and correct: the project audits identifiers against catalogues it had
not downloaded. `tools/ecosystem.py` had been reporting the gap all along — thirteen public
resources named, **five ingested, eight not** — and the consequence was visible on screen as
soon as the identifier matrix was rendered: a whole column of MONDO checks reading
`unverifiable`, which is honest and useless.

**Six sources added, ~793 MB, every URL resolved before it was written down.** A registry of
broken links would be A11 in a different medium, so each was checked with a HEAD request
first; HGNC belongs in the list and is absent from it because none of its published
endpoints resolved on the day, and a source that 404s is not registered as if it worked.

| source | MB | the open question it closes |
|---|---|---|
| MONDO | 53 | the `unverifiable` column in `lexicon_check.py` |
| Reactome (2 files) | 118 | which signalling module a gene is in — `rare-disease-mechanisms.md` §4's Stage 7 claim |
| STRING | 83 | whether our modularity 0.861 is biology or curation — `rare-disease-mechanisms.md` §5.2 |
| gnomAD v4.1 constraint | 95 | the Stage 6 prior argued for in `rare-disease-scale.md` §4 and warned about in `rare-disease-ancestry.md` §3 |
| ClinVar | 442 | the variant layer this project does not have at all |

**MONDO was wired in immediately, and one ontology turned a blank column into four
defects** — including one disease that had been *clean* before:

| disease | MONDO id | what MONDO calls it | verdict |
|---|---|---|---|
| CDKL5 deficiency disorder | `MONDO:0010726` | **"Rett syndrome"** | **WRONG DISEASE** |
| Zellweger spectrum disorder | `MONDO:0019234` | "peroxisome biogenesis disorder" | **WRONG DISEASE** (a parent term) |
| Spinal muscular atrophy | `MONDO:0001516` | "spinal muscular atrophy" | **GRANULARITY MISMATCH** |
| Dravet syndrome | `MONDO:0100135` | "Dravet syndrome" | **GRANULARITY MISMATCH** |

CDKL5 is now condemned by **two independent identifier spaces**: its ORPHA code resolves to
*Atypical Rett syndrome* (A13) and its MONDO term to *Rett syndrome*. That is no longer an
inference from one catalogue.

**And ingesting MONDO made a check possible that no amount of care could have produced
without it.** Every other field in that file asks *does this id exist?*. MONDO carries
`xref:` lines to ORPHA and OMIM, so it can be asked the harder question — **do this row's
three identifiers describe the same disease?** A row can carry three ids that all resolve
and still name three different things, and nothing before this could see it. That is what
found Dravet, which passed every existence check.

**Two kinds of conflict, separated deliberately.** The first pass called all four
`CROSS-REFERENCE CONFLICT`, which buried the worse one. When MONDO's name matches the
disease, the ids are at different *granularity* — a broad grouping paired with a narrow
subtype, a real crosswalk defect that silently changes which population a join means. When
MONDO's name is a different disease, the row points at the wrong thing. Those need different
fixes and now carry different verdicts.

*Still open:* Reactome, STRING, gnomAD and ClinVar are on disk and not yet read by anything.
Each has a named question waiting for it, listed in the table above — which is the honest
state to leave them in, and a better one than being named in a document and absent from the
machine.

### A17 — the weakest published claim was tested against new data, and held · **closed**

The first of the four newly-ingested sources (A16) was read, and it was chosen because it
could **prove this project wrong**: `rare-disease-mechanisms.md` §5.2 named its own §2 as
*"the weakest claim in the document"* and stated the falsifier — our modularity excess might
be measuring HPO curation rather than biology, since our graph makes a *k*-clique out of
every disease with *k* genes.

STRING has no disease labels in its evidence base. Same method, same Louvain, same seed:

| graph | modularity | null | excess |
|---|---|---|---|
| STRING ≥ 700 | 0.6822 | 0.1409 | **0.5413** |
| STRING ≥ 900 | 0.7727 | 0.1976 | **0.5751** |
| ours (HPO) | 0.8605 | 0.1617 | **0.6988** |

**The claim survives**, at 77 % of our excess, and strengthens as edge confidence rises. It
does not vindicate the magnitude: ours is still higher, and the clique construction is the
obvious explanation for the gap. The write-up says both, and §5.2's falsifier is struck
through with the result rather than deleted.

**One note on process, because it is the finding under the finding.** The comparison code
first reported *"nothing to compare against"* — it read `real.modularity` where the artefact
stores `real.structure.modularity`. A comparison that silently finds no comparand returns a
clean-looking null result, which is the exact failure mode this file was written to expose,
committed inside the file exposing it. It is fixed and the reason is in the source.

*Still unread:* Reactome, gnomAD and ClinVar. Each has its question waiting in A16's table.

### A18 — the library's founding claim, measured on 10,377 real patients · **closed, and it is the strongest result in this audit**

The project had no patient-level data at all, and the reflex answer — that rare-disease
patient data is entirely access-controlled — turned out to be false for a real corner of the
field. `phenopacket-store` (Monarch, BSD-3-Clause, 19.4 MB) carries **10,377 individual
patients across 780 diseases from 1,733 publications**, in the GA4GH standard, each with
their own HPO terms and a causative variant.

**The detail that makes it decisive:** a phenopacket records phenotypes that were
*explicitly absent* as well as present — 65 % of the assertions in a sample. An excluded
term is a patient who was examined and did not have the feature, so a frequency can be
**computed** as `observed / (observed + excluded)`, with the denominator the curated record
almost never has (A12b: 56.1 % of diseases carry no fraction of any kind).

**19,534 disease-feature pairs get a real denominator. 16,276 are comparable to the
catalogue, and in 91 % of those the PATIENT set has the larger one.**

Then the result that matters, grouped by the denominator **the catalogue** used:

| curated denominator | pairs | curated mean | patient mean | overstated ≥ 20 pts |
|---|---|---|---|---|
| **n = 1** | 354 | **0.932** | **0.436** | **65.2 %** |
| n = 2–4 | 6,489 | 0.700 | 0.684 | 3.5 % |
| n = 5–19 | 7,417 | 0.439 | 0.444 | 2.5 % |
| n ≥ 20 | 2,016 | 0.322 | 0.342 | 4.0 % |

**The bias is entirely concentrated at n = 1 and vanishes as the denominator grows.** A
`1/1` frequency reads 100 % and the patients say 44 %. At n = 2–4 the gap is 0.016; at
n ≥ 20 it reverses sign.

That is `docs/methodology.md` **Stage 1**, appearing in a place the library was never aimed
at. A `1/1` frequency is a *selected observation* — the first patient written up is not a
random patient, and the feature that got them written up is the one most likely to be
recorded. Selecting the largest of a few noisy estimates is positively biased, and the bias
shrinks with n. The repository has spent this entire audit arguing that from resampled
nulls; this is the same curve measured against people.

**It also retroactively strengthens A12 and A12b.** Those found the dossier rendering
single-case reports as if they were measurements, and graded 19,460 annotations as
`single-case` across the catalogue. The grade was defended as *uninformative*. This shows it
is worse than uninformative: at n = 1 the curated value is wrong in a **known direction**,
by roughly half.

**Limits, stated as prominently as the finding.** phenopacket-store is built from published
case reports, so it carries publication bias in full and is not a population sample. Both
sides read the same literature — which is what makes the comparison meaningful and what
stops either side being a population frequency. And 1,529 pairs have the larger denominator
on the *curated* side; there the curated value is the better estimate. The table reports the
direction of a bias across thousands of pairs, not a verdict on any single annotation.

Full account, plus the access plan for the tiers that are **not** open (dbGaP, EGA, UK
Biobank, RD-Connect) and the four things that must exist in the schema before any of them
can be accepted, is in [`references/patient-data.md`](references/patient-data.md).

### A19 — the patient extraction was reading a third of the record · **closed**

A18 read 10,377 phenopackets and kept the disease plus observed/excluded phenotypes. A field
census showed the rest was there all along: **allelic state on 100 %** of genomic
interpretations, gene on 99 %, ACMG class on 98 %, VCF coordinates on 94 %, sex on 92 %, age
on 77 %. The project has had per-patient **genotype** on disk and was reading phenotype only.

`tools/patient_variants.py` reads it — 11,454 variants, 699 genes — and the finding is the
**allelic spectrum**: the median gene has **66.7 %** of its variants seen exactly once, and
**189 of 699 genes have every variant private to one patient**. NF1 (405 patients, 42
variants, one allele shared by 107) and STXBP1 (462 patients, 259 variants, 81 % private) are
both "the causal gene" in every catalogue here, and the evidence behind those words is not
the same kind of thing.

**And a check of mine was wrong in an instructive way.** The first inheritance cross-check
flagged 65 diseases as "declared recessive, no homozygous patient" — which is the *expected
signature of compound heterozygosity*, since a recessive patient with two different variants
is two heterozygous calls and never a homozygote. 61 of the 65 were exactly that. The code
carried a comment stating this while the rule did the opposite; a check that fires on the
normal case is not a check. Moved to the patient (a recessive diagnosis explained by **one**
heterozygous variant), skipping diseases with both modes declared: **4 flagged** instead of
65, each backed by 4–9 patients.

**Two selection effects now recorded beside every patient number.** All 11,243 ACMG
classifications are `PATHOGENIC` — phenopacket-store holds *solved* cases, so it is an
answer key, not a diagnostic pile. And `vitalStatus` appears on 707 patients of whom **every
one is DECEASED**, with `ALIVE` never recorded: a death register that would return a 100 %
mortality rate to anyone who mistook it for survival data.

### A20 — the two patient halves were joined, and Stage 2 changed what the result means · **closed**

A18 read the phenotypes, A19 the genotypes, and neither joined them — although the join is
the only thing an aggregate catalogue cannot do at all. `tools/genotype_phenotype.py` splits
each gene's patients by loss-of-function versus missense and tests every feature assessed in
both groups: **510 comparisons across 31 genes**, Fisher exact, Benjamini-Hochberg.

**The finding that belongs to this repository rather than to genetics: only 40 of the 510
tests — 8 % — could have detected a 50-point difference at these group sizes.** That is
`sieve.stages.power` called *before* any p-value is read. 470 comparisons are incapable of
the result they are being asked for, and reporting those as "no difference" would convert a
sample-size limit into a biological claim. The real negative is the other column: **38
powered and null.**

**And the method validates, which is what makes the negatives worth anything.** Six results
survive correction and they are known biology recovered blind — most cleanly **LMNA
lipodystrophy: 0/14 in truncating patients against 120/206 in missense**, which is exactly
the published split (missense causes familial partial lipodystrophy; truncating LMNA causes
cardiomyopathy and muscular dystrophy). GNAS subcutaneous ossification and SETD2
macrocephaly reproduce their known directions too. Nothing in the pipeline was told any of
this.

**Two design choices worth naming.** Patients who could not be assigned were excluded rather
than forced — 277 carried both a truncating and a missense allele, 69 had more than one gene
— because pushing ambiguous cases into a group puts them exactly where the comparison is
being made. And the multiplicity correction is there because picking the smallest p-value
out of 510 is a selection operator, which is this library's founding argument applied one
level above itself.

**This is also the second `tools/` layer to call the library** (after `dossier.py`, A15). The
periphery is beginning to use the core it sits beside.

### A21 — ClinVar read in full, and it disagrees with a fifth of our answer key · **closed**

The last big unread source, and the longest extraction the project has run: **9,048,962
rows, 4,490,695 on GRCh38**, one pass over 442 MB.

**The field's own evidence, graded by the field itself.** ClinVar supplies a review status,
which makes it the one corpus where the evidence grade arrives *with* the data instead of
having to be invented for it (contrast A12, where the grades had to be built):

| | |
|---|---|
| uncertain significance | **52.0 %** — over half the corpus |
| pathogenic + likely pathogenic | 7.9 % |
| conflicting classifications | 166,053 — laboratories disagreeing in writing |
| at **one star or less** | **84.6 %** (3,799,044 of 4,490,695) |
| at four stars (practice guideline) | **54** |

**And the cross-check, which is why this was worth the runtime.** The phenopacket corpus is
an answer key: all 11,243 of its ACMG classifications are `PATHOGENIC` by construction
(A19). Looking those same coordinates up in ClinVar:

| what the field says | variants |
|---|---|
| pathogenic / likely pathogenic | 3,254 — **79 %** |
| **uncertain significance** | **470** |
| **conflicting** | **313** |
| likely benign / benign | 27 |
| **absent from ClinVar entirely** | **1,587 — 28 % of the corpus** |

**About a fifth of the answer key is not confidently pathogenic to the rest of the field**,
and more than a quarter of it is not in ClinVar at all. That does not make the published
cases wrong — a variant can be causative in a family and unsubmitted, and ClinVar lags the
literature. It does mean every rate this project computes over that corpus inherits a
classification the wider field has not confirmed, and now says so with a number.

This is also the strongest available argument for the caveat A19 attached to the patient
layer: an answer key is a fine thing to measure, as long as nothing calls it the truth.

### A22 — the package declared a console script that did not exist · **closed**

`pyproject.toml` has declared `sieve = "sieve.cli:main"` since the project began, and
`src/sieve/cli.py` **did not exist**. Any `pip install -e .` installed a `sieve` command
that raised `ModuleNotFoundError` on its first run. A broken promise in the package
metadata, and one that nothing in the repository could have caught: the test suite imports
`sieve`, never the entry point.

Found while building Stage 7, which needed somewhere to live. The CLI now exists, and
`sieve stages` is deliberately built so it cannot lie about what is implemented — it
*imports* each stage module and reports the ImportError if there is one, rather than reading
a hand-maintained list.

*Fix worth having:* a test that resolves every declared console script. Two lines, and it
would have failed on day one.

### A23 — Stage 7 implemented, and the model refuses to be a score · **closed**

The first stage this project has built to be **used by other people on their own data**:
`sieve.stages.target`, gene-editing target assessment in rare disease, with `sieve target`
as the entry point. **Stages implemented: 3 of 10 → 4 of 10** (Null, Power, Shortlist,
Design).

**The design decision is a refusal.** Every comparable tool emits a ranking — a druggability
score, a tractability index, a composite of normalised axes. This emits none, for the reason
`dossiers.json` has carried in its own caveat since long before the stage existed: a
composite requires deciding *how many uncertain variants are worth one recurrent allele*,
and nobody has that exchange rate. What it emits instead is **which editing strategies the
gene's own variant spectrum admits, and which gate it fails** — and every threshold is an
argument to `assess()` rather than a constant, so a reader who disagrees can move it.

Five strategies (allele-specific editing, base editing, exon skipping, gene replacement,
knockdown) each with what rules it out; four gates, one per relevant stage. The axes are all
measured elsewhere in this project and read here: the allelic spectrum from A19, the VUS
share from A21, pan-essentiality from the DepMap adapter's own `is_common_essential` flag.

**Two properties worth naming, both enforced by tests.**

1. **`None` means unmeasured and blocks; it never means zero.** A gene with no essentiality
   data must not come back as knockable. Most of the 19 tests assert a *refusal*, which is
   unusual and deliberate — a target model that always produces an answer produces one when
   it should not.
2. **`shortlist()` refuses to claim diversification without a module map.** Reactome is
   ingested and unread (roadmap 1.1), so it prints *"Stage 7 diversification COULD NOT BE
   CHECKED — this shortlist may be one hypothesis with several gene names"* rather than
   returning a list that merely looks diversified. That is the failure the stage is named
   for, refused inside the stage itself.

**And it is the third `tools`-or-CLI surface to use the library** (after `dossier.py` and
`genotype_phenotype.py`), which is A15 continuing to close: the periphery is using the core.

*Thin, and reported as such:* the quantified-endpoint axis is not yet joined per gene, so
most assessments fail the Power gate with `unmeasured`. That is the model working, not
failing — it says the evidence to clear the gate has not been assembled.

### A24 — F1 built at last, and it found drift on its first run · **closed**

**F1** was proposed in the first sweep and left unbuilt through twelve more, while the exact
failure it described happened twice:

  * **A1** — `CITATION.cff` advertised a `−4.09` anomaly that had been fixed, in the header
    block a citing author copies.
  * **A11** — three documents read `770` ultra-rare diseases while the artefact said
    `4,586`.

Both were caught by a person reading carefully. **A person reading carefully is not a
control**, and the repository already knew what the control looks like: `paper_numbers.py`
generates every figure in the manuscript from a manifest, so a LaTeX number cannot drift.
Markdown had no equivalent, which is precisely where both defects landed.

`tools/verify_claims.py` is that equivalent — a checker rather than a generator, because
prose is not LaTeX. Each registered claim names an artefact, a path into it, a formatter and
the documents that cite it, and the check is two-sided: **the artefact must still produce the
value, and every listed document must still contain it.** A renamed key fails it too.

**It found three real problems on its first run, and none of them were the ones being looked
for:**

1. **`references/rare-layers.md` had gone stale within a day of being written.** The document
   whose entire job is to be the complete map of `out/rare/` was missing four artefacts —
   the whole patient layer and ClinVar — created after it. A map that is not complete is
   worse than no map, because it reads as exhaustive.
2. **`references/patient-data.md` §3c still said ClinVar was "on disk and unread".** False
   since the previous sweep, in the paragraph arguing for reading it.
3. **The checker itself was wrong.** It demanded the literal string `52.0` and flagged
   `52 %` as drift. A verifier that fails on typography teaches people to disable it, so a
   formatter now returns *every acceptable rendering* — precision still enforced,
   presentation not.

**It is now a control, not an inspection.** `tests/test_claims_match_artefacts.py` runs the
registry as 24 parametrised tests, including a guard on the guard: a test that fails if the
registry stops covering a layer that carries headline numbers, because a checker that can be
silenced by deleting its input is not a control either. And `verify_claims` joined the
`check` submission gate beside `paper_numbers` — a gate that checked the paper and not the
documentation was checking the smaller half.

**What it cannot do**, stated so a green suite is not mistaken for a guarantee: it checks the
22 registered claims and nothing else. A figure nobody registered can still drift.
Registering a claim is part of publishing it.

### A25 — the full review, and what it confirmed · **closed**

The thirteenth sweep was a verification pass rather than a new layer. Beyond A24:

- **The pipeline still builds.** Eight stages were stale — correctly, because editing
  `patient_variants.py` invalidated `genotype_phenotype`, which is the source-code-as-input
  tracking working. Re-running them **did not move a single published number**, confirmed by
  the drift check rather than by eye.
- **DepMap held exactly.** After `depmap` and `figures` re-ran (triggered by
  `stages/power.py` and `stages/target.py` changing), every headline is unchanged:
  `nonessential_mean_z 0.036`, `common_essential_mean_z 9.452`,
  `count_spearman_calibrated −0.0377`, `null_blocks gene`.
- **The submission gate works, and currently refuses.** `tasks.py check` fails on **27
  unverified references** in `paper/refs.bib` — which is A5, unresolved since the first
  sweep, doing exactly what a gate should do: stopping the line rather than letting an
  unverified bibliography ship. *Jidoka*, on the manuscript.

**100 tests**, 27 pipeline stages, 0 broken links, and for the first time a documented number
cannot silently disagree with the artefact that produced it.

### A26 — A6 closed after fourteen sweeps, and the intervals corrected two published sentences · **closed**

**A6 is the oldest open finding in this audit.** It was raised in the first sweep — the
repository had produced *exactly one* confidence interval in its life while
`references/standards.md` §4 adopts GUM, which says in one line that **a difference smaller
than its own interval is not a difference**. Thirteen further sweeps each published new
point estimates and left it open. This one closes it.

`tools/intervals.py` puts a 95 % interval on every headline. **Seven of eight survive
comfortably.** The eighth is the one that mattered, and it needed a second attempt.

| claim | point | 95 % interval |
|---|---|---|
| prevalence class disagrees across countries | 0.735 | [0.696, 0.771] |
| diseases with a sign from a real series | 0.397 | [0.388, 0.405] |
| diseases with no fraction at all | 0.561 | [0.552, 0.570] |
| ClinVar uncertain significance | 0.520 | [0.520, 0.521] |
| ClinVar at one star or less | 0.846 | [0.846, 0.846] |
| our variants not confidently pathogenic | 0.211 | [0.199, 0.224] |
| comparisons powered for 50 points | 0.078 | [0.058, 0.105] |

**And the interval corrected two sentences that were already published**, both in the
direction of a tidier story — which is the direction error always takes when nobody is
computing bounds:

| curated denominator | difference | 95 % CI | what had been written |
|---|---|---|---|
| **n = 1** | **−0.497** | **[−0.591, −0.387]** | stands, and is now bounded |
| n = 2–4 | −0.016 | [−0.026, −0.008] | stands |
| n = 5–19 | +0.005 | **[−0.000, +0.011]** | presented as part of a trend; **there is no detectable difference at all** |
| n ≥ 20 | +0.020 | [+0.005, +0.038] | *"if anything, slightly conservative"* — the hedge was wrong, it **excludes zero** |

The shape that survives is sharper than the one first published: **enormous at n = 1, small
but real at n = 2–4, undetectable at n = 5–19, and slightly reversed above 20.**

**The first attempt at the interval was wrong, and the failure is worth recording.**
`intervals.py` initially bootstrapped the *worst-disagreement head* that
`patient_frequencies.json` ships — 25 pairs selected for having the largest differences —
and returned **−0.98**, a number that would have flattered the claim enormously. Resampling a
head that was selected for an extreme returns that extreme: a tautology wearing an interval.
The bootstrap moved to `patient_frequencies.py`, where all 16,276 comparisons live.

**The resampling unit is the disease, not the pair**, and that is not a detail. Two features
of one disease share patients, a curator and usually a publication. Bootstrapping pairs as
independent would have narrowed every interval above in the direction that flatters the
claim — which is precisely the defect that produced a z of −4.09 here for two months
(`lineage.md` §8a, ADR 0004), committed a second time in a different file.

**What still has no interval, and why.** The six statistics in `bias.json` — ascertainment
+0.2357, panel coverage −0.2469, and four others — are rank correlations over joins that
`intervals.py` cannot reconstruct from the artefact, because `atlas_bias.py` publishes the
statistic and not the per-disease vectors behind it. They are listed in `intervals.json`
under `notMeasured` rather than left to look bounded. **A6 is closed for the headline
figures; those six are its remainder**, and the fix is a change to `atlas_bias.py`, not to
this file.

### A27 — the direct methodological ancestor is uncredited, and this project rebuilt what it already had · **closed as a finding, open as a debt**

Found by surveying the reference roots the author pointed at. It is the most uncomfortable
entry in this audit and it is not a code defect.

**`nominator` (`C:\Users\yuri\Documents\code\nominator`, Apache-2.0, 921 lines) is the
direct methodological ancestor of `sieve`, and `sieve` mentions it nowhere.** Same thesis,
same ten stages — nine of them `nominator`'s, renumbered by the insertion of Stage 1 (Null),
which is `sieve`'s genuine contribution and the source of every headline in this repository.
But the frame around it was inherited, and `references/standards.md` §4 requires every
borrowed claim to appear in `CITATION.cff` *and* `lineage.md`. `nominator` is in neither.
**The rule was written for other people's work; it applies to your own.**

**And it had what this project spent fourteen sweeps rebuilding.**

```python
# nominator/core/validation.py
def bootstrap_ci(a, b, stat=spearman, n_boot: int = 2000, seed: int = 0) -> dict:
```

**A6 was closed yesterday (A26) by writing a bootstrap from scratch.** The ancestor shipped
one. The same file also carries `leave_one_entity_out`, `cold_start_split` and
`orthogonal_validation` — the leakage-safe splitting `sieve` Stage 5 describes in prose and
does not implement.

**This restates A15, and the accurate version is worse.** A15 read *"eight of the ten
headline stages have no implementation"*, which frames them as a backlog. `nominator`
implemented **all ten in 921 lines**; `sieve` has four in 1,627. The eight were not unbuilt,
they were **not carried over**. Nothing on disk records that as a decision — which is the
answer: it was not one, it was a restart.

**Two siblings carry numbers this project has never produced.**

- **`F:\CODE\climate`** opens with the constraint rather than the method: *"n = 36,
  SE(RPSS) ≈ 0.10–0.15, o erro padrão é da ordem do sinal inteiro. Consequência: não existe
  arbitragem empírica entre modelos."* That is Stage 2 promoted from a gate to the thing
  that governs the architecture — the same conclusion A26 reached for rare disease, reached
  first and acted on harder.
- **`F:\CODE\adia`** measures its own optimism: board TS-AUC **0.5910** against a local
  holdout of ~0.60, an optimism of **≈ +0.013**, with the stated direction *"regularizar/
  podar … não adicionar"*. `sieve` has no equivalent measurement of its own optimism, and
  spent this session adding.

*The debt, and it is small to pay:* one `CITATION.cff` entry and one `lineage.md` section.
*The larger item:* porting `nominator`'s `validation.py` is cheaper than writing Stage 5, and
`roadmap.md` Tier 1 was priced as though it were greenfield. Full survey in
[`references/prior-work.md`](references/prior-work.md).

### A34 — the project had no derived account of itself, and writing one found two false sentences · **closed**

Asked for a checklist of where the work stands. A hand-written one was the wrong answer, and
this repository has the evidence three times over: `CITATION.cff` advertised a resolved
anomaly as open (A1), `sieve.stages.target` called four calibrated thresholds "a judgement"
(A28), and `lib/palette.ts` said **VALIDATED** while citing a validator that was not in the
repository (A33). Every one is prose asserting a state nobody could recompute, and a progress
checklist is the most tempting possible instance of it.

So `tools/status.py` computes the checklist and `docs/status.md` is its output. It reads the
pipeline registry, the filesystem, the audit log, the ADRs, the threshold manifest, the doc
headers and the web build, and it is wired into `_check()` — the submission gate — through
`--check`.

#### What it found on its first honest run

**Two sentences that were true when written and false now**, which is the class nobody
re-reads:

  * `analyses/nf2_subgroup.py` logged *"deletion is not counted here (OmicsCNGene.csv, 1.4 GB,
    **not fetched**)"*. The file has since been downloaded: **1.39 GB, on disk, still unread
    by that analysis.** The limitation stopped being a missing download and became an unmade
    decision — a worse thing to leave unstated, not a better one.
  * `docs/methodology.md` opened by naming its worked example as `docs/case-studies/obesity.md`.
    **That document was never written.** The material is in `lineage.md`; the citation had
    been pointing at nothing since the file was created.

And several facts nobody had assembled:

  * **17 files are ingested and referenced nowhere in the source**, including every one of the
    per-disease ClinicalTrials payloads and `AchillesScreenQCReport.csv` — which
    `docs/references/deep/depmap-methods.md` explicitly recommends as a Stage 3 covariate.
  * **4 of 14 registered thresholds were calibrated to data already seen** (A28's number,
    now recomputed rather than remembered).
  * **15 of 36 documents** lack the header `.claude/skills/sieve-doc` mandates.
  * **7 audit findings are open**, and **2 ADRs are still `proposed`**.

#### Three defects in the measuring instrument, all found by disbelieving it

A status tool that lies is worse than none, so each number was checked against what it should
be before being published.

**It reported 35 of 40 data files as never read.** False. Most of this repository reads inputs
as `BY_KEY["clinvar"].dest`, never naming a file, so a detector that understood only literal
filenames declared almost everything untouched — a report lying in the most damaging direction
available, since "we have never looked at this" is the finding that provokes work. Now the
registry keys are resolved, and the answer is reported in **three states rather than two**:
`read` (a read call was found), `untouched` (the name appears nowhere at all), and, between
them, *referenced with no direct read site* — because `CRISPRGeneEffect.csv` is opened inside
an adapter that receives a directory, and calling the repository's primary input unread would
have been a confident inversion of the truth.

**It reported 128 contradictions, of which 126 were its own fault.** Citations here are written
relative to the citing file as often as to the root, and a path into an ancestor project
(`core/validation.py`) is not a broken link but a reference to somewhere this checkout cannot
see. It also flagged sentences that *state* an absence — this file's own account of the
missing palette validator. After resolving against the citing directory, ignoring first
segments that are not directories of this repository, and reading a window of context rather
than one line, **128 became 2, and both were real.**

**It scanned its own output.** Every "never read" row it wrote put a filename next to an
absence phrase, so the next run reported each of its own rows as a contradiction — a report
that manufactures findings about itself, one per row, growing every run.

**And it counted three permanent entries as stale.** `ecosystem`, `pipeline_state` and `check`
are verification stages that never cache by design; reporting them as stale padded the
headline with a number nobody could ever clear. 7 stale became 4.

`tests/test_status.py` holds the two invariants that matter: no contradictions, and the
rendered document still matches the generator. *That test also failed on a correct document
first* — it asserted `**7**` where the renderer writes `**7 open**` — and a guard that cries
wolf is a guard that gets deleted, so it was corrected rather than the document.

### A33 — the interface was never opened in light mode, and the palette's "VALIDATED" cited a file that did not exist · **closed**

A review pass over the cancer section, looking rather than adding. Four defects, and the
last two are the same defect as A28 in a different medium: **a check that is described but
never runs.**

#### Light mode had never been rendered

All of this section was built in a dark browser. In light mode `--r-text-3` — the token
carrying the lede, every panel subtitle, every axis note and every KPI caption — measured
**3.34–3.64:1** against a 4.5:1 requirement. `--unknown`, which carries the warning states and
the "you have moved off the registered value" marker, measured **3.05:1**. Twelve token/surface
pairs failed in total; dark mode had one marginal failure at 4.46.

Fixed by lightness only — hue and chroma are what make the palette recognisable, and neither
needed to move. `web/scripts/check-contrast.mjs` now resolves every text token against every
surface it can legally sit on, in **both themes**, and fails the build. It checks the tokens
rather than a rendered page deliberately: a page test needs a browser and covers only the
routes someone remembered to visit, while the token pairs are the whole space.

#### The palette said it was validated by a validator that was not in the repository

`lib/palette.ts` carried: *"VALIDATED. The categorical scale passes the six checks against
both grounds (`scripts/validate_palette.js`, adjacent pairlist)."* **That file did not
exist.** The numbers could not be reproduced or re-checked after an edit.

Its replacement failed the scale on its first run. Under a deuteranopia model, series 1
(yellow) and 4 (red) sat at **dE 1.4 in dark** and 3.8 in light — the same colour, for roughly
8 % of men, in a scale documented as validated. The six hues are kept; the lightness
assignment is now the one that clears CIEDE2000 ≥ 12 for **every** pair under normal,
deuteranopic and protanopic vision while each series holds 3:1 against its own ground.
Measured worst pair: **15.0 light / 16.0 dark**.

The cost is named in the module rather than hidden: lightness is no longer near-uniform, so
the six series do not carry identical visual weight. Red-green deficiency collapses exactly
the channel that six well-spread hues rely on, and lightness is the only axis left.

*The 24-hue identity scale added in A31 had never been checked in any vision model.* It
passes — worst adjacent pair dE 10.8 under protanopia — but that was luck, not method.

A related fix in the same family: the **chips** in the shared-dependency panel used an
identity hue as their *text* colour. That scale is defined at a constant lightness so 24 hues
read as one family, which is a mark colour, not a type colour. The hue moved to the border and
a dot; the label went back to a text token.

#### Five controls claimed `role="tab"` with no tabpanel anywhere on the page

No `aria-controls`, no ids, no keyboard model. A screen reader announced "tab, 1 of 2" with
nothing to move to, and the arrow keys a tablist promises did nothing. **Declaring a role is a
promise about behaviour**, and this one was pure assertion.

They are not tabs — a tab swaps a panel; these choose which question is being asked and
re-render the page beneath. `components/atoms/ChoiceGroup` implements the correct pattern: a
radio group, one tab stop via roving `tabindex`, arrow keys wrapping at both ends, Home and
End, and focus following the selection.

Two smaller ones in the same panel: the false-discovery slider is backed by an **index** into
a non-linear step list, so it announced "3 of 5" — the position, not the 0.05 a reader is
setting; it now carries `aria-valuetext`. And the range inputs were **24px** tall against a
44px touch-target floor.

#### And the keyboard fix exposed a worse bug than the one it was written for

With arrows working, the second arrow press did nothing and focus jumped to the document root.
The subgroup level is the **fetch key**, so changing it returned `loading`, the page rendered
its skeleton, and *everything unmounted* — including the control the reader had just operated.
Focus was lost, scroll was lost, and a keyboard user could change the level exactly once
before having nothing left to press. **A filter that destroys the page it filters is not a
filter.** `useRemoteData` gained an opt-in `keepPrevious`: the previous level stays readable
and is marked stale while the next loads.

*Not verified:* the narrow-width layout. The browser tool would not resize the viewport after
two attempts, so the responsive rules were reviewed statically and not rendered. An ad-hoc
in-browser contrast probe also returned results I could not reconcile with the deterministic
gate, and is not being reported as a pass — what is proven is the token gate.

### A32 — 1.47 GB of genotype on disk, unread, and two confounds under it · **closed**

`OmicsSomaticMutationsMatrixDamaging.csv` (141 MB) and `OmicsCNGene.csv` (1.33 GB) have been
in `data/depmap/` since the first ingest and **neither had ever been opened**. A31 grouped
cell lines by their Oncotree *label* — which is a name someone assigned. `tools/cancer_genotype.py`
groups them by **genotype**, which is a property of the cell and the grouping a target
programme actually acts on.

#### The confound was stated before the run, and it was the right one

Mutation status is not independent of lineage: BRAF mutants are melanoma, VHL mutants renal,
APC mutants colorectal. So a naive mutant-versus-wild-type contrast is partly a *lineage*
contrast wearing a genotype's name. It is handled by design — every pair is estimated twice,
naive and stratified within lineage then pooled by inverse variance (the continuous-outcome
Cochran–Mantel–Haenszel) — and **the difference between the two is reported**, because the
size of the confound is more informative than either estimate alone.

The prediction written before the run was that paralog synthetic lethality should *survive*
stratification and lineage-concentrated oncogene addiction should *shrink*. On the half that
could be tested it held:

| pair | mechanism | naive | lineage | burden-adj. |
|---|---|---|---|---|
| SMARCA4 → SMARCA2 | paralog synthetic lethality | 0.97 | 0.93 | 0.98 |
| ARID1A → ARID1B | paralog synthetic lethality | 0.88 | **0.96** | 0.90 |
| TP53 → MDM2 | dependency *lost* (negative direction) | −1.58 | −1.57 | −1.58 |
| RB1 → E2F3 | released cell-cycle dependency | 1.24 | 1.43 | 1.34 |

ARID1A → ARID1B is the interesting row: stratification made it **larger**. Lineage was
*masking* that effect, not inflating it, which is the outcome a disclaimer could never have
produced and a stratified estimate does for free.

#### Half the control set was inconstructible, and the prediction did not notice

KRAS, NRAS and CTNNB1 came back **not testable**; BRAF had 9 mutant lines and PIK3CA 6,
against the ~100 melanoma lines carrying V600E. The matrix counts **damaging** variants —
truncating, frameshift, splice — and **an activating hotspot is not damaging**. This is a
loss-of-function matrix, and the oncogene-addiction half of the prediction cannot be asked of
it at all.

That is a fact about the data source, discovered by the control set rather than by reading the
column definition, and the rows are kept in the artefact marked untestable rather than
deleted: *"the data cannot answer this" is a result about the data, and deleting the question
hides it.*

#### A second confound nobody designed for: mutational burden

`WRN` — the canonical microsatellite-instability synthetic lethality — came back for MSH3
**and** for SEC31A, KMT2B, MBD6 and CTCF. Hypermutated lines carry damaging mutations
everywhere, so a long gene becomes a synonym for "this line is hypermutated". **92 of 121
drivers** are flagged: their two arms separate by a large effect on burden alone. The top of a
frequency-ranked genotype list is mostly not genotype. This is the pan-essential confound one
level up.

**And it must not be adjusted away**, which is the part worth keeping:

* For **MSH3**, burden is a **mediator** — MMR loss *causes* instability *causes* the WRN
  dependency. Conditioning on it deletes a correct finding, and does: 1.69 → 0.82.
* For **SEC31A**, burden is a **confounder**. Nothing connects it to WRN but hypermutation.

The arithmetic is identical and **the data cannot distinguish them**; only the mechanism can.
So the burden-adjusted estimate is published beside the others and never substituted for them.
A third state was added when the diagnostic turned out to lie: SEC31A and BRAF separate so far
on burden (3.82 and 3.52) that **only one tertile contains both arms**, so there is nothing
left to compare. They now report **"not separable from burden"** rather than passing — calling
that a pass would rest the strongest available claim on the weakest available evidence.

#### The interface: gates as controls, and what that immediately exposed

Every shortlist here is the output of three thresholds, and a reader who can only see one
setting cannot tell a robust finding from one balanced on the cut. The gates are now live
controls over a wider candidate pool the artefacts ship, with settings carried in the URL.

Because ADR 0006 exists to record whether the data had been seen when a number was chosen, and
**a reader dragging a slider has seen the data**, the panel marks itself the moment any control
leaves its registered value and keeps saying so until reset. The warning travels in the link.

The panel also reports **which gate is binding** — how many candidates each one excludes
*alone* — and the first thing it said was uncomfortable:

> For Skin, **26 of 40 candidates fail on the Stage 0 dependency floor and nothing else. The
> other two gates exclude 0 between them.**

At the registered values, the false-discovery rate and the effect-size cut are doing **no work
at all**; the entire shortlist is decided by the gate added mid-A31 as a self-correction. Two
conventional statistical thresholds are inert decoration on this data, and only a control that
reports its own bindingness could have said so.

#### And it caught a third truncate-then-filter

The panel drew **14 rows beside a sentence saying 15**. Candidates were collected in
descending effect under the loose gate, and since 26 of them fail only the floor, those
high-effect floor-failures filled the 40-slot window and pushed the 15th registered hit
outside it — so the pool could not reproduce the analysis's own answer at the analysis's own
thresholds. Nothing errored.

This is the same defect as A12's `[:24]` and A31's top-60 scan, in a third place, which is now
difficult to read as bad luck. The pool is a **union** with the registered hits, an assertion
fails the run rather than shipping a pool that cannot reproduce them, and
`tests/test_candidate_pools.py` holds the invariant on the artefacts so it cannot regress into
a cap again.

### A31 — DepMap is the reference application and had never been asked the subgroup question · **closed**

`Model.csv` has shipped with every DepMap release this project has used. It carries three
nested levels of subgroup — 35 `OncotreeLineage`, 96 `OncotreePrimaryDisease`, 254
`OncotreeSubtype` — and **not one line of this repository had ever read any of them**. The
adapter loaded the 428.7 MB dependency matrix and scored 17,916 genes across 1,178 cell lines
**as one pool**, which answers "what is broadly essential": the question whose top is 60 %
pan-essential genes, and the one every calibration result here is a correction to.

`tools/cancer_subgroups.py` asks the other question — which gene does *this* cancer depend on
that others do not — and it is the first analysis in the repository to run several stages of
the library on a single question. Stage 3 removes 1,242 pan-essentials **before** ranking
rather than flagging them after; Stage 2 reports, per subgroup, the smallest effect its size
could detect, so a small cancer with no hits is reported as **underpowered rather than as
negative**. At the subtype level that is 27 of 37 subgroups.

**The result validates blind.** No gene was supplied to the ranker. Skin returns SOX10, BRAF,
MAPK1, DUSP4; Bowel returns TCF7L2, CTNNB1, KRAS; Peripheral Nervous System returns ISL1,
LDB1, GATA3, MYCN — the neuroblastoma core regulatory circuit; Kidney, Ovary and Uterus all
return PAX8; Bone returns FLI1; Eye returns MDM2, MDM4 and PPM1D; Rhabdoid Cancer returns
SMARCD1. Of nine pre-named positive controls, five came back with a rank and four did not, and
the four are published as `null` in the artefact rather than folded into a pass rate.

**And it produced a finding about grouping itself.** Pooled `Lung` has 126 screened lines —
the best-powered subgroup in the analysis — and returns **nothing at all**. Split at the
subtype level, Lung Adenocarcinoma returns KRAS and Small Cell Lung Cancer returns SKP2,
CKS1B and E2F3, the RB1/E2F axis that defines SCLC. They were cancelling. *A null result at
the coarse level is not evidence of no dependency; it can be evidence of the wrong grouping* —
and it is the argument for the level switch being part of the analysis rather than a
convenience in the interface.

#### Two defects on the way, and the second is the instructive one

**Truncate-then-filter, again.** The first ranking scanned the top 60 genes by effect size and
*then* applied the dependency gate. The genes with the most extreme effect are largely the
artefact the gate exists to remove, so the gate emptied the window and the real lineage
dependencies — moderate effect, genuine dependency — never entered it. This is audit A12's
`[:24]` in a different file, which suggests the lesson did not generalise the first time.

**The sign.** `load_matrix` returns a **sign-flipped** matrix. Its own docstring says so —
*"dependency is negative in DepMap; sieve wants larger-is-better"* — and the dataclass exposes
a `flipped` field for the purpose. Two consecutive runs ignored both and ranked the
**anti-dependency**. The output was not obviously broken: it returned plausible gene names,
in plausible numbers, per subgroup. What caught it was a positive control: SOX10 in Skin came
back at a mean of **+1.261** and was read as "not a hit", when +1.261 in a flipped matrix *is*
the melanoma lineage dependency — the single most canonical result in the dataset.

The orientation is now **read from `.flipped`** and the run aborts if the adapter changes
convention, and `CONTROLS` is checked on every run and published in the artefact. The general
form is worth stating: a sign error is the failure mode that survives review, because it
produces a well-formed answer to the opposite question. Nothing but a control with a known
direction distinguishes it from a result.

*Also closed by this:* `_run_tool` in the pipeline silently discarded any argument a stage
passed it, so the three-level stage would have produced the lineage level three times. It now
forwards argv.

### A28 — two practices transferred from sibling projects, and both found something · **closed**

A27 established that this repository has ancestors on the same machine. This sweep read the
two deepest — `F:\CODE\adia` (204 files) and `F:\CODE\climate` (102) — for practices
rather than results, and ported the two that close real holes here.

#### From `adia`: determinism as a tested constraint, not a seed

`adia` submits to a platform that **re-executes 10 % of the data and compares at a tolerance
of 1e-8**, so its architecture note states the rule as a hard one: *"infer() deve ser 100 %
determinístico — sem np.random, sem dropout, sem MCMC, sem wall-clock."*

This repository lists **Stage 9, Repro** among its ten headline stages — *"an artifact
nobody, including you, can regenerate"* — and had **twenty-eight stages, several seeded, and
nothing checking that a rerun produces the same output**. A seed in the source is an
intention; a rerun is the observation.

`tests/test_determinism.py` reruns five stages and compares content hashes. All five
reproduce exactly. **And its guard found a gap on the first run**: a test that every seeded
tool must be either covered or excluded-with-a-reason flagged `tools/figure_data.py`, which
resamples the null to build the figure series that **both the manuscript and the explorer
read**. A non-deterministic figure there would let the paper and the dashboard disagree with
the analysis they claim to render. It is now covered, and it passes.

The exclusion list is itself tested — a tool may be excluded only by name and with a reason,
and a test fails if an excluded tool stops existing, so the list cannot decay into a record
of what someone once decided not to check.

#### From `climate`: pre-registration, and the label that incriminates this project

`climate` freezes its feature-reduction rule in a dated manifest carrying `target_contact:
false`, with the consequence stated as a rule: *"Alteração motivada por resultado observado
no alvo INVALIDA o experimento."* Its acceptance criterion is an interval — the lower bound
of a 90 % CI — because *"'RPSS positivo' pontual não significa nada com n=36"*.

**This repository had the habit and not the mechanism**, and the gap was one day old.
`sieve.stages.target`'s four thresholds were all chosen **after** the allelic spectrum and
the VUS distribution had been printed. By `climate`'s standard they are not pre-registered;
they are calibrated to data already seen, and nothing said so.

`manifests/thresholds.yaml` (ADR 0006) now registers every gate this project acts on with
the one field that matters — whether the data was seen when the number was chosen — and the
honest summary is uncomfortable:

> **7 thresholds: 3 pre-registered, 4 calibrated to seen data.**
> By kind: 1 mechanistic, 3 empirical, 3 conventional.

Relabelling them would have been worse than having no manifest: a mechanism whose first act
is to hide the distinction it exists to show is decoration.

**The test forced an improvement in the scheme.** Two justification kinds — *mechanistic*
and *empirical* — could not classify the NF2 positive-control gate, which is neither derived
nor read off the data: it is arbitrary, but arbitrary **before looking**. A third kind,
*conventional*, now covers it and Cohen's 0.8. The test also rejected two rows where the
manifest pointed at the wrong module, and forced the NF2 gate to become a **named constant**
rather than `0.25` inline twice — an arbitrary number that decides whether a shortlist ships
should be visible.

*Still open:* `climate`'s third practice — **an acceptance criterion written before the
result** — is adopted in ADR 0006 part 3 and used nowhere. Every interval this project
published on 2026-08-28 was computed before anyone said what would have counted as success.

### A29 — five measured layers existed on disk and were rendered nowhere · **closed**

Raised by the user, and an audit of the build script confirmed it: `patient_frequencies`,
`patient_variants`, `genotype_phenotype`, `clinvar_evidence` and `intervals` were **generated
and never emitted to the interface.** The entire patient-level body of work, plus the
confidence intervals that bound it, was reachable only by opening a JSON file.

That is the same failure as A3 (the layer map that omitted four artefacts) and A24 (the
prose that drifted from them), in a third medium. **A dashboard that renders twenty aggregate
catalogues while its strongest result sits unpublished is publishing that result nowhere.**

**Three views, and each uses a form this app did not have.** The choice is load-bearing —
in every case the conventional chart destroys the thing being shown:

| view | form | what a conventional chart would lose |
|---|---|---|
| the single-case bias | **forest plot** | a bar chart of four point estimates hides that one interval **crosses zero**, which is the finding |
| catalogue against patients | **scatter with the identity line** | the single-case pairs form a vertical stripe at x = 1.0 spanning the whole y range; no summary statistic renders that shape, and the shape is the argument |
| the ClinVar cross-check | **Sankey** | one category splitting into many — a stacked bar shows the same numbers and loses the "from one thing into many" reading that *is* a cross-check |

**The forest plot is the one that mattered.** The intervals arrived a day after the point
estimates and corrected two published sentences (A26). Rendering a point estimate without
its interval would have put the dashboard back where the prose was **before** that
correction — so the n = 5–19 row is drawn in neutral grey with an `INCLUDES ZERO` mark,
where the other three carry their direction's colour.

**Payload discipline:** `clinvar_evidence.json` is 2.3 MB, of which 13,528 per-gene rows are
read by `sieve.stages.target` from disk and never by a browser. The build script's projection
table gained nested-path support so it ships **4 kB**.

*One defect found and fixed while looking:* the forest axis rendered
`-0.6416200000000001` — floating-point noise presented as precision, in a chart whose entire
subject is how precise a number is.

### A30 — the twin's first dynamical rung, and it recovers known biology blind · **closed**

`tools/thesis_seed.py` encodes the research thesis this repository serves, and it is explicit
about the object: *"modelar distúrbios ultra-raros como sistemas dinâmicos multiescala …
**simular a propagação de perturbações**"*. Its own audit grades the ladder that needs:

| rung | before | after |
|---|---|---|
| genotype | built | built |
| protein structure | named-only | named-only |
| conformational dynamics | named-only | named-only |
| **interactome** | **partial** | **built** |
| pathway | partial | partial |
| cell state | partial | partial |
| tissue and space | absent | absent |
| patient | built | built |

**Every layer in this project until now was a static description** — what is known, how well,
about whom. None propagated anything. `tools/twin_propagation.py` is the first that does.

**Two identifier bridges had to be ingested first**, and without them the twin is three
disconnected pictures: STRING is keyed on Ensembl protein ids, Reactome on UniProt
accessions, HPO on gene symbols. `9606.protein.info` (2 MB) and `9606.protein.aliases`
(20 MB) are the join. **16 sources, ~921 MB.**

**The method is the smallest honest dynamical step.** Random walk with restart over STRING at
score ≥ 700 — 16,201 genes, 236,930 edges — seeded on a disease's causal genes. Stationary
diffusion, not a simulation over time, *because the rungs beneath it are still named-only and
a time-resolved model standing on a named-only rung is an animation rather than a twin*.

**And the null is the whole discipline.** A walk from any seed set reaches hubs, because hubs
are what a random walk finds. Reporting the top of a propagation without a degree-matched
null measures the graph and calls it the disease — Stage 1's argument on a different object.
So every target is propagated against **200 degree-stratified seed sets**, and every value
published is a z against that null, never a raw score.

**It recovers known biology in every disease, blind:**

| disease (seed) | top reached | why that is right |
|---|---|---|
| NF2 (`NF2`) | **SCHIP1**, TRAF7 | *schwannomin-interacting protein 1* is named for binding merlin; TRAF7 is a co-driver in meningioma |
| Alkaptonuria (`HGD`) | **GSTZ1**, FAHD1/2 | GSTZ1 is the **next enzyme** in tyrosine degradation |
| Sickle cell (`HBB`) | **HBA2**, HP, HPR, NFE2 | the partner globin chain, haptoglobin which binds free haemoglobin, and the erythroid factor |
| Cystic fibrosis (`CFTR`+18) | **ANO1**, ANO2, CLCA2 | the alternative chloride channels — the actual therapeutic bypass target |
| Dravet (`SCN1A`+6) | ARX, **CDKL5**, SLC25A22 | the other developmental epileptic encephalopathy genes |

Nothing in the pipeline was told any of this. A method that recovers known biology blind is
one whose *unknown* results are worth reading — which is the only reason to build a twin at
all.

*Stated in the artefact, not only here:* this is **not** a simulation of disease progression.
There is no time, no rate constant and no direction of causality in an undirected
co-functional graph. It answers *"if this gene is perturbed, what else is implicated"* — a
reachability question wearing a probability.

### A4 — `methodology.md` still mixes Diátaxis modes · **open, acknowledged debt**

Known and declared in the documentation standard itself (*"that is a known debt, not a
licence"*). Unchanged. Recorded here only so it is counted rather than grandfathered: it
has now survived two reviews as a declared exception, which is the point at which a debt
starts behaving like a decision.

### A5 — most references are still unverified working knowledge · **materially improved**

`docs/references/README.md` carried a blanket warning: *"entries below are recorded from
working knowledge and are **not yet link-checked**."* `lineage.md` carries the same ⚠ on
its left-hand column. For a repository whose entire argument is *do not trust an
unverified number*, an unverified bibliography is the sharpest available irony.

**Improved in this pass, not closed.** Every reference introduced by the three new
documents was resolved through the Crossref API before it was written down —
title, authors, venue, year and DOI, not memory:

```bash
curl -s https://api.crossref.org/works/10.1038/s41431-019-0508-0
```

Fifteen DOIs verified this way, listed in `CITATION.cff`. The **pre-existing** entries
remain unverified, and the ⚠ stays until they are run through the same call. That is a
mechanical, scriptable job — see F2.

### A6 — no uncertainty on most published numbers · **closed 2026-08-28, see A26**

`standards.md` §4 adopts GUM: *a difference smaller than its own interval is not a
difference.* The repository has produced exactly **one** confidence interval — the 4,000-
resample paired bootstrap that settled anomaly (b), `[−0.0344, −0.0271]`. Every other
headline number is a point estimate: `0.036`, `9.452`, `−0.0377`, `0.2357`, `−0.2469`.

Some of these are descriptive counts over a complete catalogue and need no interval. Some
are rank correlations over samples and **do**. `bias.json` reports six findings with a
`verdict` field taking values *real / small / untestable* and no interval anywhere; the
verdict is doing the work an interval should be doing.

*Fix:* the machinery already exists — `tools/multiplicity.py` imports scipy, and the
bootstrap that settled (b) is written. Applying it to the six bias statistics is the
highest-value open item in this list, because those six are the numbers the new
`rare-disease-scale.md` and `-equity.md` documents now lean on.

### A7 — the `-scale` claims sit on a catalogue whose own bias is measured but not propagated · **open**

`tools/atlas_bias.py` does something admirable: it turns the library's argument on the
library's own reference data and finds five real biases and one untestable one. Nothing
downstream then *uses* those numbers. The atlas coverage figure (74.4 % of diseases have a
known gene) is quoted as a fact about the world when the same file has just shown that
"has a known gene" correlates +0.2357 with how much attention a disease received.

The honest form is a range or an explicit conditioning statement, and the new
`rare-disease-scale.md` states it that way. Propagating it into `atlas.json` itself is open.

**And the second sweep made this worse, correctly.** A9 shows the bias is not only in *how
much* a disease was studied but in *where* — Europe 8.10 against Africa 0.07. A coverage
figure of 74.4 % is a coverage figure for the populations that were looked at.

### A8 — the ⚠ files named as missing in the doc standard now exist · **closed, standard is stale**

`.claude/skills/sieve-doc/SKILL.md` §5 marks `archive/MANIFEST.md` as *"this file does not
exist yet"* and `docs/adr/` as *"that directory is empty"*. Both are false as of this pass:
the archive holds back-filled dead ends with the number that killed each, and the ADR
directory holds four decisions, one of which was scored correct. **The skill file is the
thing that is now out of date.** Left as a finding rather than edited, because a skill file
is user-owned configuration.

---

## 3. Two mechanisms worth building

Both findings above that closed *stayed* closed only because a person happened to look.

**F1 — bind prose numbers to the manifest. ✅ BUILT 2026-08-28, see A24.** `tools/paper_numbers.py` already does this for
LaTeX: no number is typed into the manuscript; each is a macro generated from
`out/*.manifest.json`, and a missing one fails the build loudly. Markdown has no equivalent,
which is why A1 could happen. The cheapest version is a checker, not a generator: a script
that greps `README.md`, `CITATION.cff` and `docs/**` for numbers registered in a manifest
and fails when a quoted value no longer matches its source. *Jidoka* applied to prose.

**F3 — assert that two readers of one file agree.** A11 existed because two parsing paths
over `en_product9_prev.xml` disagreed for months and nothing compared them. The test is
cheap and would have failed on day one: parse the prevalence classes with `ElementTree` and
with the regex, and assert the multisets are equal. Generalised: any file read by more than
one tool gets one test asserting the readers agree on a summary statistic.

**F2 — a reference verifier.** Every DOI in `CITATION.cff` resolved against Crossref, with
title and year compared to what the file claims. Stdlib-only, no key required, ~40 lines.
This retires the ⚠ in A5 permanently instead of one document at a time.

Neither is written. They are recorded here so that the next pass is measuring against a
stated intention rather than re-deriving it.

---

## 4. What this pass deliberately did not do

- It did not touch `src/`. The internal-audit lane owns the statistics, its verdict stands,
  and the fix it demanded is in place and tested.
- It did not re-run the DepMap or NF2 analyses. Every number quoted above was read from the
  manifests on disk; if those are stale the pipeline's own `describe()` will say so, and
  `tools/pipeline_state.py` publishes that staleness to the dashboard.
- It did not resolve §9 of `lineage.md` — whether NF2 is a `sieve` demonstration or simply a
  good analysis that does not need Stage 1. That is a scientific question, not a
  conformance one, and it is the most important open item in the project.


---

### A36 — a body of work landed with no audit entry, and the indexes did not move · **closed 2026-08-29**

**What happened.** On 2026-08-29 the repository gained one ADR, three reference documents,
four tools, four pipeline stages and two ingested sources. Nothing in this file mentioned any
of it, and six indexes still described the state of the day before: `rare-layers.md` mapped 26
of 34 artefacts while its own header said 34, `tools/README.md` advertised 14 sources when 18
were registered, `README.md` and `adr/README.md` both said one construct was measured when
three were, and `audit.md` itself said four of seven thresholds were calibrated when the
manifest held nineteen with five calibrated.

**Why it matters, and it is the same failure as A11.** An index that lags the work is not a
cosmetic problem in this repository: the indexes are how a reader decides what has been
measured. A file that says twelve of twenty-five layers are measured, when eighteen of
thirty-four are, understates the project in the direction that makes its strongest claims
invisible — which is exactly the shape of A2.

**Root cause.** Nothing links the addition of an artefact to the documents that are supposed
to enumerate it. `tools/verify_claims.py` protects a *number* once registered; no control
protects a *list*. The four new numbers were registered on the same commit that published
them, which is the practice A1 asked for, but their existence in the layer map was not.

**What was done.** Every count above corrected against the filesystem and `out/status.json`;
the eight unmapped artefacts added to `rare-layers.md` with grades; this entry written.

**Closed the next day by `tools/index_check.py`.** The checker described below now exists: it
enumerates artefacts, tools, stages, sources and ADRs and fails when one appears in no index.
**Its first run found sixteen of the eighteen ingested sources named nowhere at all** — not a
stale count but a whole table that had never been written. That is the same shape as
`verify_claims.py`, which also found drift on its first run, and it is the argument for
building the control rather than promising to be careful.

**What it cannot do, and this half stays open.** It checks PRESENCE, never accuracy. A stale
sentence beside a present filename is a real defect and only a reader can see it. The tool
prints that limitation with its own result rather than letting a green line imply more than
it means.


---

### A37 — the read-site detector under-reports, and one attempt to fix it made it worse · **open**

**What it is.** `tools/status.py` decides whether an ingested file has ever been *read* by
walking each module's AST for a read call whose argument resolves to a filename. It currently
reports **eight** ingested files with no read site. At least two of those are read:
`gnomad.v4.1.constraint_metrics.tsv` by `tools/gene_world.py:127` and
`rna_single_cell_type.tsv.zip` by the same module at :165 and by `gene_datasheet.py:132`. Both
use the shape `path = DATA / "name.ext"` followed by `path.open(...)`.

**The diagnosis, which is probably right.** The detector keeps one filename per variable name,
and `path` is rebound in several functions of the same module, so all but the last resolve to
the wrong file.

**The attempted fix, and why it is not in the repository.** Mapping each name to a *set* of
filenames should have been strictly more permissive. It made the count **worse — eight to
eleven** — and newly flagged `CRISPRGeneEffect.csv`, which is beyond doubt read. That means the
detector's behaviour is not explained by the diagnosis above, and shipping the change would
have traded a known under-report for an unexplained one. Reverted.

**Why this matters more than the number.** `docs/status.md` is generated precisely so the
repository cannot lie about itself, and here it does: it says nobody has looked at a 95 MB
file that a shipped tool reads. "We have never opened this" is the finding that provokes work,
so an under-report in this direction is the expensive kind.

**The test now exists** — `tests/test_read_site_detector.py`. Four cases pass, including the
one that matters most: a path that is merely NAMED must not count as read, which is the
property any permissive "fix" would destroy and the reason the last attempt made things worse.
**Two cases are marked xfail with the reason**, so the defect stays visible in the suite
without turning it red — a skip would have hidden it, and a red suite trains people to ignore
red. A fifth case asserts this finding is still recorded here, because an xfail is invisible
in a passing run and that is exactly how a defect becomes permanent.

**Still open:** the fix itself. The test is the instrument, not the repair.

### A38 — a five-agent review, and the six defects it found in one day · **closed**

*2026-08-30.* Five parallel read-only reviews were run over the repository — method against
implementation, statistics, determinism, a full tool catalogue, and scaling. Every finding
below was **verified independently before it was fixed**, and three findings from the reports
were discarded because they did not survive that verification.

**A published field that changed between runs.** `tools/language_coverage.py` iterated a set
of organ-system ids and took `min`/`max` over it, which return the FIRST extreme they meet.
Python randomises string hashing per process, so a tie returned a different id each time.
Measured directly: with `PYTHONHASHSEED=7` the Spanish best system was `HP:0000152`, with 99
it was `HP:0001507`. The same class was found and fixed in `genotype_phenotype.py` and
`patient_frequencies.py`. **A seeded RNG is not reproducibility if the thing being iterated
has no order** — the same lesson as the `gene_constraint` incident earlier the same day.

**A bootstrap that resampled into a set.** `tools/autism_convergence.py` built each replicate
as a set comprehension over draws with replacement, so duplicates collapsed and every
replicate held about 1 − 1/e of the genes — measured, 454 of 717. The statistic is a share and
is biased in set size, so the published interval belonged to a different statistic than the
point it bracketed. Point estimates and z values were unaffected; the four interval bounds
were not. The corrected pathway interval **now overlaps its null mean**, which the wrong
narrower one did not, and the verdict string — which carried its bounds as literals — is
computed from the arms and says so.

**Four parsers for one 53 MB ontology.** `gap_taxonomy`, `lexicon_check`,
`single_cell_coverage` and `tropical_gap` each hand-rolled OBO parsing over `mondo.obo`, and
`tropical_gap` bypassed the source registry entirely. Unified into
`src/sieve/pipeline/ontology.py`. The swap corrected a published figure: the old crosswalk
used a `defaultdict` and wrote a key for every OMIM term it saw, then published the total
under the name `omim_terms_with_counterpart` — 10,176, of which **6,321 had no counterpart**.
Every gap classification is byte-identical, so the finding was untouched.

**A manifest that miscounted itself.** `manifests/thresholds.yaml` exists to make threshold
provenance auditable and its own summary said "pre-registered: 3, calibrated: 4". It was
written when the file held seven entries; the file grew to 25 and the summary did not move.
Real counts: 19 and 6. `index_check` now recomputes them.

**A p-value that was a draw.** Splitting a shared RNG in `scale_information.py` left the three
scale figures byte-identical and moved the morphogenesis p from 0.0185 to 0.00625 — far
outside the sampling error 20,000 permutations give. Its INPUT had moved: the test reads the
per-system retention table, itself estimated against permutation nulls. Over five
re-derivations: 0.00625, 0.00715, 0.00955, 0.0196, 0.02185. The conclusion is robust (no seed
crosses 0.05) but **the single figure was one draw from a distribution nobody had declared**.
Now published as a median with its range.

**And the largest: a maximum compared against the wrong expectation.** `tools/gene_geometry.py`
published a clustering ratio on every gene page — the densest of 55 overlapping windows over
the share ONE fixed window would hold. Simulated with variants placed uniformly at random and
no clustering at all: ratio **3.00 at n=10, 2.00 at n=50**. The median gene carries 39
variants and the panel fired its headline at 1.5×.

| | |
|---|---|
| called clustered by the old rule | **2,637 of 2,771 — 95.2 %** |
| clears a null fitted at the same n | **1,005 of 2,771 — 36.3 %** |

This is the library's own thesis — maxima are biased and the bias grows as observations fall —
violated by one of its own tools, which had skipped Stage 1 on itself. Now calibrated against
a null fitted per observation count.

**Two mistakes of the fix itself**, both caught before shipping: a ratio was put in a field the
panel renders as a percentage, and removing a misplaced block took a loop's indentation with
it and emptied every histogram — found because the output returned zero clustering records
instead of 2,771.

**Still open from this review**, in order of damage: 44 tools have no test, the worst being
`knowledge_shape`/`knowledge_void`; five independent Orphanet prevalence readers remain, the
configuration that caused A11; and `status.py`'s `web_rows()` is the one confirmed
super-linear check, scanning the whole web source once per artefact.

*Updated 2026-08-31.* The z of −270.51 named above is no longer the reason to distrust those
two tools — **A41 explains it**. Their null's spread is 0.95 on a count centred at 575, so the
z is a statement about a denominator rather than about the world. The underlying shortfall
(318 occupied cells against 575 expected) stands and is one of the strongest measurements
here. They still have no test, which is the part that remains open.

### A39 — the documentation's strongest operational promise was false · **closed**

*2026-08-30.* `docs/references/rare-layers.md` said: *"Every layer is a pipeline stage, so
staleness is tracked and a stale artefact is not silently served."* That is the strongest
operational promise the documentation makes, and it was false for **24 of the 64 tools that
write an artefact**. Those are run by hand and nothing detects that they have gone stale
behind an input that moved.

The worst is `build_atlas.py`: `dossier`, `atlas_bias`, `capability_math` and `gene_index` all
read its output as an **undeclared dependency**, so a change to the atlas leaves four
downstream artefacts stale with nothing to notice.

The sentence is corrected to what is true, with the count in it. `tools/index_check.py` gained
a `staging` family that holds every artefact-writing tool to being either a registered stage
or exempt with a stated reason — and the exemption list marked the 24 unregistered ones
with ⚠️ rather than letting a green check hide them, so the debt was readable. The check was
verified to fail when an entry is removed.

**Paid the same day.** All 24 were registered, plus `analyses/obesity_thermogenesis.py`
and `build_atlas` itself: 26 new stages, each with declared inputs, outputs and `needs`.
`src/sieve/pipeline/paths.py` gained the 26 artefact paths, and `stages.py` a `src()` helper
that takes stage inputs from the download registry in `sources.py` rather than repeating
paths — the reason several of these stages would otherwise have declared no inputs at all,
and so never been stale.

The gene chain was eleven of the 26, and it is the part worth naming: `gene_index` →
`gene_world` → `gene_geometry`/`gene_domains`/`gene_datasheet` → `gene_insights`/
`gene_attention`/`gene_related` → `gene_facets`/`gene_space` → `gene_shards`. That order had
to be right or the artefacts are silently built from stale upstream files, and it existed
**only as a sentence at the bottom of each tool's docstring**. It is now an edge the runner
enforces. Three of the eleven — `gene_facets`, `gene_space`, `gene_shards` — had been exempt
on the stated ground that they are "derived in the same pass"; they are derived, and that is
exactly why the edge belongs in the graph rather than in a person's memory.

**The check was strengthened in the same move**, because the old one could not have caught
what replaced it: it asked whether a tool's NAME appeared anywhere in the text of
`stages.py`, which a comment satisfies. It now imports `STAGES` and asks two questions — is
this script some stage's `code`, and is the file it writes some stage's `outputs`. The second
is the one that bites: a stage with no declared outputs always runs and can never report
freshness, and nothing had ever tested for it. It also scans `analyses/`, which the grep
version did not, and which is where the obesity screen lives. Both arms were verified to fail
by deleting a stage and by deleting one stage's `outputs=`.

One ⚠️ entry remains: `capability_math`, which reads `build_atlas` output with no declared
edge. It is the whole of the outstanding debt in this family.


### A40 — three artefacts published a z with no interval, and paying the debt changed all three · **closed**

*2026-08-30.* `docs/references/standards.md` §4 requires every published number to carry its
uncertainty. An audit of the 55 bundled artefacts found **eight publishing a z and no
interval**, four of them written that same week. Four were exempt on shape — a run manifest, a
projection of it, a rendering, a calibration curve — and three were debt, recorded in
`Z_WITHOUT_INTERVAL` in `tools/index_check.py` with the resample each one needed written into
its own entry.

A z is a distance from a null's mean in units of that null's spread. It says nothing about how
far the observed value itself would move on a different sample. All three were paid, each with
the resample its entry named, and **each one changed what its artefact says**:

**`twin_propagation` — leave-one-out over the seed genes.** The seed sets are a handful of
curated causal genes, so a bootstrap with replacement over four of them draws the same gene
twice and calls it a replicate; the jackknife asks the honest version. A random walk with
restart is linear in its restart vector, so the k replicates cost k solves. 34 of 100
published reach genes keep a z above 1.96 at the bottom of their interval. **Not one of the
ten largest z values does** — the largest, DNASE2B at z = 1825, has an interval of
[−1753, +5403]. Seven of the eleven disorders have fewer than three seed genes in the graph
and get no interval at all, which is itself the finding.

The mechanism is measurable and it is a defect in the statistic this file publishes. The
degree-matched null exists so hubs cannot win by being hubs, and at that end it works. At the
other end it inverts: a gene of degree 5 is missed by almost every null draw, so the null's
spread there is near zero and any reach at all divides into an enormous z. **Ranking by z
selects the rarely reached** — median degree 8, against 15 for the interval's lower bound —
and those are exactly the genes whose intervals are widest. The artefact now publishes both
orderings, and for two of the four disorders that can be scored they share **no genes at all**:
cystic fibrosis gives ANO2, CLCA2, ANO1 by z and ALB, TMPRSS15, XPNPEP2 by lower bound; lupus
gives DNASE2B, DNASE2, CXorf21 against IFNG, CD28, PTPRC.

**`hiv_resistance` — bootstrap over isolates.** The entry said the resample had to be over
isolates because the carrier sets overlap, and that is what makes it worth doing: every
mutation is rescored on each resample, so the dependence survives. The drug is held at the one
the full data chose, or each draw would re-take the max over the panel and inflate the
interval with the selection Stage 1 exists to remove.

It found the assay's ceiling. The bootstrap returned a width of **exactly zero** for several
top-ranked mutations, which is not perfect precision: `100` is the most common value in the
dataset — **8.6% of every fold-resistance in the PI panel** — because the phenotype assay
reports ">100-fold" as 100. 13 of the 60 published mutations have every carrier at that
ceiling, including textbook majors 184V, 41L and 215Y. Their scores are equal by
construction, so **their order in the ranking comes from the permutation null, not from the
resistance data**. That is published as censoring rather than as a zero-width interval.

**`signal_energy` — bootstrap over diseases.** The negative verdict stands: 2 of 29 pathways
have an overall excess whose interval spans zero. The verdict is a difference of two family
means, and standards.md §4 says a difference smaller than its own interval is not one — so the
contrast now carries an interval computed from the members' own standard errors, with the
assumption stated: combining them treats pathways in a family as independent, which is false,
since they share diseases. The interval is therefore a lower bound on the width, and the
contrast clears zero by a margin an error a third wider would swallow. Reported as a direction
with a stated fragility, not as an established result.

**What this cost the reader, honestly.** Before this, every one of these three artefacts read
as a ranked list of findings. After it, one of them is a ranked list whose top ten do not
survive, one is a list whose top is at an assay ceiling, and one is a negative result whose
key contrast is fragile. Nothing was wrong that a rerun fixed; the numbers were always these.

### A41 — a z of 2,128, a z of −270, and what a permutation null can actually support · **closed**

*2026-08-30.* Giving `twin_propagation` an interval produced a finding about the artefact
rather than about the genes: not one of its ten largest z values kept a positive interval. The
cause was the denominator. A gene of degree five is missed by almost every draw of a
degree-matched null, so the spread there is near zero and any reach at all divides into an
enormous number.

That is a fact about **dividing by an estimated spread**, and this repository does it in nine
artefacts. `tools/z_audit.py` asks the question of all of them at once and finds
**3,166 published z values**, of which **871 are above 10** and **345 of those carry an
interval**.

**Three things make a z large, and only one is a finding.**

1. *A large effect against a well-estimated spread.* The finding.
2. *A degenerate null.* `knowledge_void` reports 318 occupied lattice cells against a null of
   575 with a standard deviation of **0.95** — under one unit, on a count — and publishes
   z = −270.51. The shortfall is real and is one of the strongest measurements here. The z is
   not a measurement of it; it is a statement about the size of a denominator. Two artefacts
   have a null whose spread is under 1% of its own centre: `knowledge_void` (0.00165) and
   `knowledge_shape` (0.00173).
3. *An extrapolation past what the null resolves.* A permutation null of N draws cannot
   distinguish any tail probability below 1/(N+1). At the 200 draws used almost everywhere
   here that floor is 0.005, about z = 2.58 under a normal reading. Every z past it is a
   distance the experiment measured, extended along a curve the experiment never sampled.

**A z carries its own error, and nobody had computed it.** The denominator is a standard
deviation estimated from N draws, whose relative standard error is 1/sqrt(2N) — 5% at 200
draws. So the propagation artefact's largest value of 2,128 carries a standard error of
**±106** before anything about biology is considered. That number now appears in the figure.

**What was paid.** `gene_constraint`'s inheritance arms published z = −25.72 and z = +9.63
against a tight null with no interval on the observed mean. Both now carry a bootstrap over
the member genes — a different resample from the length-matched null, and the difference is
the point: the null says how the statistic moves under the geometry, the interval says how the
estimate moves under the sample. All three arms survive:

| arm | observed | 95% | null | excludes the null |
|---|---|---|---|---|
| all disease genes | 0.8435 | [0.8325, 0.8545] | 0.8860 | yes |
| autosomal dominant | 0.6391 | [0.6165, 0.6618] | 0.8809 | yes |
| autosomal recessive | 0.9605 | [0.9472, 0.9738] | 0.8873 | yes |

That contrast is the reason to run the audit rather than assume its answer. The same treatment
destroyed the propagation artefact's top ten and left the constraint results standing.

**⚠️ The auditor invented a defect, again.** The first version of the interval detector carried
six literal key names and reported `knowledge_shape` as publishing z = −19 with no interval. It
publishes `mean_ci95`, which was not in the list. This is the same failure as the citation
audit that "found" nine articles with no notes when the real number was zero: a list of names
cannot see a name nobody thought of. The detector now matches by shape.

`python tools/z_audit.py --check` joined the submission gate, verified to fail by stripping the
intervals from a bundled artefact. The result is published as a section rather than filed here:
a site that reports 3,166 z values owes the reader the figure that says what they are worth.

### A42 — 2,408 communities from one run of one algorithm at one seed · **closed**

*2026-08-30.* `out/rare/gene_network.json` publishes **2,408 gene communities at modularity
0.8605**, and the number appears on the site. Every other statistic here carries a null and an
interval. This one carried neither, and three questions had never been put to it.
`tools/community_stability.py` puts all three, and takes this repository's first clustering
dependency to do it — igraph, leidenalg and scikit-learn, declared in `pyproject.toml`
alongside **networkx, which had been producing the published modularity since
`interactome_sparse.py` and was never declared at all**.

**Is it stable?** Twelve seeds of Louvain agree at **ARI 0.901 [0.888, 0.915]** — not 1, and
as low as **0.791** for one pair. Leiden 0.855, label propagation 0.819. The ARI is read
against a rewired graph with no communities to find, whose own runs still agree at **0.089**.

**Does the algorithm decide it?** Leiden and Louvain agree at 0.870. Label propagation agrees
with either at **0.29**. The modularity family agrees with itself and disagrees violently with
a method that has no objective function — so most of what separates these partitions is the
objective, not the graph.

**Was the resolution chosen?** No. Sweeping gamma from 0.25 to 3 moves modularity from 0.842
to 0.857 to 0.829 — a flat line — while the largest community falls from **777 genes to 192**
and the count of real communities rises from 201 to 238. The objective is nearly indifferent
across a range that changes the answer fourfold. The published partition inherited gamma = 1
from a default.

**What survives.** The membership. A consensus over the twelve runs gives every gene the share
of runs in which it sat with the partners the consensus finally assigned it: **83.2% of the
3,335 scored genes are at 0.9 or above** and 0.8% below 0.5. The 2,189 isolated genes are given
**no** confidence rather than a perfect one — scoring them 1.0 would have lifted the headline
by forty points on genes with no edges. That per-gene number is the interval this artefact
never had.

**Two things measured rather than assumed.** First, Louvain can return communities whose own
subgraph is disconnected (Traag et al. 2019) — checked here, and it **does not happen** on this
graph. The reason to add Leiden was that nothing had looked, not that Louvain had broken.
Second, the count itself: **2,189 of the 2,408 communities are single isolated genes**. A count
that is 91% singletons describes the ingestion, not the biology; the connected part carries
about 219.

**⚠️ The test found a defect in the tool the day it was written.** `tests/test_determinism.py`
failed the moment the tool landed, because it holds every seeded tool to being either
determinism-tested or excluded with a reason — the guard doing exactly its job. The tool is too
slow for the unit suite (161 seconds), so `tests/test_community_stability.py` checks the same
property on a planted-clique graph instead. Building that graph raised `IndexError`: the tool
assumed node labels were array positions, which is true of the CSR file it reads and of nothing
else. Positions are now computed once. The real artefact is byte-identical after the fix, which
is the point — the bug was latent, and only a test on a different graph could reach it.

---

## State of the work · 2026-08-31

*This section is a handover, not a finding. It records where the work stands and what the next
person — including a later version of me — would pick up, because a list that lives only in a
conversation is a list that does not survive one.*

### What the last two days did

Every entry from A39 to A42 came from the same move, applied five times: **take a number this
repository already published, ask what it is worth, and let the answer change the artefact.**

| | finding | what changed |
|---|---|---|
| A39 | 24 of 64 artefact-writing tools had no pipeline stage | 26 stages registered; the gene chain's run order became an edge instead of a docstring sentence; `gene_facets` was found **missing from disk entirely** — the browse index for 18,140 genes had never been generated |
| A40 | three artefacts published a z with no interval | all three paid. 34 of 100 propagation reach genes survive; the HIV shortlist's top is at an **assay ceiling**; `signal_energy`'s negative verdict now carries its own fragility |
| A41 | 3,166 published z values, never audited as a class | `tools/z_audit.py`. Two artefacts have a null whose spread is under 1% of its centre; a z of 2,128 carries ±106 from its own denominator |
| A42 | 2,408 communities from one seed of one algorithm | ARI 0.901 [0.888, 0.915] across seeds, 0.29 between algorithm families, resolution never chosen, and **83.2% of genes firm** in a consensus |

The pattern worth keeping: **the audits disagreed with each other, which is why they were worth
running.** The same interval treatment destroyed the propagation artefact's top ten and left
every arm of `gene_constraint` standing. An audit that confirms everything is measuring nothing.

### Open, in the order I would take them

1. **44 tools have no test.** The largest single risk in the repository. `knowledge_shape` and
   `knowledge_void` are the worst — not because of the z (A41 explains that) but because they
   are untested and feed a published headline.
2. **Five independent Orphanet prevalence readers.** The exact configuration that produced A11.
   One parser, as `ontology.py` already did for MONDO.
3. **`capability_math` reads `build_atlas` output with no declared edge** — the last ⚠️ entry in
   `NOT_A_STAGE`, and the whole of that family's remaining debt.
4. **`status.py:web_rows()`** scans the whole web source once per artefact; the one confirmed
   super-linear check.
5. **`docs/methodology.md` mixes Diátaxis modes** (A4), and **CARE is still not in the
   standards** (A10, ADR written).

### Two leads that are measured but not built

- **`data/hiv/INSTI_DataSet.txt` is HTML, not data** — a failed download saved under the name of
  the dataset it was meant to be. `status.py` reports it on every run. The INSTI panel is
  absent from `analyses/hiv_resistance.py` for that reason and nothing says so in the artefact.
- **The obesity screen's follow-on.** The 4.47M-pair interaction space and the gate finding
  (KIF11+NR3C1 scoring 1.1198 as pure synergy between two individually inert genes) need the
  16.8 GB `TF150.h5ad`, which is not on disk. Stage 1 on the challenge aggregate is built and
  published; the pair analysis is not started.

### How to verify a change here

```bash
python -m pytest -q                    # 162 tests
python tools/index_check.py --check    # nine index families
python tools/z_audit.py --check        # every loud z has an interval or a reason
python tools/verify_claims.py          # published numbers against their artefacts
cd web && npm run check && npm run build
```

`tasks.py status` says what is stale and why; `tasks.py build` runs it in dependency order.
The deploy is a GitHub Action on push to `main`.

### A43 — 38,746 edges the site had never drawn one of · **closed**

*2026-08-31.* `gene_network.json` has held 5,524 genes and 38,746 edges since the interactome
layer was built. The site reported it as three numbers — nodes, edges, modularity — which is
the least a graph can be reduced to, and A42 then measured that its partition agrees between
algorithm families at 0.29. Both are numbers about a picture nobody could see.

**The form is a reordered adjacency matrix** (Bertin 1967), not a node-link drawing. At this
density a force layout is a hairball: the picture is dominated by the repulsion constant, two
runs differ, and no distance in it can be read. A matrix draws every edge exactly once at a
fixed position with no parameter to tune, and puts the edges *between* communities in the open
instead of burying them in the middle. 3,335 × 3,335 is 11.1 million cells, so it is a canvas —
one typed-array pass per redraw, which is what makes switching the ordering instant.

**Three orderings ship, because the ordering is the argument** (ADR 0008). Measured as the
share of edges landing within 1 % of the diagonal:

| ordering | share | what it knew |
|---|---|---|
| consensus | **68 %** | was told where the communities are |
| spectral | **53 %** | was not |
| degree | **36 %** | the control |
| random | **2 %** | 20 shuffles |

The spectral ordering never sees the partition and still concentrates a majority of edges on
the diagonal. That is the evidence the blocks are in the graph rather than in the ordering that
assumes them — and `degree` is why the comparison needs a control at all: *some* structure
appears under any non-random ordering, and the question is always how much more.

**⚠️ Three defects, each caught by measuring rather than by looking.**

1. **The first spectral ordering was noise.** It ran the Fiedler vector over the whole
   edge-bearing subgraph, which has **191 connected components**. On a disconnected graph the
   Laplacian's zero eigenvalue has multiplicity equal to the component count, so the "second
   smallest" eigenvector is an arbitrary member of that null space. It looked plausible.
   Measured: **6.2 %** on the diagonal against 2.0 % for random and 35.6 % for degree — worse
   than sorting by degree. The caption drafted for it ("the blocks come back even without being
   told where they are") was false. Seriating each component separately fixes it, and the
   number is now published beside the figure so the caption cannot drift from it again.
2. **The eigenvector sign is arbitrary.** ARPACK returns −v as happily as v, which reverses the
   ordering and flips the matrix end for end while the caption describes the same structure.
   Canonicalised by the entry of largest magnitude.
3. **And that was not enough.** 1,584 of 3,335 positions still moved between runs, because
   ARPACK is iterative and starts from a vector SciPy draws from its own global random state.
   With eigenvalues as closely spaced as a Laplacian's smallest two it lands somewhere
   different each call. Fixed with an explicit `v0`.

All three were found by `tests/test_determinism.py`, which failed the moment the tool was added
to it — the same guard that caught `community_stability.py` the day before. A figure that
reorders itself between reloads while its caption stays the same is the worst kind of defect
this repository can ship, and nothing but a determinism test finds it.

### A44 — 216 blocks called 0 to 215 · **closed**

*2026-08-31.* A43 drew the graph and A42 measured that its partition is stable. Both describe
blocks that **had no identity**. A reader could see structure on the matrix and learn nothing
about biology, which makes a modularity score decoration.

**The enrichment had to come from outside the loop.** The edges of this graph ARE gene–disease
co-membership: two genes are joined because they cause a disease in common. Asking whether a
community shares diseases asks whether the thing that built the edges built the edges — it
returns a spectacular answer and means nothing, and the same holds for HPO phenotype terms,
which are annotations on those diseases. **Reactome is not in that loop**: curated biochemistry,
consulted by nothing in the construction. The phenotype profile is still published because a
reader wants it, and it is labelled `circular_by_construction` so it can never be quoted as
evidence.

**The control is annotation-matched, not random.** Reactome coverage is wildly uneven — a
well-studied kinase sits in dozens of pathways — so an unmatched null reports every community
holding well-studied genes as enriched for everything. Null sets are drawn from the graph's own
genes in eight quantile bins of annotation count. It is the same argument as the length
matching in `gene_constraint.py`, where two thirds of the apparent effect turned out to be the
covariate. 2,987 tests, Benjamini–Hochberg across the whole family.

**22 of the 28 testable communities get a name**, where "a name" means a pathway that both
survives FDR and covers at least a tenth of the community:

| genes | what most of it is | what is most unusual about it |
|---|---|---|
| 208 | Organelle biogenesis and maintenance, 49 % | ARL13B-mediated ciliary trafficking, **28×** |
| 182 | Immune System, 73 % | TRAF3 deficiency – HSE, **27×** |
| 165 | Signal Transduction, 47 % | Cohesin loading onto chromatin, **22×** |
| 154 | Muscle contraction, 36 % | Phase 3 – rapid repolarisation, **18×** |
| 150 | Sensory Perception, 28 % | Sound processing by outer hair cells, **13×** |

Ciliopathies, cohesinopathies, cardiac channelopathies and a deafness cluster, recovered from
disease co-membership alone and confirmed against a source that co-membership never saw.

**⚠️ Ranking by significance alone was misleading, and the first version shipped it.** The
headline for a 482-gene community was "Metabolism of Angiotensinogen to Angiotensins" on the
strength of **three genes** — a real enrichment, eleven-fold, and not what that community is. A
pathway covering 0.8 % of a group does not name it, and a figure printing it as the group's
identity lies with a correct *p* value. Coverage now gates the headline and the specific
pathway is published beside it, because the two pull opposite ways and choosing one hides half
the answer.

**⚠️ And the determinism guard fired for the third day running.** `pathways[g]` is a set of
strings; Python randomises string hashing per process, so the Counter was built in a different
order every run, ties in the sort broke differently, and the six pathways published as a
community's identity came out in a different order. The counts never changed — only what was
printed as the answer. Sets are now iterated sorted, and the sort key ends with the pathway id
so the order is total.

### A45 — the 0.29 was a number nobody could check · **closed**

*2026-08-31.* A42 measured that Louvain and Leiden agree at ARI 0.870 and that either agrees
with label propagation at **0.29**. That is a fact a reader has to take on faith, and it throws
away everything a user of the communities would want: *which* genes move, *where* they go, and
whether the disagreement is a handful of border cases or a wholesale re-partition.

**It is the third.** `tools/partition_flow.py`:

| | genes kept in matched communities | communities found |
|---|---|---|
| Louvain → Leiden | **92.5 %** | 216 → 213 |
| Leiden → label propagation | **50.0 %** | 213 → **447** |

Label propagation shatters the graph into twice as many communities and moves half the genes.
The ARI said the families disagree; this says what the disagreement *is*.

**Two real algorithms sit behind the picture, and neither is decoration.**

Community labels are arbitrary — Louvain's 7 and Leiden's 42 may be the same genes, and nothing
in either output says so. Comparing partitions therefore needs the communities matched first,
and the obvious greedy approach (best overlap, remove, repeat) is wrong: one early choice forces
every later pairing into a worse one. It is an **assignment problem** with an exact solution, so
`scipy.optimize.linear_sum_assignment` does it over the full overlap matrix. The matching moves
no gene; it decides which community is drawn opposite which, which is what makes the crossings
mean disagreement rather than an accident of labelling.

Then the bands have to be ordered or the figure is an unreadable braid. **Barycentre sweeps**
(Sugiyama's layered drawing) take ribbon crossings from **1,542 to 739**. Minimising them
exactly is NP-hard, so both counts are published rather than the result being called optimal.
Both computations are in Python per ADR 0008 — they are decisions about what the figure argues,
not rendering.

**The form is parallel sets**, chosen because the question is flow between categorisations and
no bar chart of agreement scores can show it. Matched ribbons are drawn faintly and the moved
ones carry the only colour in the figure: agreement is context, disagreement is the subject.
