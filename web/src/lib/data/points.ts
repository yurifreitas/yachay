/** One dataset, one module. A barrel that imported all four put the run corpus and the
 *  point cloud into every chunk that touched any of them. */
import raw from "../../data/generated/points.json";
import type { RawPoints } from "../dataTypes";

const points = raw as unknown as Record<string, RawPoints>;

/** Point clouds are per-run, so the lookup is by id and the caller gets undefined for a
 *  run that has none rather than an empty object pretending to be data. */
export const pointsFor = (id: string): RawPoints | undefined => points[id];
