import { useMemo } from "react";
import { useT } from "../../i18n";
import { DS } from "../../i18n/datasheet";
import { fmt, fmtInt, pct } from "../../lib/scale";
import type { GeneRecord } from "./geneModel";
import css from "./Datasheet.module.css";

/** The gene as a datasheet.
 *
 *  A transistor datasheet does not print "gain: 100". It prints a parameter, a symbol, a
 *  minimum, a typical and a maximum, the unit, and the test conditions those were obtained
 *  under. Every number carries its circumstances, and one without them is not publishable.
 *
 *  THAT DISCIPLINE IS THIS REPOSITORY'S ARGUMENT, applied to itself for the first time. Every
 *  other panel reports a gene's dependency as one number. A gene has 1,178 of them, and the
 *  spread is the question a target programme is actually asking: needed at −1.8 in forty
 *  lines and 0.0 in the rest is a selective target; −1.0 in every line is a poison. Both
 *  report a mean near −1.
 *
 *  WHERE ONLY ONE NUMBER EXISTS, min and max are left empty. A datasheet that repeats the
 *  typical across all three columns is lying about what was measured — and that is the exact
 *  failure this repository exists to name.
 */

type Row = {
  key: string;
  param: string;
  symbol?: string;
  min?: string;
  typ?: string;
  max?: string;
  unit?: string;
  cond: string;
  tone?: "warn" | "good";
};

type Block = { title: string; note: string; rows: Row[] };

