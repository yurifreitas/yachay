import { useEffect, useState } from "react";
import { useT } from "../../../i18n";
import { MEAS } from "../../../i18n/measured";
import { Provenance } from "./Provenance";
import css from "./HyperViews.module.css";

/** THE HYPERDIMENSIONAL VIEWS — four forms a bar chart cannot carry.
 *
 *  Each of these exists because the convention failed, not because the form is interesting:
 *
 *    matrix      14 languages x 23 organ systems. A bar chart of any one row hides the other
 *                thirteen, and the finding is a BLOCK — the holes line up vertically.
 *    slopegraph  pathway retention against cell-type retention per organ system. The finding
 *                is a CROSSING; two sorted bar charts would hide precisely the crossing.
 *    pcp         12,994 diseases on five axes of what is known. Drawn as polylines this is a
 *                black rectangle, so what ships is the DENSITY and the ribbon between axes.
 *    grid        submitters x conditions. The finding is a slope across two axes, and a
 *                table asks the reader to hold twenty-five numbers at once to see it.
 *
 *  EVERY LAYOUT WAS SOLVED IN PYTHON. `tools/view_models.py` computes the orderings, the bins
 *  and the ribbon counts; this file draws them. That boundary is deliberate: a seriation is an
 *  argument, and an ordering computed inside a component is an argument nobody can audit or
 *  version. It also means the browser never holds the 12,994 rows it could not draw.
 *
 *  FETCHED, NOT BUNDLED, and prefetched on intent — 46 kB that only this group needs should
 *  not be parsed before first paint for a reader who never opens it.
 */

type Models = {
  language_matrix?: {
    rows: { id: string; label: string; total: number }[];
    cols: { id: string; mean: number }[];
    cells: number[][];
    ordering: string;
  };
  scale_slopegraph?: {
    pairs: { id: string; label: string; n: number; pathway: number; cell_type: number; delta: number; crosses: boolean }[];
    crossing: number;
    reading: string;
  };
  knowledge_pcp?: {
    axes: string[]; bins: number; density: number[][];
    links: { axis: number; from: number; to: number; n: number }[];
    diseases: number; reading: string;
  };
  knowledge_void?: {
    bins: number; axes: string[];
    faces: { x: string; y: string; grid: { n: number; anti: number }[][] }[];
    occupied: { cells: number; share: number; null_mean: number; z_vs_null: number };
    shape: { frontier_cells: number; interior_cells: number; frontier_share: number };
    antiforms: { count: number; diseases_expected_in_them: number; threshold_expected: number };
    top_antiforms: { expected: number; reads_as: Record<string, string> }[];
    reading: string;
    generated?: string; provenance?: string; says?: string; limits?: string[];
    governed_by?: string; neighbour_rule?: string;
  };
  conflict_grid?: {
    rows: string[]; cols: string[]; cells: (number | null)[][];
    marginal: (number | null)[]; reading: string;
  };
};

const URL = `${import.meta.env.BASE_URL}data/view_models.json`;

let cache: Models | null = null;
let inflight: Promise<Models> | null = null;

/** Load once per session, and let anything call `prefetchViewModels()` before the reader
 *  arrives. Two callers racing share one request rather than making two. */
export function prefetchViewModels(): Promise<Models> {
  if (cache) return Promise.resolve(cache);
  if (!inflight) {
    inflight = fetch(URL)
      .then((r) => r.json())
      .then((j) => { cache = j.models ?? {}; return cache!; })
      .catch(() => ({} as Models));
  }
  return inflight;
}

function useModels() {
  const [models, setModels] = useState<Models | null>(cache);
  useEffect(() => {
    let alive = true;
    prefetchViewModels().then((m) => { if (alive) setModels(m); });
    return () => { alive = false; };
  }, []);
  return models;
}

/** A skeleton with the shape of the content, so nothing jumps when it lands. */
function Loading({ height }: { height: number }) {
  return <div className={css.skeleton} style={{ height }} aria-hidden />;
}

/* ------------------------------------------------------------------ the matrix */

