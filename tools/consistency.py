#!/usr/bin/env python
"""Where twenty layers make the same claim, do they agree?

WHY THIS FILE EXISTS, AND WHY IT IS DIFFERENT FROM EVERY OTHER CHECK HERE. The audit in
`docs/audit.md` has now found the same defect three times in three different costumes:

    A11   two readers of one XML corpus disagreed for months, and nothing compared them.
    A13   an authored crosswalk and a measured dossier disagreed about which disease an
          ORPHA code names, and nothing compared them.
    F3    the fix proposed for A11 - "assert that two readers of one file agree" - was
          implemented for exactly one file.

Each layer in this repository is careful about itself. Every one states its provenance,
marks its confidence and says what it cannot do. What nothing does is check them **against
each other**. Twenty artefacts make overlapping claims about the same diseases, genes and
prevalences, and the system as a whole has never been audited even though each of its parts
has.

That is the gap this file closes, and it is a different KIND of check: not "is this number
right" - which usually needs a source we do not have - but "do our own artefacts contradict
each other", which needs nothing external and is therefore always answerable. A
contradiction is proof that at least one layer is wrong without having to know which.

WHAT IS COMPARED, and only where an actual assertion exists in both places:

    identity     the ORPHA and OMIM codes a disease carries, across every layer naming it
    prevalence   the authored band against the measured band against the derived cohort
    gene         the authored causal gene against the catalogue's gene set for that disease
    coverage     which layers speak about which disease at all

WHAT IS NOT COMPARED. Free text - a mechanism sentence, a barrier description - is shown
side by side where both exist but never asserted equal. Two correct sentences about one
mechanism can differ in every word, and a string comparison would produce noise that buries
the real contradictions.

    python tools/consistency.py     # writes out/rare/consistency.json

Stdlib only.
"""

from __future__ import annotations

import json
import pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
RARE = ROOT / "out" / "rare"

# Which layers are authored, which measured. Read from docs/references/rare-layers.md's
# grading and restated here only so the OUTPUT can say which side of a contradiction is
# which - a disagreement between two measured layers is a very different alarm from one
# between an authored layer and a measured one.
GRADE = {
    "lexicon": "authored",
    "barriers": "authored",
    "capability": "authored",
    "nomenclature": "authored",
    "lupus": "authored",
    "dossiers": "measured",
    "atlas": "measured",
    "capability_math": "derived",
    "ancestry_geography": "measured",
}


def load(name: str):
    p = RARE / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def norm(text: str) -> str:
    """Normalise a disease name for joining.

    THE FIRST VERSION DELETED PUNCTUATION INSTEAD OF REPLACING IT, and that single choice
    hid the contradiction this file was written to find. "CDKL5-deficiency disorder" became
    `cdkl5deficiency disorder` while "CDKL5 deficiency disorder" became
    `cdkl5 deficiency disorder`, so the authored and measured records of the same disease
    never met and the ORPHA conflict between them went unreported. A weak join does not
    produce a false alarm; it produces SILENCE, which is worse, because silence reads as
    agreement.
    """
    out = "".join(c.lower() if (c.isalnum() or c.isspace()) else " " for c in (text or ""))
    return " ".join(out.split())


