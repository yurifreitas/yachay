/** One dataset, one module. A barrel that imported all four put the run corpus and the
 *  point cloud into every chunk that touched any of them. */
import raw from "../../data/generated/docs.json";
import type { Doc } from "../dataTypes";

export const docs = raw as unknown as Doc[];
