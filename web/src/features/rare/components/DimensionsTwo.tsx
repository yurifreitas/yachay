/** The half the first pass left out.
 *
 *  Seven transforms came out of `dimensions.py` and every one came from a man. That is not
 *  a sampling accident — it is what happens when you reach for the names that are famous
 *  rather than the ones whose work you are standing on. Sex chromosomes, X-inactivation,
 *  the trisomy-21 karyotype, the translocation-to-drug path, and the refusal that kept
 *  thalidomide out of one country are all load-bearing for a rare-disease atlas.
 *
 *  Same rule as before: a transform that runs on data already here, or an explicit mark
 *  that the point is historical rather than computational. Two entries carry that mark and
 *  are rendered differently, so a reader can see which is which without reading the code.
 */
import { dimensionsTwo as d2 } from "../data/dimensionsTwo";
import css from "./Dimensions.module.css";

const nf = (v: number) => v.toLocaleString("en-US");

export function DimensionsTwo() {
  return (
    <div className={css.root}>
      <p className={css.why}>
        <span className={css.whyTag}>why this section exists</span>
        {d2.why}
      </p>

      <ul className={css.list}>
        {d2.dimensions.map((x) => {
          const r = x.result as Record<string, any>;
          const computed = r.headline !== null && r.headline !== undefined;
          return (
            <li key={x.id + x.person} className={css.dim}>
              <div>
                <h4 className={css.person}>
                  {x.person}
                  <span className={css.years}>{x.years}</span>
                </h4>
                <span className={css.label}>What they actually did</span>
                <p className={css.text}>{x.contribution}</p>
                <span className={css.label}>The transform</span>
                <p className={css.transform}>{x.transform}</p>
              </div>

              <div className={css.result}>
                {computed ? (
                  <div className={css.hero}>
                    <span className={css.heroN}>
                      {typeof r.headline === "number" && r.headline < 1 && r.headline > 0
                        ? `${Math.round(r.headline * 100)}%`
                        : nf(r.headline)}
                    </span>
                    <span className={css.heroUnit}>{r.unit}</span>
                  </div>
                ) : (
                  <p className={css.notComputed}>{r.unit}</p>
                )}

                <p className={css.findingText}>{r.note}</p>
                {r.consequence && <p className={css.findingText}>{r.consequence}</p>}
                {r.link && <p className={css.findingText}><em>{r.link}</em></p>}

                {/* Stevens: the inheritance modes her chromosome sits inside. */}
                {x.id === "stevens" && r.byMode && (
                  <ul className={css.rows}>
                    {(Object.entries(r.byMode) as [string, number][])
                      .slice(0, 6)
                      .map(([mode, n]) => {
                        const max = Math.max(...(Object.values(r.byMode) as number[]));
                        return (
                          <li key={mode} className={css.row}>
                            <span className={css.rowK}>{mode}</span>
                            <span className={css.rowTrack}>
                              <span className={css.rowFill}
                                    style={{ width: `${Math.round((n / max) * 100)}%` }} />
                            </span>
                            <span className={css.rowV}>{nf(n)}</span>
                          </li>
                        );
                      })}
                  </ul>
                )}

                {/* Turing: the breadth distribution is the finding, not the median. */}
                {x.id === "turing_morph" && (
                  <ul className={css.rows}>
                    {([
                      ["narrowest gene", r.min],
                      ["25th percentile", r.p25],
                      ["median", r.headline],
                      ["75th percentile", r.p75],
                      ["broadest", r.max],
                    ] as [string, number][]).map(([k, v]) => (
                      <li key={k} className={css.row}>
                        <span className={css.rowK}>{k}</span>
                        <span className={css.rowTrack}>
                          <span className={css.rowFill}
                                style={{ width: `${Math.round((v / (r.max || 1)) * 100)}%` }} />
                        </span>
                        <span className={css.rowV}>{v}</span>
                      </li>
                    ))}
                    <li className={css.row}>
                      <span className={css.rowK}>in ≥100 cell types</span>
                      <span className={css.rowTrack}>
                        <span className={css.rowFill}
                              style={{ width: `${Math.round((r.broad / r.genes) * 100)}%` }} />
                      </span>
                      <span className={css.rowV}>{Math.round((r.broad / r.genes) * 100)}%</span>
                    </li>
                  </ul>
                )}

                {/* Nightingale: her denominator, made explicit. */}
                {x.id === "nightingale" && (
                  <p className={css.findingText}>
                    <strong>{nf(r.withoutGene)}</strong> of {nf(r.diseases)} catalogued
                    diseases have no causal gene — named, described, unexplained.
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
