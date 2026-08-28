/** One dataset, one module — so a lazily loaded section downloads its own data and
 *  nobody else's. A single barrel importing every JSON put all of them in whichever
 *  chunk touched it first, which silently undid the code split. */
import raw from "../../../data/generated/dimensions.json";
import type { Dimensions } from "./../dimensionsModel";

export const dimensions = raw as unknown as Dimensions;
