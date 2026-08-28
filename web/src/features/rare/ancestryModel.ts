import { oklchToHex } from "../../lib/palette";

/** The population axis, as a view model. Written by tools/ancestry_geography.py.
 *
 *  WHAT IS AND IS NOT AUTHORED HERE. The analysis authored two tables (populations and
 *  region assignments) and said so in its own payload; this file authors **nothing**. It
 *  types the payload, derives orderings the interface needs, and stops. Any number that
 *  appears on screen came off disk.
 *
 *  ONE MODELLING DECISION WORTH THE PARAGRAPH. A representation ratio is multiplicative:
 *  0.5 and 2.0 are the same distance from parity in opposite directions, and 0.07 against
 *  8.10 is not "eight units apart", it is two orders of magnitude. So the ratio axis is
 *  **log**, and parity sits at log(1) = 0 — which is also what makes it a genuinely
 *  DIVERGING encoding rather than a sequential one wearing two colours. Drawing this on a
 *  linear axis would squash every under-represented region into an indistinguishable stub
 *  against the one bar that is over-represented, i.e. it would make the finding invisible.
 */

/** One country's record count, priced against its population. */
export type PerCapita = {
  country: string;
  records: number;
  populationM: number;
  region: string | null;
  recordsPer100M: number;
};

/** A world region's share of records against its share of people. */
export type RegionRow = {
  region: string;
  records: number;
  recordShare: number;
  populationShare: number;
  /** 1.0 is proportional. Below is under-represented, above is over-represented. */
  representationRatio: number;
};

/** A disorder whose prevalence class is not the same in every country that measured it. */
export type DiscordantRow = {
  orpha: string;
  name: string;
  places: number;
  classes: string[];
  byPlace: Record<string, string[]>;
  /** How many bands of the ordered rarity axis the disorder spans. Null if no class parsed. */
  spanBands: number | null;
  rarestClass: string | null;
  commonestClass: string | null;
};

export type AncestryGeography = {
  generated: string;
  input: string;
  premise: string;
  caveat: string;
  authoredConstants: { populationTable: number; regionTable: number; note: string };
  /** The prevalence bands, rarest first. Supplied by the analysis so the UI never
   *  re-authors an ordering — an ordered variable read as unordered labels is the most
   *  common charting error there is. */
  classOrder: string[];
  shape: {
    records: number;
    withGeographyTag: number;
    worldwide: number;
    supranational: number;
    specificPopulation: number;
    namedCountry: number;
    distinctCountries: number;
    worldwideShare: number;
    namedCountryShare: number;
  };
  perCapita: PerCapita[];
  countriesWithoutPopulation: { country: string; records: number }[];
  disparity: {
    best: PerCapita;
    worst: PerCapita;
    ratio: number;
    says: string;
  } | null;
  regions: RegionRow[];
  concentration: {
    disordersWithAnyPlacedRecord: number;
    disordersPlacedInExactlyOneCountry: number;
    disordersPlacedInMoreThanOneCountry: number;
    disordersWithNoPlacedRecord: number;
    topCountriesForSinglePlaceDisorders: [string, number][];
    confound: string;
  };
  discordance: {
    comparableDisorders: number;
    discordant: number;
    share: number | null;
    rows: DiscordantRow[];
    says: string;
  };
  specificPopulationTag: {
    records: number;
    disorders: number;
    examples: { orpha: string; name: string; class: string | null; type: string | null }[];
    says: string;
  };
};

/** The colour of one prevalence band, built rather than borrowed.
 *
 *  WHY NOT THE `--rare-p0..p4` TOKENS. They were tempting and they are wrong here for a
 *  reason worth writing down: that ramp has five steps of which the LAST means "never
 *  measured — off the scale", not "the commonest band". Using it for six ordered bands
 *  would both run out of steps and paint the most common prevalence in the colour the rest
 *  of this dashboard uses for absent data. A token that already means something cannot be
 *  quietly reused to mean something else.
 *
 *  So the ramp is constructed the way the design system says a sequential scale is
 *  constructed — ONE hue, lightness falling monotonically — for however many bands the
 *  analysis ships, and it stays correct if a seventh band ever appears. Hue 300 is the
 *  page's prevalence hue, kept so this reads as the same variable as everywhere else.
 */
