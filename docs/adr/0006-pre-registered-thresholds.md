# 0006 — Thresholds are pre-registered, dated, and frozen against target contact

> **Role:** the decision to pre-register, date and freeze every threshold against target contact.
> **Last revised:** 2026-08-29 · **State:** proposed; written after the four thresholds it governs, and it says so.

**Status:** proposed · written 2026-08-28 **after** the thresholds it governs already existed
**Supersedes:** nothing. Adopts a practice from `F:\CODE\climate`.

## Context

`F:\CODE\climate` — a sibling project of this one, by the same author — governs its feature
reduction with a file that opens like this:

```yaml
# REGRA DE REDUCAO DE FEATURES — PRE-REGISTRADA (ADR-004)
# Datado e congelado em: 2026-08-07
# Estado: PRE-REGISTRADO. Nenhum contato com o alvo ocorreu ate esta data.
version: 1
frozen_at: 2026-08-07
target_contact: false   # vira true na primeira execucao da Camada 6
```

with the consequence stated as a rule rather than a hope:

> Qualquer alteração exige (1) nova entrada em `decisions.md` com justificativa **física**
> (não empírica), (2) bump de versão, (3) re-execução completa do walk-forward do zero.
> **Alteração motivada por resultado observado no alvo INVALIDA o experimento.**

Its decisions ledger is append-only, and ADR-007 states the acceptance criterion as an
interval — *lower bound of the 90 % CI of RPSS > 0* — because *"'RPSS positivo' pontual não
significa nada com n=36"*.

**This repository has the habit and not the mechanism.** ADR 0004 was written before the work
and scored the same day, which was good practice; ADR 0003 records a threshold *"chosen
before the result was seen but otherwise arbitrary"* and warns it must not be moved to let a
result through. Both rely on the author remembering. Nothing enforces either.

**And the gap is not hypothetical — it is a day old.** `sieve.stages.target`, written
2026-08-28, carries four thresholds:

```python
RECURRENT_ALLELE_PATIENTS = 10
PRIVATE_SPECTRUM = 0.80
UNINTERPRETABLE_VUS = 0.60
PAN_ESSENTIAL_LINES = 0.90
```

Every one was chosen **after** `tools/patient_variants.py` had printed the allelic spectrum
and `tools/clinvar_evidence.py` the VUS distribution. By `climate`'s standard that is target
contact before registration, and the honest label for those numbers is **not
pre-registered** — they are calibrated to data already seen. Nothing in the module says so.
The docstring calls them "a judgement", which is true and insufficient: a judgement made
before looking and a judgement made after looking are different objects, and only one of them
can be defended as a design choice.

## Decision

Three parts.

**1. A frozen manifest.** `manifests/thresholds.yaml`, carrying for each threshold: its
value, the date it was fixed, **whether the data it governs had been seen when it was fixed**
(`target_contact: true|false`), and the justification — marked as *mechanistic* or
*empirical*, because `climate` is right that only the first survives a change of dataset.

**2. Honest back-dating, not a fiction.** The four thresholds above enter the manifest with
`target_contact: true` and `pre_registered: false`. Relabelling them would be worse than
having no manifest: the mechanism exists to make a distinction visible, and its first act
cannot be to hide one.

**3. An acceptance criterion stated as an interval, before the result.** Adopting
`climate` ADR-007's form: a claim is accepted when the **lower bound of its 95 % interval**
clears the threshold, not when its point estimate does. `tools/intervals.py` now produces
those bounds (audit A26); what does not exist is any statement of what would have counted as
success *before* they were computed.

## Consequences

**Gained.** The difference between a threshold chosen blind and one calibrated to seen data
becomes a field rather than a memory. A reader can discount the second class without having
to reconstruct the history, and a future threshold has somewhere to be registered *before*
the run that would compromise it.

**Paid.** Every existing threshold must be audited and honestly labelled, and most of them
will come back `target_contact: true`. That is an uncomfortable manifest and it is the
accurate one.

**Risk.** A pre-registration file that is edited freely is worse than none, because it
confers the authority of the practice without the constraint. The mitigation is `climate`'s:
**append-only, with a version bump and a stated reason**, and a test that fails if a frozen
entry changes without one.

## How this will be scored

Falsifiable, in the manner of 0004:

- If the `sieve target` thresholds are ever moved and the manifest does not gain a new
  version with a *mechanistic* justification, this ADR failed and should be marked so.
- If a future claim is published whose acceptance criterion was written after its interval
  was computed, part 3 is decoration.