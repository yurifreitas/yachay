# 0009 — A section is declared once, and nothing can offer one that cannot be drawn

> **Role:** the decision that the explorer's sections are data in a registry rather than
> branches in a render chain, and the check that keeps the two lists from drifting.
> **Last revised:** 2026-08-29 · **State:** proposed, and **all three pages migrated**. 59
> sections across rare, gene and run are declared, reachable and described; the render chains
> are gone and `LEGACY` is empty.

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

**Paid, and then repaid the same day.** All three pages are migrated: rare 25, gene 17, run
17. The pages went from 1,586 lines to **709**, and the 59 branches to **none**. Two things
had to give to get there, and both are worth naming:

  * `title` and `sub` accept a **function of the context**, because several headings need the
    page's translator and a registry is a module rather than a component, so it cannot call a
    hook. The page passes `tt` in and the registry resolves it. That keeps a section a plain
    value that can be listed and checked without being mounted.
  * The gene page's panels were **local functions inside the page**, which is fine until a
    registry needs them — a registry importing from the page it feeds is a cycle. They moved
    to `genePanels.tsx`.

**And the gene page gained something the migration was not for.** Its seventeen sections had
no description at all: `{section === "x" && <Panel/>}`, with the rail's label as the only
thing telling a reader what they were looking at. A label is a name, not a claim. Each now
carries a sentence, and the sentences are deliberately **factual rather than interpretive** —
each names what the panel draws and which tool wrote the artefact behind it, which a reader
can check by opening the file.

**Risk accepted.** The checker reads the modules as text rather than importing them, because a
checker that needs a bundler is a checker that gets skipped. It therefore depends on the
literal shape of the declarations. Its first version matched group ids as well as section ids
and reported five false failures; a checker that cries wolf is one somebody deletes, so the
pattern now requires the `group:` key that only a section carries.

## What the checker learned, twice

Both times it was wrong about **form** rather than substance, and both times the fix was to
the checker:

  * It matched group ids as well as section ids and reported five false failures. A checker
    that cries wolf is one somebody deletes; the pattern now requires the `group:` key that
    only a section carries.
  * It demanded a quoted string for `sub` and failed twenty-three entries whose sentences are
    JSX with inline emphasis. It now measures the **text**, and accepts a sentence that lives
    in the i18n module — because `tt(MEAS.scaleSub)` cannot compile unless the key exists in
    both languages, so the compiler has already made the guarantee.

This is the same lesson `verify_claims.py` learned about the typographic minus on the same
day. A check that fails on notation teaches people to disable it.

## The next step, concretely

`LEGACY` is empty and stays in the file. The next page added without a registry will be named
by the check rather than passing silently, which is the only reason an empty list is worth
keeping.
