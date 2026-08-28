/** The pipeline's own state, rendered.
 *
 *  WHY THIS IS THE FIRST THING ON THE METHOD PAGE. Every figure elsewhere on this site was
 *  produced by one of these stages, and the most useful fact about a figure is whether the
 *  stage that produced it is current. That was a terminal-only fact until now, which meant the
 *  dashboard rendered results while hiding whether they were still true.
 *
 *  A STALE STAGE IS DRAWN AS LOUDLY AS A FRESH ONE. Two of twelve are stale as this ships, and
 *  the reason is printed rather than summarised — the code that changed underneath them is
 *  named file by file, because "stale" without a cause is just a warning icon.
 */
import { pipeline as p } from "../../lib/data/pipeline";

const kb = (n: number) => (n >= 1024 ? Math.round(n / 1024) + " kB" : n + " B");

export default function PipelinePanel() {
  const s = p.summary;
  return (
    <div className="pipe">
      <div className="pipe-stats">
        <div><span className="pipe-k">Stages</span><span className="pipe-v num">{s.stages}</span></div>
        <div><span className="pipe-k">Fresh</span><span className="pipe-v num ok">{s.fresh}</span></div>
        <div><span className="pipe-k">Stale</span>
             <span className={"pipe-v num " + (s.stale ? "bad" : "ok")}>{s.stale}</span></div>
        <div><span className="pipe-k">Artifacts on disk</span>
             <span className="pipe-v num">{s.artifactsPresent}/{s.artifacts}</span></div>
      </div>

      <p className="pipe-rule"><strong>The rule.</strong> {p.rule}</p>

      <ol className="pipe-list">
        {p.stages.map((st, i) => (
          <li key={st.name} className={st.stale ? "pipe-stage stale" : "pipe-stage"}>
            <span className="pipe-n num">{String(i + 1).padStart(2, "0")}</span>
            <div className="pipe-body">
              <div className="pipe-head">
                <span className="pipe-name">{st.name}</span>
                <span className={st.stale ? "chip bad" : "chip ok"}>
                  {st.stale ? "stale" : "fresh"}
                </span>
                {st.needs.length > 0 && (
                  <span className="pipe-needs">after {st.needs.join(", ")}</span>
                )}
              </div>
              <p className="pipe-sum">{st.summary}</p>
              {st.stale && st.reason && <p className="pipe-why">{st.reason}</p>}
              <div className="pipe-io">
                {st.inputs.length > 0 && (
                  <div>
                    <span className="pipe-k">Reads</span>
                    <ul>
                      {st.inputs.map((x) => (
                        <li key={x.path} className={x.exists ? "" : "missing"}>
                          {x.path}{x.exists ? "" : " — missing"}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div>
                  <span className="pipe-k">Writes</span>
                  <ul>
                    {st.outputs.map((x) => (
                      <li key={x.path} className={x.exists ? "" : "missing"}>
                        {x.path}
                        {x.exists
                          ? <span className="pipe-meta num"> {kb(x.bytes)} · {x.written?.replace("T", " ")}</span>
                          : " — not produced"}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
