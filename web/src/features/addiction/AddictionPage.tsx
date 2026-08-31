import { useT } from "../../i18n";
import { ADD } from "../../i18n/addiction";
import { IntervalPlot } from "../../components/viz/organisms/IntervalPlot";
import raw from "../../data/generated/addiction_atlas.json";
import cellsRaw from "../../data/generated/addiction_cells.json";
import { fmtInt } from "../../lib/scale";
import css from "./AddictionPage.module.css";

/** What the genetics of addiction actually measured.
 *
 *  WHY THIS IS NOT THE ANCESTRY QUESTION AGAIN. Two tools here already measure who was
 *  sequenced. Repeating that on substances would add a row rather than a finding. The question
 *  specific to this field is about WHAT was measured: "alcohol" heads hundreds of GWAS
 *  accessions, and those are studies of drinks per week, AUDIT scores, dependence, problematic
 *  use, and — the category this file had no name for until its own unclassified pile forced
 *  one — alcoholic hepatitis and cirrhosis.
 *
 *  Three different questions under one heading: who cannot stop, who drinks a lot, and whose
 *  liver fails. Their genetic architectures are known to differ, and the share of sample
 *  behind each is a number nobody had put on the page.
 */
/** The phenotype kinds, in the order they are stacked. Fixed here rather than derived from
 *  the data so the colours and the order do not change between substances — a stacked bar
 *  whose segments reorder cannot be compared across rows, which is the only thing it is for. */
const KINDS = [
  { id: "disorder", label: ADD.kDisorder },
  { id: "quantity", label: ADD.kQuantity },
  { id: "consequence", label: ADD.kConsequence },
  { id: "cessation", label: ADD.kCessation },
  { id: "response", label: ADD.kResponse },
  { id: "unclassified", label: ADD.kUnclassified },
];

