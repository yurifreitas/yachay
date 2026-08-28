/** Kept as a barrel for scripts and tests. Application code imports the per-dataset
 *  modules in ./data instead — see the note in ./data/runs.ts for why.
 */
export * from "./dataTypes";
export { runs } from "./data/runs";
export { docs } from "./data/docs";
export { figures } from "./data/figures";
export { pointsFor } from "./data/points";
