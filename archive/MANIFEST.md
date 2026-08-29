# Archive — dead ends, each with the number that killed it

> **Role:** every idea this project tried and abandoned, kept with the measurement that
> ended it. Nothing here is deleted. An idea removed without its number will be proposed
> again — by us, or by the next person.
> **Last revised:** 2026-08-26 · **State:** three entries, back-filled from the code and
> the findings files. ⚠️ Back-filled entries are marked; going forward, entries are
> written when the idea dies, not months later.

The practice is *kaizen*: the improvement belongs to whoever did the work, and it is only
cumulative if it is written down. See `docs/references/standards.md` §2.

Format — copy this:

```markdown
### <idea>
- **Died:** YYYY-MM-DD
- **The number that killed it:** <metric, value, interval, comparison to the floor>
- **Why it seemed right:** <the reasoning, stated fairly>
- **What would revive it:** <the condition, or "nothing">
```

---

### Averaging control lines before fitting the null (⚠️ back-filled)

- **Died:** during the first DepMap run, before 2026-08-26.
- **The number that killed it:** calibrated **z ≈ +750**. Not a borderline result — a
  number with no physical meaning, which is the only reason it was caught.
- **Why it seemed right:** the screen's score is a top-$k$ over a gene's per-line values,
  and the obesity adapter's null averages observations into a profile before applying the
  statistic (`reduce="mean"`). Reusing that path looked like consistency.
- **What killed it, mechanically:** averaging across ~1000 lines collapses the null's
  standard deviation toward zero — the mean of 400 lines barely moves — so every z is
  divided by almost nothing. The null was answering a different sampling question than
  the score was asking.
- **What would revive it:** nothing. It was not a tuning failure, it was the wrong
  sampling model. The lesson became the `reduce=` argument and the refusal to guess
  between the two; see `src/sieve/stages/null.py` and ADR 0002.

### Defining the NF2-null subgroup from damaging mutations alone

- **Died:** 2026-08-26, superseded rather than refuted.
- **The number that killed it:** subgroup of **32 lines** out of 1178, and a positive
  control that did **not** pass — the Hippo axis reached median rank 5216 of 17916 after
  calibration, better than the ~8958 a random gene would take but short of the 25 %
  threshold the analysis committed to in advance.
- **Why it seemed right:** `OmicsSomaticMutationsMatrixDamaging.csv` is 148 MB against
  1.4 GB for the copy-number matrix, and mutation calls are the obvious genotype source.
- **Why it was wrong:** NF2 is lost by copy-number deletion as often as by point
  mutation (`docs/references/nf2.md` §2), so lines labelled wildtype here are really
  NF2-null. That biases the contrast **toward zero** — the effect measured was a lower
  bound, and it was stated as one before the result was known.
- **What would revive it:** it is not revived, it is replaced — the subgroup is being
  redefined as mutation **or** deletion once `OmicsCNGene.csv` finishes downloading. The
  mutation-only run is kept as the comparison that shows what the deletion calls buy.

### Claiming the ranking correction improves rankings in general (⚠️ back-filled)

- **Died:** 2026-08-26, on reading Forster et al., *Biostatistics* 26(1) 2025.
- **The number that killed it:** none of ours — theirs. Their comparative study reports
  that winner's-curse correction *"generally does not improve the feature ranking"*.
- **Why it seemed right:** every result this project had measured showed the ranking
  changing, and changing toward things known to be true.
- **Why it was too broad:** their features are estimated with **equal precision**, where
  the correction is one common monotone transform and therefore cannot reorder anything.
  The claim was true in our regime and false in theirs, and it had been stated without
  the regime.
- **What replaced it:** an explicit scope condition — heterogeneous observation counts —
  enforced by `tests/test_ranking_scope.py`, which asserts the ranking is preserved under
  equal counts. The narrower claim is the defensible one.
- **What would revive the broad claim:** nothing. It was wrong as stated.


---

### Anisotropy as a measure of the shape of knowledge · **killed 2026-08-29**

**The idea.** What matters about a rare disease is not how much is known but the SHAPE of it:
a vector over genetics, phenotype, cellular, natural history and population, summarised as
`1 - normalised entropy` so that a disease bright on one axis and dark on the rest scores high.
It was the most unusual proposal in `docs/references/theory-atlas.md`.

**The number that killed it.** Two, and the second is the decisive one.

Mean anisotropy **0.2633** against an independence null of **0.2723** — *z = −19.0*. The
catalogue is LESS concentrated than independence would give, so the premise is backwards: the
axes rise and fall together.

And the statistic tracks the count of populated axes almost arithmetically: **0.590** at two
live axes, 0.346 at three, 0.160 at four, **0.021** at five. It answers "how broad is the
coverage", not "what shape is the knowledge". A measure that is a monotone function of a
denominator is not a measure of shape.

**What replaced it.** The co-occurrence question — *which axes move together* — which found
that the two strongest couplings were artefacts of construction and that the residual
structure is the OMIM/ORPHA registry boundary. And then `tools/knowledge_void.py`, which asks
the shape question of the OCCUPIED SPACE rather than of each disease, and gets an answer:
318 of 1,024 cells filled [312.5, 323.5], 95 % of them on the frontier, 232 anti-forms.

**Not deleted.** `tools/knowledge_shape.py` still runs and still ships, with the failure
stated in its own `verdict` field and drawn in the neutral on the site. This entry exists so
the idea is not re-proposed as new, and so the *replacement* is traceable to the thing it
replaced.
