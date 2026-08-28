/** One dataset, one module — so a lazily loaded section downloads its own data and nobody
 *  else's. Written by tools/evidence_atlas.py: the catalogue-wide evidence profile, which
 *  is what lets a single disease's panel say how it compares to the field. */
import raw from "../../../data/generated/evidence_atlas.json";
import type { EvidenceAtlas } from "../evidenceAtlasModel";

export const evidenceAtlas = raw as unknown as EvidenceAtlas;