export function LanguageMatrix() {
  const tt = useT();
  const models = useModels();
  const m = models?.language_matrix;
  const [hover, setHover] = useState<{ r: number; c: number } | null>(null);

  if (!models) return <Loading height={420} />;
  if (!m) return null;

  const short = (id: string) => id.replace("HP:", "");

  return (
    <figure className={css.figure}>
      <figcaption className={css.caption}>
        <strong>{tt(MEAS.matrixTitle)}</strong> {tt(MEAS.matrixRead)}
      </figcaption>

      <div className={css.matrixScroll}>
        <div
          className={css.matrix}
          style={{ gridTemplateColumns: `132px repeat(${m.cols.length}, 1fr)` }}
          onMouseLeave={() => setHover(null)}
        >
          <span />
          {m.cols.map((c) => (
            <span key={c.id} className={css.matrixColHead} title={c.id}>{short(c.id)}</span>
          ))}

          {m.rows.map((row, ri) => (
            <div key={row.id} className={css.matrixRowGroup} style={{ display: "contents" }}>
              <span className={css.matrixRowHead}>
                {row.label}
                <em>{(100 * row.total).toFixed(0)}%</em>
              </span>
              {m.cells[ri].map((v, ci) => (
                <button
                  key={ci}
                  type="button"
                  className={css.cell}
                  style={{ opacity: 0.12 + 0.88 * v }}
                  data-hot={hover && hover.r === ri && hover.c === ci ? true : undefined}
                  onMouseEnter={() => setHover({ r: ri, c: ci })}
                  onFocus={() => setHover({ r: ri, c: ci })}
                  aria-label={`${row.label}, ${m.cols[ci].id}: ${(100 * v).toFixed(0)} percent`}
                />
              ))}
            </div>
          ))}
        </div>
      </div>

      <div className={css.readout} aria-live="polite">
        {hover
          ? <>
              <strong>{m.rows[hover.r].label}</strong> · {m.cols[hover.c].id} ·{" "}
              <span className={css.readoutVal}>
                {(100 * m.cells[hover.r][hover.c]).toFixed(0)} %
              </span>
            </>
          : <span className={css.readoutHint}>{m.ordering}</span>}
      </div>
    </figure>
  );
}

/* ------------------------------------------------------------------ the slopegraph */

