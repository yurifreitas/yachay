/** One dataset, one module — so a lazily loaded section downloads its own data. */
import raw from "../../../data/generated/prevalence_audit.json";
import type { PrevalenceAudit } from "../prevalenceAuditModel";

export const prevalenceAudit = raw as unknown as PrevalenceAudit;
