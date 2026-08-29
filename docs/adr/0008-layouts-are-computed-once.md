# 0008 — A layout is computed once, in Python, and versioned with the artefact

> **Role:** the decision that orderings, bins and projections are precomputed rather than
> derived at render time, and the boundary that separates a layout from a statistic.
> **Last revised:** 2026-08-29 · **State:** proposed. ⚠️ Written **after** the change it
> governs, and it says so below.

**Status:** proposed · ⚠️ back-filled the same day, after `tools/view_models.py` existed
**Supersedes:** nothing · **Relates to:** [0007](0007-theory-enters-by-measurement.md)

## Context

The explorer has always run on one rule: **no statistic is computed in the browser.** Every
figure is read from the artefact the analysis wrote, which is what allows
`tools/verify_claims.py` to fail the build when prose and artefact disagree.

A layout is not a statistic, and the boundary was never stated. In practice components were
sorting twenty rows, bucketing values and choosing orderings at render time. At twenty rows
that is free. At 12,994 five-dimensional vectors it is not possible at all — and the moment
the hyperdimensional views were attempted, three separate problems arrived together:

1. **A payload the browser cannot use.** `knowledge_shape.json` carries 12,994 vectors. A
   parallel-coordinates plot of 12,994 polylines is a filled rectangle. What a reader can see
   is density, and density is a reduction — so shipping the rows shipped a cost with no
   corresponding capability.
2. **An argument nobody can audit.** A matrix heatmap says something different depending on
   how its rows and columns are ordered. The language matrix is only legible because rows
   descend by coverage and columns by mean, and *that ordering is the finding* — the holes
   line up. An ordering computed inside a component is an argument with no version, no
   provenance and no diff.
3. **No place to put the reasoning.** A component can carry a comment. It cannot carry a
   `says` field, a `limits` list or a line in `docs/references/rare-layers.md`.

## Decision

**Layouts are solved in `tools/view_models.py`, written to an artefact, and graded `derived`
in the layer map.** The browser draws them and computes nothing.

The boundary, stated so it can be applied:

| computed in Python | computed in the browser |
|---|---|
| orderings and seriations | which row the pointer is over |
| bin edges and bin counts | pixel coordinates from a solved model |
| projections and adjacency | show/hide, expand/collapse |
| anything a `says` field would need to qualify | anything a screen resize changes |

The test is not cost. It is **whether the result is an argument.** A seriation is an argument.
A hover highlight is not.

## Consequences

**Gained.** Every ordering now has a name, a stated rationale and a version. The language
matrix's seriation is one sentence in the artefact, and changing it produces a diff.

**Gained.** The payload shrinks. 12,994 rows become a grid of counts: the view model is 53 kB
where the source artefact is 4.1 MB, and the per-disease table never reaches a browser.

**Gained.** Sorting and selection in the interface are now unambiguously *reordering*, which
keeps `verify_claims` able to protect every number on screen.

**Paid.** A round trip to regenerate. Changing a chart's ordering means running a Python stage
and rebuilding the bundle, where before it was an edit in a component. That is slower and it
is the correct trade: the thing that got slower is the thing that should not be done casually.

**Paid.** A second artefact to keep in step. `view_models.json` is derived from five upstream
artefacts and goes stale when any of them moves. The pipeline declares those dependencies, so
the staleness is visible rather than silent — but it is one more edge in the graph.

**Risk accepted.** The boundary will be argued at the margin. A component that picks a colour
scale from a value range is deciding something; is that a layout? The rule of thumb: if you
would have to explain the choice in a caption, it belongs in Python.

**⚠️ Written after the fact.** `view_models.py` was built first and this record followed the
same day. ADR 0004 was written before its change and scored correct; this one cannot claim
that, and the header says so rather than implying otherwise.