export function ScaleSlopegraph() {
  const tt = useT();
  const models = useModels();
  const m = models?.scale_slopegraph;
  const [hover, setHover] = useState<string | null>(null);

  if (!models) return <Loading height={460} />;
  if (!m) return null;

  const H = 420, W = 560, PAD = 28;
  const max = Math.max(...m.pairs.flatMap((p) => [p.pathway, p.cell_type])) * 1.08;
  const y = (v: number) => H - PAD - (v / max) * (H - 2 * PAD);

  return (
    <figure className={css.figure}>
      <figcaption className={css.caption}>
        <strong>{tt(MEAS.slopeTitle)}</strong> {m.reading}
      </figcaption>

      <svg viewBox={`0 0 ${W} ${H}`} className={css.svg} role="img"
           aria-label={`${m.pairs.length} organ systems, pathway retention against cell-type retention`}>
        <line x1={140} y1={PAD} x2={140} y2={H - PAD} className={css.axis} />
        <line x1={W - 140} y1={PAD} x2={W - 140} y2={H - PAD} className={css.axis} />
        <text x={140} y={16} className={css.axisLabel} textAnchor="middle">pathway</text>
        <text x={W - 140} y={16} className={css.axisLabel} textAnchor="middle">cell type</text>

        {m.pairs.map((p) => {
          const on = hover === p.id;
          return (
            <g key={p.id}
               className={`${css.slope} ${p.crosses ? css.slopeUp : ""}`}
               data-on={on || undefined}
               onMouseEnter={() => setHover(p.id)}
               onMouseLeave={() => setHover(null)}>
              <line x1={140} y1={y(p.pathway)} x2={W - 140} y2={y(p.cell_type)} />
              <circle cx={140} cy={y(p.pathway)} r={3} />
              <circle cx={W - 140} cy={y(p.cell_type)} r={3} />
              {on && (
                <text x={W - 132} y={y(p.cell_type) + 4} className={css.slopeLabel}>
                  {p.label}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      <div className={css.readout} aria-live="polite">
        {hover
          ? (() => {
              const p = m.pairs.find((x) => x.id === hover)!;
              return <><strong>{p.label}</strong> · {p.n} diseases · pathway {p.pathway.toFixed(2)} → cell {p.cell_type.toFixed(2)}</>;
            })()
          : <span className={css.readoutHint}>{tt(MEAS.slopeHint)} — {m.crossing} of {m.pairs.length}</span>}
      </div>
    </figure>
  );
}

/* ------------------------------------------------------------------ parallel coordinates */

export function KnowledgePCP() {
  const tt = useT();
  const models = useModels();
  const m = models?.knowledge_pcp;
  if (!models) return <Loading height={420} />;
  if (!m || !m.density) return null;

  const H = 360, W = 700, PAD = 40;
  const cols = m.axes.length;
  const x = (i: number) => PAD + (i * (W - 2 * PAD)) / (cols - 1);
  const yb = (b: number) => PAD + ((m.bins - 1 - b) * (H - 2 * PAD)) / (m.bins - 1);
  const maxLink = Math.max(...m.links.map((l) => l.n));
  const maxDen = Math.max(...m.density.flat());

  return (
    <figure className={css.figure}>
      <figcaption className={css.caption}>
        <strong>{tt(MEAS.pcpTitle)}</strong> {m.reading}
      </figcaption>

      <svg viewBox={`0 0 ${W} ${H}`} className={css.svg} role="img"
           aria-label={`${m.diseases} diseases on ${cols} axes of what is known`}>
        {m.links.map((l, i) => (
          <line
            key={i}
            x1={x(l.axis)} y1={yb(l.from)} x2={x(l.axis + 1)} y2={yb(l.to)}
            className={css.ribbon}
            strokeOpacity={0.05 + 0.5 * (l.n / maxLink)}
            strokeWidth={0.6 + 2.4 * (l.n / maxLink)}
          />
        ))}
        {m.axes.map((a, i) => (
          <g key={a}>
            <line x1={x(i)} y1={PAD} x2={x(i)} y2={H - PAD} className={css.axis} />
            {m.density[i].map((n, b) => (
              n > 0 ? (
                <rect key={b} x={x(i) - 4} y={yb(b) - 3}
                      width={8} height={6} rx={1}
                      className={css.densityMark}
                      opacity={0.15 + 0.85 * (n / maxDen)} />
              ) : null
            ))}
            <text x={x(i)} y={H - 12} className={css.axisLabel} textAnchor="middle">
              {a.replace(/_/g, " ")}
            </text>
          </g>
        ))}
      </svg>

      <div className={css.readout}>
        <span className={css.readoutHint}>
          {m.diseases.toLocaleString()} {tt(MEAS.pcpHint)}
        </span>
      </div>
    </figure>
  );
}

/* ------------------------------------------------------------------ the conflict grid */

export function ConflictGrid() {
  const tt = useT();
  const models = useModels();
  const m = models?.conflict_grid;
  if (!models) return <Loading height={260} />;
  if (!m) return null;

  const max = Math.max(...m.cells.flat().filter((v): v is number => v != null));

  return (
    <figure className={css.figure}>
      <figcaption className={css.caption}>
        <strong>{tt(MEAS.gridTitle)}</strong> {m.reading}
      </figcaption>
      <div className={css.gridWrap}>
        <div className={css.grid} style={{ gridTemplateColumns: `96px repeat(${m.cols.length}, 1fr)` }}>
          <span />
          {m.cols.map((c) => <span key={c} className={css.gridHead}>{c}</span>)}
          {m.rows.map((r, ri) => (
            <div key={r} style={{ display: "contents" }}>
              <span className={css.gridRowHead}>{r}</span>
              {m.cells[ri].map((v, ci) => (
                <span key={ci} className={css.gridCell}
                      style={{ opacity: v == null ? 0.08 : 0.14 + 0.86 * (v / max) }}>
                  {v == null ? "" : `${(100 * v).toFixed(0)}`}
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>
    </figure>
  );
}

/* ------------------------------------------------------------------ the void */

/** THE ANTI-FORM VIEW — what is not there, drawn as an object.
 *
 *  Every atlas in this field renders what exists and lets the rest disappear as background.
 *  This inverts it. Five axes of what is known, cut into four bands each, is a lattice of
 *  1,024 cells; only 318 of them hold a disease. The other 706 are not background — they are
 *  ways of knowing a disease that do not occur.
 *
 *  Two marks, and the second is the point:
 *
 *    a filled square   diseases sit here; opacity is how many
 *    an outlined ring  an ANTI-FORM lies in the fibre over this face cell — an empty region
 *                      of the lattice where the catalogue's own marginals predict diseases
 *                      and none are found
 *
 *  Ten pairwise faces, because five dimensions cannot be drawn and a projection that hides
 *  which pair you are looking at is worse than ten that say so. The reader is meant to notice
 *  that the rings cluster in the corners: the absent combinations are the ones that mix a
 *  well-studied axis with an unstudied one, and the catalogue has almost none of those.
 */
export function KnowledgeVoid() {
  const tt = useT();
  const models = useModels();
  const m = models?.knowledge_void;
  if (!models) return <Loading height={520} />;
  if (!m) return null;

  const maxN = Math.max(...m.faces.flatMap((f) => f.grid.flatMap((r) => r.map((c) => c.n))));
  const short = (a: string) => a.replace(/_/g, " ").slice(0, 10);

  return (
    <figure className={css.figure}>
      <figcaption className={css.caption}>
        <strong>{tt(MEAS.voidTitle)}</strong> {tt(MEAS.voidRead)}
      </figcaption>

      <div className={css.voidStats}>
        <div><em>{m.occupied.cells}</em><span>of {m.faces.length > 0 ? Math.pow(m.bins, m.axes.length) : 0} cells occupied</span></div>
        <div><em>{m.occupied.z_vs_null}</em><span>z against independence — the void is structural</span></div>
        <div><em>{(100 * m.shape.frontier_share).toFixed(0)} %</em><span>of occupied cells are frontier: a filament, not a blob</span></div>
        <div><em>{m.antiforms.count}</em><span>anti-forms, holding {Math.round(m.antiforms.diseases_expected_in_them)} expected diseases and none real</span></div>
      </div>

      <div className={css.faces}>
        {m.faces.map((f) => (
          <div key={`${f.x}-${f.y}`} className={css.face}>
            <span className={css.faceLabel}>{short(f.x)} × {short(f.y)}</span>
            <div className={css.faceGrid} style={{ gridTemplateColumns: `repeat(${m.bins}, 1fr)` }}>
              {f.grid.flatMap((row, ri) =>
                row.map((cell, ci) => (
                  <span
                    key={`${ri}-${ci}`}
                    className={css.faceCell}
                    title={`${cell.n} diseases · ${cell.anti} anti-forms`}
                  >
                    <span className={css.faceFill} style={{ opacity: 0.08 + 0.92 * (cell.n / maxN) }} />
                    {cell.anti > 0 && (
                      <span className={css.faceAnti} style={{ opacity: 0.35 + 0.65 * Math.min(1, cell.anti / 20) }} />
                    )}
                  </span>
                ))
              )}
            </div>
          </div>
        ))}
      </div>

      <div className={css.legend}>
        <span><span className={`${css.key} ${css.keyFill}`} /> {tt(MEAS.voidFilled)}</span>
        <span><span className={`${css.key} ${css.keyAnti}`} /> {tt(MEAS.voidAnti)}</span>
      </div>

      <div className={css.antiList}>
        <span className={css.antiK}>{tt(MEAS.voidTop)}</span>
        {m.top_antiforms.map((a, i) => (
          <div key={i} className={css.antiRow}>
            <span className={css.antiVal}>{a.expected.toFixed(0)}</span>
            <span className={css.antiText}>
              {Object.entries(a.reads_as).map(([k, v]) => `${k.replace(/_/g, " ")} ${v}`).join(" · ")}
            </span>
          </div>
        ))}
      </div>

      <Provenance
        generated={m.generated}
        provenance={m.provenance}
        method={{ "neighbour rule": m.neighbour_rule ?? "",
                  "anti-form threshold": `independence expects >= ${m.antiforms.threshold_expected} diseases` }}
        says={m.says}
        limits={m.limits}
        governedBy={m.governed_by}
      />
    </figure>
  );
}
