/** Types for the tooling survey. Written by tools/ecosystem.py.
 *
 *  `status` is derived at generation time by importing the module and grepping the repository,
 *  so it is a measurement rather than an intention.
 */
export type LibRow = {
  module: string; name: string; rung: string;
  would: string; note: string;
  installed: boolean; version: string | null;
  inUse: boolean;
  status: "in use" | "installed, unused" | "not installed";
};

export type ResourceRow = {
  id: string; name: string; rung: string;
  gives: string; licence: string; ingested: boolean; note: string;
};

export type Ecosystem = {
  generated: string;
  premise: string;
  confession: string;
  libraries: LibRow[];
  resources: ResourceRow[];
  summary: {
    libraries: number;
    byStatus: Record<string, number>;
    installedUnused: string[];
    resources: number; resourcesIngested: number; resourcesNamed: number;
  };
};
