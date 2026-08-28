import { useEffect, useMemo, useState } from "react";
import { useRemoteData } from "../../lib/useRemoteData";
import { useHashParam } from "../../lib/useHashParam";
import { useSectionNav, type NavGroupDef, type NavSectionDef } from "../../lib/nav";
import { SectionHeading } from "../../components/molecules/SectionHeading";
import { useT, fill } from "../../i18n";
import { GENE } from "../../i18n/gene";
import { fmt, fmtInt, pct } from "../../lib/scale";
import { layersFor, searchGenes, type GeneSearchIndex, type GeneRecord,
         type GeneShard } from "./geneModel";
import { shardOf } from "./shard";
import { WORLD } from "../../i18n/world";
import { ConstraintPanel, ExpressionPanel, Form, VariantsPanel } from "./WorldPanels";
import { Needle, Pathways, Routes } from "./GeometryPanels";
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
  { id: "world", label: WORLD.gWorld, question: WORLD.qWorld },
  { id: "shape", label: GEO.gShape, question: GEO.qShape },
  { id: "screen", label: GENE.gScreen, question: GENE.qScreen },
  { id: "context", label: GENE.gContext, question: GENE.qContext },
  { id: "clinic", label: GENE.gClinic, question: GENE.qClinic },
];

const SECTIONS: NavSectionDef[] = [
  { id: "form", label: WORLD.sForm, group: "world" },
  { id: "constraint", label: WORLD.sConstraint, group: "world" },
  { id: "expression", label: WORLD.sExpression, group: "world" },
  { id: "variants", label: WORLD.sVariants, group: "world" },
  { id: "needle", label: GEO.sNeedle, group: "shape" },
  { id: "routes", label: GEO.sRoutes, group: "shape" },
  { id: "pathways", label: GEO.sPathways, group: "shape" },
  { id: "dependency", label: GENE.sDependency, group: "screen" },
  { id: "cancer", label: GENE.sCancer, group: "screen" },
  { id: "genotype", label: GENE.sGenotype, group: "screen" },
  { id: "network", label: GENE.sNetwork, group: "context" },
  { id: "disease", label: GENE.sDisease, group: "clinic" },
];

