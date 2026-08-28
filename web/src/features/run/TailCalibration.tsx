/** How wrong the normal assumption is, at the threshold the shortlist actually uses.
 *
 *  THE RATIO LADDER IS THE WHOLE PANEL. A Kolmogorov-Smirnov p-value says a distribution is
 *  wrong; it says nothing about where. This ladder walks up the threshold and reports, at each
 *  step, how much control mass sits above the line against how much the normal predicts. It is
 *  flat at z = 1.5 and a factor of 130 at z = 4 — which means the failure lives entirely in the
 *  tail, and the tail is the only part of the distribution this project uses.
 *
 *  THE LAMBDA ROW IS A TRAP, DRAWN AS ONE. Genomic control is the reflex correction and it is
 *  the wrong one here: lambda comes out BELOW one, so dividing by it inflates every statistic
 *  and moves the count in the wrong direction. Applying a standard fix because it is standard
 *  is a specific way to be rigorous and wrong at the same time, and the panel shows the number
 *  it would have produced.
 */
import { tailCalibration as t } from "../../lib/data/tailCalibration";
import css from "./TailCalibration.module.css";

const fmtN = (v: number) => v.toLocaleString("en-US");
const sci = (v: number) => (v >= 0.001 ? v.toFixed(4) : v.toExponential(1));

export default function TailCalibration() {
  const maxRatio = Math.max(...t.tail.map((r) => r.ratio ?? 1));
  const best = t.fits[t.bestFit];
  const fitted = t.consequence[`fitted_${t.bestFit}`];

  return (
    <div className={css.wrap}>
      <p className={css.premise}>{t.premise}</p>

      {/* ---- which moment is wrong ------------------------------------------ */}
      <div className={css.moments}>
        <Moment k="Skewness" v={t.shape.skew.toFixed(2)}
                se={`${t.shape.skewInSEs} standard errors from zero`} />
        <Moment k="Excess kurtosis" v={t.shape.excessKurtosis.toFixed(2)}
                se={`${t.shape.kurtosisInSEs} standard errors out`} big />
        <Moment k="Controls measured" v={fmtN(t.controls)}
                se="genes that should score at zero" />
      </div>
      <p className={css.says}>{t.shape.says}</p>

      {/* ---- the ladder ------------------------------------------------------ */}
      <section className={css.ladder}>
        <h4 className={css.h4}>
          How much control mass sits above each line, against what the normal predicts
        </h4>
        <div className={css.rows}>
          {t.tail.map((r) => {
            const ratio = r.ratio ?? 1;
            return (
              <div key={r.z} className={css.row}>
                <span className={css.z}>z &gt; {r.z.toFixed(1)}</span>
                <span className={css.frac}>
                  <span className={css.obs}>{sci(r.observedFraction)}</span>
                  <span className={css.vs}>vs</span>
                  <span className={css.exp}>{sci(r.normalFraction)}</span>
                </span>
                <span className={css.track}>
                  <span className={css.ratioBar}
                        data-bad={ratio > 2}
                        style={{ width: `${(Math.log10(Math.max(ratio, 1)) / Math.log10(maxRatio)) * 100}%` }} />
                </span>
                <span className={ratio > 2 ? css.ratioBad : css.ratioOk}>
                  {ratio.toFixed(ratio > 10 ? 0 : 2)}&times;
                </span>
                <span className={css.inside}>
                  {r.normalInsideInterval ? "normal inside the interval" : "normal outside it"}
                  <span className={css.count}>{r.controlsAbove} controls</span>
                </span>
              </div>
            );
          })}
        </div>
        <p className={css.verdict}>{t.tailVerdict}</p>
      </section>

      {/* ---- the lambda trap -------------------------------------------------- */}
      <section className={css.trap}>
        <span className={css.kicker}>The standard fix, and why it is the wrong one here</span>
        <div className={css.lam}>
          <span className={css.lamV}>&lambda; = {t.lambda.value.toFixed(3)}</span>
          <p>{t.lambdaTrap}</p>
        </div>
      </section>

      {/* ---- what fits, and what it costs ------------------------------------- */}
      <section className={css.fits}>
        <h4 className={css.h4}>Three distributions fitted to the same controls</h4>
        <div className={css.fitRows}>
          {Object.entries(t.fits).map(([name, f]) => (
            <div key={name} className={f.best ? css.fitBest : css.fit}>
              <span className={css.fitName}>
                {name === "norm" ? "Normal" : name === "t" ? "Student-t" : "Skew-normal"}
                {f.best && <span className={css.badge}>best by AIC</span>}
              </span>
              <span className={css.fitAic}>
                {f.deltaAIC === 0 ? "reference" : `ΔAIC +${f.deltaAIC.toFixed(0)}`}
              </span>
              <span className={css.fitParams}>
                {Object.entries(f.params)
                  .map(([k, v]) => `${k} ${(v as number).toFixed(3)}`)
                  .join(" · ")}
              </span>
            </div>
          ))}
        </div>
        <p className={css.says}>
          A Student-t is what a normal becomes when the variance itself is uncertain — which is
          exactly the position a resampled null is in, so it is the candidate to reach for
          before it is the one that wins.
        </p>
      </section>

      {/* ---- the consequence -------------------------------------------------- */}
      <section className={css.cons}>
        <h4 className={css.h4}>What the shortlist looks like under each</h4>
        <table className={css.table}>
          <thead>
            <tr>
              <th>Tail model</th>
              <th className={css.r}>FDR 5%</th>
              <th className={css.r}>FDR 1%</th>
              <th className={css.r}>candidates at 1%</th>
              <th className={css.r}>controls rejected at 5%</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(t.consequence).map(([k, v]) => {
              const label = k === "standardNormal" ? "Standard normal — what this site used"
                : k === "genomicControl" ? "Genomic control — the wrong fix"
                : `Fitted ${t.bestFit === "t" ? "Student-t" : t.bestFit} — the defensible one`;
              return (
                <tr key={k} className={k.startsWith("fitted") ? css.best : undefined}>
                  <td>{label}</td>
                  <td className={css.r}>{fmtN(v.at05.total)}</td>
                  <td className={css.r}><strong>{fmtN(v.at01.total)}</strong></td>
                  <td className={css.r}>{fmtN(v.at01.candidates)}</td>
                  <td className={css.r}>{fmtN(v.at05.controls)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className={css.finding}>{t.finding}</p>
        <p className={css.says}>
          {fmtN(t.genesChangingStatus)} genes cross a Bonferroni line in one direction or the
          other between the two models. Under the fitted {t.bestFit === "t" ? "Student-t" : t.bestFit}{" "}
          the 1% list holds {fmtN(fitted.at01.candidates)} candidates against{" "}
          {fmtN(t.consequence.standardNormal.at01.candidates)} before, and the fit is worth{" "}
          {best.deltaAIC === 0 ? `${t.fits.norm.deltaAIC.toFixed(0)}` : ""} AIC over the normal.
        </p>
      </section>

      <p className={css.uses}>
        Fitted and tested with {t.uses.join(" and ")}. The moments carry the standard error of
        their own estimate so a number can be read against how precisely it is known, and the
        observed tail fractions carry Wilson intervals because above z = 4 the count is a
        handful of genes and a bare ratio would be a confident statement about noise.
      </p>
    </div>
  );
}

function Moment({ k, v, se, big }: { k: string; v: string; se: string; big?: boolean }) {
  return (
    <div className={big ? css.momentBig : css.moment}>
      <span className={css.mk}>{k}</span>
      <span className={css.mv}>{v}</span>
      <span className={css.ms}>{se}</span>
    </div>
  );
}
