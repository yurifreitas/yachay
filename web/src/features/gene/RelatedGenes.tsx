import { useT, fill } from "../../i18n";
import { REL } from "../../i18n/related";
import { fmtInt } from "../../lib/scale";
import css from "./RelatedGenes.module.css";

/** WHERE TO GO NEXT, AND WHY.
 *
 *  The navigator was a dead end: a reader arrived at a gene, read seven layers, and the only
 *  way out was back to the search box. But a gene is never the unit of a real question. A
 *  curator checking NF2 wants the other genes causing the same disease. A therapy team wants
 *  the rest of the fold family. Someone tracing a mechanism wants the graph neighbours.
 *
 *  EVERY ROUTE STATES ITS RELATION. A related-genes list with no stated relation is guesswork
 *  with a layout — and it is the commonest way an interface smuggles in a similarity score
 *  nobody can audit. There is no embedding here and no composite: the ordering is shared
 *  evidence, and the count that produced it is printed next to the gene.
 */

export type RelRecord = {
  graph?: { gene: string; shared: number }[];
  graphTotal?: number;
  family?: { name: string; size: number; genes: string[] };
  lineage?: { name: string; size: number; genes: string[] };
  disease?: { id: string; name: string; size: number; genes: string[] };
};

export function RelatedGenes(
  { rel, onPick }: { rel?: RelRecord; onPick: (symbol: string) => void },
) {
  const t = useT();
  if (!rel || !(rel.graph || rel.family || rel.lineage || rel.disease)) {
    return <p className={css.absent}>{t(REL.absent)}</p>;
  }

  return (
    <div className={css.wrap}>
      <p className={css.lede}>{t(REL.lede)}</p>

      {rel.graph?.length && (
        <Route
          title={t(REL.rGraph)}
          note={t(REL.nGraph)}
          meta={rel.graphTotal && rel.graphTotal > rel.graph.length
            ? fill(t(REL.showingOf), {
                shown: rel.graph.length, total: fmtInt(rel.graphTotal) })
            : undefined}
        >
          {rel.graph.map((n) => (
            <Chip key={n.gene} symbol={n.gene} onPick={onPick}
                  badge={n.shared > 1 ? `${n.shared}` : undefined}
                  title={fill(t(REL.sharedDiseases), { n: n.shared })} />
          ))}
        </Route>
      )}

      {rel.disease && (
        <Route
          title={t(REL.rDisease)}
          note={t(REL.nDisease)}
          subject={rel.disease.name}
          meta={fill(t(REL.geneCount), { n: rel.disease.size })}
        >
          {rel.disease.genes.map((g) => (
            <Chip key={g} symbol={g} onPick={onPick} />
          ))}
        </Route>
      )}

      {rel.family && (
        <Route
          title={t(REL.rFamily)}
          note={t(REL.nFamily)}
          subject={rel.family.name}
          meta={fill(t(REL.geneCount), { n: rel.family.size })}
        >
          {rel.family.genes.map((g) => (
            <Chip key={g} symbol={g} onPick={onPick} />
          ))}
        </Route>
      )}

      {rel.lineage && (
        <Route
          title={t(REL.rLineage)}
          note={t(REL.nLineage)}
          subject={rel.lineage.name}
          meta={fill(t(REL.geneCount), { n: rel.lineage.size })}
        >
          {rel.lineage.genes.map((g) => (
            <Chip key={g} symbol={g} onPick={onPick} />
          ))}
        </Route>
      )}
    </div>
  );
}

function Route(
  { title, note, subject, meta, children }:
  { title: string; note: string; subject?: string; meta?: string; children: React.ReactNode },
) {
  return (
    <section className={css.route}>
      <div className={css.routeHead}>
        <h4 className={css.routeTitle}>
          {title}
          {subject && <span className={css.subject}>{subject}</span>}
        </h4>
        {meta && <span className={css.meta}>{meta}</span>}
      </div>
      {/* The relation, said before the list. This is the line that stops the panel from
          being an unauditable similarity score with a layout. */}
      <p className={css.note}>{note}</p>
      <div className={css.chips}>{children}</div>
    </section>
  );
}

function Chip(
  { symbol, onPick, badge, title }:
  { symbol: string; onPick: (s: string) => void; badge?: string; title?: string },
) {
  return (
    <button type="button" className={css.chip} onClick={() => onPick(symbol)} title={title}>
      <span className={css.chipSym}>{symbol}</span>
      {badge && <span className={css.chipBadge}>{badge}</span>}
    </button>
  );
}
