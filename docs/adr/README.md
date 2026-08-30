# Architecture decision records

> **Role:** decisions recorded with their context and consequences, written **before** the
> change where possible — *nemawashi*, laying the groundwork rather than narrating it
> afterwards (`../references/standards.md` §2).
> **Last revised:** 2026-08-29 · **State:** nine records. 0001-0003 are ⚠️ back-filled from
> decisions already taken; 0004 was written before the work and scored correct; 0005, 0006 and
> 0007 are open. **0006 is written *after* the thresholds it governs**, and it says so — it
> registers four thresholds chosen after seeing the data rather than pretending otherwise.
> **0007 is written *before* the tool it governs**, and it governs a catalogue of ninety
> proposed formalisms of which exactly three are measured.

Format: Nygard's. Context, decision, consequences, status. Each record carries the
repository's Role / Last revised header **and** Nygard's Status / Supersedes / Governs line;
the status table below is their index. A record is never edited once
accepted — it is superseded by a later record that names it.

| # | Decision | Status |
|---|---|---|
| [0001](0001-empirical-null.md) | Fit the null empirically from controls, not parametrically | accepted (⚠️ back-filled) |
| [0002](0002-reduce-argument.md) | Make the sampling model an explicit `reduce=` argument and refuse to guess | accepted (⚠️ back-filled) |
| [0003](0003-positive-control-gates.md) | A failed positive control blocks the shortlist | accepted (⚠️ back-filled) |
| [0004](0004-block-nulls.md) | Fit nulls on blocks, not rows | accepted — prediction scored correct |
| [0005](0005-population-as-a-typed-field.md) | Population is a typed field, and CARE joins FAIR in the standards | proposed |
| [0006](0006-pre-registered-thresholds.md) | Thresholds are pre-registered, dated, and frozen against target contact | proposed |
| [0007](0007-theory-enters-by-measurement.md) | A theory enters this repository only as a measurement | proposed |
| [0008](0008-layouts-are-computed-once.md) | A layout is computed once, in Python, and versioned with the artefact | proposed (⚠️ back-filled same day) |
| [0009](0009-sections-are-declared.md) | A section is declared once, and nothing can offer one that cannot be drawn | proposed |
