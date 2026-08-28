# Prior work — the ancestors this repository has, and the one it credited

> **Role:** the methodological lineage across the author's own projects. `lineage.md` traces
> the *published* ancestors — Bailey, Menche, Norio. This file traces the *local* ones, and
> it exists because the closest of them is not mentioned anywhere in this repository.
> **Last revised:** 2026-08-28 · **State:** five projects surveyed across two roots
> (`C:\Users\yuri\Documents\code`, `F:\CODE`). Line counts and API listings are measured
> from the source; the claims about what each project solved are read from its own README
> and quoted rather than paraphrased.
>
> Explanation-mode. The published lineage is [`../lineage.md`](../lineage.md); the finding
> this file produced is [`../audit.md`](../audit.md) A27.

---

## The finding, first

**`nominator` is the direct methodological ancestor of `sieve`, and `sieve` does not
mention it.** Same thesis, same ten stages, one insertion:

| # | `nominator` | `sieve` |
|---|---|---|
| 0 | Decode the objective & its degeneracies | Objective |
| — | *(absent)* | **1 · Null** ← inserted |
| 1 | Reliability / power modelling | 2 · Power |
| 2 | Confound identification | 3 · Confound |
| 3 | Baseline-first modelling | 4 · Baseline |
| 4 | Orthogonal validation | 5 · Validation |
| 5 | Leakage-safe evaluation | *(merged into 5)* |
| 6 | Mechanism-prior integration | 6 · Prior |
| 7 | Nomination & portfolio | 7 · Shortlist |
| 8 | Honest reporting | 8 · Report |
| 9 | Reproducibility engineering | 9 · Repro |

`sieve`'s README presents the ten stages as its own frame. Nine of them are `nominator`'s,
renumbered by the insertion of Stage 1. **What `sieve` genuinely contributed is the Null
stage** — and that is a real contribution, since it is the stage that produced every headline
result this repository has. But the frame it sits in was inherited, and
`references/standards.md` §4 requires that every borrowed claim get two entries: one in
`CITATION.cff` with the claim it supports, one in `lineage.md` saying what our measurement
does to it. `nominator` has neither.

The rule was written for other people's work. It applies to your own.

---

## What each ancestor solved, and what `sieve` failed to inherit

### `nominator` — the frame, and a bootstrap this project rebuilt fourteen sweeps later

**921 lines, Apache-2.0, `C:\Users\yuri\Documents\code\nominator`.** A module per stage:
`reliability`, `confounds`, `baselines`, `validation`, `priors`, `nominate`, `report`,
`repro`, `pipeline`.

**`sieve` has 4 of 10 stages implemented in 1,627 lines. `nominator` had all of them in
921.** That reframes [`../audit.md`](../audit.md) A15 completely: the eight missing stages
were not *unbuilt*, they were **not carried over from a predecessor that had them**. A
backlog and a regression are different things, and nothing in this repository said which
this was.

And the sharpest instance:

```python
# nominator/core/validation.py
def bootstrap_ci(a, b, stat=spearman, n_boot: int = 2000, seed: int = 0) -> dict:
```

**A6 — "no uncertainty on most published numbers" — was open in this repository for
fourteen audit sweeps and was closed on 2026-08-28 by writing a bootstrap from scratch.**
The ancestor shipped one. `validation.py` also has `leave_one_entity_out`,
`cold_start_split` and `orthogonal_validation`: leakage-safe splitting that `sieve` Stage 5
describes in prose and does not implement.

### `climate` — power as a governing constraint, not a check

**102 Python files, 14 documents, `F:\CODE\climate`.** A regime engine for Rio Grande do Sul,
and its README opens with the constraint rather than the method:

> `n_avaliação = 36` (1991–2026). `SE(RPSS) ≈ 0.10–0.15`. O erro padrão é da ordem do sinal
> inteiro. Consequência: **não existe arbitragem empírica** entre modelos.

*The standard error is the order of the whole signal, therefore there is no empirical
arbitrage between models.* That is `sieve` Stage 2 promoted from a gate to **the thing that
governs the architecture** — and it is the same conclusion A26 reached for rare disease,
reached first, and reached more decisively: `climate` lets it dictate what may be built,
where `sieve` computes an interval and then keeps ranking.

Its documentation map also promises something `sieve` only partly does: *"o que cada modelo
afirma e como derrubá-lo"* — what each model claims **and how to falsify it**, per model.
`references/rare-disease-mechanisms.md` §5 does this; most of this repository does not.

### `adia` — a measured optimism gap

**204 Python files, `F:\CODE\adia`.** Real-time structural-break detection, and it carries
the number `sieve` Stage 5 exists to produce and has never produced:

| | TS-AUC |
|---|---|
| board (the truth) | **0.5910** |
| local holdout | ~0.60 |
| **optimism** | **≈ +0.013** |

> "O holdout local **superestima** o board → estamos superajustando. Direção da próxima
> versão: **regularizar/podar** … não adicionar."

A quantified leakage penalty, and a stated direction of *prune, do not add*. `sieve` spent
this session adding — six sources, twelve tools, four stages — and has no equivalent
measurement of its own optimism anywhere.

### `knee` — the only ancestor credited, and only for form

`F:\CODE\knee`, 20 Python files and 20 documents. `lineage.md` credits it for the
documentation discipline: the role/last-revised/state header, the lineage file, the archive
of dead ends with the number that killed each. That credit is correct and it is also the
*smallest* of the debts on this page.

### `Financial_networkj` — the cross-domain transfer, already attempted

**92 Python files.** *"the result of a long journey to translate biological principles into"*
finance — dueling DQN with a continuous regression head. `expansion-map.md` argues `sieve`'s
stages are domain-agnostic and lists candidate domains; this is the author's own prior
attempt at exactly that transfer, and the expansion map does not know it exists.

---

## What this changes

**1. A15 has to be restated.** The finding read: *the periphery is 6.5× the core, and eight
of ten stages have no implementation*. The accurate version is worse and more useful — those
eight stages **were implemented in the predecessor and left behind**, so the question is not
"when will they be built" but "why were they dropped, and was that deliberate?". Nothing on
disk answers it, which is itself the answer: it was not a decision, it was a restart.

**2. The `roadmap.md` priorities move.** Tier 1 assumed the missing stages were greenfield.
Porting `nominator`'s `validation.py` — `leave_one_entity_out`, `cold_start_split`,
`orthogonal_validation` — is cheaper than writing Stage 5, and it comes with a working
`bootstrap_ci` that would have closed A6 on day one.

**3. The attribution debt is real and small to pay.** `CITATION.cff` and `lineage.md` each
need an entry. The rule this repository applies to Bailey and Menche applies to the author's
own prior work, and applying it selectively is the failure the rule exists to prevent.

---

## What this file does not cover

Surveyed and not analysed: `obesity` (the origin screen, 41 Python files — the data `sieve`
was distilled from), `quant`, `synth` (probabilistic density forecasting), `fractal`,
`dna/viz` (genomic visualisation, and the reference for the visualisation work not yet
done), `agentComp`, `Arandu` and `trans` (public-money transparency, 20 and 20 documents).

Each was opened far enough to see it holds something and no further. Listing them unexamined
is the honest state; claiming a survey that did not happen would be the exact failure
`nominator` Stage 8 is named for.
