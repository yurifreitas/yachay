# Standards — the external canon this repository answers to

> **Role:** the global standards and engineering traditions yachay is held to, each with
> **what it demands of this repository** — not a reading list.
> **Last revised:** 2026-08-26 · **State:** mapped; conformance is partial and marked per row.
>
> Two halves. §1–3 are the **Eastern engineering canon** — the Japanese quality tradition
> and Taguchi's robust design, which is the deepest match to what this library does and is
> the reason this file exists. §4–7 are the **international standards** for measurement,
> reporting, and software.

---

## Why the Japanese quality tradition, specifically

Not decoration. `sieve` is a library about **separating a real effect from variation caused
by how the measurement was made**. That is the founding question of Japanese quality
engineering, asked from the 1950s onward with more rigour than most statistical-genomics
practice applies to it today. Four of its ideas are already implemented here under other
names, and naming them correctly is what lets the rest of the tradition be borrowed on
purpose instead of reinvented.

| tradition | the idea | where it already lives in `sieve` |
|---|---|---|
| **Taguchi** — robust parameter design | separate *control* factors from *noise* factors; a result that moves with the noise factor is not a result | Stage 1: observation count is a noise factor, and the score must be made insensitive to it |
| **Genchi genbutsu** (現地現物) — go and see | trust the actual place and the actual thing, not the report about it | the empirical null: resample the screen's **own** controls rather than assume a distribution |
| **Jidoka** (自働化) — stop the line on a defect | never pass a known-bad part downstream | `ContractError`: the schema raises instead of silently coercing |
| **Poka-yoke** (ポカヨケ) — mistake-proofing | make the wrong action impossible, not merely discouraged | `fit_null` takes the *statistic itself*, so you cannot calibrate against a different one than you scored with |

---

## 1. Taguchi methods — the closest intellectual relative

**Genichi Taguchi**, quality engineering, from the 1950s (Electrical Communication
Laboratory, then widely at Toyota and its suppliers).

Three ideas, in order of how much they matter here:

**a) The quality loss function.** Quality is not "inside the tolerance band". Loss grows
continuously — roughly quadratically — with distance from target. *Demand on this repo:* a
shortlist is not "the genes above a threshold". A gene barely inside a cut and one far
inside carry different expected loss on validation, and Stage 7 should reflect that rather
than treating the cut as a binary gate. **Not yet implemented.**

**b) Signal-to-noise ratio and inner/outer arrays.** Deliberately vary the noise factors and
select the configuration whose performance is *least sensitive* to them, instead of the one
whose mean is best. *Demand on this repo:* this is Stage 1 stated in the other direction. We
measure the noise factor's effect (observation count) and remove it; Taguchi would design
the screen so the effect is small to begin with. Where we can influence the screen design —
which observations to spend on which entities — that is the better move, and it is not in
the methodology yet. **Gap worth closing.**

**c) Orthogonal arrays.** Cover a factor space with a fraction of the runs. *Demand:* the
confound stage (3) currently regresses out covariates observed as they fell. Where we choose
the validation batch (Stage 5, Stage 7), the slots should be *designed* across the confound
space, not sampled from the top of a list. Directly relevant to picking 8 genes to validate.

> The honest caveat, because the field has one: Taguchi's *analysis* has been criticised by
> statisticians (the S/N ratio conflates location and dispersion; the designs can confound
> interactions). His *framing* — noise factors, robustness over optimality, loss as a
> continuum — is the durable part, and it is the part borrowed here.

## 2. The Toyota / TQC practice — how the work is run

**Deming** (PDCA, statistical process control, taken to Japan 1950), **Ishikawa** (QC
circles, the cause-and-effect diagram, "quality begins and ends with education"), the
**Toyota Production System** (Ohno).

| term | meaning | demand on this repository | state |
|---|---|---|---|
| **PDCA** | plan-do-check-act; the loop, never the one-shot | every claim goes propose → measure → record. Nothing skips the measurement | partially — `methodology.md` encodes it |
| **A3** | one problem, one sheet: context, current state, analysis, countermeasure, plan | the shape of `out/DEPMAP_FINDINGS.md`. Should be the shape of every analysis output | adopted informally |
| **Genchi genbutsu** | go to the actual thing | the empirical null. Also: read the release file, do not trust the paper's description of it | **done** |
| **Jidoka** | stop the line the moment a defect appears | contract violations raise; a failed Stage-3 assertion must abort the analysis, not annotate it | partial — contracts raise; stage assertions do not yet abort |
| **Poka-yoke** | design out the mistake | API shapes that make the wrong call impossible | partial |
| **Hansei** (反省) | unflinching reflection, especially after success | `lineage.md` §8, the two open anomalies. Recorded *because* the headline results were good | **done** |
| **Kaizen** | continuous small improvement, by the people doing the work | the `archive/` of dead ends, each with the number that killed it | **done** — `archive/MANIFEST.md`, three entries |
| **Muda / mura / muri** | waste / unevenness / overburden | *mura* is literally this library's subject: **unevenness in observation count** | **done**, under another name |
| **Nemawashi** (根回し) | lay the groundwork before the decision | ADRs written before the change, not after | **partial** — four records; 0004 written before the work, 0001-0003 back-filled |
| **5 whys** | drive to the cause, not the symptom | "the score correlates with count" → why → … → "the statistic is a maximum" | the method's own origin story |

