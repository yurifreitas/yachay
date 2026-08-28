/** One dataset, one module — so a lazily loaded section downloads its own data. */
import raw from "../../../data/generated/thesis.json";
import type { Thesis } from "../thesisModel";

export const thesis = raw as unknown as Thesis;
