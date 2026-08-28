/** One dataset, one module. */
import raw from "../../../data/generated/interactome_sparse.json";
import type { InteractomeSparse } from "../interactomeModel";

export const interactomeSparse = raw as unknown as InteractomeSparse;
