export type CrosswalkEntry = { ontology: string; id: string | null; role: string };

export type CrosswalkRowProps = {
  entries: CrosswalkEntry[];
};