export function bandColor(index: number, bands: number, mode: "light" | "dark"): string {
  const t = bands <= 1 ? 0 : index / (bands - 1);
  // Rarest is darkest in light mode and lightest in dark mode: on a dark ground the
  // high-lightness end is the salient one, so the ramp is re-stepped rather than inverted.
  const L = mode === "dark" ? 0.84 - 0.5 * t : 0.38 + 0.46 * t;
  const C = 0.17 - 0.1 * Math.abs(t - 0.15);
  return oklchToHex([L, Math.max(0.03, C), 300]);
}

/** Region -> slot in the categorical scale. Fixed, so a region is the same colour in the
 *  ratio chart and in the country beeswarm; a colour that changes meaning between two
 *  charts on one screen is worse than no colour. Six regions, six slots — at the limit of
 *  what a categorical scale should carry, which is why nothing else is ever coloured by
 *  region on this page. */
export const REGION_SLOT: Record<string, number> = {
  Europe: 0,
  Asia: 1,
  Africa: 2,
  "Latin America & Caribbean": 3,
  "Northern America": 4,
  Oceania: 5,
};

export const REGION_ORDER = Object.keys(REGION_SLOT);

/** Regions sorted by how far they are from parity, most over-represented first. Sorting by
 *  the ratio rather than by record count is the whole point: a count ranks the regions by
 *  size, which is the fact nobody needed. */
export function byDistanceFromParity(regions: RegionRow[]): RegionRow[] {
  return [...regions].sort((a, b) => b.representationRatio - a.representationRatio);
}

/** Distance from parity in orders of magnitude, signed. Used for the diverging encoding
 *  and for the spoken summary, so the chart and its aria-label cannot disagree. */
export function parityLog(ratio: number): number {
  return ratio > 0 ? Math.log10(ratio) : 0;
}

/** "8.1x over" / "14x under" — the ratio said the way a person says it. A ratio below 1 is
 *  reported as its reciprocal, because "0.07x" makes a reader do arithmetic to learn that
 *  it means fourteen times too few. */
export function parityPhrase(ratio: number): string {
  if (ratio >= 1) return `${ratio.toFixed(ratio < 10 ? 1 : 0)}× over-represented`;
  if (ratio <= 0) return "no records";
  return `${(1 / ratio).toFixed(1 / ratio < 10 ? 1 : 0)}× under-represented`;
}

export type DiscordanceSort = "span" | "places" | "name";

/** Filter and order the discordant disorders.
 *
 *  Search is a plain case-insensitive substring over name and ORPHA code, and it runs over
 *  the FULL 386 rows rather than over a page of them — the reason the build script ships
 *  the whole table and refuses to truncate it.
 */
export function selectDiscordant(
  rows: DiscordantRow[],
  { query, sort, minPlaces }: { query: string; sort: DiscordanceSort; minPlaces: number }
): DiscordantRow[] {
  const q = query.trim().toLowerCase();
  const filtered = rows.filter((r) => {
    if (r.places < minPlaces) return false;
    if (!q) return true;
    return r.name.toLowerCase().includes(q) || r.orpha.includes(q);
  });
  const ordered = [...filtered];
  if (sort === "span") {
    ordered.sort(
      (a, b) => (b.spanBands ?? 0) - (a.spanBands ?? 0) || b.places - a.places
    );
  } else if (sort === "places") {
    ordered.sort((a, b) => b.places - a.places || (b.spanBands ?? 0) - (a.spanBands ?? 0));
  } else {
    ordered.sort((a, b) => a.name.localeCompare(b.name));
  }
  return ordered;
}

/** Which band indices a disorder occupies, on the ordered rarity axis. Classes the
 *  analysis could not place (there are none today, but the payload permits them) are
 *  dropped rather than defaulted to zero — a band that means "unknown" drawn at the rarest
 *  end would read as a measurement. */
export function bandIndices(row: DiscordantRow, classOrder: string[]): number[] {
  return row.classes
    .map((c) => classOrder.indexOf(c))
    .filter((i) => i >= 0)
    .sort((a, b) => a - b);
}

/** Per-country bands for the expanded row, ordered by the rarest band each country reports
 *  so the countries themselves form a gradient rather than an alphabet. */
export function placesByRarity(
  row: DiscordantRow,
  classOrder: string[]
): { place: string; bands: number[] }[] {
  return Object.entries(row.byPlace)
    .map(([place, classes]) => ({
      place,
      bands: classes
        .map((c) => classOrder.indexOf(c))
        .filter((i) => i >= 0)
        .sort((a, b) => a - b),
    }))
    .sort((a, b) => (a.bands[0] ?? 99) - (b.bands[0] ?? 99) || a.place.localeCompare(b.place));
}
