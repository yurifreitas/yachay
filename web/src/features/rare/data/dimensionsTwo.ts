/** One dataset, one module — so a lazily loaded section downloads its own data and
 *  nobody else's. A single barrel importing every JSON put all of them in whichever
 *  chunk touched it first, which silently undid the code split. */
import raw from "../../../data/generated/dimensions_two.json";
import type { DimensionsTwo } from "./../dimensionsModel";

export const dimensionsTwo = raw as unknown as DimensionsTwo;
