# 0003 — A failed positive control blocks the shortlist

**Status:** accepted · ⚠️ back-filled 2026-08-26, the same day it first fired
**Supersedes:** nothing

## Context

The NF2 analysis has something the rest of the repository lacks: an answer known
independently of the data. Merlin acts upstream of the Hippo pathway, so NF2-null lines
should depend on YAP/TAZ-TEAD. If the pipeline cannot recover that, its novel hits are
numbers with nothing behind them.

The temptation, once a pipeline is built, is to report the shortlist anyway and note the
control failure as a caveat.

## Decision

The shortlist is **not printed** when the positive control fails. The analysis says the
gate fired and lists the candidate causes.

## Consequences

**Gained.** *Jidoka*: the defect does not move downstream. A reader cannot lift a gene list
out of a run whose own control says the run is unreliable.

**Paid.** A run can end with no shortlist, which feels like wasted compute. It is not — the
failed control is the result, and it is more informative than a list would have been.

**Fired immediately.** The first NF2 run (32 NF2-null lines, mutation calls only) reached a
Hippo median rank of 5216 of 17916 after calibration — better than the ~8958 of a random
gene, short of the 25 % threshold committed to in advance. No shortlist was printed.

**Note on the threshold.** 25 % was chosen before the result was seen but is otherwise
arbitrary, and a gate whose threshold is arbitrary is only as good as its pre-registration.
It must not be moved to let a result through; if it is ever changed, the change belongs in
a superseding record with its reasoning, not in a commit.
