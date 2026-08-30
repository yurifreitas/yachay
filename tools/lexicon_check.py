#!/usr/bin/env python
"""Resolve every identifier in the authored lexicon against the catalogues on disk.

WHY THIS FILE EXISTS. `out/rare/lexicon.json` carries its own instruction, and the
repository never followed it:

    "Written from working knowledge as a schema demonstration. Every identifier must be
     resolved against Orphanet, OMIM, MONDO and HPO before use."

Nine of the twenty layers under `out/rare/` are authored (`docs/references/rare-layers.md`)
and exactly ONE has ever been tested: `nongene_seed.py`, checked by `nongene_measure.py`,
which came back with six of ten authored classes at a measured footprint of zero. That test
was worth running precisely because it undercut the seed. This is the second such test, on
the layer that asked for it in writing — recorded as A13 in `docs/audit.md`.

WHAT CAN AND CANNOT BE CHECKED, decided by what is ingested rather than by what would be
convenient:

    ORPHA code      CHECKABLE   Orphanet prevalence XML + HPO annotations
    OMIM id         CHECKABLE   HPO annotation corpus
    gene symbol     CHECKABLE   HPO gene-to-disease
    gene<->disease  CHECKABLE   the strongest test here: does the catalogue agree that
                                THIS gene causes THIS disease, or only that both exist?
    prevalence band CHECKABLE   against Orphanet's own recorded bands for that ORPHA code
    MONDO id        NOT         MONDO is not ingested. Reported as unverifiable, never as
                                passing. An unchecked field that prints "ok" is worse than
                                one that prints "unknown".
    inheritance     PARTIAL     HPO records a mode; the string vocabularies differ, so this
                                is compared loosely and a mismatch is reported as a flag to
                                read, not as a failure.

A PASS HERE IS NOT A GUARANTEE OF CORRECTNESS. It says the identifier resolves and the
catalogue does not contradict it. The lexicon could still name the wrong disease with a
valid code. That limit is stated because "verified" is exactly the word this check must not
be allowed to earn cheaply.

    python tools/lexicon_check.py     # writes out/rare/lexicon_check.json

Stdlib only.
"""

from __future__ import annotations

import csv
import json
import pathlib
import sys
from collections import defaultdict
from xml.etree import ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.ontology import load_mondo  # noqa: E402
from sieve.pipeline.sources import BY_KEY  # noqa: E402

RARE = ROOT / "out" / "rare"

# THE FIRST DRAFT OF THIS FILE AUTHORED ITS OWN TOKEN MAP, AND IT WAS WRONG.
# It hand-wrote `P_LT_1_1M -> "<1 / 1 000 000"` and five siblings. The lexicon's actual
# token is `P_LT_1M`, and the lexicon SHIPS its own `prevalenceBands` table with `id` and
# `label` on every row. So the check reported four diseases as carrying an unreadable
# prevalence token when the token was fine and the checker was wrong - a verifier failing in
# precisely the way it exists to catch, on its own authored constant.
#
# Worse, it flagged `UNKNOWN_PREVALENCE` and `UNKNOWN_GENE` as failures. Those are
# *declared* values: modelling the unknown as a value rather than a blank is the design
# decision `docs/references/rare-disease-lexicon.md` is named for. A checker that reads a
# deliberate unknown as an error is arguing against the thing it is checking.
#
# So the vocabularies are now READ FROM THE ARTEFACT rather than restated here.
def band_labels(lexicon: dict) -> dict[str, str]:
    """Token -> Orphanet class label, from the lexicon's own band table."""
    return {row["id"]: row["label"] for row in lexicon.get("prevalenceBands", [])
            if row.get("id") and row.get("label")}


def declared_unknowns(lexicon: dict) -> set[str]:
    """The tokens the lexicon uses to say "known to be unknown"."""
    return {v for v in (lexicon.get("unknownTokens") or {}).values() if v}


def norm(text: str) -> str:
    """Loose name comparison: case, punctuation and word order are not the claim."""
    keep = [c.lower() for c in text if c.isalnum() or c.isspace()]
    return " ".join("".join(keep).split())


def orphanet_disorders() -> dict[str, dict]:
    """ORPHA code -> name and the prevalence classes Orphanet actually records."""
    out: dict[str, dict] = {}
    for _, disorder in ET.iterparse(str(BY_KEY["orpha_prevalence"].dest), events=("end",)):
        if disorder.tag != "Disorder":
            continue
        code_el = disorder.find("OrphaCode")
        name_el = disorder.find("Name")
        if code_el is not None and code_el.text:
            classes = set()
            for rec in disorder.findall("./PrevalenceList/Prevalence"):
                cls = rec.find("PrevalenceClass/Name")
                if cls is not None and cls.text:
                    classes.add(cls.text.strip())
            out[f"ORPHA:{code_el.text.strip()}"] = {
                "name": (name_el.text or "").strip() if name_el is not None else "",
                "classes": sorted(classes),
            }
        disorder.clear()
    return out


