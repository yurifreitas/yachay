import { useState } from "react";
import { useT } from "../../i18n";
import { CRISPR } from "../../i18n/crispr";
import { useViewModels } from "../rare/components/HyperViews";
import css from "./CrisprViews.module.css";

/** THREE VIEWS OF THE DEPMAP RUN THAT A BAR CHART CANNOT CARRY.
 *
 *  The run dashboard had the numbers and drew them one dimension at a time. Each of these
 *  puts back the dimension that does the work:
 *
 *    field    z over (raw score, observation count). The library's thesis is that the same
 *             score means different things at different n, and on the usual score-against-z
 *             scatter n is a colour nobody reads. Here it is an axis, and the iso-lines bend.
 *    bump     raw rank against calibrated rank for the raw top sixty. A reordering cannot be
 *             shown by a bar chart of either ranking — only by the lines between them.
 *    matrix   lineages against the genes they nominated, seriated. A per-lineage bar answers
 *             "what did Lung find" and hides the only question worth asking: whether anything
 *             Lung found was found anywhere else.
 *
 *  Layouts solved in `tools/view_models.py` under ADR 0008; this file draws.
 */


/* ------------------------------------------------------------------ the calibration field */

export function CalibrationField() {
  const tt = useT();
  const models = useViewModels();
  const m = models?.calibration_field;
  const [hover, setHover] = useState<{ r: number; c: number } | null>(null);
  if (!models) return <div className={css.skeleton} style={{ height: 380 }} aria-hidden />;
  if (!m) return null;

  const maxN = Math.max(...m.grid.flatMap((row) => row.map((c) => c.n)));
  const cell = hover ? m.grid[hover.r][hover.c] : null;
  const nAt = (r: number) =>
    Math.round(m.n_range[0] + (r / (m.rows_n - 1)) * (m.n_range[1] - m.n_range[0]));
  const scoreAt = (c: number) =>
    m.score_range[0] + (c / (m.cols - 1)) * (m.score_range[1] - m.score_range[0]);

  return (
    <figure className={css.figure}>
      <figcaption className={css.caption}>
        <strong>{tt(CRISPR.fieldTitle)}</strong> {m.reading}
      </figcaption>

      <div className={css.fieldWrap}>
        <div className={css.fieldY}>
          <span>{m.n_range[1]}</span><span>{tt(CRISPR.lines)}</span><span>{m.n_range[0]}</span>
        </div>
        <div
          className={css.field}
          style={{ gridTemplateColumns: `repeat(${m.cols}, 1fr)` }}
          onMouseLeave={() => setHover(null)}
        >
          {[...m.grid].reverse().map((row, ri) =>
            row.map((c, ci) => {
              const r = m.rows_n - 1 - ri;
              return (
                <span
                  key={`${r}-${ci}`}
                  className={css.fieldCell}
                  data-hot={hover && hover.r === r && hover.c === ci ? true : undefined}
                  onMouseEnter={() => setHover({ r, c: ci })}
                >
                  <span className={css.fieldFill}
                        style={{ opacity: c.n ? 0.1 + 0.9 * Math.sqrt(c.n / maxN) : 0 }} />
                  {c.ess > 0 && (
                    <span className={css.fieldEss}
                          style={{ opacity: 0.3 + 0.7 * Math.min(1, c.ess / 12) }} />
                  )}
                </span>
              );
            })
          )}
        </div>
      </div>
      <div className={css.fieldX}>
        <span>{m.score_range[0].toFixed(1)}</span>
        <span>{tt(CRISPR.rawScore)}</span>
        <span>{m.score_range[1].toFixed(1)}</span>
      </div>

      <div className={css.readout} aria-live="polite">
        {cell && cell.n > 0
          ? <>
              <strong>{cell.n}</strong> {tt(CRISPR.genes)} · {tt(CRISPR.around)}{" "}
              {scoreAt(hover!.c).toFixed(2)} · {nAt(hover!.r)} {tt(CRISPR.lines)} ·{" "}
              <span className={css.readoutVal}>mean z {cell.z}</span>
              {cell.ess > 0 && <> · <span className={css.essNote}>{cell.ess} pan-essential</span></>}
            </>
          : <span className={css.readoutHint}>{tt(CRISPR.fieldHint)}</span>}
      </div>

      <div className={css.legend}>
        <span><span className={`${css.key} ${css.keyFill}`} /> {tt(CRISPR.keyGenes)}</span>
        <span><span className={`${css.key} ${css.keyEss}`} /> {tt(CRISPR.keyEssential)}</span>
      </div>
    </figure>
  );
}

/* ------------------------------------------------------------------ the bump */

