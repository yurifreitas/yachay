/** The visualisation layer.
 *
 *  Three levels, and the split is the same one the rest of the app uses: atoms know geometry
 *  and nothing else, organisms know a FORM, and neither knows what a gene is. A feature
 *  supplies arrays, scales and sentences; it never draws an axis.
 *
 *  The arithmetic these are built on lives in `lib/viz/` as pure functions, checked by
 *  `scripts/check-viz.mjs` in the build.
 */
export { PlotFrame, PlotClip } from "./atoms/PlotFrame";
export type { PlotBox } from "./atoms/PlotFrame";
export { AxisX, AxisY, RuleX, RuleY } from "./atoms/Axis";
export { ReadAloud } from "./atoms/ReadAloud";
export { HexbinPlot } from "./organisms/HexbinPlot";
export { RaincloudPlot } from "./organisms/RaincloudPlot";
export type { RaincloudGroup } from "./organisms/RaincloudPlot";
export { UpSetPlot } from "./organisms/UpSetPlot";
