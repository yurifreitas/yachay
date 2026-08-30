# 0009 — A section is declared once, and nothing can offer one that cannot be drawn

> **Role:** the decision that the explorer's sections are data in a registry rather than
> branches in a render chain, and the check that keeps the two lists from drifting.
> **Last revised:** 2026-08-29 · **State:** proposed. One page migrated of three, and the
> check names the other two rather than pretending they are done.

**Status:** proposed · written after the first migration, before the remaining two
**Supersedes:** nothing · **Relates to:** [0008](0008-layouts-are-computed-once.md)

## Context

Adding a measurement to this project cost four touch points: an i18n block, a component, an
entry in a page's `SECTIONS` array, and a branch in that page's render chain. Nothing
connected the last two, so they were two lists maintained by hand.

By 2026-08-29 that was **59 branches across three pages and 1,586 lines**, and the failure
mode is the one this repository keeps finding in its own prose: a list and the thing it
describes drift apart, silently. `tools/index_check.py` found sixteen of eighteen ingested
sources named in no index the first time it ran. The interface had no equivalent, and its
version of the failure is worse — a nav entry with no branch renders **nothing at all**. No
error, no log, a blank panel, and a reader with no way to report it as a defect.

The pipeline settled this long ago for stages: `sieve.pipeline.stages` declares each one in a
single place and the runner reads it. Adding a stage is an entry. This is that move, applied
to the interface.

## Decision

**Sections are entries in a registry**, typed in `web/src/lib/sectionRegistry.tsx`, carrying an
`id`, a `title`, a `sub` and a `view` that receives the page's context. A page renders with one
call, `renderSection(REGISTRY, section, ctx)`.

**`sub` is required, not optional.** In this project a figure's sentence is where it states
what it does *not* show — that is the whole `says` discipline, moved one layer out. A section
that cannot be described in a sentence is a section nobody can argue with, and the check fails
on an entry whose sentence is missing or under twenty characters.

**`web/scripts/check-sections.mjs` runs in `npm run check`** and fails the build on three
things: a rail entry nothing draws, a registered section unreachable from the rail, and an
entry with no sentence.

## Consequences

**Gained.** Adding a measurement is one entry. `RunDash.tsx` went from **351 lines and 17
branches to 201 lines and none**, and the seventeen sections now live as data that can be
read, diffed and checked.

**Gained, and this is the larger half.** A blank panel is no longer possible in a migrated
page. If the rail offers something the registry cannot draw, the build fails; if it somehow
ships, the reader gets a stated absence naming the id rather than white space.

**Paid.** A migrated page loses the ability to do something bespoke inline. Every section is
now heading + sentence + view, and a section that genuinely needs a different shape has to
either fit that or stay out of the registry — at which point it is unchecked again. The
constraint is the point, but it is a constraint.

**Paid.** Two patterns exist until the migration finishes. `RarePage.tsx` (25 branches) and
`GenePage.tsx` (17) still use render chains. **The check prints them by name on every run**
rather than staying silent, so the debt is visible in the same place the passing page is —
which is the only reason it is acceptable to stop at one.

**Risk accepted.** The checker reads the modules as text rather than importing them, because a
checker that needs a bundler is a checker that gets skipped. It therefore depends on the
literal shape of the declarations. Its first version matched group ids as well as section ids
and reported five false failures; a checker that cries wolf is one somebody deletes, so the
pattern now requires the `group:` key that only a section carries.

## The next step, concretely

Migrate `RarePage.tsx`. It is the largest and it holds the ADR 0007 measured group, which is
where new sections keep landing — so it is the page where the drift this record exists to
prevent is most likely to happen next.
