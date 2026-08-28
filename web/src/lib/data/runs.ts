/** One dataset, one module. A barrel that imported all four put the run corpus and the
 *  point cloud into every chunk that touched any of them. */
import raw from "../../data/generated/runs.json";
import type { Run } from "../dataTypes";

export const runs = raw as unknown as Run[];
