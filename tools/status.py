#!/usr/bin/env python
"""The project's state, derived from the project rather than typed out.

WHY THIS IS GENERATED AND NOT WRITTEN. A hand-maintained checklist is a claim about a
repository that stops being checked the moment it is committed, and this one has now been
caught three separate times shipping exactly that:

  * `CITATION.cff` advertised a resolved anomaly as open (audit A1)
  * `sieve.stages.target`'s thresholds were called "a judgement" with no record of whether
    the data had been seen when they were chosen (A28)
  * `lib/palette.ts` said "VALIDATED" and cited a validator **that was not in the
    repository** (A33)

Every one of those is the same failure: prose asserting a state nobody could recompute. A
checklist of progress is the most tempting possible instance of it, so this file computes the
checklist and `docs/status.md` is its output, regenerated rather than edited.

WHAT IT MEASURES, and the distinctions it refuses to blur:

  **registered vs read.** A dataset with a path constant is not a dataset anyone reads.
  `OmicsCNGene.csv` is 1.33 GB on disk, has a constant in `pipeline/paths.py`, and no read
  site anywhere — so it counts as ingested-and-unread, not as a capability.

  **present vs fresh.** A stage whose outputs exist may still be stale against its inputs or
  its own source. `Stage.is_stale()` already knows; this reports it rather than reimplementing.

  **claimed vs true.** The last section is the point of the file: statements the repository
  makes about itself that the filesystem contradicts. That is where a status document usually
  goes wrong, so it is the one section that can fail the build.

    python tools/status.py            # write out/status.json and docs/status.md
    python tools/status.py --check    # exit non-zero if a contradiction is found

Pure standard library plus PyYAML, so it can run before anything else in a cold checkout.
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import subprocess
import sys
import datetime as _dt

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

OUT = ROOT / "out"
DOC = ROOT / "docs" / "status.md"

#: Directories whose Python is "the analysis", as opposed to plumbing.
CODE_DIRS = ("tools", "analyses", "src/sieve")


# --------------------------------------------------------------------------- data on disk

#: Functions that constitute actually READING a file, as opposed to naming one.
READ_CALLS = {"read_csv", "read_table", "read_parquet", "open", "load_matrix",
              "load_gene_set", "read_text", "read_bytes", "loadtxt", "genfromtxt"}


def _source_keys() -> dict[str, str]:
    """`BY_KEY` registry key -> filename, read out of pipeline/sources.py.

    Most of this repository reads its inputs as `BY_KEY["hpo_genes"].dest`, never naming the
    file. A reader-detector that only understands literal filenames therefore reports almost
    everything as unread — which is a status document lying in the most damaging direction it
    can, since "we have never looked at this" is the finding that provokes work.
    """
    text = (ROOT / "src" / "sieve" / "pipeline" / "sources.py").read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for block in text.split("Source(")[1:]:
        k = re.search(r'key\s*=\s*"([^"]+)"', block)
        f = re.search(r'filename\s*=\s*"([^"]+)"', block)
        if k and f:
            out[k.group(1)] = f.group(1)
    return out


SOURCE_KEYS = _source_keys()


def _read_sites(py: str) -> set[str]:
    """Filenames that appear inside a read call in this source.

    An AST walk rather than a grep, because the distinction the whole file rests on is
    between a *mention* and a *use*. `CN_GENE = DEPMAP / "OmicsCNGene.csv"` mentions a file;
    `pd.read_csv(CN_GENE)` uses it. A grep cannot tell those apart, and the difference is
    exactly what an honest status report has to get right.
    """
    try:
        tree = ast.parse(py)
    except SyntaxError:
        return set()
    names: set[str] = set()

    # Constants bound to a name, so `pd.read_csv(MODEL)` resolves back to Model.csv.
    bindings: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                for sub in ast.walk(node.value):
                    if isinstance(sub, ast.Constant) and isinstance(sub.value, str) \
                            and sub.value.endswith((".csv", ".tsv", ".txt", ".gz", ".obo")):
                        bindings[target.id] = sub.value

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        fname = fn.attr if isinstance(fn, ast.Attribute) else \
            fn.id if isinstance(fn, ast.Name) else ""
        if fname not in READ_CALLS:
            continue
        targets = list(node.args) + [k.value for k in node.keywords]
        if isinstance(fn, ast.Attribute):
            targets.append(fn.value)     # BY_KEY["x"].dest.open() / path.read_text()
        for arg in targets:
            for sub in ast.walk(arg):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    names.add(sub.value.split("/")[-1])
                elif isinstance(sub, ast.Name) and sub.id in bindings:
                    names.add(bindings[sub.id].split("/")[-1])
                elif isinstance(sub, ast.Attribute):
                    names.add(sub.attr)          # paths.MODEL -> "MODEL"
                    # BY_KEY["hpo_genes"].dest -> genes_to_disease.txt
                    if isinstance(sub.value, ast.Subscript):
                        idx = sub.value.slice
                        if isinstance(idx, ast.Constant) and idx.value in SOURCE_KEYS:
                            names.add(SOURCE_KEYS[idx.value])
                elif isinstance(sub, ast.Subscript):
                    idx = sub.slice
                    if isinstance(idx, ast.Constant) and idx.value in SOURCE_KEYS:
                        names.add(SOURCE_KEYS[idx.value])
    return names


#: Every line of source in the repository, for the weaker "is it mentioned at all" test.
ALL_TEXT = ""


def data_inventory() -> list[dict]:
    """Every ingested file, its size, and what is known about whether anything reads it."""
    global ALL_TEXT
    chunks = []
    for d in CODE_DIRS:
        for py in (ROOT / d).rglob("*.py"):
            if "__pycache__" not in py.parts:
                chunks.append(py.read_text(encoding="utf-8", errors="replace"))
    ALL_TEXT = "\n".join(chunks)

    sources: dict[str, set[str]] = {}
    for d in CODE_DIRS:
        for py in (ROOT / d).rglob("*.py"):
            if "__pycache__" in py.parts:
                continue
            try:
                hits = _read_sites(py.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            for h in hits:
                sources.setdefault(h, set()).add(str(py.relative_to(ROOT)).replace("\\", "/"))

    # A read site may name the CONSTANT rather than the filename, so both are consulted.
    const_for: dict[str, str] = {}
    paths_py = (ROOT / "src" / "sieve" / "pipeline" / "paths.py").read_text(encoding="utf-8")
    for m in re.finditer(r'^([A-Z_0-9]+)\s*=.*?"([^"]+\.\w+)"', paths_py, re.M):
        const_for[m.group(2)] = m.group(1)

    rows = []
    for f in sorted((ROOT / "data").rglob("*")):
        if not f.is_file() or f.suffix in (".json",) and f.parent.name == "data":
            continue
        name = f.name
        readers = set(sources.get(name, set()))
        const = const_for.get(name)
        if const:
            readers |= sources.get(const, set())
        # THREE STATES, BECAUSE A BINARY HERE WOULD BE WRONG.
        #
        # A direct read site is provable: `pd.read_csv(paths.MODEL)`. Its absence is NOT
        # proof of disuse — `dm.load_matrix(DATA)` takes a DIRECTORY and opens
        # CRISPRGeneEffect.csv inside the adapter, so the 428.7 MB matrix every result in
        # this repository rests on has no read site naming it. Reporting that as "never
        # read" would be a status document confidently asserting the opposite of the truth
        # about its own primary input.
        #
        # So the strong claim is reserved for what can be shown: a file that appears NOWHERE
        # in the source, by name or by constant, is genuinely untouched. Everything between
        # is reported as "referenced, no direct read site", which is what is actually known.
        mentioned = name in ALL_TEXT or (const is not None and const in ALL_TEXT)
        state = ("read" if readers else
                 "referenced" if mentioned else "untouched")
        rows.append({
            "file": str(f.relative_to(ROOT)).replace("\\", "/"),
            "megabytes": round(f.stat().st_size / 1e6, 1),
            "readers": sorted(readers),
            "state": state,
            "read": bool(readers),
            "registered": bool(const),
        })
    return rows


# ------------------------------------------------------------------------------- sections

def stage_rows() -> list[dict]:
    from sieve.pipeline.stages import STAGES
    rows = []
    for name, st in STAGES.items():
        stale, why = st.is_stale()
        # A verification stage is never cached BY DESIGN, so reporting it as "stale" pads the
        # headline with three permanent entries that can never be cleared — a status number
        # nobody can act on is a status number nobody reads.
        always = "never cached" in why
        rows.append({
            "alwaysRuns": always,
            "stage": name,
            "outputs": [p.name for p in st.outputs],
            "present": all(p.exists() for p in st.outputs),
            "missingInputs": [p.name for p in st.missing_inputs()],
            "stale": bool(stale) and not always,
            "why": why,
        })
    return rows


def audit_rows() -> list[dict]:
    text = (ROOT / "docs" / "audit.md").read_text(encoding="utf-8")
    rows = []
    for m in re.finditer(r"^### (A\d+[a-z]?) — (.+?) · \*\*(.+?)\*\*", text, re.M):
        rows.append({"id": m.group(1), "title": m.group(2).strip(),
                     "state": m.group(3).split(",")[0].strip()})
    return rows


def adr_rows() -> list[dict]:
    rows = []
    for f in sorted((ROOT / "docs" / "adr").glob("[0-9]*.md")):
        head = f.read_text(encoding="utf-8")[:600]
        m = re.search(r"^\*\*Status:\*\*\s*(\w+)", head, re.M)
        title = re.search(r"^#\s*(.+)", head, re.M)
        rows.append({"file": f.name, "status": m.group(1) if m else "unknown",
                     "title": title.group(1).strip() if title else f.stem})
    return rows


def threshold_rows() -> list[dict]:
    path = ROOT / "manifests" / "thresholds.yaml"
    if not path.exists():
        return []
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [{"id": t["id"], "module": t["module"], "value": t["value"],
             "preRegistered": bool(t.get("pre_registered")),
             "justification": t.get("justification")}
            for t in doc.get("thresholds", [])]


def doc_rows() -> list[dict]:
    """Docs, and whether they carry the header `.claude/skills/sieve-doc` mandates."""
    rows = []
    for f in sorted((ROOT / "docs").rglob("*.md")):
        head = f.read_text(encoding="utf-8", errors="replace")[:400]
        rows.append({
            "file": str(f.relative_to(ROOT)).replace("\\", "/"),
            "hasRole": "**Role:**" in head,
            "hasRevised": "**Last revised:**" in head,
        })
    return rows


def web_rows() -> list[dict]:
    """Emitted datasets, and whether any component actually consumes them.

    An emitted payload nobody reads is dead weight in the bundle or in `public/`, and it is
    invisible: nothing errors, the file is simply shipped and ignored.
    """
    web = ROOT / "web"
    if not web.exists():
        return []
    build = (web / "scripts" / "build-data.mjs").read_text(encoding="utf-8")
    emitted = sorted({m.group(1) for m in re.finditer(r'emit\(\s*[`"]([\w$-{}]+)', build)
                      if "$" not in m.group(1)})
    src = "\n".join(p.read_text(encoding="utf-8", errors="replace")
                    for p in (web / "src").rglob("*.ts*"))
    rows = []
    for name in emitted:
        used = bool(re.search(rf'\b{re.escape(name)}\b', src))
        rows.append({"dataset": name, "consumed": used})
    return rows


# ------------------------------------------------------- the section that can fail a build

#: Phrases a file may use about ANOTHER file, paired with what must then be true on disk.
ABSENCE_CLAIMS = [
    r"not fetched", r"not present", r"never (?:been )?(?:read|opened)",
    r"is not in the repository", r"does not exist", r"has not been downloaded",
]


def contradictions(data: list[dict]) -> list[dict]:
    """Statements the repository makes about itself that the filesystem falsifies.

    Two kinds, both computable:

      1. **A referenced path that does not exist.** `lib/palette.ts` cited
         `scripts/validate_palette.js` for three weeks; it was never there. A citation to a
         missing file is a claim with no possible verification.
      2. **An absence claimed about a file that is present.** `analyses/nf2_subgroup.py`
         still logs that `OmicsCNGene.csv` was "not fetched" while 1.33 GB of it sits in
         `data/depmap/`. The sentence was true when written, which is exactly why nobody
         re-read it.
    """
    found: list[dict] = []
    present = {pathlib.Path(r["file"]).name for r in data}

    scan = []
    for pattern in ("tools/**/*.py", "analyses/**/*.py", "src/**/*.py",
                    "web/src/**/*.ts", "web/src/**/*.tsx", "web/scripts/*.mjs",
                    "docs/**/*.md"):
        scan.extend(ROOT.glob(pattern))

    for f in scan:
        if "__pycache__" in f.parts or "node_modules" in f.parts:
            continue
        # The detector quotes the phrases it looks for, so scanning itself would report its
        # own documentation as a defect for as long as the documentation is accurate.
        if f.name == "status.py":
            continue
        # And never the document this tool writes. Every "never read" row it emits contains
        # a filename next to an absence phrase, so scanning its own output turns the report
        # into a generator of contradictions about itself — one per row, growing each run.
        if f.name == "status.md" and f.parent.name == "docs":
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(f.relative_to(ROOT)).replace("\\", "/")

        # (1) a cited path inside backticks that resolves nowhere.
        #
        # Citations in this repository are written relative to the CITING file as often as to
        # the root — `docs/audit.md` says `references/standards.md`, meaning
        # `docs/references/standards.md`. Resolving against the root alone reported 120
        # false positives on the first run, which would have made the whole section ignorable
        # within a day. Each candidate root is tried before anything is reported.
        roots = [ROOT, f.parent, ROOT / "web", ROOT / "docs", ROOT / "web" / "src",
                 ROOT / "src", ROOT / "src" / "sieve"]
        own = {p.name for p in ROOT.iterdir() if p.is_dir()} | {"stages", "adapters",
                                                                "pipeline", "components"}
        for m in re.finditer(r"`([\w./-]+\.(?:py|mjs|js|ts|tsx|yaml|json|md|cff))`", text):
            target = m.group(1)
            if target.startswith(("http", "@")) or "*" in target or "/" not in target:
                continue
            # A citation into another repository (the ancestor's `core/validation.py`, a
            # sibling's `knee/docs/METHOD.md`) is not a broken link here; it is a reference
            # to somewhere this checkout cannot see.
            if target.split("/")[0] not in own:
                continue
            if any((r / target).exists() for r in roots) or target == "docs/status.md":
                continue
            # A WINDOW, not a single line. A retraction almost always sits on the line AFTER
            # the citation it retracts: the broken path is quoted first, then corrected. The
            # one-line version of this check read only the quote and reported every honest
            # correction in this repository as a fresh defect.
            _lines = text.splitlines()
            _at = text[:m.start()].count("\n")
            line_text = "\n".join(_lines[max(0, _at - 3):_at + 4])
            # A sentence SAYING a file is absent is a deliberate statement, not a broken
            # citation — this file's own docstring cites the palette validator precisely
            # because it was missing.
            if re.search(r"was not|were not|did not|does not exist|is not in the repository"
                         r"|never (?:there|committed|written|existed)|no longer",
                         line_text, re.I):
                continue
            found.append({"kind": "missing-path", "file": rel, "claim": target,
                          "line": text[:m.start()].count("\n") + 1})

        # (2) an absence asserted about a file that is on disk
        for line_no, line in enumerate(text.splitlines(), 1):
            if not any(re.search(p, line, re.I) for p in ABSENCE_CLAIMS):
                continue
            for name in re.findall(r"([\w.-]+\.(?:csv|tsv|gz|obo|json))", line):
                if name in present:
                    found.append({"kind": "absence-claimed-but-present", "file": rel,
                                  "claim": line.strip()[:150], "subject": name,
                                  "line": line_no})
    return found


# ------------------------------------------------------------------------------- rendering

def render(payload: dict) -> str:
    s = payload
    L = []
    add = L.append
    add("# Project status")
    add("")
    add("> **Role:** the single derived checklist of where this repository actually is.")
    add(f"> **Last revised:** {s['generated']['date']} (generation time) · "
        f"**State:** generated by `tools/status.py` against the working tree at commit "
        f"`{s['generated']['commit']}`; edit the repository, not this file.")
    add("")
    add("⚠️ **This document is written by a program.** Every number below is recomputed from "
        "the filesystem, the pipeline registry, the audit log and the manifests. Editing it "
        "by hand produces a file that disagrees with itself on the next run — which is the "
        "failure mode (A1, A28, A33) that caused it to be generated in the first place.")
    add("")

    c = s["counts"]
    add("## At a glance")
    add("")
    add("| | |")
    add("|---|---|")
    add(f"| Pipeline stages | **{c['stages']}** registered · {c['stagesStale']} stale · "
        f"{c['stagesAlwaysRun']} verification stages that never cache · "
        f"{c['stagesMissingInputs']} missing inputs |")
    add(f"| Audit findings | **{c['auditTotal']}** · {c['auditClosed']} closed · "
        f"**{c['auditOpen']} open** |")
    add(f"| Decision records | **{c['adrs']}** · {c['adrProposed']} still `proposed` |")
    add(f"| Registered thresholds | **{c['thresholds']}** · {c['thresholdsPre']} "
        f"pre-registered · **{c['thresholdsCalibrated']} calibrated to seen data** |")
    add(f"| Ingested data | **{c['dataFiles']}** files, {c['dataGb']} GB · "
        f"**{c['dataUntouched']} referenced nowhere in the source** · "
        f"{c['dataNoReadSite']} referenced but with no direct read site |")
    add(f"| Emitted datasets | **{c['datasets']}** · {c['datasetsDead']} consumed by no "
        "component |")
    add(f"| Docs | **{c['docs']}** · {c['docsNoHeader']} missing the mandated header |")
    add(f"| Self-contradictions | **{c['contradictions']}** |")
    add("")

    add("## Contradictions — where the repository disagrees with the disk")
    add("")
    if not s["contradictions"]:
        add("None. Every cited path resolves, and no file asserts the absence of something "
            "that is present.")
    else:
        add("These are not style problems. Each one is a sentence that was true when it was "
            "written and is false now, which is precisely the class nobody re-reads.")
        add("")
        add("| kind | where | claim |")
        add("|---|---|---|")
        for r in s["contradictions"]:
            add(f"| {r['kind']} | `{r['file']}:{r['line']}` | {r['claim'][:110]} |")
    add("")

    add("## Ingested data, and whether anything reads it")
    add("")
    add("Three states, because a binary would be wrong here. **read** means a read call "
        "naming the file or its constant was found by walking the AST. **untouched** means "
        "the name appears nowhere in the source at all — the strong claim, and the only one "
        "worth acting on. Between them sits *referenced, no direct read site*: "
        "`CRISPRGeneEffect.csv` is opened inside an adapter that receives a directory, so no "
        "call names it, and calling that unread would be the report asserting the opposite "
        "of the truth about the repository's primary input.")
    add("")
    add("| file | MB | state | read by |")
    add("|---|---|---|---|")
    for r in sorted(s["data"], key=lambda x: -x["megabytes"])[:26]:
        who = ", ".join(f"`{p}`" for p in r["readers"]) if r["readers"] else "—"
        mark = {"read": "read", "referenced": "referenced, no read site",
                "untouched": "**untouched**"}[r["state"]]
        add(f"| `{r['file']}` | {r['megabytes']} | {mark} | {who} |")
    add("")
    untouched = [r for r in s["data"] if r["state"] == "untouched"]
    if untouched:
        add("**Ingested and referenced nowhere:** "
            + ", ".join(f"`{pathlib.Path(r['file']).name}` ({r['megabytes']} MB)"
                        for r in sorted(untouched, key=lambda x: -x["megabytes"])))
    add("")

    add("## Open audit findings")
    add("")
    open_rows = [r for r in s["audit"] if not r["state"].startswith("closed")]
    if not open_rows:
        add("None open.")
    else:
        add("| id | finding | state |")
        add("|---|---|---|")
        for r in open_rows:
            add(f"| {r['id']} | {r['title'][:96]} | {r['state']} |")
    add("")

    add("## Decision records")
    add("")
    add("| record | status |")
    add("|---|---|")
    for r in s["adrs"]:
        add(f"| `{r['file']}` — {r['title'][:70]} | {r['status']} |")
    add("")

    add("## Thresholds this project acts on")
    add("")
    add("From `manifests/thresholds.yaml` (ADR 0006). The column that matters is the last "
        "one: a number chosen before the data was seen and one calibrated to a plot already "
        "looked at are different objects.")
    add("")
    add("| id | value | justification | pre-registered |")
    add("|---|---|---|---|")
    for r in s["thresholds"]:
        add(f"| `{r['id']}` | {r['value']} | {r['justification']} | "
            f"{'yes' if r['preRegistered'] else '**no**'} |")
    add("")

    stale = [r for r in s["stages"] if r["stale"] or r["missingInputs"]]
    add("## Pipeline")
    add("")
    add(f"{c['stages']} stages registered, of which {c['stagesAlwaysRun']} are verification "
        "stages that re-run every time by design and are not counted as stale. "
        + ("Every other stage is fresh against its inputs and its own source."
           if not stale else "The following are stale or blocked:"))
    if stale:
        add("")
        add("| stage | why |")
        add("|---|---|")
        for r in stale:
            add(f"| `{r['stage']}` | {r['why']} |")
    add("")

    dead = [r for r in s["web"] if not r["consumed"]]
    add("## Interface")
    add("")
    add(f"{c['datasets']} datasets are emitted by `web/scripts/build-data.mjs`. "
        + ("Every one is consumed by a component."
           if not dead
           else f"**{len(dead)} are consumed by nothing** — shipped and ignored: "
                + ", ".join(f"`{r['dataset']}`" for r in dead)))
    add("")

    missing_head = [r for r in s["docs"] if not (r["hasRole"] and r["hasRevised"])]
    add("## Documentation")
    add("")
    add("`.claude/skills/sieve-doc` requires every document to open with a **Role** and a "
        "**Last revised** line.")
    add("")
    if not missing_head:
        add("All documents carry it.")
    else:
        add(f"{len(missing_head)} of {c['docs']} do not:")
        add("")
        for r in missing_head:
            add(f"- `{r['file']}`")
    add("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit non-zero if the repository contradicts the filesystem")
    args = ap.parse_args()

    # GENERATION time, not the last commit. The document describes the WORKING TREE — stale
    # stages, uncommitted files, data on disk — so stamping it with a commit date would date
    # the report to a state it is not describing.
    date = _dt.date.today().isoformat()
    commit = subprocess.run(["git", "log", "-1", "--format=%h %cs"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip() or "unknown"

    data = data_inventory()
    stages = stage_rows()
    audit = audit_rows()
    adrs = adr_rows()
    thresholds = threshold_rows()
    docs = doc_rows()
    web = web_rows()
    bad = contradictions(data)

    payload = {
        "generated": {"by": "tools/status.py", "date": date, "commit": commit},
        "counts": {
            "stages": len(stages),
            "stagesStale": sum(1 for r in stages if r["stale"]),
            "stagesAlwaysRun": sum(1 for r in stages if r["alwaysRuns"]),
            "stagesMissingInputs": sum(1 for r in stages if r["missingInputs"]),
            "auditTotal": len(audit),
            "auditClosed": sum(1 for r in audit if r["state"].startswith("closed")),
            "auditOpen": sum(1 for r in audit if not r["state"].startswith("closed")),
            "adrs": len(adrs),
            "adrProposed": sum(1 for r in adrs if r["status"] == "proposed"),
            "thresholds": len(thresholds),
            "thresholdsPre": sum(1 for r in thresholds if r["preRegistered"]),
            "thresholdsCalibrated": sum(1 for r in thresholds if not r["preRegistered"]),
            "dataFiles": len(data),
            "dataGb": round(sum(r["megabytes"] for r in data) / 1000, 2),
            "dataUntouched": sum(1 for r in data if r["state"] == "untouched"),
            "dataNoReadSite": sum(1 for r in data if r["state"] == "referenced"),
            "datasets": len(web),
            "datasetsDead": sum(1 for r in web if not r["consumed"]),
            "docs": len(docs),
            "docsNoHeader": sum(1 for r in docs if not (r["hasRole"] and r["hasRevised"])),
            "contradictions": len(bad),
        },
        "data": data, "stages": stages, "audit": audit, "adrs": adrs,
        "thresholds": thresholds, "docs": docs, "web": web, "contradictions": bad,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "status.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                                     encoding="utf-8")
    DOC.write_text(render(payload), encoding="utf-8")

    c = payload["counts"]
    print("stages %d (%d stale) · audit %d open of %d · thresholds %d (%d calibrated)"
          % (c["stages"], c["stagesStale"], c["auditOpen"], c["auditTotal"],
             c["thresholds"], c["thresholdsCalibrated"]))
    print("data %d files / %.2f GB · %d untouched, %d with no read site · datasets %d (%d dead)"
          % (c["dataFiles"], c["dataGb"], c["dataUntouched"], c["dataNoReadSite"],
             c["datasets"], c["datasetsDead"]))
    print("wrote out/status.json and docs/status.md")

    if bad:
        print()
        print("CONTRADICTIONS (%d):" % len(bad))
        for r in bad[:20]:
            print("  %-28s %s:%s  %s" % (r["kind"], r["file"], r["line"], r["claim"][:80]))
        if args.check:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
