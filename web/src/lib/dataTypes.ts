/** The shapes of the generated data. Types only — no JSON is imported here, so importing
 *  this module costs nothing at runtime.
 *
 *  Original note follows.
 *
 *  Typed access to the generated data.
 *
 * Adapter-driven: `npm run data` reads whatever manifests exist under out/, so a new
 * adapter appears here without the UI knowing its name. Nothing parses CSV at runtime.
 */

export interface NullPoint {
  n: number;
  null_mean: number;
  null_sd: number;
  p95?: number;
  p99?: number;
}

/** One candidate entity. Adapters may add columns; the first four are the contract. */
export interface Entity {
  entity: string;
  score: number;
  n: number;
  z: number;
  [extra: string]: string | number | boolean | null;
}

export interface Run {
  id: string;
  title: string;
  subtitle: string;
  statistic: string;
  reduce: string;
  headline: Record<string, number | string>;
  entities: Entity[];
  entitiesTotal: number;
  null: NullPoint[];
}

export interface Doc {
  id: string;
  group: "method" | "adr" | "case" | "findings";
  file: string;
  title: string;
  words: number;
  body: string;
}


/** The columnar point cloud for a run, or undefined if that adapter emitted none.
 *
 *  Kept out of `Run` on purpose: it is base64 and typed arrays, not rows, and nothing
 *  that renders a table should reach for it by accident.
 */
export interface RawPoints {
  n: string; score: string; z: string; cls: string; names: string;
  total: number; shown: number; sampleRate: number;
}

/** Reduced figure series, keyed by run id then by figure id.
 *
 *  These are computed by `tools/figure_data.py`, never here. A chart that derives its own
 *  statistic is a second implementation of the analysis, and the two will disagree.
 */
export interface CountDistribution {
  total: number; distinct: number; modal_n: number; modal_share: number;
  bars: { n: number; genes: number; share: number }[];
}
export interface ControlQQ {
  theoretical: number[];
  series: { id: string; label: string; sample: number[] }[];
}
export interface ControlDensity {
  panels: { id: string; label: string; mean: number; sd: number }[];
}
export interface RankShiftFig {
  total: number;
  classes: { id: string; note: string; n: number; raw: number; cal: number }[];
}
export interface Ridge {
  n: number; lo: number; hi: number; mean: number; p99: number;
  density: { x: number; density: number }[];
}
export interface NullRidgelineFig {
  title: string; question: string;
  series: Record<string, Ridge[]>;
}
export interface FunnelFig {
  limits: { n: number; mean: number; p95: number; p99: number }[];
  points: { n: number; score: number; z: number; entity: string; cls: string }[];
}
export interface FigureSet {
  null_ridgeline?: NullRidgelineFig;
  funnel?: FunnelFig;
  count_distribution?: CountDistribution;
  control_qq?: ControlQQ;
  control_calibration?: ControlDensity;
  rank_shift?: RankShiftFig;
}

/** Rank an entity list by a column, returning an entity -> rank map. */
export function rankBy(entities: Entity[], key: "score" | "z"): Map<string, number> {
  const sorted = [...entities].sort((a, b) => (b[key] as number) - (a[key] as number));
  return new Map(sorted.map((e, i) => [e.entity, i + 1]));
}
