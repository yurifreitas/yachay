import { useT, fill } from "../../i18n";
import { GEO } from "../../i18n/geometry";
import { NeedlePlot } from "../../components/viz/organisms/NeedlePlot";
import { fmt, fmtInt, pct } from "../../lib/scale";
import css from "./GenePage.module.css";

/** The molecular geometry: where the damage falls, how it breaks, what it operates in.
 *
 *  These three panels are the answer to a question every other panel on the site sidesteps.
 *  A count of variants says how much is known. It cannot say whether the damage sits in one
 *  interface or runs the length of the chain, and those are different diseases.
 *
 *  WHAT THIS IS NOT. It is not structure. There is no fold here, no domain boundary, no
 *  binding pocket — those need UniProt features or a solved structure, and inventing them
 *  from variant density would be drawing a molecule from the shape of the attention paid to
 *  it. What there is, is the exact residue each reported variant lands on, which is real,
 *  measured, and was sitting unparsed in a file already on disk.
 */

export type GeoRecord = {
  consequence?: Record<string, number>;
  placed?: number;
  length?: number | null;
  lengthFrom?: string | null;
  span?: number;
  bins?: number;
  hist?: Record<string, number[]>;
  recurrent?: { pos: number; n: number }[];
  clustering?: { share: number; expected: number; ratio: number; n: number };
  pathways?: { id: string; name: string }[];
  pathwayTotal?: number;
};

/* --------------------------------------------------------------- the needle */

export function Needle({ geo }: { geo?: GeoRecord }) {
  const t = useT();
  if (!geo?.hist || !geo.span || !geo.bins) {
    return <p className={css.absentPanel}>{t(GEO.aNeedle)}</p>;
  }

  const c = geo.clustering;
  return (
    <div className={css.block}>
      <p className={css.sub}>{t(GEO.needleLede)}</p>

      <NeedlePlot
        series={geo.hist}
        span={geo.span}
        bins={geo.bins}
        recurrent={geo.recurrent ?? []}
        height={340}
        lengthFrom={t(geo.lengthFrom === "STRING" ? GEO.lengthFromString : GEO.lengthFromObserved)}
        ariaLabel={t(GEO.needleLede)}
        readAloud={t(GEO.needleRead)}
        labels={{
          axis: t(GEO.axis),
          residues: t(GEO.residues),
          placed: t(GEO.placed),
          pathogenic: t(GEO.lPathogenic),
          uncertain: t(GEO.lUncertain),
          benign: t(GEO.lBenign),
          conflicting: t(GEO.lConflicting),
        }}
      />

      <section className={css.cluster}>
        <h4 className={css.clusterTitle}>{t(GEO.clusterTitle)}</h4>
        {c ? (
          <>
            <p className={c.ratio >= 1.5 ? css.clusterHead : css.clusterFlatHead}>
              {c.ratio >= 1.5
                ? fill(t(GEO.clusterHead),
                       { share: pct(c.share, 0), ratio: fmt(c.ratio, 1) })
                : t(GEO.clusterFlat)}
            </p>
            {/* The comparison drawn, not just stated: the measured share against the share a
                uniform spread would give. Two bars on one baseline is the whole argument. */}
            <div className={css.clusterBars}>
              <span className={css.clusterRow}>
                <span className={css.clusterLabel}>{pct(c.share, 0)}</span>
                <span className={css.clusterTrack}>
                  <span className={css.clusterFill} style={{ width: `${c.share * 100}%` }} />
                </span>
              </span>
              <span className={css.clusterRow}>
                <span className={css.clusterLabel}>{pct(c.expected, 0)}</span>
                <span className={css.clusterTrack}>
                  <span className={css.clusterExpected}
                        style={{ width: `${c.expected * 100}%` }} />
                </span>
              </span>
            </div>
          </>
        ) : (
          <p className={css.caution}>{t(GEO.clusterTooFew)}</p>
        )}
        <p className={css.caution}>{t(GEO.clusterCaution)}</p>
      </section>
    </div>
  );
}

/* --------------------------------------------------------------- the routes */

const ROUTE_LABEL: Record<string, keyof typeof GEO> = {
  missense: "rMissense",
  stopGained: "rStopGained",
  stopLost: "rStopLost",
  frameshift: "rFrameshift",
  splice: "rSplice",
  inFrameIndel: "rInFrameIndel",
  synonymous: "rSynonymous",
  structural: "rStructural",
  other: "rOther",
};

export function Routes({ geo }: { geo?: GeoRecord }) {
  const t = useT();
  const cons = geo?.consequence;
  if (!cons || !Object.keys(cons).length) {
    return <p className={css.absentPanel}>{t(GEO.aNeedle)}</p>;
  }

  const rows = Object.entries(cons).sort((a, b) => b[1] - a[1]);
  const total = rows.reduce((s, [, n]) => s + n, 0);
  const peak = rows[0]?.[1] ?? 1;

  return (
    <div className={css.block}>
      <p className={css.sub}>{t(GEO.routesLede)}</p>
      <ul className={css.cells}>
        {rows.map(([k, n]) => (
          <li key={k}>
            <span className={css.cellName}>
              {ROUTE_LABEL[k] ? t(GEO[ROUTE_LABEL[k]] as never) : k}
            </span>
            <span className={css.cellTrack}>
              <span className={css.cellBar} style={{ width: `${(n / peak) * 100}%` }} />
            </span>
            <span className={css.cellVal}>{fmtInt(n)}</span>
            <span className={css.cellPct}>{pct(n / total, 0)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ------------------------------------------------------------- the pathways */

export function Pathways({ geo }: { geo?: GeoRecord }) {
  const t = useT();
  const ps = geo?.pathways ?? [];
  if (!ps.length) return <p className={css.absentPanel}>{t(GEO.aPathways)}</p>;

  return (
    <div className={css.block}>
      <p className={css.sub}>{t(GEO.pathwaysLede)}</p>
      <div className={css.facts}>
        <Fact k={t(GEO.pathwayCount)} v={fmtInt(geo?.pathwayTotal ?? ps.length)}
              s={t(GEO.pathwayCountSub)} />
      </div>
      <ul className={css.pathways}>
        {ps.map((p) => (
          <li key={p.id}>
            <span className={css.pathName}>{p.name}</span>
            <span className={css.pathId}>{p.id}</span>
          </li>
        ))}
      </ul>
      {(geo?.pathwayTotal ?? 0) > ps.length && (
        <p className={css.foot}>{t(GEO.pTruncated)} {geo?.pathwayTotal}.</p>
      )}
    </div>
  );
}

function Fact({ k, v, s }: { k: string; v: string; s: string }) {
  return (
    <div className={css.fact}>
      <span className={css.factK}>{k}</span>
      <span className={css.factV}>{v}</span>
      <span className={css.factS}>{s}</span>
    </div>
  );
}
