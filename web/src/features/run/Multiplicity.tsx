/** From a calibrated z to a defensible cut — and the assumption test that decides which cut.
 *
 *  THE ASSUMPTION PANEL COMES FIRST ON PURPOSE. Everything downstream is a p-value, and every
 *  p-value here rests on the calibrated z being standard normal. The controls say it is not:
 *  the mean is 0.036 and the standard deviation 1.013, which is what a textbook pass looks
 *  like, and the distribution still fails Kolmogorov-Smirnov at 5.6e-05. First two moments
 *  right, shape wrong. Reporting mean and sd alone would have declared the calibration correct
 *  — and this project has spent a lot of pages arguing that a summary statistic can be right
 *  while the thing it summarises is not.
 *
 *  BOTH COLUMNS ARE SHOWN, INCLUDING THE ONE THAT RETURNS ZERO. The empirical route makes no
 *  distributional assumption and pays for it in resolution: with 781 controls no p can fall
 *  below 1/782, so at a 1% false discovery rate it rejects nothing at all. That is not a bug to
 *  be smoothed away with interpolation, it is what resampling against a finite control set can
 *  and cannot buy, and hiding it would be the more comfortable of two dishonest options.
 */
import { multiplicity as m } from "../../lib/data/multiplicity";
import css from "./Multiplicity.module.css";

const fmtN = (v: number) => v.toLocaleString("en-US");
const sci = (v: number) =>
  v === 0 ? "0" : v < 1e-3 ? v.toExponential(1) : v.toFixed(4);

export default function Multiplicity() {
  const a = m.assumption;
  const passes = a.verdict.startsWith("PASSES");
  const par = m.fdr.parametric;
  const emp = m.fdr.empirical;

  return (
    <div className={css.wrap}>
      <p className={css.premise}>{m.premise}</p>

      {/* ---- the assumption, tested ---------------------------------------- */}
      <section className={passes ? css.assumeOk : css.assumeBad}>
        <span className={css.kicker}>
          The assumption every p-value below rests on, tested against the controls
        </span>
        <p className={css.claim}>{a.claim}</p>

        <div className={css.tests}>
          <T k="Control mean" v={a.controlMean.toFixed(3)} s="should be 0" ok />
          <T k="Control sd" v={a.controlSd.toFixed(3)} s="should be 1" ok />
          <T k="Kolmogorov–Smirnov" v={sci(a.ksP)} s={`D = ${a.ksStatistic}`} ok={a.ksP > 0.01} />
          <T k="Cramér–von Mises" v={sci(a.cvmP)} s={`W² = ${a.cvmStatistic}`} ok={a.cvmP > 0.01} />
          {a.shapiroP !== null && (
            <T k="Shapiro–Wilk" v={sci(a.shapiroP)} s="on the control genes" ok={a.shapiroP > 0.01} />
          )}
        </div>

        <p className={css.matters}>{a.whyItMatters}</p>
        <p className={css.verdict}>{a.verdict}</p>
      </section>

      {/* ---- what a cut actually buys --------------------------------------- */}
      <div className={css.cols}>
        <Route name="Parametric" sub="upper tail of N(0,1) — the usual route, and the one the test above just failed"
               d={par} tone="warn" />
        <Route name="Empirical" sub={`fraction of the ${fmtN(m.empiricalResolution.controls)} controls at least as extreme — no distributional assumption`}
               d={emp} tone="ok" />
        <div className={css.route} data-tone="muted">
          <span className={css.routeName}>Naive threshold</span>
          <span className={css.routeSub}>|z| &gt; 3, which is what the shortlist used before this file existed</span>
          <div className={css.big}>
            <span className={css.bigV}>{fmtN(m.naive.zOver3)}</span>
            <span className={css.bigL}>genes past the line</span>
          </div>
          <dl className={css.dl}>
            <div><dt>Candidates among them</dt><dd>{fmtN(m.naive.zOver3Candidates)}</dd></div>
            <div><dt>Expected false, at this scale</dt><dd>{m.naive.expectedFalsePositives}</dd></div>
          </dl>
          <p className={css.routeNote}>{m.naive.says}</p>
        </div>
      </div>

      <p className={css.resolution}>
        <span className={css.kicker}>Why the empirical column rejects nothing at 1%</span>
        {m.empiricalResolution.says}
      </p>

      <p className={css.finding}>{m.finding}</p>

      <p className={css.uses}>
        Computed with {m.uses.join(" and ")}. Benjamini–Hochberg is four lines to write, and the
        four lines are where the off-by-one lives; a project whose argument is statistical care
        should not be hand-rolling the statistics it can import.
      </p>
    </div>
  );
}

function Route({ name, sub, d, tone }: {
  name: string; sub: string; tone: string;
  d: typeof m.fdr.parametric;
}) {
  return (
    <div className={css.route} data-tone={tone}>
      <span className={css.routeName}>{name}</span>
      <span className={css.routeSub}>{sub}</span>
      <div className={css.big}>
        <span className={css.bigV}>{fmtN(d.atFDR05)}</span>
        <span className={css.bigL}>at a 5% false discovery rate</span>
      </div>
      <dl className={css.dl}>
        <div><dt>Candidates among them</dt><dd>{fmtN(d.atFDR05Candidates)}</dd></div>
        <div><dt>At 1% instead</dt><dd>{fmtN(d.atFDR01)}</dd></div>
        <div>
          <dt>Estimated null fraction (π₀)</dt>
          <dd>{d.pi0.toFixed(3)} — about {fmtN(d.impliedNull)} genes</dd>
        </div>
        <div><dt>Controls wrongly rejected at 5%</dt><dd>{fmtN(d.controlsRejectedAt05)}</dd></div>
      </dl>
    </div>
  );
}

function T({ k, v, s, ok }: { k: string; v: string; s: string; ok: boolean }) {
  return (
    <div className={ok ? css.testOk : css.testBad}>
      <span className={css.tk}>{k}</span>
      <span className={css.tv}>{v}</span>
      <span className={css.ts}>{s}</span>
    </div>
  );
}
