/** Typed access to the generated data.
 *
 * Adapter-driven: `npm run data` reads whatever manifests exist under out/, so a new
 * adapter appears here without the UI knowing its name. Nothing parses CSV at runtime.
 */
import runsRaw from "../data/generated/runs.json";
import docsRaw from "../data/generated/docs.json";

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

export const runs = runsRaw as unknown as Run[];
export const docs = docsRaw as unknown as Doc[];

/** Rank an entity list by a column, returning an entity -> rank map. */
export function rankBy(entities: Entity[], key: "score" | "z"): Map<string, number> {
  const sorted = [...entities].sort((a, b) => (b[key] as number) - (a[key] as number));
  return new Map(sorted.map((e, i) => [e.entity, i + 1]));
}
