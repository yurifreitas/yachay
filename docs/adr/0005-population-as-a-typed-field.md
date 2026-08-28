# 0005 — Population is a typed field, and CARE joins FAIR in the standards

**Status:** proposed · written 2026-08-27 **before** the work
**Supersedes:** nothing. Extends the data contracts, and amends `references/standards.md`.

## Context

Two findings landed on the same day and they have one cause.

**The measurement.** `tools/ancestry_geography.py` read the `PrevalenceGeographic` field
that no layer here had opened, over Orphanet's 17,108 prevalence records
(`references/rare-disease-ancestry.md` §1):

- **386 of 525 (73.5 %)** disorders with records in more than one country fall into
  **different prevalence classes** in different countries. Prevalence is not a scalar.
- **55.6 %** of tagged records assert `Worldwide` — a claim of population-independence that
  §1c shows is false for three quarters of the cases where it can be tested.
- Representation by region against population: Europe **8.10**, Africa **0.07** — a factor
  of 116.
- The catalogue's entire vocabulary for a population is **one untyped string**,
  `Specific population`: 105 records, 87 disorders, no identifier, nothing to join on. It
  is currently hiding Canavan disease, mucolipidosis II and IV and cystinosis — Ashkenazi
  founder disorders the catalogue can record but cannot name.

**The standard.** `references/standards.md` lists FAIR among the canons this project answers
to. FAIR governs data *movement*. It is silent on who a dataset is about and who decides
what happens to it, and there is a framework for exactly that — the **CARE Principles for
Indigenous Data Governance** (Carroll et al., *Data Science Journal*, 2020; Hudson,
Garrison, Sterling et al., *Nat Rev Genet*, 2020). CARE is absent from the standards file
and from the code.

The two findings meet at the same hole: **this architecture has nowhere to write down which
population a number is about.** Today that is a statistical defect. The moment any
patient-derived, biobank or registry data enters, it becomes an ethical one, and it would
then be designed under deadline.

## Decision

Two parts, taken together because separating them reproduces the hole.

**1. Population becomes a typed field in the data contracts,** not a string and not an
inference from geography. Minimally it carries: the population as named by its source, the
identifier scheme if any, whether the value is a *place of measurement* or a *described
population* (these are different facts and the catalogue conflates them), and the record's
provenance. Where a source has no population, the field is **explicitly unknown** — the same
modelling choice `references/rare-disease-lexicon.md` already makes, where the unknown is a
value rather than a blank.

**2. `references/standards.md` gains a CARE row beside FAIR,** with its conformance status
set honestly: *not applicable to current inputs — all are public aggregates — and not
designed for.* A standard listed with an accurate non-conformance is worth more than a
standard omitted.

Consistent with §7 of the documentation standard, `Worldwide` is then rendered as **an
assertion of population-independence**, never as a default or an absence.

## Consequences

**Gained.** A prevalence, a cohort size and a frequency prior can each say whose they are.
Stage 2's cohort arithmetic stops silently averaging three quarters of disorders across
populations that disagree. Stage 6 can carry a panel's composition next to `null_blocks`,
which is the fix `rare-disease-ancestry.md` §3 asks for. And the ethical field exists before
the data that needs it arrives.

**Paid.** Every adapter that emits a prevalence or a frequency gains a field it must fill or
explicitly mark unknown — and "explicitly unknown" will be the honest answer for the
**5,773 of 6,728** disorders with no placed record at all. That is a lot of unknowns to
write, and writing them is the point: the current architecture reports the same ignorance as
silence.

**Risk, and the reason this is `proposed` and not `accepted`.** A population field invites
exactly the inference this project must not make — treating a place of measurement as a
genetic ancestry group. The field's *type* is the mitigation: place-of-measurement and
described-population are separate values, and no code path may coerce one into the other.
If that separation cannot be enforced in the contract, this ADR should be rejected rather
than weakened.

## How this will be scored

Falsifiable, in the manner of 0004:

- The 73.5 % is a proportion over 525 disorders and **has no interval**
  ([`../audit.md`](../audit.md) A6). If a bootstrap puts it below 50 %, the "prevalence is
  not a scalar" premise weakens and the cost/benefit of part 1 changes.
- If the same geographic skew appears in a **non-European** rare-disease registry, §1b is
  the field's problem and the design stands. If it does not, part of the skew is Orphanet's
  remit and the framing must be restated — `rare-disease-ancestry.md` §7.1.
