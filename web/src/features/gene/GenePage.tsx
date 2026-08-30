import { useEffect, useMemo, useState } from "react";

// The multiscale ladder. Lazy and fetched: 78 kB read by one section, and the connectors
// between rungs are the argument, so it is worth its own view rather than a panel.

import { useRemoteData } from "../../lib/useRemoteData";
import { LADDER } from "../../i18n/ladder";
import { useHashParam } from "../../lib/useHashParam";
import { useSectionNav, type NavGroupDef, type NavSectionDef } from "../../lib/nav";
import { SectionHeading } from "../../components/molecules/SectionHeading";
import { useT, fill } from "../../i18n";
import { GENE } from "../../i18n/gene";
import { fmtInt } from "../../lib/scale";
import { layersFor, searchGenes, type GeneSearchIndex, type GeneRecord,
         type GeneShard } from "./geneModel";
import { shardOf } from "./shard";
import { Empty } from "./genePanels";
import { renderSection } from "../../lib/sectionRegistry";
import { GENE_SECTIONS } from "./geneSections";
import { WORLD } from "../../i18n/world";







import { ATT } from "../../i18n/attention";
import { INS } from "../../i18n/insights";
import { DS } from "../../i18n/datasheet";
import { REL } from "../../i18n/related";
import { GEO } from "../../i18n/geometry";
import css from "./GenePage.module.css";

/** ONE GENE, EVERY LAYER — the view this site was missing.
 *
 *  Everything here already existed and was scattered across four pages. A DepMap dependency
 *  on the run dashboard, the cancer subgroups that need it on a second page, the diseases it
 *  causes on a third, its position in the interaction graph on a fourth. A reader arrives
 *  holding a gene symbol — that is how a clinician, a curator, or a family arrives — and the
 *  interface offered them four dashboards and no way in.
 *
 *  So the index is inverted. `tools/gene_index.py` joins every artefact on disk by symbol,
 *  and this page reads the join.
 *
 *  THE ABSENCES ARE RENDERED. A gene screened in 1,178 cell lines and selected in none of the
 *  92 cancer subgroups gets a panel saying exactly that, with the denominator. Hiding the
 *  panel would make "tested and not found" indistinguishable from "never asked", and the
 *  difference between those two is the entire subject of this repository.
 */

const GROUPS: NavGroupDef[] = [
  /* WHAT IT IS COMES FIRST. A reader who does not yet know what the protein does cannot
     weigh a dependency score, and the screen results are meaningless without it. The order
     is: what it is, what breaking it costs, what our screen found, what it is linked to. */
  /* FIRST. Everything after it is one aspect argued at length; this is the whole component
     on one page, with every number's conditions beside it. A reader who wants the summary
     should not have to assemble it from nine sections. */
  { id: "sheet", label: DS.group, question: DS.question },
  /* SECOND, and deliberately before the layer-by-layer groups. The datasheet is the whole
     component on one page; this is what two of its rows mean when read together, which is
     the question a reader has after the table and before the detail. */
  { id: "observed", label: INS.group, question: INS.question },
  { id: "attention", label: ATT.group, question: ATT.question },
  { id: "world", label: WORLD.gWorld, question: WORLD.qWorld },
  { id: "shape", label: GEO.gShape, question: GEO.qShape },
  { id: "ladder", label: LADDER.rProtein, question: LADDER.lede1 },
  { id: "screen", label: GENE.gScreen, question: GENE.qScreen },
  { id: "context", label: GENE.gContext, question: GENE.qContext },
  { id: "clinic", label: GENE.gClinic, question: GENE.qClinic },
  /* LAST, AND IT IS A DESTINATION. Everything above describes this gene; this is the only
     group that takes the reader somewhere else, so it sits where a reader arrives after
     reading rather than before. */
  { id: "next", label: REL.section, question: REL.question },
];

const SECTIONS: NavSectionDef[] = [
  { id: "datasheet", label: DS.section, group: "sheet" },
  { id: "insights", label: INS.section, group: "observed" },
  { id: "attention", label: ATT.section, group: "attention" },
  { id: "form", label: WORLD.sForm, group: "world" },
  { id: "constraint", label: WORLD.sConstraint, group: "world" },
  { id: "expression", label: WORLD.sExpression, group: "world" },
  { id: "variants", label: WORLD.sVariants, group: "world" },
  { id: "ladder", label: LADDER.rResidue, group: "ladder" },
  { id: "needle", label: GEO.sNeedle, group: "shape" },
  { id: "routes", label: GEO.sRoutes, group: "shape" },
  { id: "pathways", label: GEO.sPathways, group: "shape" },
  { id: "dependency", label: GENE.sDependency, group: "screen" },
  { id: "cancer", label: GENE.sCancer, group: "screen" },
  { id: "genotype", label: GENE.sGenotype, group: "screen" },
  { id: "network", label: GENE.sNetwork, group: "context" },
  { id: "disease", label: GENE.sDisease, group: "clinic" },
  { id: "related", label: REL.group, group: "next" },
];

