/** One dataset, one module — so a lazily loaded section downloads its own data and
 *  nobody else's. A single barrel importing every JSON put all of them in whichever
 *  chunk touched it first, which silently undid the code split. */
import raw from "../../../data/generated/lupus.json";
import type { Lupus } from "./../lupusModel";

export const lupus = raw as unknown as Lupus;
