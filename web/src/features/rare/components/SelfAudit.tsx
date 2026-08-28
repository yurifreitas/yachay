/** Does this dashboard agree with itself?
 *
 *  Every other section renders findings about disease. This one renders findings about the
 *  project, and it exists because two measured artefacts — `consistency.json` and
 *  `lexicon_check.json` — had been computed, documented and then left on disk. A dashboard
 *  that publishes twenty layers of other people's gaps while keeping its own contradictions
 *  in a file nobody opens is publishing them nowhere.
 *
 *  THREE VIEWS, THREE DATA STRUCTURES, THREE FORMS:
 *
 *    contradictions   claim x layer, tiny n     -> a Cleveland dot plot, read as a table
 *    identifiers      12 x 5 verdict grid       -> a status matrix, colour + glyph + label
 *    evidence         23 systems x 4 grades     -> a MARIMEKKO
 *
 *  The marimekko is the one that needs defending, because an exotic form has to answer
 *  better than the plain one or it is decoration. The question is "which organ systems does
 *  the field quantify, and how big are they?" — two variables at once. A normalised stacked
 *  bar shows composition and throws away size, so the genitourinary system (13,770 signs)
 *  and the thoracic cavity (63) look equally important. A plain bar shows size and throws
 *  away composition. The marimekko encodes size as WIDTH and composition as HEIGHT, which
 *  is the only common form that keeps both — and the finding here is precisely that the
 *  badly-measured systems are the large ones.
 */
import { useMemo, useState } from "react";
import { EChart } from "../../../components/organisms/EChart";
import { chartInk } from "../../../lib/palette";
import { useHashParam } from "../../../lib/useHashParam";
import { consistency, lexiconCheck } from "../data/selfAudit";
import { evidenceAtlas } from "../data/evidenceAtlas";
import { verdictTone } from "../selfAuditModel";
import css from "./SelfAudit.module.css";

const VIEWS = [
  { id: "contradictions", label: "Where the layers disagree" },
  { id: "identifiers", label: "Do the identifiers resolve?" },
  { id: "evidence", label: "What the field measures" },
];

const nf = (v: number) => v.toLocaleString("en-US");

export function SelfAudit() {
  const [view, setView] = useHashParam("q", "contradictions");

  return (
    <div className={css.root}>
      <p className={css.premise}>
        {consistency.premise} <strong>{consistency.caveat}</strong>
      </p>

      <div className={css.viewNav} role="tablist" aria-label="Self-audit views">
        {VIEWS.map((v) => (
          <button
            key={v.id}
            type="button"
            role="tab"
            aria-selected={view === v.id}
            className={view === v.id ? css.viewOn : css.view}
            onClick={() => setView(v.id)}
          >
            {v.label}
          </button>
        ))}
      </div>

      {view === "contradictions" && <Contradictions />}
      {view === "identifiers" && <Identifiers />}
      {view === "evidence" && <EvidenceShape />}
    </div>
  );
}

/* -------------------------------------------------------- view 1: contradictions ------- */

