"""What has actually been authorised for use on a patient, by specialty and by year.

THE FOUNDING MEASUREMENT OF THE PREDICTIVE-TECHNOLOGY LAYER, and it exists so that layer can
be built without breaking ADR 0007.

The obvious way to build an atlas of clinical AI is to write cards: model, dataset, AUROC,
sensitivity, regulatory status. That is a catalogue of numbers typed from papers, it drifts
the day after it is written, and this repository has an ADR whose entire purpose is to forbid
exactly that — a construct enters only when a tool computes it from an ingested source. A
hand-typed leaderboard would be the eleventh authored layer in a project whose one claim on
the reader is that every number can be traced to the artefact that produced it.

So the layer starts from the one thing that is published, dated, and not self-reported: the
FDA's own list of AI-enabled devices authorised for clinical use. Nothing here is an opinion
about whether a model is good. It is a count of what a regulator has allowed.

WHAT THE COUNT TURNS OUT TO SAY, and it is the reason this is worth a screen:

  * 1,164 of 1,524 authorisations are RADIOLOGY. Two thirds of a field's entire deployed
    surface is one specialty.
  * The list contains NO DERMATOLOGY PANEL AT ALL — and that fact, on its own, is a trap.
    The first version of this tool concluded from it that no AI device for skin cancer has
    been authorised. That is FALSE, and the tool's own stated limitation is what caught it: a
    panel is the committee that reviewed a device, not the disease it addresses. Scanning the
    device names finds MelaFind (2011) and DermaSensor (2024), both reviewed under General
    and Plastic Surgery. So the true statement is narrower and still stark: two devices out of
    1,524 address skin lesions, against 1,164 for radiology. The scan is computed below rather
    than described here, because a correction that lives in a comment is one the next reader
    has to trust.
  * Ophthalmology has 10 and pathology 9, against 147 for cardiovascular.

WHAT THIS IS NOT. It is not a measure of quality, of accuracy, or of clinical value, and it
is not a complete picture of deployment: it is one jurisdiction, one authorisation pathway,
and a device can be authorised and unused or used and unauthorised elsewhere. It answers one
question exactly — has a regulator here permitted this class of thing — and the answer to that
question is the top of a readiness scale, not the whole of it.

NOT AN ADAPTER (.claude/skills/sieve-new-adapter): question 1 fails. Nothing is ranked, no
entity carries a score, there is no selection operator and therefore no null. This is a
tabulation with its denominators, said plainly so nobody looks for the Stage 1 apparatus and
concludes it was forgotten.

    python tools/cleared_devices.py
"""
from __future__ import annotations

import collections
import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sieve.pipeline.sources import BY_KEY  # noqa: E402

DEST = ROOT / "out" / "devices" / "cleared_devices.json"

#: Words that would appear in the NAME of a device addressing skin lesions. Used to check the
#: panel counts against the devices themselves, because a panel is a review committee and not
#: a disease area — the distinction that made the first version of this tool wrong.
SKIN_TERMS = ("skin", "derm", "melanom", "lesion", "cutaneous", "nevus", "pigment")

#: The specialties a reader of the medical-AI literature would expect to find, written down
#: BEFORE the counts are read, so that "dermatology is absent" is a prediction that failed
#: rather than an observation selected after the fact. Panels the FDA does not use are marked
#: as such rather than quietly dropped — an expectation that the data cannot even express is
#: a different result from one it contradicts.
EXPECTED = [
    "Radiology", "Cardiovascular", "Neurology", "Ophthalmic", "Pathology",
    "Dermatology", "Gastroenterology-Urology", "Hematology", "Clinical Chemistry",
    "Microbiology", "Orthopedic", "Anesthesiology",
]


def rows() -> list[dict[str, str]]:
    with BY_KEY["fda_ai_devices"].dest.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def year_of(value: str) -> str | None:
    value = (value or "").strip()
    return value[-4:] if len(value) >= 4 and value[-4:].isdigit() else None