**Nonaka & Takeuchi — SECI and *ba*.** Knowledge converts between tacit and explicit
(socialisation → externalisation → combination → internalisation). *Demand:* the tacit
knowledge in this project is "which numbers to distrust". Externalising it is exactly what
`lineage.md` and the annotated `CITATION.cff` do. This is the theoretical warrant for the
documentation apparatus borrowed from `knee`, and the reason it is not busywork.

## 3. Standards bodies of the region

- **JIS** (Japanese Industrial Standards) — the national standard system through which the
  above became mandatory practice rather than philosophy.
- **JIS Z 8101 / ISO 3534** — statistical vocabulary. *Demand:* use *trueness*, *precision*,
  and *accuracy* as defined, not interchangeably. Stage 1 corrects **trueness** (bias); it
  does nothing for precision. Saying so precisely prevents the most common misreading of
  this library.
- **KS** (Korea), **GB** (China) — noted for completeness; nothing here depends on them yet.

---

## 4. Measurement and uncertainty

- **JCGM 100 (GUM) — Guide to the Expression of Uncertainty in Measurement.** Every reported
  value carries a stated uncertainty and a stated coverage. *Demand:* the two anomalies in
  `lineage.md` §8 cannot be resolved without intervals; "−0.0252 → −0.0559" is not a result
  until it has one. ⚠️ **not conformant.**
- **JCGM 200 (VIM) — International Vocabulary of Metrology.** Same vocabulary discipline as
  JIS Z 8101, internationally.
- **ISO 5725 — Accuracy (trueness and precision) of measurement methods.** The formal
  version of the trueness/precision split above.

## 5. Reporting guidelines — the biomedical side

Relevant the moment a disease shortlist leaves this repository.

| guideline | covers | relevance |
|---|---|---|
| **TRIPOD+AI** | prediction-model reporting | if a model ranks the shortlist, this is the reporting checklist |
| **STARD** | diagnostic accuracy studies | |
| **ARRIVE** | animal experiments | the validation step a shortlist feeds into |
| **MIQE** | qPCR reporting | the wet-lab validation of a hit |
| **FAIR** | findable, accessible, interoperable, reusable data | `out/depmap.manifest.json` is a start |
| **FAIR4RS** | the same, for research **software** | what `CITATION.cff` serves |
| **CRediT** | contributor roles | for any paper |
| **Model Cards / Datasheets for Datasets** | intended use, limits, populations | the honest place to put "this needs a control pool and has none for your screen" |

## 6. Software and repository standards

| standard | demand | state |
|---|---|---|
| **Semantic Versioning 2.0.0** | version numbers that mean something | declared, 0.1.0 |
| **Keep a Changelog** | a human changelog | ⚠️ missing |
| **BibTeX/biblatex + biber** | one canonical bibliography, annotated | **done** — `paper/refs.bib`, every entry carries the claim it supports |
| **Conventional Commits** | machine-readable history | not adopted |
| **CITATION.cff 1.2.0** | machine-readable citation | **done** |
| **SPDX / REUSE** | unambiguous licensing | ⚠️ `LICENSE` file missing; `CITATION.cff` claims CC-BY-4.0 |
| **ADR** (Nygard) | decisions recorded with context and consequences | **done** — `docs/adr/`, four records |
| **Diátaxis** | tutorial / how-to / reference / explanation, never mixed | partial — `methodology.md` mixes explanation and reference |
| **C4 model** | architecture at four zoom levels | not needed at current size |
| **ISO/IEC 25010** | software quality characteristics | the vocabulary for "quality" if it is ever argued about |
| **PEP 621 / pyproject** | packaging | **done** |

## 7. Conformance summary — what is actually missing

Ordered by cost of the gap, highest first:

1. **No intervals on reported numbers** (GUM). The anomalies cannot be adjudicated without
   them. This is the one that blocks a conclusion.
2. ~~No `archive/` of dead ends~~ — **closed 2026-08-26**, `archive/MANIFEST.md`.
3. ~~Empty `docs/adr/`~~ — **closed 2026-08-26**, four records; the `reduce=` decision is
   ADR 0002 and the block-null prediction is ADR 0004, written before the work.
4. **No `LICENSE` file** (SPDX/REUSE) while `CITATION.cff` declares a licence.
5. **Stage assertions do not abort** (jidoka). A failed Stage-3 check should stop the run.
6. **`docs/case-studies/obesity.md` is cited by `methodology.md` and does not exist.**
