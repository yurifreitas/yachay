/** One dataset, one module. */
import raw from "../../data/generated/multiplicity.json";
import type { Multiplicity } from "../multiplicityModel";

export const multiplicity = raw as unknown as Multiplicity;
