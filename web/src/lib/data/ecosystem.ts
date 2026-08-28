/** One dataset, one module. */
import raw from "../../data/generated/ecosystem.json";
import type { Ecosystem } from "../ecosystemModel";

export const ecosystem = raw as unknown as Ecosystem;