function Contradictions() {
  const c = consistency;
  const cover = c.coverage.filter((r) => r.count > 1).slice(0, 12);

  return (
    <>
      <div className={css.tiles}>
        <Tile label="Contradictions between layers" value={nf(c.summary.contradictions)}
              note="each proves at least one layer is wrong, without saying which" tone="bad" />
        <Tile label="Diseases in more than one layer" value={nf(c.summary.diseasesInMoreThanOneLayer)}
              note="the only ones anything can be checked against" />
        <Tile label="Diseases in one layer only" value={nf(c.summary.diseasesInOnlyOneLayer)}
              note="no disagreement — which is not agreement" tone="gap" />
        <Tile label="Layers indexed" value={nf(c.scope.layersIndexed.length)}
              note={`joined on ${c.scope.joinedOn}`} />
      </div>

      {c.contradictions.length === 0 ? (
        <p className={css.reading}>No contradictions. That is a result, not a default.</p>
      ) : (
        <ul className={css.conflicts}>
          {c.contradictions.map((x, i) => (
            <li key={`${x.disease}-${x.field}-${i}`} className={css.conflict}>
              <div className={css.conflictHead}>
                <span className={css.conflictName}>{x.disease}</span>
                <span className={css.conflictField}>{x.field}</span>
                <span className={`${css.sev} ${x.severity === "identity" ? css.sevHigh : ""}`}>
                  {x.severity}
                </span>
              </div>
              {/* A dot plot would be overkill for two values; the honest form at this n is
                  the values side by side, LABELLED WITH THEIR GRADE — because which layer
                  is authored and which is measured is the whole reading. */}
              <div className={css.claims}>
                {Object.entries(x.byLayer).map(([layer, v]) => (
                  <div key={layer} className={css.claim}>
                    <span className={`${css.grade} ${css[v.grade] ?? ""}`}>{v.grade}</span>
                    <span className={css.claimLayer}>{layer}</span>
                    <span className={css.claimValue}>
                      {Array.isArray(v.value) ? v.value.join(", ") : v.value}
                    </span>
                  </div>
                ))}
              </div>
              {x.recordedByOrphanet && x.recordedByOrphanet.length > 0 && (
                <p className={css.orphanet}>
                  Orphanet records {x.recordedByOrphanet.length} bands for this disorder:{" "}
                  {/* Mapped to elements, not joined with markup in a string: React escapes
                      the latter, which is correct of it and rendered a literal `</code>`
                      on screen. */}
                  {x.recordedByOrphanet.map((b, j) => (
                    <span key={b}>
                      {j > 0 && " · "}
                      <code>{b}</code>
                    </span>
                  ))}
                </p>
              )}
              <p className={css.conflictSays}>{x.says}</p>
            </li>
          ))}
        </ul>
      )}

      <details className={css.more}>
        <summary className={css.summary}>
          Which layers speak about which disease ({cover.length} cross-referenced)
        </summary>
        <ul className={css.coverList}>
          {cover.map((r) => (
            <li key={r.disease} className={css.coverRow}>
              <span className={css.coverName}>{r.disease}</span>
              <span className={css.coverLayers}>
                {r.layers.map((l) => (
                  <span key={l} className={css.layerChip}>{l}</span>
                ))}
              </span>
            </li>
          ))}
        </ul>
      </details>
    </>
  );
}

/* ---------------------------------------------------------- view 2: identifiers -------- */

