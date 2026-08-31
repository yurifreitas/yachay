import { useT } from "../../i18n";
import { ADD } from "../../i18n/addiction";
import { IntervalPlot } from "../../components/viz/organisms/IntervalPlot";
import raw from "../../data/generated/addiction_atlas.json";
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