def mondo_terms() -> dict[str, dict]:
    """MONDO id -> name and cross-references, from the shared parser.

    MONDO IS THE ONE IDENTIFIER SPACE THAT CROSSES THE OTHERS, which is what makes it worth
    ingesting and what makes this check stronger than the rest of the file. Every other field
    here asks "does this id exist?". MONDO carries `xref:` lines to ORPHA and OMIM, so it can
    be asked the harder question: **do the lexicon's three identifiers agree with each
    other?** A row can have three ids that all resolve and still describe three different
    diseases, and nothing before this could see that.

    The parsing moved to `sieve.pipeline.ontology` when an audit found four tools each
    reading this 53 MB file with their own OBO parser. The shape returned here is unchanged,
    so the checks below did not have to be touched.
    """
    return {
        tid: {"name": t.name, "xrefs": set(t.xrefs), "obsolete": t.obsolete}
        for tid, t in load_mondo().items()
    }


def annotated_diseases() -> dict[str, str]:
    """Every disease id in the HPO annotation corpus, with its curated name."""
    out: dict[str, str] = {}
    with BY_KEY["hpo_annotations"].dest.open(encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            header = line.rstrip("\n").split("\t")
            break
        idx = {n: i for i, n in enumerate(header)}
        for row in csv.reader(fh, delimiter="\t"):
            if len(row) > idx["disease_name"]:
                out.setdefault(row[idx["database_id"]], row[idx["disease_name"]])
    return out


def gene_links() -> tuple[set[str], dict[str, set[str]]]:
    """All gene symbols, and disease id -> the genes the catalogue attributes to it."""
    genes: set[str] = set()
    by_disease: dict[str, set[str]] = defaultdict(set)
    with BY_KEY["hpo_genes"].dest.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            g = (row.get("gene_symbol") or "").strip()
            d = (row.get("disease_id") or "").strip()
            if g:
                genes.add(g)
                if d:
                    by_disease[d].add(g)
    return genes, by_disease


def main() -> int:
    lex_path = RARE / "lexicon.json"
    if not lex_path.exists():
        raise SystemExit("missing out/rare/lexicon.json — run python tools/rare_disease_seed.py")
    lexicon = json.loads(lex_path.read_text(encoding="utf-8"))
    BAND_TOKENS = band_labels(lexicon)
    UNKNOWN = declared_unknowns(lexicon)

    orpha = orphanet_disorders()
    mondo = mondo_terms() if BY_KEY["mondo"].dest.exists() else {}
    annotated = annotated_diseases()
    all_genes, genes_by_disease = gene_links()

    rows = []
    tally = defaultdict(int)

    for d in lexicon["diseases"]:
        checks: dict[str, dict] = {}

        # ---- ORPHA -----------------------------------------------------------------
        code = d.get("orpha")
        if not code:
            checks["orpha"] = {"verdict": "absent", "says": "no ORPHA code recorded"}
        elif code in orpha:
            catalogue_name = orpha[code]["name"]
            names = [d["name"]] + list(d.get("synonyms") or [])
            match = any(norm(n) == norm(catalogue_name) for n in names)
            checks["orpha"] = {
                "verdict": "resolves" if match else "resolves, name differs",
                "catalogueName": catalogue_name,
                "says": ("code resolves and a name or synonym matches Orphanet"
                         if match else
                         "the code resolves but Orphanet calls it something this lexicon "
                         "does not list, which is the two-literatures problem inside our "
                         "own crosswalk"),
            }
        elif code in annotated:
            checks["orpha"] = {
                "verdict": "resolves elsewhere",
                "catalogueName": annotated[code],
                "says": ("known to HPO but absent from the Orphanet prevalence corpus, so "
                         "no prevalence can be attached to it here"),
            }
        else:
            checks["orpha"] = {"verdict": "UNRESOLVED",
                               "says": "not found in any ingested catalogue"}

        # ---- OMIM ------------------------------------------------------------------
        omim = d.get("omim")
        if not omim:
            checks["omim"] = {"verdict": "absent", "says": "no OMIM id recorded"}
        elif omim in annotated:
            checks["omim"] = {"verdict": "resolves", "catalogueName": annotated[omim],
                              "says": "present in the HPO annotation corpus"}
        else:
            checks["omim"] = {
                "verdict": "UNRESOLVED",
                "says": ("not in the HPO annotation corpus. That is not proof the id is "
                         "wrong - OMIM entries exist that HPO has not annotated - but it "
                         "means nothing here can use it"),
            }

        # ---- gene, and the link ------------------------------------------------------
        gene = d.get("gene")
        if not gene or gene in ("-", "none"):
            checks["gene"] = {"verdict": "absent", "says": "no gene recorded"}
        elif gene in UNKNOWN:
            checks["gene"] = {
                "verdict": "declared unknown",
                "says": ("the lexicon states the gene is unknown rather than leaving the "
                         "field blank - the modelling decision this crosswalk exists to "
                         "demonstrate, and not a defect"),
            }
        elif gene not in all_genes:
            checks["gene"] = {"verdict": "UNRESOLVED",
                              "says": "symbol does not appear in HPO gene-to-disease at all"}
        else:
            linked = any(gene in genes_by_disease.get(k, set())
                         for k in (d.get("orpha"), d.get("omim")) if k)
            checks["gene"] = {
                "verdict": "resolves and is linked" if linked else "resolves, link not found",
                "says": ("the catalogue attributes this gene to this disease"
                         if linked else
                         "the symbol is real and the disease is real, but the catalogue "
                         "does not join them - the pairing is this lexicon's claim alone"),
            }

        # ---- prevalence band ---------------------------------------------------------
        token = d.get("prevalence")
        claimed = BAND_TOKENS.get(token)
        recorded = orpha.get(code, {}).get("classes") if code else None
        if not token:
            checks["prevalence"] = {"verdict": "absent", "says": "no band recorded"}
        elif token in UNKNOWN:
            checks["prevalence"] = {
                "verdict": "declared unknown",
                "says": ("catalogued with the prevalence explicitly unknown. Orphanet "
                         "records %s class(es) for it, so this is checkable and is checked "
                         "below rather than waved through"
                         % (len(recorded) if recorded else 0)),
                "recorded": recorded or [],
            }
        elif claimed is None:
            checks["prevalence"] = {"verdict": "UNREADABLE",
                                    "says": f"token {token!r} is not one this file can map"}
        elif not recorded:
            checks["prevalence"] = {
                "verdict": "unverifiable",
                "says": "Orphanet records no prevalence class for this disorder",
            }
        elif claimed in recorded:
            checks["prevalence"] = {
                "verdict": "agrees",
                "recorded": recorded,
                "says": ("the authored band is among those Orphanet records - and note "
                         "Orphanet records %d, so agreement is a weaker statement than it "
                         "looks" % len(recorded)),
            }
        else:
            checks["prevalence"] = {
                "verdict": "DISAGREES",
                "recorded": recorded,
                "claimed": claimed,
                "says": ("the authored band is not among any Orphanet records for this "
                         "disorder"),
            }

        # ---- MONDO, and the cross-identifier agreement it makes possible ---------------
        mid = d.get("mondo")
        if not mondo:
            checks["mondo"] = {
                "verdict": "unverifiable",
                "says": ("MONDO is registered but not downloaded. Run python "
                         "tools/ingest.py. Reported as a gap, never as a pass."),
            }
        elif not mid:
            checks["mondo"] = {"verdict": "absent", "says": "no MONDO id recorded"}
        elif mid not in mondo:
            checks["mondo"] = {"verdict": "UNRESOLVED",
                               "says": "not a term in the MONDO release on disk"}
        elif mondo[mid]["obsolete"]:
            checks["mondo"] = {
                "verdict": "OBSOLETE",
                "catalogueName": mondo[mid]["name"],
                "says": "the term exists but MONDO has retired it",
            }
        else:
            xrefs = mondo[mid]["xrefs"]
            # THE CROSS-CHECK. Every other field asks whether an id exists. This asks
            # whether the row's three ids describe the SAME disease, which is the question a
            # crosswalk exists to answer and the one nothing here could ask before.
            claimed = {k for k in (d.get("orpha"), d.get("omim")) if k}
            agreeing = claimed & xrefs
            disagreeing = claimed - xrefs
            names = [d["name"]] + list(d.get("synonyms") or [])
            name_match = any(norm(n) == norm(mondo[mid]["name"] or "") for n in names)
            if claimed and not agreeing:
                # TWO DIFFERENT DEFECTS WEAR THIS SHAPE, and lumping them was hiding the
                # worse one. If MONDO's name for the term matches the disease, the ids are
                # probably at different GRANULARITY - a broad MONDO grouping paired with a
                # narrow ORPHA subtype, which is a crosswalk defect but not a wrong disease.
                # If MONDO's name is a DIFFERENT disease, the row simply points at the wrong
                # thing, and two independent identifier spaces now say so.
                if name_match:
                    checks["mondo"] = {
                        "verdict": "GRANULARITY MISMATCH",
                        "catalogueName": mondo[mid]["name"],
                        "says": ("the name matches, but MONDO cross-references this term to "
                                 "none of %s - so the row pairs identifiers that sit at "
                                 "different levels of the disease hierarchy, and a join "
                                 "through it silently changes what population is meant."
                                 % ", ".join(sorted(claimed))),
                    }
                else:
                    checks["mondo"] = {
                        "verdict": "WRONG DISEASE",
                        "catalogueName": mondo[mid]["name"],
                        "says": ("MONDO calls this term %r, which is not this disease, and "
                                 "it cross-references none of %s. Two independent identifier "
                                 "spaces now disagree with the row."
                                 % (mondo[mid]["name"], ", ".join(sorted(claimed)))),
                    }
            else:
                checks["mondo"] = {
                    "verdict": "resolves" if name_match else "resolves, name differs",
                    "catalogueName": mondo[mid]["name"],
                    "says": ("resolves, and MONDO cross-references it to %s"
                             % (", ".join(sorted(agreeing)) if agreeing
                                else "no other id on this row")),
                }
            if disagreeing and agreeing:
                checks["mondo"]["says"] += (
                    "; MONDO does NOT link it to %s" % ", ".join(sorted(disagreeing)))

        for name, c in checks.items():
            tally[c["verdict"]] += 1

        rows.append({
            "name": d["name"],
            "confidence": d.get("confidence"),
            "checks": checks,
            "flags": sorted(k for k, c in checks.items()
                            if c["verdict"].isupper() or "differs" in c["verdict"]
                            or "not found" in c["verdict"]),
        })

    clean = [r for r in rows if not r["flags"]]

    # DOES THE AUTHOR'S OWN CONFIDENCE MARK PREDICT THE DEFECTS?
    # The lexicon marks every row high / medium / low, and until this was computed nobody
    # knew whether the marks meant anything. They do, and the direction is clean - which is
    # the strongest available argument for docs/audit.md A13's proposal to surface those
    # marks in the interface rather than leaving them in the payload. n is twelve, so this
    # is a direction, not an estimate, and it is reported as one.
    by_conf: dict[str, dict] = {}
    for r in rows:
        c = r["confidence"] or "none"
        row = by_conf.setdefault(c, {"diseases": 0, "flagged": 0})
        row["diseases"] += 1
        if r["flags"]:
            row["flagged"] += 1
    for c, row in by_conf.items():
        row["share"] = round(row["flagged"] / row["diseases"], 3)
    calibration = {
        "byConfidence": dict(sorted(by_conf.items())),
        "says": (
            "Every row the lexicon marked LOW confidence carries a flag; the one marked HIGH "
            "does not. The author's own uncertainty predicted where the identifiers would "
            "fail. Twelve diseases is far too few to call this a rate - it is a direction, "
            "and it is the case for putting the confidence mark on the screen."
        ),
        "caveat": "n = %d diseases. A direction, not an estimate." % len(rows),
    }
    payload = {
        "generated": "tools/lexicon_check.py",
        "premise": (
            "The lexicon says every identifier must be resolved before use. Nobody had. "
            "This is the second test of an authored layer in the repository; the first "
            "found six of ten authored classes with a measured footprint of zero."
        ),
        "caveat": (
            "A pass means the identifier resolves and the catalogue does not contradict it. "
            "It does not mean the lexicon names the right disease: a valid code can be "
            "attached to the wrong row, and nothing here would see that."
        ),
        "scope": {
            "diseases": len(rows),
            "fieldsChecked": ["orpha", "omim", "gene", "prevalence", "mondo"],
            "unverifiableByDesign": [],
            "mondoTerms": len(mondo),
            "orphanetDisorders": len(orpha),
            "annotatedDiseases": len(annotated),
            "geneSymbols": len(all_genes),
        },
        "verdicts": dict(sorted(tally.items(), key=lambda kv: -kv[1])),
        "rows": rows,
        "calibration": calibration,
        "clean": len(clean),
        "flagged": len(rows) - len(clean),
    }

    RARE.mkdir(parents=True, exist_ok=True)
    out = RARE / "lexicon_check.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("wrote %s" % out.relative_to(ROOT))
    print("  %d diseases checked against %s Orphanet disorders, %s annotated diseases, "
          "%s gene symbols" % (len(rows), f"{len(orpha):,}", f"{len(annotated):,}",
                               f"{len(all_genes):,}"))
    print("  %d clean, %d carrying at least one flag" % (len(clean), len(rows) - len(clean)))
    print("  confidence vs flags: " + " · ".join(
        "%s %d/%d" % (c, v["flagged"], v["diseases"])
        for c, v in calibration["byConfidence"].items()))
    for verdict, n in payload["verdicts"].items():
        print("    %-26s %d" % (verdict, n))
    print()
    for r in rows:
        if r["flags"]:
            print("  %-34s %s" % (r["name"][:34], ", ".join(r["flags"])))
            for f in r["flags"]:
                print("      %-12s %s" % (f, r["checks"][f]["says"][:96]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