export function AddictionPage() {
  const tt = useT();
  const d = raw as any;
  const subs: any[] = d.by_substance ?? [];
  const t = d.totals ?? {};
  const overall = d.disorder_share_overall ?? {};

  const rows = subs
    .filter((s) => s.disorder_share_of_sample?.share != null)
    .map((s) => ({
      label: s.substance,
      note: `${s.studies} studies · ${fmtInt(s.sample_summed_over_studies)} sample`,
      point: s.disorder_share_of_sample.share,
      lo: s.disorder_share_of_sample.ci95?.[0] ?? null,
      hi: s.disorder_share_of_sample.ci95?.[1] ?? null,
      ok: s.disorder_share_of_sample.share >= 0.5,
    }));

  return (
    <div className={css.page}>
      <header className={css.head}>
        <h1>{tt(ADD.title)}</h1>
        <p className={css.value}>
          {Math.round((overall.share ?? 0) * 100)}%
        </p>
        <p className={css.sub}>{d.says}</p>
      </header>

      <section className={css.block}>
        <span className={css.k}>{tt(ADD.bySubstance)}</span>
        <IntervalPlot
          rows={rows}
          xLabel="share of the reported sample behind a disorder phenotype"
          scale="linear"
          rowH={30}
          refs={[{ at: 0.5, label: "half", dashed: true }, { at: 1, label: "all of it" }]}
          format={(v) => `${Math.round(v * 100)}%`}
          ariaLabel="Share of each substance's GWAS sample that measures a disorder rather than a quantity"
          source={`${t.accessions} accessions · bootstrap over studies`}
          readAloud={
            <>
              One row per substance: how much of the sample behind its genetics is behind a
              phenotype that is actually a disorder, rather than how much or how often somebody
              uses. Nicotine is the extreme — the great majority of that sample measures smoking
              status and cigarettes per day, not dependence. The bands are bootstrap intervals
              over studies, so a substance carried by a handful of papers has a wide one and
              says so.
            </>
          }
        />
      </section>

      {/* THE FULL COMPOSITION, not just the disorder share. The headline number answers one
          question — how much is a disorder — and the artefact has measured four kinds. A
          stacked proportion is the right form for a part-of-whole with a fixed set of parts,
          and it shows the thing the single share hides: `consequence` is a third category,
          not a rounding error, and `unclassified` is published rather than folded into the
          others to make the bar look complete. */}
      <section className={css.block}>
        <span className={css.k}>{tt(ADD.compositionK)}</span>
        <div className={css.legend}>
          {KINDS.map((k) => (
            <span key={k.id} className={css.legendItem}>
              <span className={css.swatch} data-kind={k.id} />
              {tt(k.label)}
            </span>
          ))}
        </div>
        <div className={css.comp}>
          {subs.map((s) => {
            const by = s.people_by_kind ?? {};
            const total = Object.values(by).reduce((a: number, b: any) => a + b, 0) || 1;
            return (
              <div key={s.substance} className={css.compRow}>
                <span className={css.compLabel}>{s.substance}</span>
                <span className={css.compTrack}>
                  {KINDS.map((k) => {
                    const v = (by[k.id] ?? 0) / total;
                    if (v <= 0) return null;
                    return (
                      <span
                        key={k.id}
                        className={css.compSeg}
                        data-kind={k.id}
                        style={{ width: `${v * 100}%` }}
                        title={`${k.id}: ${Math.round(v * 100)}%`}
                      />
                    );
                  })}
                </span>
                <span className={css.compNote}>
                  {s.studies_by_kind?.disorder ?? 0}/{s.studies} {tt(ADD.studiesDisorder)}
                </span>
              </div>
            );
          })}
        </div>
        <p className={css.caveat}>{tt(ADD.compositionNote)}</p>
      </section>

      {/* WHO WAS SEQUENCED, per substance. Computed by the artefact and rendered nowhere until
          now — the failure docs/audit.md calls A29, committed again on new work. It belongs
          here rather than in the ancestry area because the answer differs by substance, and
          the reason it differs is biology: alcohol carries the highest East Asian share of
          any substance in this table, and the best-established protective variants in
          alcohol genetics are East-Asian-specific. */}
      <section className={css.block}>
        <span className={css.k}>{tt(ADD.ancestryK)}</span>
        <div className={css.comp}>
          {subs.filter((s) => s.ancestry?.by_weight?.length).map((s) => (
            <div key={s.substance} className={css.compRow}>
              <span className={css.compLabel}>{s.substance}</span>
              <span className={css.compTrack}>
                {s.ancestry.by_weight.slice(0, 6).map((a: any, i: number) => (
                  <span
                    key={a.ancestry}
                    className={css.compSeg}
                    data-anc={i}
                    style={{ width: `${a.share * 100}%` }}
                    title={`${a.ancestry}: ${Math.round(a.share * 100)}%`}
                  />
                ))}
              </span>
              <span className={css.compNote}>
                {Math.round((s.ancestry.european_share ?? 0) * 100)}% {tt(ADD.european)}
                {" · "}
                {s.ancestry.african_majority_analyses ?? 0} {tt(ADD.africanMajority)}
              </span>
            </div>
          ))}
        </div>
        <p className={css.caveat}>{tt(ADD.ancestryNote)}</p>
      </section>

      <section className={css.block}>
        <span className={css.k}>{tt(ADD.scaleK)}</span>
        <div className={css.pair}>
          {subs.slice(0, 6).map((s) => (
            <div key={s.substance} className={css.stat}>
              <span className={css.statVal}>{fmtInt(s.sample_summed_over_studies)}</span>
              <span className={css.statK}>
                <strong>{s.substance}</strong> — {s.studies} {tt(ADD.studies)}
              </span>
            </div>
          ))}
        </div>
        {/* The double-count warning belongs beside the number, not in a footnote. */}
        <p className={css.caveat}>{t.why_that_name}</p>
      </section>

      {(cellsRaw as any).disorder_versus_quantity?.length > 0 && (
        <section className={css.block}>
          <span className={css.k}>{tt(ADD.cellsK)}</span>
          <p className={css.body}>{(cellsRaw as any).says}</p>

          {/* Two lists per substance, side by side, with what they share between them. A
              Jaccard of zero is the kind of number a reader should be able to check by
              looking, and the only way to make that possible is to print both sets. */}
          <div className={css.cells}>
            {(cellsRaw as any).disorder_versus_quantity.map((s: any) => (
              <div key={s.substance} className={css.cellRow}>
                <div className={css.cellHead}>
                  <strong>{s.substance}</strong>
                  <span className={css.jac}>
                    {tt(ADD.shared)} {s.shared.length}/
                    {new Set([...s.disorder_cells, ...s.quantity_cells]).size}
                  </span>
                </div>
                <div className={css.cellCols}>
                  <div>
                    <span className={css.cellK}>{tt(ADD.disorderCells)}</span>
                    <ul>
                      {s.disorder_cells.length
                        ? s.disorder_cells.slice(0, 6).map((c: string) => (
                            <li key={c} className={s.shared.includes(c) ? css.both : undefined}>{c}</li>
                          ))
                        : <li className={css.none}>{tt(ADD.noneSurvive)}</li>}
                    </ul>
                  </div>
                  <div>
                    <span className={css.cellK}>{tt(ADD.quantityCells)}</span>
                    <ul>
                      {s.quantity_cells.length
                        ? s.quantity_cells.slice(0, 6).map((c: string) => (
                            <li key={c} className={s.shared.includes(c) ? css.both : undefined}>{c}</li>
                          ))
                        : <li className={css.none}>{tt(ADD.noneSurvive)}</li>}
                    </ul>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {/* THE ENRICHMENTS THEMSELVES. The overlap counts above say the two halves differ;
              this says what each one actually found, with the fold over its matched null and
              the corrected q beside it. Without them a reader has to take "these cells" on
              trust, which is the thing this site is against. */}
          <div className={css.enrich}>
            {(cellsRaw as any).by_set
              .filter((r: any) => ["disorder", "quantity"].includes(r.kind)
                && r.top.some((e: any) => e.survives_fdr))
              .slice(0, 8)
              .map((r: any) => (
                <div key={`${r.substance}-${r.kind}`} className={css.enrichSet}>
                  <span className={css.enrichHead}>
                    <strong>{r.substance}</strong> · {r.kind} · {r.genes} {tt(ADD.genes)}
                  </span>
                  <table className={css.table}>
                    <thead>
                      <tr>
                        <th>{tt(ADD.cellType)}</th>
                        <th>{tt(ADD.genesIn)}</th>
                        <th>{tt(ADD.expected)}</th>
                        <th>{tt(ADD.fold)}</th>
                        <th>q</th>
                      </tr>
                    </thead>
                    <tbody>
                      {r.top.filter((e: any) => e.survives_fdr).slice(0, 5).map((e: any) => (
                        <tr key={e.cell_type}>
                          <td className={css.tdName}>{e.cell_type}</td>
                          <td>{e.genes}</td>
                          <td className={css.tdMuted}>{e.null_mean}</td>
                          <td><strong>{e.fold}&times;</strong></td>
                          <td className={css.tdMuted}>{e.q}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
          </div>

          <p className={css.caveat}>{(cellsRaw as any).control}</p>
          <p className={css.caveat}>{(cellsRaw as any).no_z}</p>
        </section>
      )}

      <section className={css.block}>
        <span className={css.k}>{tt(ADD.filterK)}</span>
        <p className={css.body}>{d.classification_is_authored}</p>
        <div className={css.pair}>
          <div className={css.stat}>
            <span className={css.statVal}>{t.excluded_as_not_about_the_substance}</span>
            <span className={css.statK}>{tt(ADD.excluded)}</span>
          </div>
          <div className={css.stat}>
            <span className={css.statVal}>{t.unclassified}</span>
            <span className={css.statK}>{tt(ADD.unclassified)}</span>
          </div>
        </div>
        <ul className={css.examples}>
          {(t.excluded_examples ?? []).slice(0, 4).map((x: string) => (
            <li key={x}><span className={css.x}>excluded</span> {x}</li>
          ))}
          {(t.unclassified_examples ?? []).slice(0, 3).map((x: string) => (
            <li key={x}><span className={css.q}>unclassified</span> {x}</li>
          ))}
        </ul>
      </section>

      <section className={css.block}>
        <span className={css.k}>{tt(ADD.fitK)}</span>
        <p className={css.caveat}>{d.fit_test?.verdict}</p>
      </section>
    </div>
  );
}
