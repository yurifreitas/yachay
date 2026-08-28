# 0002 — Make the sampling model an explicit `reduce=` argument, and refuse to guess

**Status:** accepted · ⚠️ back-filled 2026-08-26
**Supersedes:** nothing

## Context

Two real adapters need opposite sampling models for the same library call.

- **The screening case** (obesity, DepMap gene profiles): an entity's score is a statistic
  over its *aggregate profile*. More observations make the profile less noisy, so the bias
  **falls** with n.
- **The selection case** (best-of-N, pass@k, top-k over a gene's per-line values): the
  statistic is applied directly to the n observations. More observations mean more chances
  to draw a high value, so the bias **rises** with n.

The direction of the correction is therefore opposite in the two cases. Getting it wrong
does not fail loudly: it produces a confident number. The first DepMap run averaged control
lines before fitting and produced z ≈ +750 (`../../archive/MANIFEST.md`).

## Decision

Expose `reduce="mean"` and `reduce="raw"` as an explicit argument with no inference from
the data, and document the failure mode in the parameter's own docstring.

## Consequences

**Gained.** The caller cannot silently get the sampling model wrong without having typed
the wrong word — *poka-yoke* rather than a warning in a tutorial.

**Paid.** The API asks a question the caller may not know the answer to. Mitigated by the
docstring stating which case is which in the caller's own vocabulary, not in the library's.

**Discovered.** This flaw was found by building the second adapter, in a domain that did
not produce the method. That is now the stated reason to build adapters at all, and it is
the acceptance criterion in the `sieve-new-adapter` skill.
