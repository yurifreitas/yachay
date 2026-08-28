/** Seven re-lookings at the same data, each borrowed from someone who changed how a field
 *  sees — and each one actually run.
 *
 *  THE RULE, enforced in `tools/dimensions.py` and repeated on the page: a name earns a
 *  place only if it yields a transform that runs on data already in this repository AND
 *  produces a different number than the default view. Two famous connections are listed as
 *  *omitted* rather than invoked, because naming them without running them is the
 *  decoration this section refuses.
 */
import { dimensions as d } from "../data/dimensions";
import css from "./Dimensions.module.css";

const nf = (v: number) => v.toLocaleString("en-US");

export function Dimensions() {
  const by = Object.fromEntries(d.dimensions.map((x) => [x.id, x]));

  return (
    <div className={css.root}>
      <p className={css.rule}>
        <strong>The rule for this section.</strong> {d.rule}
      </p>

      <ul className={css.list}>
        {/* --- Feynman ------------------------------------------------------------ */}
        <Dim x={by.feynman}>
          {(r) => {
            const tie = r.tiedButDifferent["2"];
            return (
              <>
                <div className={css.hero}>
                  <span className={css.heroN}>{tie ? `${tie.ratio}×` : "—"}</span>
                  <span className={css.heroUnit}>
                    spread in connection strength among {tie?.genes ?? 0} genes the
                    shortest-path view calls identical
                  </span>
                </div>
                <p className={css.findingText}>
                  The network tab reports <strong>hops</strong>: {tie?.genes ?? 0} genes sit
                  at two hops from a therapy and are therefore indistinguishable there.
                  Summing over <em>all</em> paths instead separates them — the strongest is{" "}
                  <strong>{r.strongest}</strong>, and a gene joined by one fragile route no
                  longer looks like one joined by a thicket. The shortest path is one
                  history.
                </p>
                <ul className={css.rows}>
                  {(Object.entries(r.tiedButDifferent) as [string, { genes: number; ratio: number }][]).map(([hops, v]) => (
                    <li key={hops} className={css.row}>
                      <span className={css.rowK}>{hops} hops · {v.genes} genes</span>
                      <span className={css.rowTrack}>
                        <span className={css.rowFill}
                              style={{ width: `${Math.min(100, (v.ratio - 1) * 160)}%` }} />
                      </span>
                      <span className={css.rowV}>{v.ratio}×</span>
                    </li>
                  ))}
                </ul>
              </>
            );
          }}
        </Dim>

        {/* --- Kimura -------------------------------------------------------------- */}
        <Dim x={by.kimura}>
          {(r) => (
            <>
              <div className={css.hero}>
                <span className={css.heroN}>{Math.round(r.neutralFraction * 100)}%</span>
                <span className={css.heroUnit}>
                  of the {nf(r.genesMeasured)} measured genes have no rare-disease
                  association at all
                </span>
              </div>
              <p className={css.findingText}>
                That is the field&rsquo;s own null, measured rather than assumed:{" "}
                <strong>{nf(r.genesWithAnyDisease)}</strong> genes carry every rare disease
                in the catalogue between them. {r.note}
              </p>
              <p className={css.findingText}>
                <strong>This number was 0.0% on the first run</strong> — a circular bug:
                the gene universe had been derived from the disease table, so every gene had
                a disease by construction. It is reported here because a null that comes out
                exactly zero should always be disbelieved before it is published.
              </p>
            </>
          )}
        </Dim>

        {/* --- Hawking ------------------------------------------------------------- */}
        <Dim x={by.hawking}>
          {(r) => (
            <>
              <div className={css.hero}>
                <span className={css.heroN}>{Math.round(r.shareAboveMean * 100)}%</span>
                <span className={css.heroUnit}>
                  of diseases are above the mean number of genes — the mean describes almost
                  nobody
                </span>
              </div>
              <p className={css.findingText}>
                Median <strong>{r.median}</strong>, mean <strong>{r.mean}</strong>, p95{" "}
                <strong>{r.p95}</strong>, maximum <strong>{r.max}</strong> across{" "}
                {nf(r.n)} diseases. A distribution this skewed has no useful centre, and any
                sentence of the form &ldquo;a rare disease has <em>n</em> genes&rdquo; is a
                sentence about the median while the tail runs to {r.max}.
              </p>
            </>
          )}
        </Dim>

        {/* --- Sidis --------------------------------------------------------------- */}
        <Dim x={by.sidis}>
          {(r) => (
            <>
              <div className={css.hero}>
                <span className={css.heroN}>{Math.round(r.highShare * 100)}%</span>
                <span className={css.heroUnit}>
                  of this project&rsquo;s hand-authored claims are marked high-confidence
                </span>
              </div>
              <p className={css.findingText}>
                {r.highConfidence} of {r.totalClaims} across the seeds. {r.ingestedInstead}
              </p>
              <ul className={css.rows}>
                {(r.audited as { source: string; highShare: number }[]).map((a) => (
                  <li key={a.source} className={css.row}>
                    <span className={css.rowK}>{a.source}</span>
                    <span className={css.rowTrack}>
                      <span className={css.rowFill}
                            style={{ width: `${Math.round(a.highShare * 100)}%` }} />
                    </span>
                    <span className={css.rowV}>{Math.round(a.highShare * 100)}%</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </Dim>

        {/* --- Lionel Penrose ------------------------------------------------------ */}
        <Dim x={by.penrose}>
          {(r) => (
            <>
              <div className={css.hero}>
                <span className={css.heroN}>{r.aggregatePercentUpperBound}%</span>
                <span className={css.heroUnit}>
                  of people, as an upper bound — the union of {nf(r.ultraRareEntities)}{" "}
                  individually negligible ultra-rare diseases
                </span>
              </div>
              <p className={css.findingText}>
                Roughly <strong>1 in {Math.round(100 / r.aggregatePercentUpperBound)}</strong>{" "}
                at the ceiling of each band. {r.note}
              </p>
            </>
          )}
        </Dim>

        {/* --- Weller -------------------------------------------------------------- */}
        <Dim x={by.weller}>
          {(r) => (
            <>
              <div className={css.hero}>
                <span className={css.heroN}>{r.cellTypes}</span>
                <span className={css.heroUnit}>
                  cell types on the axis, {nf(r.diseasesPlaceable)} diseases placed on them
                </span>
              </div>
              <p className={css.findingText}>{r.note}</p>
            </>
          )}
        </Dim>

        {/* --- McKusick ------------------------------------------------------------ */}
        <Dim x={by.mckusick}>
          {(r) => (
            <>
              <div className={css.hero}>
                <span className={css.heroN}>{Math.round(r.omimShare * 100)}%</span>
                <span className={css.heroUnit}>
                  of the catalogue is OMIM — an editorial structure, not a natural kind
                </span>
              </div>
              <p className={css.findingText}>{r.note}</p>
            </>
          )}
        </Dim>
      </ul>

      <div className={css.omitted}>
        <span className={css.omittedTitle}>Named as omitted, rather than invoked</span>
        {d.omitted.map((o) => (
          <p key={o.person} className={css.omittedItem}>
            <strong>{o.person}.</strong> {o.why}
          </p>
        ))}
      </div>
    </div>
  );
}

/* eslint-disable @typescript-eslint/no-explicit-any */
function Dim({ x, children }: { x: any; children: (r: any) => React.ReactNode }) {
  if (!x) return null;
  return (
    <li className={css.dim}>
      <div>
        <h4 className={css.person}>{x.person}</h4>
        <span className={css.label}>What they actually did</span>
        <p className={css.text}>{x.contribution}</p>
        <span className={css.label}>The transform</span>
        <p className={css.transform}>{x.transform}</p>
      </div>
      <div className={css.result}>{children(x.result)}</div>
    </li>
  );
}
