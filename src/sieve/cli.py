"""The `sieve` command.

WHY THIS FILE APPEARED LATE. `pyproject.toml` has declared `sieve = "sieve.cli:main"` as a
console script since the project began, and `src/sieve/cli.py` did not exist. A
`pip install -e .` therefore installed a `sieve` command that raised `ModuleNotFoundError`
on its first run — a broken promise in the package metadata, found while building the target
stage that needed somewhere to live. Recorded as A22 in `docs/audit.md`.

WHAT IT IS FOR. `sieve target` runs Stage 7's target assessment over the measured artefacts
in `out/rare/`, so the model can be used without importing anything. It prints what the
evidence admits and which gates fail — never a ranking, for the reason
`sieve.stages.target` gives at length.

    sieve target LMNA STXBP1 NF1        # assess named genes
    sieve target --top 20               # the genes with the most patients on file
    sieve target --json LMNA            # machine-readable, for a pipeline
    sieve stages                        # what is implemented, and what is not
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from .stages import target as target_stage

# The artefacts this command reads. Kept as a table so a missing one produces a message
# naming the tool that writes it, rather than a KeyError three frames down.
ARTEFACTS = {
    "patient_variants": ("out/rare/patient_variants.json", "python tools/patient_variants.py"),
    "clinvar_evidence": ("out/rare/clinvar_evidence.json", "python tools/clinvar_evidence.py"),
    "evidence_atlas": ("out/rare/evidence_atlas.json", "python tools/evidence_atlas.py"),
    # The project's own screen. Optional: most rare-disease genes are in it, and a gene that
    # is not simply keeps essentiality unknown, which blocks the knockdown strategy rather
    # than permitting it.
    "depmap_genes": ("out/depmap_genes.csv", "python tasks.py depmap"),
}


def _repo_root() -> pathlib.Path:
    """Walk up for the directory holding `out/` — the CLI may be run from anywhere."""
    here = pathlib.Path.cwd()
    for candidate in (here, *here.parents):
        if (candidate / "out" / "rare").is_dir():
            return candidate
    return here


def _load(root: pathlib.Path, key: str) -> dict | None:
    rel, how = ARTEFACTS[key]
    path = root / rel
    if not path.exists():
        print(f"  missing {rel} — run `{how}`", file=sys.stderr)
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _assemble(root: pathlib.Path) -> dict[str, dict]:
    """Per-gene evidence, joined from whatever artefacts are on disk.

    A gene present in one artefact and absent from another keeps the axes it has and leaves
    the rest unknown. The stage treats unknown as blocking, never as zero.
    """
    pv = _load(root, "patient_variants")
    cv = _load(root, "clinvar_evidence")

    genes: dict[str, dict] = {}
    if pv:
        for row in pv.get("allelicSpectrum", {}).get("all", []):
            genes.setdefault(row["gene"], {}).update(
                patients=row.get("patients"),
                distinct_variants=row.get("distinctVariants"),
                private_share=row.get("privateShare"),
                most_recurrent=row.get("mostRecurrent"),
                consequences=row.get("consequenceRecords") or row.get("consequences"),
            )
    if cv:
        for row in cv.get("vusByGene", {}).get("all", []):
            genes.setdefault(row["gene"], {}).update(vus_share=row.get("vusShare"))

    # DepMap essentiality, read from the project's own screen. `dependent_line_share` is the
    # fraction of screened lines that depend on the gene - the quantity Stage 3 needs to
    # tell a selective dependency from pan-essential toxicity.
    dm = root / ARTEFACTS["depmap_genes"][0]
    if dm.exists():
        import csv as _csv
        with dm.open(encoding="utf-8") as fh:
            for row in _csv.DictReader(fh):
                # The column is `entity`, not `gene`, and the essentiality signal is the
                # measured `is_common_essential` flag rather than a fraction to threshold.
                g = (row.get("entity") or "").strip()
                if not g or g not in genes:
                    continue
                flag = (row.get("is_common_essential") or "").strip().lower()
                if flag in ("true", "false"):
                    genes[g]["pan_essential"] = flag == "true"
    return genes


def cmd_target(args: argparse.Namespace) -> int:
    root = _repo_root()
    genes = _assemble(root)
    if not genes:
        print("no gene evidence on disk; nothing to assess", file=sys.stderr)
        return 1

    if args.genes:
        wanted = list(args.genes)
        missing = [g for g in wanted if g not in genes]
        for g in missing:
            print(f"  {g}: no measured evidence on file", file=sys.stderr)
        wanted = [g for g in wanted if g in genes]
    else:
        wanted = sorted(genes, key=lambda g: -(genes[g].get("patients") or 0))[: args.top]

    assessments = [target_stage.assess(g, **genes[g]) for g in wanted]

    if args.json:
        print(json.dumps([{
            "gene": a.gene,
            "admitted": a.admitted,
            "failedGates": [{"stage": g.stage, "name": g.name, "because": g.because}
                            for g in a.failed_gates],
            "unknownAxes": a.unknown_axes,
            "strategies": [{"name": s.name, "admitted": s.admitted, "because": s.because}
                           for s in a.strategies],
        } for a in assessments], indent=2))
        return 0

    for a in assessments:
        print()
        print(f"  {a.gene}")
        ev = {e.name: e.value for e in a.evidence if e.known}
        if ev.get("patients"):
            print(f"    {ev['patients']} patients · {ev.get('distinctVariants')} variants · "
                  f"{(ev.get('privateShare') or 0):.0%} private · "
                  f"top allele {ev.get('mostRecurrentAllele')}")
        for s in a.strategies:
            print(f"    {'YES' if s.admitted else ' no'}  {s.name:26s} {s.because}")
        for g in a.gates:
            if not g.passed:
                print(f"    GATE  Stage {g.stage} {g.name}: {g.because}")
        if a.unknown_axes:
            print(f"    unmeasured: {', '.join(a.unknown_axes)}")

    print()
    print(target_stage.shortlist(assessments, slots=args.top)["says"])
    return 0


def cmd_stages(_args: argparse.Namespace) -> int:
    """What is implemented and what is prose. Honest by construction: it imports."""
    import importlib

    declared = [
        (0, "Objective"), (1, "Null"), (2, "Power"), (3, "Confound"), (4, "Baseline"),
        (5, "Validation"), (6, "Prior"), (7, "Shortlist"), (8, "Report"), (9, "Repro"),
        (10, "Design"),
    ]
    modules = {1: "null", 2: "power", 7: "target", 10: "design"}
    print("  stage                implementation")
    for n, name in declared:
        mod = modules.get(n)
        status = "—"
        if mod:
            try:
                importlib.import_module(f"sieve.stages.{mod}")
                status = f"sieve.stages.{mod}"
            except ImportError:                              # pragma: no cover
                status = f"declared as {mod}, does not import"
        print(f"  {n:>2}  {name:<16s} {status}")
    print()
    print("  Stage 7 is implemented for TARGET SELECTION only; the general shortlist")
    print("  logic is not. See docs/roadmap.md.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sieve",
        description="Turn a large, noisy, confounded screen into a defensible shortlist.")
    sub = parser.add_subparsers(dest="command")

    t = sub.add_parser("target", help="assess genes as gene-editing targets (Stage 7)")
    t.add_argument("genes", nargs="*", help="gene symbols; omit to use --top")
    t.add_argument("--top", type=int, default=10,
                   help="assess the N genes with the most patients on file")
    t.add_argument("--json", action="store_true", help="machine-readable output")
    t.set_defaults(func=cmd_target)

    s = sub.add_parser("stages", help="which of the ten stages are implemented")
    s.set_defaults(func=cmd_stages)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
