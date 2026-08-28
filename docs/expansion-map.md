# Expansion map — where else this applies

A method validated on one screen has not been validated. This is the honest inventory of
where `sieve` should apply next, drawn from work that already exists in this workspace
rather than from imagined use cases. Each entry states **the entity, the observation, the
aggregate, and whether observation counts vary** — because if those four do not map, the
method does not apply and the entry should be deleted rather than stretched.

Ordered by expected value: how likely the bug is present × how cheaply it can be checked.

This file covers the *non-biology* neighbours. The disease portfolio — schizophrenia
(GWAS), NF2-related schwannomatosis, and Duchenne muscular dystrophy, alongside the obesity
origin — is planned separately in [`disease-expansion.md`](disease-expansion.md), and the
data / method / domain citations live in [`references/`](references/README.md).

---

## 1. `prompt-workbench` (Oráculo) — **implemented**

*LLM prompt/model evaluation. React dashboard + FastAPI, runs prompts × inputs × N
executions, grouped by prompt-content hash.*

| | |
|---|---|
| entity | prompt variant (content hash), model, config |
| observation | one execution on one input |
| aggregate | pass rate, best-of-N, structured-JSON match, judge score |
| counts vary | **yes, and systematically** — iterating gives promising variants more runs |

The strongest non-biology instance, which is why it became the second adapter. Two
failure forms, both live in any workbench of this shape:

- **best-of-N selection** — the winner is largely the variant that got lucky, and the
  score you publish will not reproduce. This is the familiar "the winning prompt got
  worse after we shipped it".
- **unequal run budgets** — run count correlates with expected quality in one direction
  and with score inflation in the other, so which way the leaderboard leans is not
  knowable without calibrating.

Building this adapter immediately found a design flaw in the core (`reduce="mean"` vs
`reduce="raw"`), which is the return on doing it at all.

**Next concrete step:** point `adapters/llm_eval` at a real `runs/` directory from the
workbench and report how much of its current leaderboard ordering is run budget. That is
a one-afternoon check on real data you already own.

---

## 2. `adia/structural-break-real-time-ethersym` — high value, direct fit

*CrunchDAO structural-break detection, real-time edition.*

| | |
|---|---|
| entity | a candidate break point (series, timestamp) |
| observation | one window / one tick of evidence |
| aggregate | a detection statistic — almost always a **maximum over candidate change points** |
| counts vary | **yes** — series differ in length, and windows near the edges are short |

Change-point detection is a textbook max-order statistic: you scan positions and take
the largest test statistic. The scan itself inflates the maximum, and the inflation
depends on how many positions were scanned and how long the series is. This is exactly
Stage 1, and the classical literature already agrees (Darling–Erdős, scan statistics) —
which makes it a strong *validation* target: `sieve` should reproduce a known analytic
correction empirically. If it does not, the library is wrong.

**Why this is the best next adapter:** it has a ground truth. DepMap and the obesity
screen do not.

---

## 3. `synth` — Synthetic Price Data

*Probabilistic density forecasting of incremental returns, two horizons, many step
resolutions.*

| | |
|---|---|
| entity | a model / configuration |
| observation | one scored forecast at one (horizon, step) |
| aggregate | CRPS or log-score, aggregated across steps |
| counts vary | **yes** — 24 h and 1 h rounds fire at different frequencies |

Weaker fit, and worth saying so: a mean log-score is **not** a max-order statistic, so
Stage 1 barely moves it (see `test_mean_is_unbiased...`). The bug appears only where
model *selection* happens — picking the best configuration by its best observed round is
best-of-N again. Use `sieve` here for Stages 3–5 (confounds, baseline-first,
leakage-safe evaluation), not for Stage 1.

Listed deliberately as the case where the headline correction does **not** apply.

---

## 4. `markov-bots`, `Financial_networkj` — strategy selection

*Backtesting and DRL trading agents.*

| | |
|---|---|
| entity | a strategy / hyperparameter configuration |
| observation | one backtest period, one episode |
| aggregate | best Sharpe, max return, best drawdown-adjusted score |
| counts vary | **yes** — configurations get unequal numbers of episodes |

Backtest overfitting is this exact bias with its own literature ("deflated Sharpe
ratio", "probability of backtest overfitting"). A strategy selected as the max over many
trials has an inflated expected Sharpe, and the inflation grows with the number of trials.
`sieve` would compute the empirical version of the deflation, from the project's own
control periods rather than from a formula's assumptions.

---

## 5. `dna`, `paper-track` — adjacent, partial

- `dna` — raw data plus an analysis report. Whether it fits depends on the aggregate; if
  anything is scored by a top-k or max over probes, it fits.
- `paper-track` — ARC Prize paper track. Not a screen, but it already keeps a `STATE.md`
  lab notebook, which is the Stage 8/9 practice this method leans on hardest.

---

## Where it does NOT apply

Kept explicitly so the scope does not creep:

- **`real-search`** — Grover search on real IBM hardware. Genuinely a maximum-finding
  problem, but the maximum is *exact and verifiable*, not estimated from noisy
  observations. No estimation, no bias, no Stage 1.
- **`beatbe-vst`, `Universal-Language`, `gerber_parser`** — no scored candidate set.
- Any leaderboard scored by a **plain mean with equal sample sizes**. Then the problem is
  variance, and the fix is a confidence interval, not a null model.

---

## The test for a new domain

Four questions. If any answer is no, do not force it:

1. Are there many candidate entities you must rank?
2. Is each entity's score estimated from a number of noisy observations?
3. Does that number **vary** across entities?
4. Is the aggregate a **selection** operator — max, top-k, quantile, enrichment, best-of-N
   — rather than a plain mean?

Yes to all four means the ranking is partly a ranking of observation count, and Stage 1
is the cheapest correction available. Yes to 1–3 but no to 4 means you have a variance
problem: report intervals, and skip to Stage 3.