export function RankBump() {
  const tt = useT();
  const models = useViewModels();
  const m = models?.rank_shift;
  const [hover, setHover] = useState<string | null>(null);
  if (!models) return <div className={css.skeleton} style={{ height: 460 }} aria-hidden />;
  if (!m) return null;

  const H = 460, W = 620, PAD = 26;
  const maxCal = Math.max(...m.rows.map((r) => r.cal));
  const y = (rank: number, scale: number) => PAD + ((rank - 1) / scale) * (H - 2 * PAD);

  return (
    <figure className={css.figure}>
      <figcaption className={css.caption}>
        <strong>{tt(CRISPR.bumpTitle)}</strong> {m.reading}
      </figcaption>

      <svg viewBox={`0 0 ${W} ${H}`} className={css.svg} role="img"
           aria-label={`${m.rows.length} genes, raw rank against calibrated rank`}>
        <text x={130} y={14} className={css.axisLabel} textAnchor="middle">{tt(CRISPR.rawRank)}</text>
        <text x={W - 130} y={14} className={css.axisLabel} textAnchor="middle">{tt(CRISPR.calRank)}</text>
        <line x1={130} y1={PAD} x2={130} y2={H - PAD} className={css.axis} />
        <line x1={W - 130} y1={PAD} x2={W - 130} y2={H - PAD} className={css.axis} />

        {m.rows.map((r) => {
          const on = hover === r.gene;
          return (
            <g key={r.gene}
               className={`${css.bump} ${r.ess ? css.bumpEss : ""}`}
               data-on={on || undefined}
               onMouseEnter={() => setHover(r.gene)}
               onMouseLeave={() => setHover(null)}>
              <line x1={130} y1={y(r.raw, m.rows.length)} x2={W - 130} y2={y(r.cal, maxCal)} />
              <circle cx={130} cy={y(r.raw, m.rows.length)} r={2.6} />
              <circle cx={W - 130} cy={y(r.cal, maxCal)} r={2.6} />
              {on && (
                <text x={122} y={y(r.raw, m.rows.length) + 4} className={css.bumpLabel}
                      textAnchor="end">{r.gene}</text>
              )}
            </g>
          );
        })}
      </svg>

      <div className={css.readout} aria-live="polite">
        {hover
          ? (() => {
              const r = m.rows.find((x) => x.gene === hover)!;
              return <>
                <strong>{r.gene}</strong> · {tt(CRISPR.rawRank)} {r.raw} → {r.cal} ·{" "}
                {r.n} {tt(CRISPR.lines)}
                {r.ess && <> · <span className={css.essNote}>pan-essential</span></>}
              </>;
            })()
          : <span className={css.readoutHint}>
              {m.of_which_essential} {tt(CRISPR.bumpHint1)} · {m.fell} {tt(CRISPR.bumpHint2)} ·{" "}
              {m.essential_among_fallen} {tt(CRISPR.bumpHint3)}
            </span>}
      </div>
    </figure>
  );
}

/* ------------------------------------------------------------------ the lineage matrix */

export function LineageMatrix() {
  const tt = useT();
  const models = useViewModels();
  const m = models?.lineage_matrix;
  const [hover, setHover] = useState<{ r: number; c: number } | null>(null);
  if (!models) return <div className={css.skeleton} style={{ height: 420 }} aria-hidden />;
  if (!m) return null;

  const max = Math.max(...m.cells.flat());
  const shared = Object.values(m.shared).filter((v) => v > 1).length;

  return (
    <figure className={css.figure}>
      <figcaption className={css.caption}>
        <strong>{tt(CRISPR.matrixTitle)}</strong> {m.reading}
      </figcaption>

      <div className={css.matrixScroll}>
        <div className={css.matrix}
             style={{ gridTemplateColumns: `140px repeat(${m.cols.length}, 1fr)` }}
             onMouseLeave={() => setHover(null)}>
          <span />
          {m.cols.map((g) => (
            <span key={g} className={css.matrixColHead} data-shared={m.shared[g] > 1 || undefined}>
              {g}
            </span>
          ))}
          {m.rows.map((lineage, ri) => (
            <div key={lineage} style={{ display: "contents" }}>
              <span className={css.matrixRowHead}>{lineage}</span>
              {m.cells[ri].map((v, ci) => (
                <span key={ci} className={css.matrixCell}
                      data-hot={hover && hover.r === ri && hover.c === ci ? true : undefined}
                      onMouseEnter={() => setHover({ r: ri, c: ci })}>
                  {v > 0 && <span className={css.matrixDot}
                                  style={{ opacity: 0.25 + 0.75 * (v / max) }} />}
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>

      <div className={css.readout} aria-live="polite">
        {hover && m.cells[hover.r][hover.c] > 0
          ? <>
              <strong>{m.cols[hover.c]}</strong> {tt(CRISPR.inLineage)}{" "}
              {m.rows[hover.r]} · d = {m.cells[hover.r][hover.c]} ·{" "}
              {tt(CRISPR.nominatedBy)} {m.shared[m.cols[hover.c]]}
            </>
          : <span className={css.readoutHint}>
              {shared} {tt(CRISPR.matrixHint)} {m.cols.length}
            </span>}
      </div>
    </figure>
  );
}