def main() -> int:
    path = BY_KEY["fda_ai_devices"].dest
    if not path.exists():
        print(f"missing {path}", file=sys.stderr)
        return 1

    data = rows()
    panels = collections.Counter(r.get("Panel (Lead)", "").strip() for r in data)
    panels.pop("", None)
    years = collections.Counter(filter(None, (year_of(r.get("Date of Final Decision", ""))
                                              for r in data)))
    companies = collections.Counter(r.get("Company", "").strip() for r in data)
    companies.pop("", None)
    products = collections.Counter(r.get("Primary Product Code", "").strip() for r in data)
    products.pop("", None)

    total = sum(panels.values())
    top = panels.most_common(1)[0] if panels else ("", 0)

    # How concentrated is the deployed surface? Reported as the share held by the largest
    # specialty and as the count needed to reach half, because both are readable and neither
    # needs a coefficient nobody can check by eye.
    running = 0
    half = 0
    for _, n in panels.most_common():
        running += n
        half += 1
        if running >= total / 2:
            break

    per_year_panel: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in data:
        y = year_of(r.get("Date of Final Decision", ""))
        p = r.get("Panel (Lead)", "").strip()
        if y and p:
            per_year_panel[y][p] += 1

    # THE PANEL COUNT CHECKED AGAINST THE DEVICE NAMES.
    #
    #  "No dermatology panel" is a fact about review pathways and says nothing directly about
    #  skin cancer. Reading it as though it did is the mistake this scan exists to prevent,
    #  and it is a mistake this tool made before the scan was added.
    skin = []
    for r in data:
        blob = f"{r.get('Device', '')} {r.get('Company', '')}".lower()
        if any(t in blob for t in SKIN_TERMS) and "cardio" not in blob:
            skin.append({
                "device": (r.get("Device") or "").strip(),
                "company": (r.get("Company") or "").strip(),
                "panel": (r.get("Panel (Lead)") or "").strip(),
                "decided": (r.get("Date of Final Decision") or "").strip(),
                "submission": (r.get("Submission Number") or "").strip(),
            })

    expected_rows = []
    for name in EXPECTED:
        expected_rows.append({
            "panel": name,
            "devices": panels.get(name, 0),
            "present_in_list": name in panels,
        })

    payload = {
        "generated": "2026-08-30",
        "provenance": "FDA, Artificial Intelligence-Enabled Medical Devices, "
                      "https://www.fda.gov/medical-devices/software-medical-device-samd/"
                      "artificial-intelligence-enabled-medical-devices",
        "governed_by": "docs/adr/0007-theory-enters-by-measurement.md",
        "question": "Of the clinical AI that gets published, how much has a regulator "
                    "actually authorised for use on a patient — and in which specialties?",
        "not_an_adapter": {
            "gate": ".claude/skills/sieve-new-adapter",
            "fails": "question 1 — nothing is ranked and no entity carries a score. This is a "
                     "tabulation with its denominators, and it carries no null because there "
                     "is no statistic to calibrate.",
        },
        "why_this_and_not_a_card_catalogue": (
            "An atlas of clinical AI written as cards — model, dataset, AUROC, regulatory "
            "status — is a page of numbers typed from papers, and ADR 0007 exists to forbid "
            "exactly that. This starts from the one record that is published, dated and not "
            "self-reported. It says nothing about whether a model is good; it counts what a "
            "regulator has permitted."
        ),
        "scale": {
            "devices": len(data),
            "panels": len(panels),
            "first_decision": min(years) if years else None,
            "last_decision": max(years) if years else None,
            "distinct_companies": len(companies),
            "distinct_product_codes": len(products),
        },
        "concentration": {
            "largest_panel": top[0],
            "largest_panel_devices": top[1],
            "largest_panel_share": round(top[1] / total, 4) if total else None,
            "panels_to_reach_half": half,
            "reading": f"{top[1]:,} of {total:,} authorisations sit in one specialty. "
                       f"{half} panel(s) account for half the list.",
        },
        "by_panel": [{"panel": p, "devices": n, "share": round(n / total, 4)}
                     for p, n in panels.most_common()],
        "expected_versus_found": {
            "written_before_reading_the_counts": True,
            "rows": expected_rows,
            "absent": [r["panel"] for r in expected_rows if not r["present_in_list"]],
            "reading": "The specialties a reader of this literature would expect, listed "
                       "before the counts were read. A panel that does not appear at all is "
                       "a stronger statement than a small count, and dermatology is the case: "
                       "dermatology is the case. Read `skin_lesion_devices` before drawing "
                       "any conclusion from it: the panel is absent, the devices are not.",
        },
        "skin_lesion_devices": {
            "matched_by_name": skin,
            "count": len(skin),
            "share_of_list": round(len(skin) / len(data), 5) if data else None,
            "reading": "A panel is a review committee, not a disease area. The absence of a "
                       "Dermatology panel does NOT mean no authorised device addresses skin "
                       "lesions — scanning the device names finds these, reviewed under "
                       "General and Plastic Surgery. The honest comparison is the one this "
                       "makes: a handful of skin-lesion devices against 1,164 radiology "
                       "authorisations. The first version of this tool got that wrong, and "
                       "its own stated limitation is what caught it.",
            "method": "substring match on device and company name over "
                      + ", ".join(SKIN_TERMS)
                      + "; a name-based scan misses a device whose name says nothing about "
                        "what it looks at, so this count is a floor",
        },
        "by_year": [{"year": y, "devices": years[y]} for y in sorted(years)],
        "by_year_and_panel": {
            y: dict(per_year_panel[y].most_common(6)) for y in sorted(per_year_panel)[-6:]
        },
        "busiest_companies": [{"company": c, "devices": n} for c, n in companies.most_common(15)],
        "says": "Authorisation, not quality and not use. A device on this list has been "
                "permitted; it has not been shown to help anyone, and nothing here reports an "
                "accuracy, a population or an outcome. Read it as the top rung of a readiness "
                "scale — regulated deployment — and as nothing else.",
        "limits": [
            "One jurisdiction. A device authorised in the EU under CE marking, or in Brazil "
            "by ANVISA, is invisible here, so the specialty distribution is partly a "
            "statement about the FDA's pathways rather than about the technology.",
            "The FDA's own list is curated and has been revised repeatedly; devices whose AI "
            "component was not described as such in the submission may be missing, and the "
            "direction of that error is unknown rather than conservative.",
            "A panel is the committee that reviewed the device, not the disease it addresses. "
            "A melanoma-detection device reviewed under Radiology would be counted as "
            "radiology, so 'no dermatology device' is a statement about review panels and "
            "needs the device names read before it becomes a statement about skin cancer.",
        ],
    }

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {DEST.relative_to(ROOT)}")
    print(f"  {len(data):,} authorised devices, {len(panels)} panels, "
          f"{min(years)}–{max(years)}")
    print(f"  {top[0]}: {top[1]:,} ({100 * top[1] / total:.1f} %) — "
          f"{half} panel(s) hold half the list")
    absent = [r["panel"] for r in expected_rows if not r["present_in_list"]]
    if absent:
        print(f"  expected panel ABSENT from the list: {', '.join(absent)}")
    print(f"  but {len(skin)} device(s) address skin lesions by name, reviewed elsewhere: "
          + "; ".join(f"{d['device'][:28]} ({d['panel']}, {d['decided'][-4:]})" for d in skin))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
