/** One dataset, one module — so a lazily loaded section downloads its own data and
 *  nobody else's. A single barrel importing every JSON put all of them in whichever
 *  chunk touched it first, which silently undid the code split. */
import raw from "../../../data/generated/barriers.json";
import type { Barriers } from "./../barriersModel";

export const barriers = raw as unknown as Barriers;