export default function GenePage() {
  const t = useT();
  const { section } = useSectionNav({
    owner: "gene", groups: GROUPS, sections: SECTIONS, initial: "datasheet",
  });
  const [symbol, setSymbol] = useHashParam("g", "");
  const [query, setQuery] = useState("");

  /* TWO FETCHES, NOT ONE FILE. The search index is 185 kB and loads up front; the records
     live in 128 shards and only the one holding the chosen symbol is ever fetched. The
     alternative was a 20 MB download before a reader could type a single letter. */
  const idx = useRemoteData<GeneSearchIndex>("data/gene/idx.json");
  const [shard, setShard] = useState<{ id: string; data: GeneShard } | null>(null);
  const [shardError, setShardError] = useState(false);

  const wanted = symbol ? shardOf(symbol) : null;
  useEffect(() => {
    if (!wanted || shard?.id === wanted) return;
    let live = true;
    setShardError(false);
    fetch(`data/gene/${wanted}.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((data: GeneShard) => { if (live) setShard({ id: wanted, data }); })
      .catch(() => { if (live) setShardError(true); });
    // `live` guards the case a reader types faster than the network answers: an older
    // shard resolving after a newer one would overwrite the gene actually on screen.
    return () => { live = false; };
  }, [wanted, shard?.id]);

  const symbols = useMemo(
    () => (idx.state === "ready" ? Object.keys(idx.data.genes) : []),
    [idx],
  );
  const matches = useMemo(() => searchGenes(symbols, query), [symbols, query]);

  if (idx.state === "loading") return <Skeleton />;
  if (idx.state === "error") {
    return (
      <section className={css.page}>
        <p className={css.absent}>
          {t(GENE.loadFailed)} (<code>{idx.message}</code>)
          <br />
          <code>python tools/gene_index.py</code>
        </p>
      </section>
    );
  }

  const data = idx.data;
  const rec: GeneRecord | undefined =
    symbol && shard?.id === wanted ? shard.data[symbol] : undefined;
  const loadingGene = !!symbol && !shardError && shard?.id !== wanted;
  const layers = layersFor(rec, data.scope);

  return (
    <section className={css.page}>
      <header className={css.hero}>
        <div>
          <p className={css.eyebrow}>{t(GENE.eyebrow)}</p>
          <h2 className={css.title}>{t(GENE.title)}</h2>
          <p className={css.lede}>{t(GENE.lede)}</p>
        </div>

        <div className={css.search}>
          <label className={css.searchLabel} htmlFor="gene-search">{t(GENE.searchLabel)}</label>
          <input
            id="gene-search"
            type="search"
            className={css.input}
            placeholder={t(GENE.searchPlaceholder)}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoComplete="off"
            spellCheck={false}
          />
          <p className={css.searchNote}>
            {fmtInt(data.scope.genes)} {t(GENE.indexed)}
          </p>

          {matches.length > 0 && (
            <ul className={css.results}>
              {matches.map((s) => {
                const has = data.genes[s] ?? 0;
                return (
                  <li key={s}>
                    <button
                      type="button"
                      className={s === symbol ? css.resultOn : css.result}
                      onClick={() => { setSymbol(s); setQuery(""); }}
                    >
                      <span className={css.sym}>{s}</span>
                      {/* How many layers speak about this gene, before it is opened. A
                          result list that does not say this makes every row look equal. */}
                      <span className={css.layers} aria-label={`${has} of 7 layers`}>
                        {[0, 1, 2, 3, 4, 5, 6].map((i) => (
                          <i key={i} className={i < has ? css.pipOn : css.pip} />
                        ))}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </header>

      {!symbol ? (
        <Empty scope={data.scope} onPick={setSymbol} />
      ) : (
        <>
          <div className={css.chosen}>
            <h3 className={css.symbol}>{symbol}</h3>
            <ul className={css.layerBar}>
              {layers.map((l) => (
                <li key={l.id} className={l.present ? css.layerOn : css.layerOff}>
                  <span className={css.layerName}>
                    {l.id === "world" ? t(WORLD.layerWorld)
                      : l.id === "geo" ? t(GEO.layerGeo)
                      : t(GENE.layer[l.id as never])}
                  </span>
                  <span className={css.layerDetail}>
                    {fill(t(l.id === "world"
                              ? (l.present ? WORLD.layerWorldHas : WORLD.layerWorldNone)
                              : l.id === "geo"
                              ? (l.present ? GEO.layerGeoHas : GEO.layerGeoNone)
                              : (l.present ? GENE.layerHas[l.id] : GENE.layerNone[l.id])),
                          Object.fromEntries(Object.entries(l.vars)
                            .map(([k, v]) => [k, fmtInt(v)])))}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <SectionHeading />

          {loadingGene ? (
            <div className={css.skeleton} role="status" aria-live="polite" />
          ) : shardError ? (
            <p className={css.absentPanel}>{t(GENE.loadFailed)}</p>
          ) : (
            <>
              {/* ONE CALL. Seventeen branches, declared in geneSections.tsx — and every one of them
                  given a sentence there, because the rail's label was the only thing telling a
                  reader what a panel was. ADR 0009. */}
              {renderSection(GENE_SECTIONS, section,
                { rec, data, symbol, setSymbol, setQuery }, {})}
            </>
          )}
        </>
      )}

      <p className={css.provenance}>
        {data.premise} {data.worldPremise} <code>{data.generated}</code>
      </p>
    </section>
  );
}

/* ------------------------------------------------------------------- panels */





function Skeleton() {
  return <div className={css.skeleton} role="status" aria-live="polite" />;
}