function Identifiers() {
  const lc = lexiconCheck;
  const fields = lc.scope.fieldsChecked;

  return (
    <>
      <div className={css.tiles}>
        <Tile label="Diseases clean" value={`${lc.clean} of ${lc.rows.length}`}
              note="every identifier resolves and nothing contradicts it" />
        <Tile label="Carrying a flag" value={nf(lc.flagged)} note="see the grid" tone="bad" />
        <Tile label="Checked against" value={nf(lc.scope.orphanetDisorders)}
              note={`Orphanet disorders · ${nf(lc.scope.annotatedDiseases)} annotated diseases`} />
        {/* This tile used to read "mondo": the ontology was named in the lexicon and never
            ingested, so a whole column of the grid meant "never checked". Ingesting MONDO
            emptied the tile and turned that column into four defects. The empty state says
            so rather than rendering a blank. */}
        <Tile
          label="Unverifiable by design"
          value={lc.scope.unverifiableByDesign.length
            ? lc.scope.unverifiableByDesign.join(", ")
            : "none"}
          note={lc.scope.unverifiableByDesign.length
            ? "not ingested, so neither confirmed nor refuted — never shown as passing"
            : "every identifier space in this crosswalk is now on disk and checked"}
          tone={lc.scope.unverifiableByDesign.length ? "gap" : undefined}
        />
      </div>

      {/* A STATUS MATRIX, not a heatmap. Colour alone would fail anyone who cannot separate
          the hues, and these three states are not ordered — a "gap" is not between "ok" and
          "bad", it is a different kind of answer. So each cell carries colour AND a glyph
          AND its verdict in words on hover. */}
      <div className={css.matrixWrap}>
        <table className={css.matrix}>
          <caption className={css.caption}>
            Every identifier in the authored crosswalk, resolved against the catalogues.
            <span className={css.legend}>
              <span className={css.ok}>● resolves</span>
              <span className={css.gap}>◐ unverifiable or declared unknown</span>
              <span className={css.bad}>▲ defect</span>
            </span>
          </caption>
          <thead>
            <tr>
              <th scope="col" className={css.thName}>disease</th>
              {fields.map((f) => (
                <th key={f} scope="col" className={css.th}>{f}</th>
              ))}
              <th scope="col" className={css.th}>confidence</th>
            </tr>
          </thead>
          <tbody>
            {lc.rows.map((r) => (
              <tr key={r.name} className={r.flags.length ? css.rowFlagged : undefined}>
                <th scope="row" className={css.rowName} title={r.name}>{r.name}</th>
                {fields.map((f) => {
                  const check = r.checks[f];
                  const tone = check ? verdictTone(check.verdict) : "gap";
                  return (
                    <td key={f} className={css.cell}>
                      <span className={`${css.mark} ${css[tone]}`}
                            title={check ? `${check.verdict} — ${check.says}` : "not checked"}>
                        {tone === "ok" ? "●" : tone === "gap" ? "◐" : "▲"}
                      </span>
                    </td>
                  );
                })}
                <td className={css.cell}>
                  <span className={css.confidence}>{r.confidence ?? "—"}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* A13 proposed surfacing the confidence marks in the interface as the cheap honest
          move for judgement layers. This is the evidence that it is worth doing: the marks
          are not decoration, they predicted where the identifiers would fail. */}
      <div className={css.calibration}>
        <span className={css.calibLabel}>Did the author&rsquo;s own confidence mark predict this?</span>
        <div className={css.calibRow}>
          {Object.entries(lc.calibration.byConfidence).map(([conf, v]) => (
            <div key={conf} className={css.calibCell}>
              <span className={css.calibConf}>{conf}</span>
              <span className={css.calibBar}>
                <span className={css.calibFill}
                      style={{ width: `${v.share * 100}%` }} />
              </span>
              <span className={css.calibCount}>{v.flagged}/{v.diseases}</span>
            </div>
          ))}
        </div>
        <p className={css.conflictSays}>
          {lc.calibration.says} <em>{lc.calibration.caveat}</em>
        </p>
      </div>

      <p className={css.reading}>{lc.caveat}</p>
    </>
  );
}

/* ------------------------------------------------------------- view 3: evidence -------- */

function EvidenceShape() {
  const e = evidenceAtlas;
  const [minSigns, setMinSigns] = useState(0);

  const systems = useMemo(
    () => e.bySystem.filter((s) => s.signs >= minSigns).slice(0, 20),
    [e.bySystem, minSigns]
  );
  const grades = ["quantified", "single-case", "class", "none"] as const;

  return (
    <>
      <div className={css.tiles}>
        <Tile label="Diseases with a quantified sign"
              value={`${Math.round(e.profile.shareWithAQuantifiedSign * 100)}%`}
              note={`${nf(e.profile.diseasesWithAQuantifiedSign)} of ${nf(e.profile.diseasesWithPhenotypeAnnotations)}`}
              tone="bad" />
        <Tile label="Median denominator" value={`${e.profile.denominators.median} patients`}
              note={`${Math.round(100 * e.profile.denominators.underTen / e.profile.denominators.count)}% of quantified signs rest on fewer than ten`}
              tone="bad" />
        <Tile label="Annotations graded" value={nf(e.profile.annotations)}
              note="every phenotype row in the catalogue" />
        <Tile label="Largest series in the corpus" value={nf(e.profile.denominators.max ?? 0)}
              note={`p95 is ${e.profile.denominators.p95} — the tail is very short`} />
      </div>

      <div className={css.toolbar}>
        <label className={css.searchLabel} htmlFor="min-signs">
          Hide systems below
        </label>
        <input id="min-signs" type="range" min={0} max={5000} step={250}
               value={minSigns} onChange={(ev) => setMinSigns(Number(ev.target.value))} />
        <span className={css.searchResult}>
          {minSigns === 0 ? "showing all" : `${nf(minSigns)} signs`} · {systems.length} systems
        </span>
      </div>

      {/* THE MARIMEKKO. Width = how many signs the system carries; height = how those signs
          are graded. Both variables at once, which is the point: the finding is that the
          badly-measured systems are the LARGE ones, and a normalised bar chart would make
          every system the same width and hide exactly that. */}
      <div className={css.chart}>
        <EChart
          height={340}
          deps={[systems]}
          ariaLabel={
            "Marimekko of organ systems. Column width is the number of signs, height is the "
            + "share of each evidence grade. " +
            systems.slice(0, 6).map((s) =>
              `${s.name}: ${s.signs} signs, ${Math.round(100 * (s.shareQuantified ?? 0))}% quantified`
            ).join(". ")
          }
          build={(mode) => {
            const ink = chartInk(mode);
            const total = systems.reduce((a, s) => a + s.signs, 0) || 1;
            // Colours are the evidence ramp used everywhere else on this page: one hue,
            // falling lightness, plus the reserved neutral for "nothing recorded".
            const ramp = mode === "dark"
              ? ["#8fd4e8", "#4fa6c4", "#2f6f8a", "#4a4f55"]
              : ["#2d7d99", "#5aa8c2", "#9ecfdf", "#b9bcc0"];

            let x = 0;
            const boxes: unknown[] = [];
            systems.forEach((s) => {
              const w = (s.signs / total) * 100;
              let y = 0;
              grades.forEach((g, gi) => {
                const share = s.byGrade[g] / (s.signs || 1);
                const h = share * 100;
                if (h > 0) {
                  boxes.push({
                    value: [x, y, w, h],
                    itemStyle: { color: ramp[gi], borderColor: ink.surface, borderWidth: 1 },
                    meta: { system: s.name, grade: g, count: s.byGrade[g], signs: s.signs,
                            share },
                  });
                }
                y += h;
              });
              x += w;
            });

            return {
              grid: { left: 44, right: 12, top: 16, bottom: 74 },
              xAxis: { type: "value", min: 0, max: 100, show: false },
              yAxis: {
                type: "value", min: 0, max: 100, inverse: true,
                axisLine: { show: false }, axisTick: { show: false },
                splitLine: { show: false },
                axisLabel: { color: ink.muted, formatter: (v: number) => `${v}%` },
              },
              tooltip: {
                backgroundColor: ink.surface, borderColor: ink.grid,
                textStyle: { color: ink.text },
                formatter: (p: { data: { meta: Record<string, string | number> } }) => {
                  const m = p.data.meta;
                  return `<strong>${m.system}</strong><br/>${m.grade}: ${m.count} of ${m.signs} signs`
                    + `<br/>${Math.round(Number(m.share) * 100)}% of this system`;
                },
              },
              series: [{
                type: "custom",
                renderItem: (_p: unknown, api: {
                  value: (i: number) => number;
                  coord: (v: [number, number]) => [number, number];
                  style: () => Record<string, unknown>;
                }) => {
                  const [x0, y0] = api.coord([api.value(0), api.value(1)]);
                  const [x1, y1] = api.coord([
                    api.value(0) + api.value(2), api.value(1) + api.value(3),
                  ]);
                  return {
                    type: "rect",
                    shape: { x: x0, y: y0, width: x1 - x0, height: y1 - y0 },
                    style: api.style(),
                  };
                },
                data: boxes,
              }],
            };
          }}
        />
        {/* Column labels live outside the canvas: rotated axis labels under a marimekko are
            unreadable at these widths, and the reader needs the name beside the width. */}
        <ol className={css.mekkoKey}>
          {systems.map((s) => (
            <li key={s.id} className={css.mekkoKeyRow}
                style={{ flexGrow: s.signs, flexBasis: 0 }}>
              <span className={css.mekkoName}>
                {s.name.replace(/^Abnormality of (the )?/, "")}
              </span>
              <span className={css.mekkoPct}>
                {Math.round(100 * (s.shareQuantified ?? 0))}%
              </span>
            </li>
          ))}
        </ol>
      </div>

      <p className={css.reading}>
        Column width is the number of signs; height is how those signs are graded. Across{" "}
        <strong>{e.bySystem.length}</strong> systems the quantified share runs{" "}
        <strong>
          {Math.round(100 * Math.min(...e.bySystem.map((s) => s.shareQuantified ?? 1)))}%
        </strong>{" "}
        to{" "}
        <strong>
          {Math.round(100 * Math.max(...e.bySystem.map((s) => s.shareQuantified ?? 0)))}%
        </strong>{" "}
        — there is no well-measured system, and the widest columns are not the best ones.
      </p>
      <p className={css.reading}>{e.attention.says}</p>
    </>
  );
}

/* ----------------------------------------------------------------------- shared -------- */

function Tile({
  label, value, note, tone,
}: { label: string; value: string; note: string; tone?: "bad" | "gap" }) {
  return (
    <div className={css.tile}>
      <span className={css.tileLabel}>{label}</span>
      <span className={`${css.tileValue} ${tone ? css[tone] : ""}`}>{value}</span>
      <span className={css.tileNote}>{note}</span>
    </div>
  );
}
