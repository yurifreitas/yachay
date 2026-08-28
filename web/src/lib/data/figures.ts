/** One dataset, one module. A barrel that imported all four put the run corpus and the
 *  point cloud into every chunk that touched any of them. */
import raw from "../../data/generated/figures.json";
import type { FigureSet } from "../dataTypes";

export const figures = raw as unknown as Record<string, FigureSet>;