export function Datasheet({ rec }: { rec?: GeneRecord }) {
  const t = useT();
  const ds = rec?.ds;

  const blocks = useMemo<Block[]>(() => {
    const out: Block[] = [];

    /* ------------------------------------------------------------- package */
    const prot = rec?.world?.prot;
    const dom = rec?.dom;
    if (prot || dom) {
      const kinds = (dom?.features ?? []).reduce<Record<string, number>>((a, f) => {
        a[f.kind] = (a[f.kind] ?? 0) + 1;
        return a;
      }, {});
      out.push({
        title: t(DS.bPhysical),
        note: t(DS.nPhysical),
        rows: [
          prot?.size != null && {
            key: "len", param: t(DS.pLength), symbol: "L", typ: fmtInt(prot.size),
            unit: t(DS.uResidues), cond: "UniProt",
          },
          kinds.domain && {
            key: "dom", param: t(DS.pDomains), symbol: "N_D", typ: String(kinds.domain),
            cond: t(DS.cCurated),
          },
          kinds.membrane && {
            key: "tm", param: t(DS.pMembrane), symbol: "N_TM", typ: String(kinds.membrane),
            cond: t(DS.cCurated),
            tone: "warn" as const,
          },
          kinds.binding && {
            key: "bind", param: t(DS.pBinding), symbol: "N_B", typ: String(kinds.binding),
            cond: t(DS.cCurated),
          },
          kinds.active && {
            key: "act", param: t(DS.pActive), symbol: "N_A", typ: String(kinds.active),
            cond: t(DS.cCurated),
          },
        ].filter(Boolean) as Row[],
      });
    }

    /* ----------------------------------------------- absolute maximum */
    const con = rec?.world?.con;
    if (con) {
      out.push({
        title: t(DS.bLimits),
        note: t(DS.nLimits),
        rows: [
          con.oe != null && {
            key: "oe", param: t(DS.pOe), symbol: "o/e",
            // The CI is a real min and max: gnomAD publishes the bound, not just the point.
            min: con.loeuf != null ? fmt(con.oe, 2) : undefined,
            typ: fmt(con.oe, 2),
            max: con.loeuf != null ? fmt(con.loeuf, 2) : undefined,
            cond: `gnomAD v4.1 · ${fmtInt(con.lofObs)} ${t(DS.cObserved)} / ${fmt(con.lofExp, 1)} ${t(DS.cExpected)}`,
            tone: con.loeuf != null && con.loeuf < 0.35 ? ("warn" as const) : undefined,
          },
          con.pLI != null && {
            key: "pli", param: t(DS.pPli), symbol: "pLI", typ: fmt(con.pLI, 2),
            cond: "gnomAD v4.1",
          },
          con.misZ != null && {
            key: "misz", param: t(DS.pMisZ), symbol: "Z_mis", typ: fmt(con.misZ, 1),
            cond: "gnomAD v4.1",
          },
        ].filter(Boolean) as Row[],
      });
    }

    /* --------------------------------------------------- dependency */
    if (ds?.dep) {
      const d = ds.dep;
      out.push({
        title: t(DS.bDependency),
        note: t(DS.nDependency),
        rows: [
          {
            key: "effect", param: t(DS.pEffect), symbol: "GE",
            min: fmt(d.min, 2), typ: fmt(d.median, 2), max: fmt(d.max, 2),
            unit: t(DS.uChronos),
            cond: `DepMap 24Q2 · ${fmtInt(d.n)} ${t(DS.cLines)}`,
            tone: d.median < -0.5 ? ("warn" as const) : undefined,
          },
          {
            key: "iqr", param: t(DS.pIqr), symbol: "IQR",
            min: fmt(d.q1, 2), typ: fmt(d.median, 2), max: fmt(d.q3, 2),
            unit: t(DS.uChronos), cond: t(DS.cQuartiles),
          },
          d.sd != null && {
            key: "sd", param: t(DS.pSpread), symbol: "σ", typ: fmt(d.sd, 3),
            unit: t(DS.uChronos), cond: `${fmtInt(d.n)} ${t(DS.cLines)}`,
          },
          {
            key: "dep", param: t(DS.pDependent), symbol: "N_dep",
            typ: `${fmtInt(d.dependent)} / ${fmtInt(d.n)}`,
            unit: pct(d.dependent / Math.max(1, d.n), 0),
            cond: `GE < −0.5`,
          },
          {
            key: "strong", param: t(DS.pStrong), symbol: "N_str",
            typ: `${fmtInt(d.strong)} / ${fmtInt(d.n)}`,
            unit: pct(d.strong / Math.max(1, d.n), 0),
            cond: `GE < −1.0`,
            tone: d.strong / Math.max(1, d.n) > 0.9 ? ("warn" as const) : undefined,
          },
        ].filter(Boolean) as Row[],
      });
    }

    /* --------------------------------------------------- expression */
    if (ds?.exp) {
      const e = ds.exp;
      out.push({
        title: t(DS.bExpression),
        note: t(DS.nExpression),
        rows: [
          {
            key: "ncpm", param: t(DS.pExpression), symbol: "E",
            min: fmt(e.min, 1), typ: fmt(e.median, 1), max: fmt(e.max, 1),
            unit: "nCPM",
            cond: `HPA · ${fmtInt(e.types)} ${t(DS.cCellTypes)}`,
          },
          e.ratio != null && {
            key: "ratio", param: t(DS.pFocus), symbol: "E_max/E_typ",
            typ: `${fmt(e.ratio, 1)}×`,
            cond: t(DS.cFocus),
            tone: e.ratio > 20 ? ("good" as const) : undefined,
          },
        ].filter(Boolean) as Row[],
      });
    }

    /* ----------------------------------------------------- variants */
    const clin = rec?.world?.clin;
    if (clin) {
      out.push({
        title: t(DS.bVariants),
        note: t(DS.nVariants),
        rows: [
          {
            key: "total", param: t(DS.pSubmitted), symbol: "N_v",
            typ: fmtInt(clin.total), cond: "ClinVar · GRCh38",
          },
          {
            key: "path", param: t(DS.pPathogenic), symbol: "N_P",
            typ: fmtInt(clin.pathogenic),
            unit: pct(clin.pathogenic / Math.max(1, clin.total), 0),
            cond: t(DS.cIncludingLikely),
          },
          {
            key: "vus", param: t(DS.pVus), symbol: "N_U",
            typ: fmtInt(clin.uncertain),
            unit: pct(clin.vusShare, 0),
            cond: t(DS.cVus),
            tone: clin.total >= 20 && clin.vusShare > 0.5 ? ("warn" as const) : undefined,
          },
        ],
      });
    }

    return out.filter((b) => b.rows.length);
  }, [rec, ds, t]);

  if (!blocks.length) return <p className={css.absent}>{t(DS.absent)}</p>;

  return (
    <div className={css.wrap}>
      <p className={css.lede}>{t(DS.lede)}</p>

      {blocks.map((b) => (
        <section key={b.title} className={css.block}>
          <h4 className={css.blockTitle}>{b.title}</h4>
          <p className={css.blockNote}>{b.note}</p>

          <div className={css.tableWrap}>
            <table className={css.table}>
              <thead>
                <tr>
                  <th className={css.thParam}>{t(DS.hParam)}</th>
                  <th className={css.thSym}>{t(DS.hSymbol)}</th>
                  <th className={css.thNum}>{t(DS.hMin)}</th>
                  <th className={css.thNum}>{t(DS.hTyp)}</th>
                  <th className={css.thNum}>{t(DS.hMax)}</th>
                  <th className={css.thUnit}>{t(DS.hUnit)}</th>
                  <th className={css.thCond}>{t(DS.hCond)}</th>
                </tr>
              </thead>
              <tbody>
                {b.rows.map((r) => (
                  <tr key={r.key} data-tone={r.tone}>
                    <th scope="row" className={css.param}>{r.param}</th>
                    <td className={css.sym}>{r.symbol ?? ""}</td>
                    {/* An empty min or max is the honest rendering of a single measurement.
                        Repeating the typical across all three would claim a range nobody
                        measured — the exact failure this whole page argues against. */}
                    <td className={css.num}>{r.min ?? <span className={css.dash}>—</span>}</td>
                    <td className={css.numTyp}>{r.typ ?? ""}</td>
                    <td className={css.num}>{r.max ?? <span className={css.dash}>—</span>}</td>
                    <td className={css.unit}>{r.unit ?? ""}</td>
                    <td className={css.cond}>{r.cond}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ))}

      <p className={css.convention}>{t(DS.convention)}</p>
    </div>
  );
}
