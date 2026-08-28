/** One dataset, one module. */
import raw from "../../../data/generated/references.json";
import type { References } from "../referencesModel";

export const references = raw as unknown as References;
