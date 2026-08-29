# Deep review — 2026-08-26

> **Role:** the index for a five-lane adversarial review of the whole project. Each lane
> was briefed to try to **break** its subject rather than confirm it, because a project
> that has only ever been reviewed by its author has not been reviewed.
> **Last revised:** 2026-08-29 · **State:** lanes running; this index is filled in as
> each deliverable lands, with its verdict quoted rather than paraphrased.

## Why five lanes, and why adversarial

The repository had reached the point where every remaining risk was one of four kinds, and
they do not share a method of investigation:

| risk | how you find out | lane |
|---|---|---|
| the claim is already solved in the literature | read the field, adversarially | `selection-bias.md` |
| the claim is right but our application of it is wrong | read the field's *practice* | `depmap-methods.md` |
| the domain framing does not survive contact with the biology | read the domain | `nf2-biology.md` |
| the claim is narrower than we say | look for it elsewhere | `cross-domain.md` |
| the code does not do what the docs say | read the code and compute | `internal-audit.md` |

The fifth lane is the only one forbidden from using the web: its findings must come from
numbers it computed against the data on disk.

## The lanes

| lane | question it must answer | deliverable |
|---|---|---|
| Selection bias | Is the core claim novel, partly novel, or already solved? | [`selection-bias.md`](selection-bias.md) |
| DepMap methods | What does the field actually do, and what are we getting wrong? | [`depmap-methods.md`](depmap-methods.md) |
| NF2 biology | Does the disease framing survive external validity? | [`nf2-biology.md`](nf2-biology.md) |
| Cross-domain | How general is this really, and where has it already been solved? | [`cross-domain.md`](cross-domain.md) |
| Internal audit | Are the two open anomalies defects or noise? | [`internal-audit.md`](internal-audit.md) |

## The questions that were live when this started

Recorded before the answers arrived, so the review cannot be reread as having confirmed
whatever it happens to find.

1. **Does the ranking claim survive Forster et al. (2025)?** They report that winner's-curse
   correction "generally does not improve the feature ranking". Our scope answer —
   heterogeneous $n$ — is now enforced by `tests/test_ranking_scope.py`, but nobody outside
   this repository has checked it.
2. **Is the NF2 contrast statistically valid at all?** Differencing two z-scores fitted
   against two different nulls (32 lines vs 1146) may not be a coherent statistic. If it is
   not, the positive-control failure is our arithmetic, not the biology.
3. **Is there a copy-number circularity?** Chronos corrects gene effect for copy number.
   NF2 is frequently lost *by* copy number. A contrast defined on NF2 deletion, scored on a
   CN-corrected matrix, may be attenuated by construction.
4. **Do mesothelioma cell lines say anything about schwannoma?** The disease is benign and
   the cell lines are malignant. If the answer is no, the NF2 framing is a cancer-biology
   project wearing a rare-disease name, and the documentation must say so.
5. **Why does the control pool calibrate to −4.09?** Still unexplained
   (`docs/lineage.md` §8a).
6. **Is the −0.0252 → −0.0559 move a defect or noise?** Unanswerable without an interval,
   which the repository has never computed anywhere.

## How to read the results

Each deliverable opens with a blunt verdict. Where a lane contradicts the repository's
existing documentation, **the lane wins until its evidence is disputed with numbers** —
and the contradicted document gets corrected rather than quietly left standing. Where two
lanes contradict each other, that goes in `docs/lineage.md` §8 as a new open anomaly.


---

## Two later files, which are not review lanes

Added 2026-08-29 under [`../../adr/0007-theory-enters-by-measurement.md`](../../adr/0007-theory-enters-by-measurement.md),
and they say so in their own headers rather than pretending to be lanes:

- [`multiscale-formalism.md`](multiscale-formalism.md) — the mathematics behind
  [`../theory-atlas.md`](../theory-atlas.md): for each family, the formal object, the estimator
  it reduces to on this project's data, the identification problem, and the blocker.
- [`foundations.md`](foundations.md) — the mid-century work those families descend from, each
  tied to a number measured here or to a named open problem. Two of the ancestors made
  predictions that were tested; one failed.

**And two of the questions this directory lists as open have since been answered**, which is
recorded here rather than by editing them away:

- *"Why does the control pool calibrate to −4.09?"* — addressed by fitting nulls on blocks
  rather than rows, [`../../adr/0004-block-nulls.md`](../../adr/0004-block-nulls.md), whose
  prediction was scored correct.
- *"Is the −0.0252 → −0.0559 move a defect or noise? Unanswerable without an interval, which
  the repository has never computed anywhere."* — the repository now computes intervals
  everywhere (`tools/intervals.py`, audit A26), and the sentence is no longer true.
