/** Barrel over the per-dataset modules in `./data`.
 *
 *  IMPORT FROM THE MODULE, NOT FROM HERE, inside anything lazily loaded. This file
 *  references every dataset, so importing it pulls all of them into that chunk — which
 *  is exactly the bug the split fixed. It remains for scripts and tests that genuinely
 *  want the whole set.
 */
export { lexicon } from "./data/lexicon";
export { lupus } from "./data/lupus";
export { lupusGraph } from "./data/lupusGraph";
export { atlas } from "./data/atlas";
export { bias } from "./data/bias";
export { nomenclature } from "./data/nomenclature";
export { dimensions } from "./data/dimensions";
export { dimensionsTwo } from "./data/dimensionsTwo";
export { dossiers } from "./data/dossiers";
export { barriers } from "./data/barriers";
export { capability } from "./data/capability";
export { capabilityMath } from "./data/capabilityMath";
export { nongene } from "./data/nongene";
export { nongeneMeasured } from "./data/nongeneMeasured";
export { prevalenceAudit } from "./data/prevalenceAudit";
export { thesis } from "./data/thesis";
