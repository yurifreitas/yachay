





import { useT } from "../../i18n";
import { GENE } from "../../i18n/gene";
import { fmt, fmtInt, pct } from "../../lib/scale";
import { type GeneRecord, type GeneSearchIndex } from "./geneModel";



import { GeneBrowse } from "./GeneBrowse";









import css from "./GenePage.module.css";

/** The gene page's panels, lifted out of the page so both the page and its section registry
 *  can reach them. They were local functions, which is fine until a registry needs them —
 *  and a registry that has to import from the page it feeds is a cycle. */

export function Dependency({ rec, scope }: PanelProps) {
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


export function Cancer({ rec, scope }: PanelProps) {
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
      <div className={css.tableWrap}><table className={css.table}>
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
      </table></div>
      {(rec?.cancerTotal ?? 0) > hits.length && (
        <p className={css.foot}>
          {t(GENE.cTruncated)} {rec?.cancerTotal}.
        </p>
      )}
    </div>
  );
}


export function Genotype({ rec, scope }: PanelProps) {
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
      <div className={css.tableWrap}><table className={css.table}>
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
      </table></div>
    </div>
  );
}


export function Network({ rec, scope }: PanelProps) {
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


export function Diseases({ rec }: { rec?: GeneRecord }) {
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


export type PanelProps = { rec?: GeneRecord; scope: GeneSearchIndex["scope"] };






/* -------------------------------------------------------------------- parts */

export function Empty({ scope, onPick }: { scope: GeneSearchIndex["scope"]; onPick: (s: string) => void }) {
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

      {/* THE OTHER WAY IN. The four seeds above teach what the page does; this is how
          someone who does not have a symbol in mind actually gets to a gene. */}
      <GeneBrowse onPick={onPick} />
    </div>
  );
}


export function Absent({ children }: { children: React.ReactNode }) {
  return <p className={css.absentPanel}>{children}</p>;
}


export function Fact(
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


export function Note({ tone, children }: { tone: "good" | "warn" | "info"; children: React.ReactNode }) {
  return <p className={css.note} data-tone={tone}>{children}</p>;
}