def main() -> int:
    lexicon = load("lexicon")
    dossiers = load("dossiers")
    barriers = load("barriers")
    capability = load("capability")
    cap_math = load("capability_math")
    nomenclature = load("nomenclature")
    lupus = load("lupus")

    if not (lexicon and dossiers):
        raise SystemExit("need at least lexicon.json and dossiers.json — run tasks.py build")

    # ---- 1. build the claim index ------------------------------------------------------
    # Diseases are joined on a normalised name, because that is the only key every layer
    # shares. The join itself is therefore a claim, and its failures are reported: a
    # disease present in one layer under a name no other layer uses is not a contradiction,
    # but it IS a place where nothing can be cross-checked, and that is worth counting.
    claims: dict[str, dict[str, dict]] = defaultdict(dict)

    for d in lexicon["diseases"]:
        claims[norm(d["name"])]["lexicon"] = {
            "name": d["name"], "orpha": d.get("orpha"), "omim": d.get("omim"),
            "gene": d.get("gene"), "prevalenceToken": d.get("prevalence"),
        }
    band_label = {r["id"]: r["label"] for r in lexicon.get("prevalenceBands", [])}

    for d in dossiers["dossiers"]:
        entry = {
            "name": d["name"], "orpha": d.get("orpha"), "omim": d.get("omim"),
            "genes": d.get("genes", []), "rarestBand": d.get("rarestBand"),
            "bands": [b["band"] for b in d.get("prevalenceSpread", [])],
        }
        claims[norm(d["name"])]["dossiers"] = entry
        # The dossier also records the name it queried under, which is frequently the name
        # the authored layers use. Joining on both is what lets NF2 line up at all.
        if d.get("query") and norm(d["query"]) != norm(d["name"]):
            claims[norm(d["query"])]["dossiers"] = entry

    for d in (barriers or {}).get("diseases", []):
        claims[norm(d.get("catalogueName", ""))]["barriers"] = {
            "name": d.get("catalogueName"), "confidence": d.get("confidence"),
        }

    for p in (capability or {}).get("plans", []):
        claims[norm(p.get("catalogueName", ""))].setdefault("capability", {
            "name": p.get("catalogueName"),
        })

    for r in (cap_math or {}).get("capitalPerPatient", []):
        claims[norm(r.get("catalogueName", ""))]["capability_math"] = {
            "name": r.get("catalogueName"), "orpha": f"ORPHA:{r['orpha']}" if r.get("orpha") else None,
            "prevalenceClass": r.get("prevalenceClass"),
        }

    for n in (nomenclature or {}).get("names", []):
        key = norm(n.get("current") or n.get("id") or "")
        if key:
            claims[key]["nomenclature"] = {"name": n.get("current"),
                                           "confidence": n.get("confidence")}

    # ---- 2. the contradictions ---------------------------------------------------------
    contradictions = []
    unjoinable = []

    for key, layers in sorted(claims.items()):
        if not key:
            continue
        names = {k: v.get("name") for k, v in layers.items()}

        if len(layers) == 1:
            only = next(iter(layers))
            unjoinable.append({
                "disease": names[only], "onlyIn": only, "grade": GRADE.get(only, "?"),
                "says": ("named in one layer only, so nothing here can contradict it - "
                         "an absence of disagreement that is not agreement"),
            })
            continue

        # --- identity: ORPHA -------------------------------------------------------------
        orphas = {k: v.get("orpha") for k, v in layers.items() if v.get("orpha")}
        distinct = set(orphas.values())
        if len(distinct) > 1:
            contradictions.append({
                "disease": names.get("dossiers") or next(iter(names.values())),
                "field": "orpha",
                "byLayer": {k: {"value": v, "grade": GRADE.get(k, "?")}
                            for k, v in orphas.items()},
                "severity": "identity",
                "says": ("two layers give this disease different ORPHA codes. One of them "
                         "joins to a different disease, and every number computed through "
                         "it is about that other disease."),
            })

        omims = {k: v.get("omim") for k, v in layers.items() if v.get("omim")}
        if len(set(omims.values())) > 1:
            contradictions.append({
                "disease": names.get("dossiers") or next(iter(names.values())),
                "field": "omim",
                "byLayer": {k: {"value": v, "grade": GRADE.get(k, "?")}
                            for k, v in omims.items()},
                "severity": "identity",
                "says": "two layers give this disease different OMIM ids",
            })

        # --- prevalence: authored token vs measured band vs derived class -----------------
        stated = {}
        if "lexicon" in layers and layers["lexicon"].get("prevalenceToken"):
            token = layers["lexicon"]["prevalenceToken"]
            stated["lexicon"] = band_label.get(token, token)
        if "dossiers" in layers and layers["dossiers"].get("rarestBand"):
            stated["dossiers"] = layers["dossiers"]["rarestBand"]
        if "capability_math" in layers and layers["capability_math"].get("prevalenceClass"):
            stated["capability_math"] = layers["capability_math"]["prevalenceClass"]

        if len(stated) > 1 and len(set(stated.values())) > 1:
            recorded = layers.get("dossiers", {}).get("bands", [])
            # A layer naming a band Orphanet DOES record for this disorder is disagreeing
            # about which of several to quote; one naming a band Orphanet never records is
            # simply wrong. The distinction is the whole finding of the ancestry work.
            outside = {k: v for k, v in stated.items()
                       if recorded and v not in recorded and v != "never measured"}
            contradictions.append({
                "disease": names.get("dossiers") or next(iter(names.values())),
                "field": "prevalence",
                "byLayer": {k: {"value": v, "grade": GRADE.get(k, "?")}
                            for k, v in stated.items()},
                "recordedByOrphanet": recorded,
                "severity": "wrong band" if outside else "which band to quote",
                "says": (
                    "at least one layer names a band Orphanet never records for this "
                    "disorder" if outside else
                    "the layers quote different bands, and Orphanet records all of them - "
                    "this is the collapse-of-a-spread problem, not an error of fact"
                ),
            })

        # --- gene: authored single vs measured set ----------------------------------------
        if "lexicon" in layers and "dossiers" in layers:
            g = layers["lexicon"].get("gene")
            catalogue = layers["dossiers"].get("genes") or []
            unknown_tokens = set((lexicon.get("unknownTokens") or {}).values())
            if g and g not in unknown_tokens and catalogue and g not in catalogue:
                contradictions.append({
                    "disease": names.get("dossiers"),
                    "field": "gene",
                    "byLayer": {"lexicon": {"value": g, "grade": "authored"},
                                "dossiers": {"value": catalogue, "grade": "measured"}},
                    "severity": "attribution",
                    "says": ("the authored causal gene is not among the genes the "
                             "catalogue attributes to this disease"),
                })

    # ---- 3. the coverage matrix --------------------------------------------------------
    layer_names = sorted({k for v in claims.values() for k in v})
    matrix = []
    for key, layers in sorted(claims.items()):
        if not key:
            continue
        matrix.append({
            "disease": (layers.get("dossiers") or layers.get("lexicon")
                        or next(iter(layers.values()))).get("name"),
            "layers": sorted(layers),
            "count": len(layers),
        })
    matrix.sort(key=lambda r: -r["count"])

    by_severity = defaultdict(int)
    for c in contradictions:
        by_severity[c["severity"]] += 1

    payload = {
        "generated": "tools/consistency.py",
        "premise": (
            "Each layer here is careful about itself. Nothing checks them against each "
            "other. Twenty artefacts make overlapping claims about the same diseases and "
            "the system has never been audited even though every part of it has."
        ),
        "caveat": (
            "A contradiction proves at least one layer is wrong without saying which. Where "
            "an authored layer contradicts a measured one the measured one is the better "
            "bet, but that is a prior, not a finding."
        ),
        "scope": {
            "layersIndexed": layer_names,
            "diseaseKeys": len(claims),
            "joinedOn": "normalised disease name - the only key every layer shares",
        },
        "contradictions": contradictions,
        "bySeverity": dict(by_severity),
        "unjoinable": unjoinable,
        "coverage": matrix,
        "summary": {
            "contradictions": len(contradictions),
            "diseasesInMoreThanOneLayer": sum(1 for r in matrix if r["count"] > 1),
            "diseasesInOnlyOneLayer": len(unjoinable),
            "mostCrossReferenced": matrix[0] if matrix else None,
        },
    }

    RARE.mkdir(parents=True, exist_ok=True)
    out = RARE / "consistency.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("wrote %s" % out.relative_to(ROOT))
    s = payload["summary"]
    print("  %d layers indexed, %d disease keys" % (len(layer_names), len(claims)))
    print("  %d cross-referenced in more than one layer, %d in only one"
          % (s["diseasesInMoreThanOneLayer"], s["diseasesInOnlyOneLayer"]))
    print("  %d CONTRADICTIONS" % s["contradictions"])
    for sev, n in sorted(by_severity.items(), key=lambda kv: -kv[1]):
        print("      %-22s %d" % (sev, n))
    print()
    for c in contradictions:
        print("  %-34s %-11s %s" % ((c["disease"] or "?")[:34], c["field"], c["severity"]))
        for layer, v in c["byLayer"].items():
            print("      %-18s %-9s %s" % (layer, v["grade"], v["value"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
