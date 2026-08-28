/** One dataset, one module — so a lazily loaded section downloads its own data and
 *  nobody else's. */
import raw from "../../../data/generated/nongene_measured.json";
import type { NonGeneMeasured } from "../nongeneMeasuredModel";

export const nongeneMeasured = raw as unknown as NonGeneMeasured;
