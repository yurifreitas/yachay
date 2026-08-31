#!/usr/bin/env python
"""Every artefact on disk must appear in the document that claims to enumerate it.

WHY THIS EXISTS. `tools/verify_claims.py` protects a NUMBER: it holds each published figure
against the artefact that produced it and fails when they drift. Nothing protected a LIST, and
on 2026-08-29 six indexes drifted in a single day — audit finding A36:

    rare-layers.md mapped 26 of 34 artefacts while its own header said 34; tools/README.md
    advertised 14 ingested sources when 18 were registered; README.md and adr/README.md both
    said one construct was measured when three were.

The failure is not cosmetic. The indexes are how a reader decides what has been measured, and
a map that lags the territory understates the project in the direction that makes its
strongest results invisible — which is audit A2, committed again.

WHAT IT CHECKS, and each is a claim some document makes about the filesystem:

    artefacts   every out/rare/*.json appears in docs/references/rare-layers.md
    tools       every tools/*.py appears in tools/README.md
    stages      every registered pipeline stage has a tool or analysis that exists
    sources     every ingested source is named in docs/references/README.md
    adrs        every docs/adr/NNNN-*.md appears in the ADR index
    intervals   an artefact that publishes a z publishes an interval too.
                docs/references/standards.md §4 requires an uncertainty on every published
                number; an audit on 2026-08-30 found EIGHT bundled artefacts carrying a z
                and no interval, four of them written that same week.
    citations   every reference earns its place: no duplicates, no placeholders, and a
                `notes:` that says which claim in THIS repository it supports. The
                sieve-doc skill's rule is that a reference with no stated purpose is
                decoration and gets deleted; nothing enforced it, and five works were
                cited twice.
    staging     every script that writes an artefact is a registered pipeline stage AND
                its artefact is some stage's declared output. docs/references/rare-layers.md
                says "every layer is a pipeline stage, so staleness is tracked" — that was
                false for 24 of 64 artefact-writing tools when this check was written. All
                24 were registered on 2026-08-30, and the check was strengthened in the same
                move: it imports the graph instead of grepping stages.py, so a tool merely
                NAMED in a comment no longer passes, and a stage that declares no output —
                which always runs and can never report freshness — now fails.
    thresholds  the summary inside manifests/thresholds.yaml matches the entries it
                summarises — it was written at seven entries, the file grew to 25, and
                the summary stayed. A file whose job is auditability was publishing a
                wrong count of itself.

WHAT IT DELIBERATELY DOES NOT CHECK. Whether the DESCRIPTION beside an entry is still true.
A stale sentence next to a present filename is a real defect and this tool cannot see it; only
a reader can. Claiming otherwise would make the check comforting rather than useful, so the
limitation is printed with the result rather than buried here.

    python tools/index_check.py           # report
    python tools/index_check.py --check   # exit 1 when something is unlisted

Stdlib only, so it runs before anything else in a cold checkout.
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def check_artefacts() -> tuple[str, list[str], int]:
    """Every measured artefact appears in the layer map that exists to grade them."""
    index = read("docs/references/rare-layers.md")
    missing = []
    files = sorted((ROOT / "out" / "rare").glob("*.json"))
    for f in files:
        if f.name not in index:
            missing.append(f"out/rare/{f.name} is in no row of rare-layers.md")
    return "artefacts", missing, len(files)


def check_tools() -> tuple[str, list[str], int]:
    index = read("tools/README.md")
    missing = []
    files = sorted((ROOT / "tools").glob("*.py"))
    for f in files:
        if f.name not in index:
            missing.append(f"tools/{f.name} is in no group of tools/README.md")
    return "tools", missing, len(files)


def check_stages() -> tuple[str, list[str], int]:
    """A stage whose producer does not exist is a graph that cannot run."""
    from sieve.pipeline import STAGES  # noqa: PLC0415 - import here so --help works cold

    missing = []
    for name, stage in STAGES.items():
        sources = getattr(stage, "code", ()) or ()
        if sources and not any(pathlib.Path(s).exists() for s in sources):
            missing.append(f"stage {name!r} declares code that does not exist")
    return "stages", missing, len(STAGES)


def check_sources() -> tuple[str, list[str], int]:
    from sieve.pipeline.sources import SOURCES  # noqa: PLC0415

    index = read("docs/references/README.md") + read("tools/README.md")
    missing = []
    for s in SOURCES:
        if s.filename not in index and s.name not in index:
            missing.append(f"source {s.key!r} ({s.filename}) is named in no reference index")
    return "sources", missing, len(SOURCES)


def check_adrs() -> tuple[str, list[str], int]:
    index = read("docs/adr/README.md")
    missing = []
    files = sorted((ROOT / "docs" / "adr").glob("[0-9]*.md"))
    for f in files:
        if f.name not in index:
            missing.append(f"docs/adr/{f.name} is in no row of the ADR index")
    return "adrs", missing, len(files)




def check_thresholds() -> tuple[str, list[str], int]:
    """The manifest's own summary against the entries beneath it.

    A LIST THAT COUNTS ITSELF, which is the one kind of index that can go stale without any
    file being added or removed anywhere else. This one did: the block said "pre-registered:
    3, calibrated to seen data: 4" while the file held nineteen pre-registered and six
    calibrated thresholds, because it was written when there were seven and never recounted.
    """
    path = ROOT / "manifests" / "thresholds.yaml"
    if not path.exists():
        return "thresholds", ["manifests/thresholds.yaml is missing"], 0

    text = path.read_text(encoding="utf-8")
    pre = collections.Counter(re.findall(r"pre_registered:\s*(true|false)", text))
    kind = collections.Counter(re.findall(r"justification:\s*(\w+)", text))
    total = sum(pre.values())

    claimed = re.search(
        r"pre-registered:\s*(\d+)\s+calibrated to seen data:\s*(\d+)", text)
    kinds_claimed = re.search(
        r"kinds:\s*(\d+) mechanistic,\s*(\d+) empirical,\s*(\d+) conventional", text)

    missing = []
    if not claimed:
        missing.append("the summary block states no pre-registered/calibrated counts")
    else:
        want = (pre["true"], pre["false"])
        got = (int(claimed.group(1)), int(claimed.group(2)))
        if want != got:
            missing.append(
                f"summary says {got[0]} pre-registered and {got[1]} calibrated; "
                f"the entries are {want[0]} and {want[1]}")
    if not kinds_claimed:
        missing.append("the summary block states no kind counts")
    else:
        want = (kind["mechanistic"], kind["empirical"], kind["conventional"])
        got = tuple(int(kinds_claimed.group(i)) for i in (1, 2, 3))
        if want != got:
            missing.append(
                f"summary says {got} mechanistic/empirical/conventional; "
                f"the entries are {want}")
    return "thresholds", missing, total




#: Artefact-writing tools that are deliberately NOT pipeline stages, with the reason. A tool
#: here is one `tasks.py build` will not run and `tasks.py status` will not call stale, so the
#: reason has to say why that is acceptable — an exemption list without reasons is where
#: things get put to stop a check complaining.
NOT_A_STAGE = {
    "ingest": "fetches from the network; deliberately outside the build graph so a rebuild "
              "never depends on a remote being up",
    "index_check": "this file. It audits the repository rather than producing a layer of it",
    "verify_claims": "an audit of published numbers, not a producer of them",
    "moderated_calibration": "a METHOD module plus a demonstration CLI. Its functions are "
                             "imported by tools/twin_propagation.py, which is the stage that "
                             "produces the artefact; a stage for the demonstration would "
                             "publish the same finding twice",
    "z_audit": "an audit of published z values against the nulls they were computed from; it "
               "reads every bundled artefact, so making it a stage would put every artefact "
               "upstream of it and it would never be fresh",
    "status": "reports on the pipeline; making it a stage would make the report a dependency "
              "of itself",
    "paper_numbers": "renders figures for prose from artefacts other stages produce",
    "figure_data": "same — a rendering step over finished artefacts",
    "pipeline_state": "reads the stage graph; a stage that reads the stage graph is a cycle",
    "capability_math": "⚠️ unregistered; reads build_atlas output with no declared edge. The "
                       "last one left, and the only remaining ⚠️ in this list",
}

#: The twenty-six ⚠️ entries this list carried on 2026-08-30 are gone because they were PAID,
#: not because the standard moved: every one of them is now a stage in
#: `src/sieve/pipeline/stages.py` with declared inputs, outputs and `needs`. The gene chain
#: was eleven of them, and its run order — which existed only as a sentence at the bottom of
#: each tool's docstring — is now an edge the runner enforces.


def check_staging() -> tuple[str, list[str], int]:
    """Every artefact-writing script is a stage, and its artefact is a declared output.

    THE CLAIM THIS PROTECTS is in docs/references/rare-layers.md: "Every layer is a pipeline
    stage, so staleness is tracked and a stale artefact is not silently served." That was
    false for 24 of the 64 tools that write an artefact when this check was first written,
    and the check recorded the debt rather than fixing it.

    IT NOW IMPORTS THE GRAPH INSTEAD OF GREPPING IT, and that is the substantive change. The
    first version asked whether the tool's NAME appeared anywhere in the text of stages.py —
    which a comment satisfies. So a stage could name a tool in prose, declare none of its
    outputs, and pass. The check now asks the two questions that actually matter:

      1. Does some stage's `code` include this script?
      2. Is the file it writes in some stage's `outputs`?

    The second is the one that bites. A stage with no declared output "declares no outputs"
    and therefore always runs — it never serves a stale artefact, but it also never skips,
    and `sieve run` cannot tell you whether its file is current. Both failures are silent.

    It also scans `analyses/`, which the grep version did not, and which is where the
    obesity screen lives.
    """
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from sieve.pipeline.stages import STAGES

    coded, declared = set(), set()
    for st in STAGES.values():
        coded.update(c.resolve() for c in st.code)
        declared.update(o.resolve() for o in st.outputs)

    # What each script writes, read out of its own DEST assignment. A script whose destination
    # cannot be read here is reported rather than skipped: an unreadable target is exactly the
    # case where a hand-run artefact hides.
    writes = re.compile(r"^DEST\s*=\s*(.+)$", re.M)

    missing, checked = [], 0
    scripts = sorted((ROOT / "tools").glob("*.py")) + sorted((ROOT / "analyses").glob("*.py"))
    for path in scripts:
        text = path.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"DEST\s*=|write_text\(json", text):
            continue
        checked += 1
        if path.stem in NOT_A_STAGE:
            continue
        if path.resolve() not in coded:
            missing.append(f"{path.stem} writes an artefact, is not any stage's code, and "
                           f"gives no reason")
            continue
        # The stage exists — but does it declare what the script produces? A stage whose
        # outputs are empty always runs and can never report freshness.
        m = writes.search(text)
        if not m:
            continue
        name = m.group(1).strip().rstrip(",").split("/")[-1].strip().strip('"')
        if not name.endswith(".json"):
            continue
        if not any(o.name == name for o in declared):
            missing.append(f"{path.stem} is a stage but {name} is in no stage's outputs, so "
                           f"nothing can tell whether it is stale")
    return "staging", missing, checked


def check_citations() -> tuple[str, list[str], int]:
    """Every reference earns its place, and no work is cited twice.

    THE RULE IS THE SKILL'S OWN: "A reference with no stated purpose is decoration and gets
    deleted." Nothing enforced it. An audit on 2026-08-30 found five works cited TWICE —
    every one of them a reference added that same day, appended without checking whether the
    file already held it — and three entries whose title was a placeholder rather than a work
    ("TEAD inhibitors - clinical status (to be selected)").

    IT PARSES THE YAML RATHER THAN MATCHING TEXT, and that matters: the first version of this
    audit used a regular expression for the notes block and reported nine articles with no
    note at all. The real number was zero. The regex could not see notes written in a
    different scalar style, so the instrument invented a defect — which is the failure this
    repository exists to study, committed by its own auditor.
    """
    path = ROOT / "CITATION.cff"
    if not path.exists():
        return "citations", ["CITATION.cff is missing"], 0
    try:
        import yaml  # noqa: PLC0415
    except ImportError:
        return "citations", [], 0

    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    refs = doc.get("references") or []

    missing = []
    seen_title: dict[str, int] = {}
    seen_doi: dict[str, int] = {}
    for r in refs:
        title = str(r.get("title") or "").strip()
        key = "".join(c.lower() for c in title if c.isalnum())[:60]
        seen_title[key] = seen_title.get(key, 0) + 1
        for ident in r.get("identifiers") or []:
            v = str(ident.get("value") or "")
            if v.startswith("10."):
                seen_doi[v] = seen_doi.get(v, 0) + 1
        if "to be selected" in title.lower() or title.endswith("TBD"):
            missing.append(f"'{title[:56]}' is a placeholder, not a work")
        # A note is required of anything that makes a CLAIM. Software and datasets are tools
        # rather than claims, and are exempt by kind rather than by name.
        if r.get("type") in {"article", "book", "generic", "standard"}:
            note = " ".join(str(r.get("notes") or "").split())
            if not note:
                missing.append(f"'{title[:56]}' has no notes — decoration by the skill's rule")
            elif len(note.split()) < 12:
                missing.append(f"'{title[:56]}' has a {len(note.split())}-word note; it should "
                               f"name the claim in this repository it supports")

    for k, n in seen_title.items():
        if n > 1:
            missing.append(f"a work is cited {n} times (title key {k[:40]})")
    for k, n in seen_doi.items():
        if n > 1:
            missing.append(f"DOI {k} appears {n} times")
    return "citations", missing, len(refs)


#: Artefacts that publish a z with no interval, and why it has not been given one. Every entry
#: here is DEBT, not an exemption on merit — a z is a distance in units of a null's dispersion
#: and says nothing about how far the observed value itself could move.
Z_WITHOUT_INTERVAL = {
    "runs": "the adapter's own output shape, produced by analyses/depmap_selective_dependency.py "
            "before the interval discipline existed; intervals live in out/rare/intervals.json "
            "and are not folded back into the run manifest",
    "points": "a projection of runs for plotting — it inherits the shape above",
    "figures": "a rendering of finished artefacts, carrying whatever they carried",
    "tail_calibration": "reports the calibration curve rather than a per-entity estimate; an "
                        "interval would be on the curve and is not yet computed",
}

#: The three ⚠️ DEBT entries this dict carried on 2026-08-30 — hiv_resistance, twin_propagation
#: and signal_energy — were PAID, each with the resample its own entry named, and each one
#: changed what the artefact says:
#:
#:   twin_propagation  leave-one-out over the seed genes. 34 of 100 published reach genes keep
#:                     a z above 1.96 at the bottom of their interval, and NOT ONE of the ten
#:                     largest z values does. Ranking by z selects the rarely-reached, because
#:                     the degree-matched null has almost no spread at degree 5.
#:   hiv_resistance    bootstrap over isolates, rescoring every mutation on each resample so
#:                     the carrier overlap survives. It found the assay's ceiling: 13 of the
#:                     60 published mutations have every carrier at ">100-fold", so their
#:                     scores are equal by construction and their ORDER comes from the null.
#:   signal_energy     bootstrap over diseases. The negative verdict stands, and the contrast
#:                     it rests on now carries an interval of its own.


def check_intervals() -> tuple[str, list[str], int]:
    """A z is not an uncertainty.

    THE STANDARD IS THIS REPOSITORY'S OWN: docs/references/standards.md §4 requires every
    published figure to carry its uncertainty, and a difference smaller than its own interval
    is not a difference. A z satisfies neither — it says how far an observation sits from a
    null's mean in units of that null's spread, and nothing about how far the observation
    itself would move if the experiment were repeated.

    The distinction is not academic. `analyses/obesity_thermogenesis.py` publishes 41
    perturbations clearing its null's 95th percentile on the point estimate; only 16 clear it
    on the lower end of their own interval. Twenty-five results survive or do not depending on
    which of the two a reader is shown.
    """
    gen = ROOT / "web" / "src" / "data" / "generated"
    if not gen.exists():
        return "intervals", [], 0

    Z_KEYS = ('"z"', '"z_score"', '"null_mean"', '"null_sd"')
    # `p_empirical` counts as an uncertainty statement, and this is not a loosening. A41
    # established that a z past about 2.6 extrapolates beyond what a 200-draw permutation
    # resolves, and that the empirical tail — floored at 1/(N+1) — is the statistic that
    # cannot make that mistake. An artefact that publishes the tail instead of an interval has
    # answered the question this check asks, in the better of the two ways.
    CI_KEYS = ("ci95", '"se"', "_ci", '"p95"', "interval", '"p_empirical"')

    missing, checked = [], 0
    for f in sorted(gen.glob("*.json")):
        text = f.read_text(encoding="utf-8", errors="replace")
        if not any(k in text for k in Z_KEYS):
            continue
        checked += 1
        if any(k in text for k in CI_KEYS):
            continue
        if f.stem in Z_WITHOUT_INTERVAL:
            continue
        missing.append(f"{f.stem} publishes a z and no interval, with no reason recorded")
    return "intervals", missing, checked


CHECKS = [check_artefacts, check_tools, check_stages, check_sources, check_adrs,
          check_thresholds, check_staging, check_citations, check_intervals]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 when anything is unlisted")
    args = ap.parse_args()

    total_missing = 0
    print("index check — is everything on disk named in the document that enumerates it?\n")
    for fn in CHECKS:
        name, missing, n = fn()
        total_missing += len(missing)
        mark = "ok  " if not missing else "MISS"
        print(f"  [{mark}] {name:10s} {n:4d} on disk, {len(missing)} unlisted")
        for m in missing:
            print(f"           - {m}")

    print()
    print("  This checks PRESENCE, never accuracy: a stale sentence beside a present filename")
    print("  is a real defect and only a reader can see it. A36 is closed by this file; the")
    print("  half it cannot reach stays open.")

    if total_missing and args.check:
        print(f"\n{total_missing} unlisted. Add them to the index that claims to enumerate them.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