export default function GenePage() {
  const t = useT();
  const { section } = useSectionNav({
    owner: "gene", groups: GROUPS, sections: SECTIONS, initial: "form",
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
              {section === "form" && <Form world={rec?.world} scope={data.scope} />}
              {section === "constraint" && <ConstraintPanel world={rec?.world} scope={data.scope} />}
              {section === "expression" && <ExpressionPanel world={rec?.world} scope={data.scope} />}
              {section === "variants" && <VariantsPanel world={rec?.world} scope={data.scope} />}
              {section === "needle" && <Needle geo={rec?.geo} />}
              {section === "routes" && <Routes geo={rec?.geo} />}
              {section === "pathways" && <Pathways geo={rec?.geo} />}
              {section === "dependency" && <Dependency rec={rec} scope={data.scope} />}
              {section === "cancer" && <Cancer rec={rec} scope={data.scope} />}
              {section === "genotype" && <Genotype rec={rec} scope={data.scope} />}
              {section === "network" && <Network rec={rec} scope={data.scope} />}
              {section === "disease" && <Diseases rec={rec} />}
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

type PanelProps = { rec?: GeneRecord; scope: GeneSearchIndex["scope"] };

function Dependency({ rec, scope }: PanelProps) {
  const t = useT();
  const d = rec?.dep;
  if (!d) {
    return (
      <Absent>
        {t(GENE.aDependency)} {fmtInt(scope.dependency.genes)}.
      </Absent>
    );
  }

  const moved = d.rankRaw - d.rankCal;
  return (
    <div className={css.block}>
      <div className={css.facts}>
        <Fact k={t(GENE.fScore)} v={fmt(d.score, 3)}
              s={`${t(GENE.fScoreSub)} ${fmtInt(d.n)}`} />
        <Fact k={t(GENE.fNull)} v={`${fmt(d.nullMean, 3)} ± ${fmt(d.nullSd, 3)}`}
              s={t(GENE.fNullSub)} />
        <Fact k={t(GENE.fZ)} v={fmt(d.z, 2)} s={t(GENE.fZSub)} tone={d.z > 2.326 ? "good" : undefined} />
        <Fact k={t(GENE.fRank)} v={`#${fmtInt(d.rankCal)}`}
              s={`${t(GENE.fRankSub)} #${fmtInt(d.rankRaw)}${
                moved !== 0 ? ` (${moved > 0 ? "+" : ""}${fmtInt(moved)})` : ""}`} />
        <Fact k={t(GENE.fSelectivity)} v={fmt(d.selectivity, 3)} s={t(GENE.fSelectivitySub)} />
        <Fact k={t(GENE.fMedian)} v={fmt(d.medianDependency, 3)} s={t(GENE.fMedianSub)} />
      </div>

      {/* THE FLAGS ARE THE WARNING, and they belong above the numbers, not beside them.
          A pan-essential gene with a spectacular z is not a finding — it is the metric
          measuring toxicity, which is the failure this whole repository exists to name. */}
      {d.commonEssential && <Note tone="warn">{t(GENE.flagEssential)}</Note>}
      {d.control && <Note tone="info">{t(GENE.flagControl)}</Note>}
      {!d.commonEssential && !d.control && d.z > 2.326 && (
        <Note tone="good">{t(GENE.flagCandidate)}</Note>
      )}
    </div>
  );
}

function Cancer({ rec, scope }: PanelProps) {
  const t = useT();
  const hits = rec?.cancer ?? [];
  if (!hits.length) {
    return (
      <Absent>
        {t(GENE.aCancer)} {scope.cancer.subgroups} {t(GENE.aCancerTail)}
      </Absent>
    );
  }
  return (
    <div className={css.block}>
      <p className={css.sub}>{t(GENE.cancerLede)}</p>
      <table className={css.table}>
        <thead>
          <tr>
            <th>{t(GENE.cSubgroup)}</th><th>{t(GENE.cLevel)}</th>
            <th className={css.num}>{t(GENE.cEffect)}</th>
            <th className={css.num}>q</th>
            <th className={css.num}>{t(GENE.cLines)}</th>
          </tr>
        </thead>
        <tbody>
          {hits.map((h) => (
            <tr key={`${h.level}:${h.subgroup}`}>
              <th scope="row">{h.subgroup}</th>
              <td className={css.level}>{h.level}</td>
              <td className={css.num}>{fmt(h.d, 3)}</td>
              <td className={css.num}>{h.q < 0.001 ? h.q.toExponential(1) : fmt(h.q, 3)}</td>
              <td className={css.num}>{h.lines != null ? fmtInt(h.lines) : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {(rec?.cancerTotal ?? 0) > hits.length && (
        <p className={css.foot}>
          {t(GENE.cTruncated)} {rec?.cancerTotal}.
        </p>
      )}
    </div>
  );
}

function Genotype({ rec, scope }: PanelProps) {
  const t = useT();
  const hits = rec?.genotype ?? [];
  if (!hits.length) {
    return (
      <Absent>
        {t(GENE.aGenotype)} {scope.genotype.subgroups} {t(GENE.aGenotypeTail)}
      </Absent>
    );
  }
  return (
    <div className={css.block}>
      <p className={css.sub}>{t(GENE.genotypeLede)}</p>
      <table className={css.table}>
        <thead>
          <tr>
            <th>{t(GENE.gMutated)}</th>
            <th className={css.num}>{t(GENE.cEffect)}</th>
            <th className={css.num}>q</th>
            <th className={css.num}>{t(GENE.cLines)}</th>
          </tr>
        </thead>
        <tbody>
          {hits.map((h) => (
            <tr key={h.mutatedGene}>
              <th scope="row">{h.mutatedGene}</th>
              <td className={css.num}>{fmt(h.d, 3)}</td>
              <td className={css.num}>{h.q < 0.001 ? h.q.toExponential(1) : fmt(h.q, 3)}</td>
              <td className={css.num}>{h.lines != null ? fmtInt(h.lines) : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Network({ rec, scope }: PanelProps) {
  const t = useT();
  const n = rec?.net;
  if (!n) {
    return <Absent>{t(GENE.aNetwork)} {fmtInt(scope.network.nodes)}.</Absent>;
  }
  return (
    <div className={css.block}>
      <p className={css.sub}>{t(GENE.networkLede)}</p>
      <div className={css.facts}>
        <Fact k={t(GENE.nDegree)} v={fmtInt(n.degree)} s={t(GENE.nDegreeSub)} />
        <Fact k={t(GENE.nDiseases)} v={fmtInt(n.diseases)} s={t(GENE.nDiseasesSub)} />
        <Fact k={t(GENE.nCommunity)} v={n.community != null ? `#${n.community}` : "—"}
              s={t(GENE.nCommunitySub)} />
      </div>
    </div>
  );
}

function Diseases({ rec }: { rec?: GeneRecord }) {
  const t = useT();
  const dis = rec?.dis ?? [];
  if (!dis.length) return <Absent>{t(GENE.aDisease)}</Absent>;

  // Grouped by association type, because MENDELIAN and UNKNOWN are different claims and a
  // single alphabetical list would present them as equal evidence.
  const byAssoc = dis.reduce<Record<string, typeof dis>>((acc, d) => {
    (acc[d.assoc] ??= []).push(d);
    return acc;
  }, {});
  const order = ["MENDELIAN", "POLYGENIC", "UNKNOWN"];
  const keys = Object.keys(byAssoc).sort(
    (a, b) => (order.indexOf(a) + 9) % 9 - (order.indexOf(b) + 9) % 9,
  );

  return (
    <div className={css.block}>
      <p className={css.sub}>{t(GENE.diseaseLede)}</p>
      {keys.map((k) => (
        <section key={k} className={css.assoc}>
          <h4 className={css.assocName}>
            {k}
            <span className={css.assocCount}>
              {byAssoc[k].length} ({pct(byAssoc[k].length / dis.length, 0)})
            </span>
          </h4>
          <ul className={css.diseaseList}>
            {byAssoc[k].map((d) => (
              <li key={d.id}>
                <span className={css.diseaseName}>{d.name}</span>
                <span className={css.diseaseId}>{d.id}</span>
              </li>
            ))}
          </ul>
        </section>
      ))}
      {(rec?.disTotal ?? 0) > dis.length && (
        <p className={css.foot}>{t(GENE.dTruncated)} {rec?.disTotal}.</p>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------- parts */

function Empty({ scope, onPick }: { scope: GeneSearchIndex["scope"]; onPick: (s: string) => void }) {
  const t = useT();
  // Openings, not a random sample: one gene per kind of story this page can tell, so the
  // first click teaches what the page is for.
  const seeds = [
    { s: "NF2", why: GENE.seedNF2 },
    { s: "CFTR", why: GENE.seedCFTR },
    { s: "SNRPD3", why: GENE.seedSNRPD3 },
    { s: "KRAS", why: GENE.seedKRAS },
  ];
  return (
    <div className={css.empty}>
      <p className={css.emptyLede}>{t(GENE.emptyLede)}</p>
      <ul className={css.seeds}>
        {seeds.map((x) => (
          <li key={x.s}>
            <button type="button" className={css.seed} onClick={() => onPick(x.s)}>
              <span className={css.seedSym}>{x.s}</span>
              <span className={css.seedWhy}>{t(x.why)}</span>
            </button>
          </li>
        ))}
      </ul>
      <p className={css.foot}>
        {fmtInt(scope.genes)} {t(GENE.indexed)} · {fmtInt(scope.disease.pairs)}{" "}
        {t(GENE.pairs)}
      </p>
    </div>
  );
}

function Fact(
  { k, v, s, tone }: { k: string; v: string; s: string; tone?: "good" | "warn" },
) {
  return (
    <div className={css.fact} data-tone={tone}>
      <span className={css.factK}>{k}</span>
      <span className={css.factV}>{v}</span>
      <span className={css.factS}>{s}</span>
    </div>
  );
}

function Note({ tone, children }: { tone: "good" | "warn" | "info"; children: React.ReactNode }) {
  return <p className={css.note} data-tone={tone}>{children}</p>;
}

function Absent({ children }: { children: React.ReactNode }) {
  return <p className={css.absentPanel}>{children}</p>;
}

function Skeleton() {
  return <div className={css.skeleton} role="status" aria-live="polite" />;
}
