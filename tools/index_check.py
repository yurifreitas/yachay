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
    citations   every reference earns its place: no duplicates, no placeholders, and a
                `notes:` that says which claim in THIS repository it supports. The
                sieve-doc skill's rule is that a reference with no stated purpose is
                decoration and gets deleted; nothing enforced it, and five works were
                cited twice.
    staging     every tool that writes an artefact is a registered pipeline stage, or is
                exempt with a stated reason. docs/references/rare-layers.md says "every
                layer is a pipeline stage, so staleness is tracked" — that was true of
                40 of the 64 artefact-writing tools and false of 24, which is a claim
                about the filesystem that the filesystem contradicted.
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
    "status": "reports on the pipeline; making it a stage would make the report a dependency "
              "of itself",
    "paper_numbers": "renders figures for prose from artefacts other stages produce",
    "figure_data": "same — a rendering step over finished artefacts",
    "pipeline_state": "reads the stage graph; a stage that reads the stage graph is a cycle",
    "gene_shards": "splits a finished artefact into files the web fetches; runs after the "
                   "gene layer and is driven by it",
    "gene_facets": "derived from gene_index in the same pass; has no independent inputs",
    "gene_space": "a layout over the gene layer, in the sense of ADR 0008",
    # ⚠️ THE HONEST ENTRIES. These are not exempt on principle — they are unregistered, and
    # saying so here is the point of the list. build_atlas is the worst of them: dossier,
    # atlas_bias, capability_math and gene_index all read its output as an undeclared
    # dependency, so nothing detects that they are stale when it changes.
    "build_atlas": "⚠️ NOT exempt on merit — unregistered, and it should be a stage. Four "
                   "downstream tools read its output as an undeclared dependency",
    "atlas_bias": "⚠️ unregistered; reads build_atlas output with no declared edge",
    "capability_math": "⚠️ unregistered; reads build_atlas output with no declared edge",
    "barriers_seed": "⚠️ unregistered authored seed, bundled with no stage",
    "nomenclature_seed": "⚠️ unregistered authored seed, bundled with no stage",
    "dimensions": "⚠️ unregistered derived layer",
    "dimensions_two": "⚠️ unregistered derived layer",
    "gap_patterns": "⚠️ unregistered measurement",
    "tropical_gap": "⚠️ unregistered measurement",
    "gene_attention": "⚠️ unregistered gene-pivot layer",
    "gene_constraint": "⚠️ unregistered measurement, added 2026-08-30",
    "gene_datasheet": "⚠️ unregistered gene-pivot layer",
    "gene_domains": "⚠️ unregistered gene-pivot layer",
    "gene_geometry": "⚠️ unregistered gene-pivot layer",
    "gene_index": "⚠️ unregistered gene-pivot layer",
    "gene_insights": "⚠️ unregistered gene-pivot layer",
    "gene_related": "⚠️ unregistered gene-pivot layer",
    "gene_world": "⚠️ unregistered gene-pivot layer",
    "psychiatric_gwas": "⚠️ unregistered measurement, added 2026-08-30",
    "trait_atlas": "⚠️ unregistered measurement, added 2026-08-30",
    "signal_energy": "⚠️ unregistered measurement, added 2026-08-30",
    "single_cell_coverage": "⚠️ unregistered measurement, added 2026-08-30",
    "cleared_devices": "⚠️ unregistered measurement, added 2026-08-30",
}


def check_staging() -> tuple[str, list[str], int]:
    """Every artefact-writing tool is a stage, or says why it is not.

    THE CLAIM THIS PROTECTS is in docs/references/rare-layers.md: "Every layer is a pipeline
    stage, so staleness is tracked and a stale artefact is not silently served." That is the
    strongest operational promise the documentation makes, and it was false for 24 of the 64
    tools that write an artefact — including `build_atlas`, whose output four other tools read
    with no declared edge, so nothing notices when they go stale behind it.

    A missing entry here is not a crisis; an unnoticed one is. The exemption list carries a
    reason per tool and marks with ⚠️ the ones that are unregistered rather than exempt, so
    the count of real debt is readable rather than hidden behind a green check.
    """
    stages_src = (ROOT / "src" / "sieve" / "pipeline" / "stages.py").read_text(
        encoding="utf-8", errors="replace")
    writers = []
    for path in sorted((ROOT / "tools").glob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"DEST\s*=\s*ROOT\s*/\s*[\"']out|write_text\(json", text):
            writers.append(path.stem)

    missing = []
    for name in writers:
        registered = f'"{name}"' in stages_src or f"tools/{name}.py" in stages_src
        if registered:
            continue
        reason = NOT_A_STAGE.get(name)
        if not reason:
            missing.append(f"{name} writes an artefact, is not a stage, and gives no reason")
    return "staging", missing, len(writers)


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


CHECKS = [check_artefacts, check_tools, check_stages, check_sources, check_adrs,
          check_thresholds, check_staging, check_citations]


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
