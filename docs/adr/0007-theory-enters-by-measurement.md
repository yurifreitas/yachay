# 0007 — A theory enters this repository only as a measurement

> **Role:** the decision that a mathematical construct enters this repository only when a tool computes it, with a null and an interval.
> **Last revised:** 2026-08-29 · **State:** proposed. Governs `../references/theory-atlas.md`.

**Status:** proposed · written 2026-08-29, **before** the tool it governs
**Supersedes:** nothing · **Governs:** [`../references/theory-atlas.md`](../references/theory-atlas.md)

## Context

A long design conversation produced a catalogue of roughly ninety mathematical constructs
proposed for this project: renormalisation and causal emergence for the scale problem,
Koopman operators for multimodal observation, sheaf cohomology for evidence conflict,
Finsler geometry for the asymmetry of *healthy → disease* against *disease → healthy*,
Mori–Zwanzig for where memory comes from when scales are collapsed, viability theory for
severity, partial information decomposition for synergy, category theory for model
composition. The catalogue is recorded in `references/theory-atlas.md`.

Every one of them is more interesting than anything currently in `tools/`. That is exactly
the danger. This repository already carries a named finding about authored layers: nine of
them exist, **two have been tested**, and `tools/README.md` §5 lists the other seven as
untested in public. A catalogue of ninety formalisms would be the tenth authored layer and
the largest — a page of mathematics that describes nothing that was measured, in a project
whose one claim on the reader is that every number on it can be traced to the artefact that
produced it.

The failure mode has a name in the source conversation itself: *"descobriremos rapidamente
quais partes são matemática útil e quais são apenas analogias bonitas"* — we will find out
quickly which parts are useful mathematics and which are merely pretty analogies. Nothing in
the catalogue distinguishes the two, and prose cannot.

## Decision

**The theory atlas is a reference document with no standing.** A construct listed there
carries no weight in this project — it may not be cited in the manuscript, may not appear in
the explorer, and may not be described as part of the method — until it exists as a tool that
reads real ingested data and writes a number with a null and an interval.

Three grades, and every entry in the atlas carries exactly one:

| grade | meaning |
|---|---|
| **measured** | a tool in `tools/` computes it from an ingested source; the artefact exists |
| **buildable** | the data required is already on disk; nothing but work stands in the way |
| **analogy** | it would need data this project does not have, or it is a metaphor with no estimator attached |

The default grade for a new entry is **analogy**. Promotion is by measurement only; nothing
is promoted by argument.

**The first promotion is the scale rung**, because it is the one the project's own thesis
audit grades as partial and because it needs no new download: information preserved when the
catalogue is coarse-grained from genes to pathways and to cell types. `tools/scale_information.py`.

## Consequences

**Gained.** The catalogue can be as ambitious as it likes without contaminating anything.
Sheaf cohomology for conflicting evidence stays written down where it can be found, marked
`analogy`, and no reader can mistake it for something this project does.

**Gained.** A concrete queue. The atlas sorts by grade, so "what is worth building next" is
read off the `buildable` rows rather than argued about.

**Paid.** Slow. Ten research problems are named in the atlas and one is being built. The
honest form of that is a table with one **measured** row and many empty ones, which reads as
weakness and is in fact the only thing that makes the one row worth anything.

**Paid, and specifically.** Comparing mutual information across scales with different
alphabet sizes is biased: 5,260 genes will beat 29 pathways on raw MI because 5,260
categories can memorise the label. Every cross-scale number this decision admits must
therefore be reported as **excess over a permutation null at the same alphabet size**, never
as raw MI. A cross-scale comparison without that null is not a weaker version of this
result; it is a measurement of the alphabet.

**Risk accepted.** Grading is a judgement, and the boundary between `buildable` and `analogy`
will be argued. The rule of thumb: if you cannot name the ingested file it would read, it is
an analogy.