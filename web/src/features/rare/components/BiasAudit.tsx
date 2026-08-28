/** What the catalogue is measuring, and what it is only measuring about itself.
 *
 *  A disease catalogue is a screen: entities carry aggregate scores estimated from a
 *  varying number of observations. That is this library's founding shape, so its argument
 *  applies to its own reference data — and declining to apply it there would be the most
 *  obvious failure available.
 *
 *  Six biases, each stated as a mechanism and then measured. The section exists because
 *  three of the five testable ones came out with **the opposite sign to the prediction**,
 *  and one of them contradicts a sentence this dashboard had already published. Those are
 *  reported here rather than quietly corrected upstream.
 */
import { bias } from "../data/bias";
import css from "./BiasAudit.module.css";

const pct = (v: number) => `${Math.round(v * 100)}%`;

export function BiasAudit() {
  const streetlight = bias.findings.find((f) => f.id === "streetlight");
  const bands = streetlight?.byBand ?? {};

  return (
    <div className={css.root}>
      <p className={css.premise}>
        {bias.premise} <strong>Three of the five testable biases came out with the opposite
        sign to the prediction.</strong> That is the reason to run the test rather than
        assert the mechanism.
      </p>

      {/* The correction goes first, because it is about this dashboard. */}
      <p className={css.correction}>
        <span className={css.correctionTag}>correction</span>
        The world-atlas section states &ldquo;<em>the rarer the disease, the less likely
        anyone knows what causes it</em>&rdquo;. <strong>Measured against Orphanet&rsquo;s own
        prevalence bands, that is backwards.</strong>{" "}
        {Object.entries(bands)
          .map(([b, v]) => `${b}: ${pct(v.share)}`)
          .join(" · ")}
        {" "}— the <em>rarer</em> bands have <strong>more</strong> genes known, not fewer,
        because an ultra-rare disease is usually ultra-rare <em>because</em> it is
        monogenic. The original claim compared the 770 ultra-rare against a whole-catalogue
        figure dominated by OMIM entries, which are mendelian by construction: a
        <strong> denominator fallacy</strong>, and one this project made.
      </p>

      <ul className={css.list}>
        {bias.findings.map((f) => (
          <li
            key={f.id}
            className={`${css.item} ${f.selfTest ? css.itemSelf : ""}`}
          >
            <div>
              <div className={css.head}>
                <span className={css.name}>{f.name}</span>
                <span className={`${css.verdict} ${css[f.verdict] ?? ""}`}>{f.verdict}</span>
                {f.selfTest && <span className={css.selfTag}>tests our own chart</span>}
              </div>
              <p className={css.mech}>{f.mechanism}</p>
            </div>

            <div className={css.right}>
              <span className={css.testLabel}>How it was tested</span>
              <p className={css.test}>{f.test}</p>
              <div className={css.statRow}>
                {f.statistic === null ? (
                  <span className={css.statNa}>not measurable</span>
                ) : (
                  <span className={css.stat}>
                    {typeof f.statistic === "number" && Math.abs(f.statistic) < 10
                      ? (f.statistic > 0 ? "+" : "") + f.statistic.toFixed(3)
                      : `${f.statistic}×`}
                  </span>
                )}
              </div>
              <span className={css.detail}>{f.detail}</span>

              {f.id === "streetlight" && (
                <div className={css.bands}>
                  {Object.entries(bands).map(([band, v]) => (
                    <div key={band} className={css.band}>
                      <span className={css.bandName}>{band}</span>
                      <span className={css.bandTrack}>
                        <span className={css.bandFill} style={{ width: pct(v.share) }} />
                      </span>
                      <span className={css.bandPct}>{pct(v.share)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
