/** One dataset, one module — the code-split rule the rest of this feature follows. */
import rawConsistency from "../../../data/generated/consistency.json";
import rawLexiconCheck from "../../../data/generated/lexicon_check.json";
import type { Consistency, LexiconCheck } from "../selfAuditModel";

export const consistency = rawConsistency as unknown as Consistency;
export const lexiconCheck = rawLexiconCheck as unknown as LexiconCheck;
