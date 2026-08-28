/** Types for the reference map. Written by tools/references_seed.py.
 *
 *  `provenance` is the load-bearing field: "author-supplied" marks a claim about a person, a
 *  post, a programme or a sum of money that this repository has not verified, and it is on
 *  every row rather than in a footnote.
 */
export type Provenance = "public-artifact" | "author-supplied";

export type Reference = {
  id: string; name: string; kind: string;
  community: string; rung: string;
  where: string; why: string;
  provenance: Provenance; country: string;
};

export type Community = { id: string; name: string; inAuthorFormula: boolean; note: string };

export type Bridge = {
  rung: string; communities: string[]; communityCount: number;
  references: number; bridged: boolean;
};

export type Pair = { a: string; b: string; rungs: string[]; count: number };
export type NeverMeet = { a: string; b: string; refsA: number; refsB: number };
export type Confined = { community: string; rung: string; references: number; sharesWith: string[] };

export type References = {
  generated: string;
  premise: string;
  provenanceNote: string;
  communities: Community[];
  references: Reference[];
  bridges: Bridge[];
  communityPairs: Pair[];
  neverMeet: NeverMeet[];
  confined: Confined[];
  authorFormula: string;
  finding: string;
  theGap: string;
  summary: {
    references: number;
    byCommunity: Record<string, number>;
    byKind: Record<string, number>;
    byProvenance: Record<string, number>;
    byRung: Record<string, number>;
    countries: number;
    topCountries: Record<string, number>;
    bridgedRungs: number;
    singleCommunityRungs: number;
    communityPairs: number;
    neverMeet: number;
    confinedCommunities: string[];
    authorSupplied: number;
  };
};
