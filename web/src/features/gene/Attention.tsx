import { useMemo, useState } from "react";
import { useRemoteData } from "../../lib/useRemoteData";
import { useT, fill } from "../../i18n";
import { ATT } from "../../i18n/attention";
import { ParallelCoordinates } from "../../components/viz/organisms/ParallelCoordinates";
import { fmt, fmtInt, pct } from "../../lib/scale";
import type { GeneRecord, GeneSearchIndex } from "./geneModel";
import css from "./Attention.module.css";

/** How much anyone has looked — the number this site had been asserting.
 *
 *  Every panel here invokes attention bias. The VUS share "is a measurement of attention, not
 *  of the gene". Constraint "is measured where people sequenced". A protein with no annotated
 *  domain "is usually one nobody has characterised". All asserted; none measured.
 *
 *  gene2pubmed measures it, and the measurement holds: the median share of unreadable
 *  variants falls from 87 % in the least-studied decile to 53 % in the most-studied. The
 *  claim stops being a caveat and becomes a gradient.
 *
 *  WHICH MAKES THE RESIDUAL POSSIBLE. "Is this share high" is a weak question. "Is it high
 *  FOR A GENE THIS STUDIED" is the one a curator needs, and it separates two situations the
 *  site could not previously tell apart: a field that looked hard and still cannot read the
 *  gene, and a field that has not looked.
 */

type Space = {
  premise: string;
  sampling: string;
  axes: string[];
  scope: {
    eligible: number; flagged: number; flaggedTotal: number;
    ground: number; thinnedEvery: number; total: number;
    perRule: Record<string, number>;
  };
  rows: { id: string; v: Record<string, number>; c?: string[] }[];
};

const RULES = [
  "selective", "organismal", "unreadable", "broadButSelective",
  "damageInDomains", "cultureArtefact",
] as const;

export function Attention(
  { rec, scope, deciles, caution, baseline, onPick }:
  {
    rec?: GeneRecord;
    scope: GeneSearchIndex["scope"];
    deciles: { decile: number; papersFrom: number; papersTo: number; genes: number;
               medianVus: number }[];
    caution: string;
    baseline: string;
    onPick: (symbol: string) => void;
  },
) {
  const t = useT();
  const [highlight, setHighlight] = useState<string>("organismal");
  const space = useRemoteData<Space>("data/gene/space.json");

  const att = rec?.att;
  const peakVus = Math.max(...deciles.map((d) => d.medianVus), 0.01);

  const pcRows = useMemo(
    () => (space.state === "ready"
      ? space.data.rows.map((r) => ({ id: r.id, values: r.v, classes: r.c }))
      : []),
    [space],
  );

  return (
    <div className={css.wrap}>
      <p className={css.lede}>{t(ATT.lede)}</p>

      {/* ------------------------------------------------- this gene's own numbers */}
      {att && (
        <div className={css.facts}>
          <Fact k={t(ATT.pPapers)} v={fmtInt(att.papers)}
                s={fill(t(ATT.sPapers), {
                  median: fmtInt(scope.att?.median ?? 0),
                  max: fmtInt(scope.att?.max ?? 0),
                })} />
          {att.vusResidual != null && (
            <Fact
              k={t(ATT.pResidual)}
              v={`${att.vusResidual > 0 ? "+" : ""}${pct(att.vusResidual, 0)}`}
              s={t(att.vusResidual > 0.05 ? ATT.sResidualHigh
                  : att.vusResidual < -0.05 ? ATT.sResidualLow : ATT.sResidualPar)}
              tone={att.vusResidual > 0.05 ? "warn" : undefined}
            />
          )}
        </div>
      )}

      {/* ------------------------------------------------------------ the gradient */}
      <section className={css.block}>
        <h4 className={css.blockTitle}>{t(ATT.ladderTitle)}</h4>
        <p className={css.blockNote}>{t(ATT.ladderNote)}</p>

        <ul className={css.ladder}>
          {deciles.map((d) => {
            const here = att?.papers != null
              && att.papers >= d.papersFrom && att.papers <= d.papersTo;
            return (
              <li key={d.decile} className={here ? css.rungOn : css.rung}>
                <span className={css.rungRange}>
                  {fmtInt(d.papersFrom)}–{fmtInt(d.papersTo)}
                </span>
                <span className={css.rungTrack}>
                  <span className={css.rungBar}
                        style={{ width: `${(d.medianVus / peakVus) * 100}%` }} />
                </span>
                <span className={css.rungVal}>{pct(d.medianVus, 0)}</span>
                <span className={css.rungN}>{fmtInt(d.genes)}</span>
              </li>
            );
          })}
        </ul>
        <p className={css.baseline}>{baseline}</p>
      </section>

      {/* -------------------------------------------------- the hyperspatial view */}
      <section className={css.block}>
        <h4 className={css.blockTitle}>{t(ATT.spaceTitle)}</h4>

        <div className={css.rules} role="tablist" aria-label={t(ATT.spaceTitle)}>
          {RULES.filter((r) => space.state === "ready" && space.data.scope.perRule[r])
            .map((r) => (
              <button
                key={r}
                type="button"
                role="tab"
                aria-selected={r === highlight}
                className={r === highlight ? css.ruleOn : css.rule}
                onClick={() => setHighlight(r)}
              >
                {r}
                <span className={css.ruleCount}>
                  {fmtInt(scope.ins?.byRule?.[r] ?? 0)}
                </span>
              </button>
            ))}
        </div>

        {space.state === "ready" ? (
          <>
            <ParallelCoordinates
              axes={[
                { key: "papers", label: t(ATT.axPapers), top: t(ATT.axPapersTop),
                  bottom: t(ATT.axPapersBottom), format: (v) => fmtInt(v) },
                { key: "constraint", label: t(ATT.axConstraint), top: t(ATT.axConstraintTop),
                  bottom: t(ATT.axConstraintBottom), format: (v) => fmt(-v, 2) },
                { key: "dependency", label: t(ATT.axDependency), top: t(ATT.axDependencyTop),
                  bottom: t(ATT.axDependencyBottom), format: (v) => pct(v, 0) },
                { key: "breadth", label: t(ATT.axBreadth), top: t(ATT.axBreadthTop),
                  bottom: t(ATT.axBreadthBottom), format: (v) => fmtInt(v) },
                { key: "unread", label: t(ATT.axUnread), top: t(ATT.axUnreadTop),
                  bottom: t(ATT.axUnreadBottom), format: (v) => pct(v, 0) },
              ]}
              rows={pcRows}
              highlight={highlight}
              onPick={onPick}
              ariaLabel={t(ATT.spaceTitle)}
              readAloud={t(ATT.spaceRead)}
              labels={{
                order: t(ATT.axisOrder),
                moveLeft: t(ATT.moveLeft),
                moveRight: t(ATT.moveRight),
                count: t(ATT.linesDrawn),
                lit: t(ATT.linesLit),
              }}
            />
            {/* The sampling, said in full. A sample a reader mistakes for a census is worse
                than no plot at all. */}
            <p className={css.sampling}>{space.data.sampling}</p>
          </>
        ) : (
          <div className={css.skeleton} role="status" />
        )}
      </section>

      <p className={css.caution}>{caution}</p>
    </div>
  );
}

function Fact(
  { k, v, s, tone }: { k: string; v: string; s: string; tone?: "warn" },
) {
  return (
    <div className={css.fact} data-tone={tone}>
      <span className={css.factK}>{k}</span>
      <span className={css.factV}>{v}</span>
      <span className={css.factS}>{s}</span>
    </div>
  );
}
