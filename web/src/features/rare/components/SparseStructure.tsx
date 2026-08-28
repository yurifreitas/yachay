/** The gene graph as a sparse matrix, and the hypothesis it was built to test.
 *
 *  THE NULL IS THE PANEL. Any ordering improves locality on any sparse matrix, so "reordering
 *  helped" is not evidence of anything. The question is whether it helps a REAL biological
 *  graph more than a rewiring with the identical degree sequence — and that comparison is the
 *  only row in the table anyone should read first.
 *
 *  AND THE RESULT CUTS BOTH WAYS, SO BOTH ARE SHOWN AT THE SAME WEIGHT. Biology beats its null
 *  by about fifty points, which says the structure is real and exploitable. Reverse
 *  Cuthill-McKee — a bandwidth heuristic that predates the field and knows nothing about
 *  biology — still beats the community ordering. Reporting only the first would be reporting
 *  the half that flatters the hypothesis.
 */
import { interactomeSparse as s } from "../data/interactomeSparse";
import css from "./SparseStructure.module.css";

const pct = (v: number) => `${v >= 0 ? "+" : ""}${(v * 100).toFixed(1)}%`;
const ms = (v: number) => `${(v * 1000).toFixed(3)} ms`;
const nf = (v: number) => v.toLocaleString("en-US");

const ORDER_NOTE: Record<string, string> = {
  natural: "alphabetical by gene symbol — the order the file happened to be in",
  random: "the floor: any ordering that does not beat this is doing nothing",
  rcm: "reverse Cuthill–McKee, 1969, knows nothing about biology",
  degree: "hubs first — the cheapest heuristic there is",
  community: "Louvain communities kept contiguous — the thesis's own proposal",
};

export function SparseStructure() {
  const real = s.real;
  const nul = s.null;
  const orderings = Object.keys(real.orderings);

  return (
    <div className={css.root}>
      <p className={css.premise}>{s.premise}</p>

      <section className={css.hypothesis}>
        <span className={css.kicker}>The hypothesis, in the form that can fail</span>
        <p>{s.hypothesis}</p>
      </section>

      {/* ---- the two graphs, side by side ---------------------------------- */}
      <div className={css.sides}>
        {[real, nul].map((side, i) => (
          <section key={side.label} className={i === 0 ? css.sideReal : css.sideNull}>
            <h4 className={css.h4}>{side.label}</h4>
            <dl className={css.props}>
              <Row k="nodes" v={nf(side.structure.nodes)} />
              <Row k="nonzeros" v={nf(side.structure.nonzeros)} />
              <Row k="density" v={side.structure.density.toExponential(2)} />
              <Row k="modularity" v={side.structure.modularity.toFixed(3)} hot={i === 0} />
              <Row k="clustering" v={side.structure.clustering.toFixed(3)} hot={i === 0} />
              <Row k="communities" v={nf(side.structure.communities)} />
              <Row k="max degree" v={nf(side.structure.maxDegree)} />
              <Row k="degree skew" v={side.structure.degreeSkew?.toFixed(2) ?? "—"} />
              <Row k="power-law α (tail ≥ 3)" v={side.structure.powerLawAlpha?.toFixed(3) ?? "—"} />
              <Row k="components" v={nf(side.structure.components)} />
            </dl>
          </section>
        ))}
      </div>
      <p className={css.sideNote}>
        The rewiring keeps the degree sequence and destroys everything else: modularity falls
        from {real.structure.modularity.toFixed(3)} to {nul.structure.modularity.toFixed(3)} and
        clustering from {real.structure.clustering.toFixed(3)} to{" "}
        {nul.structure.clustering.toFixed(3)}. The power-law exponent barely moves, which is the
        point — degree skew alone is not the structure being tested.{" "}
        {s.nullFidelity.note} It lost{" "}
        {nf(s.nullFidelity.lostToSimplification)} of{" "}
        {nf(s.nullFidelity.requestedEdges)} edges.
      </p>

      {/* ---- the orderings ------------------------------------------------- */}
      <section className={css.panel}>
        <h4 className={css.h4}>Five orderings of the same matrix</h4>
        <div className={css.scrollX}>
          <table className={css.table}>
            <thead>
              <tr>
                <th>ordering</th>
                <th className={css.r}>bandwidth</th>
                <th className={css.r}>cache lines / row</th>
                <th className={css.r}>SpMV</th>
                <th className={css.r}>locality vs natural</th>
                <th className={css.r}>clock vs natural</th>
              </tr>
            </thead>
            <tbody>
              {orderings.map((name) => {
                const o = real.orderings[name];
                return (
                  <tr key={name} className={name === "natural" ? css.base : undefined}>
                    <td>
                      <span className={css.oName}>{name}</span>
                      <span className={css.oNote}>{ORDER_NOTE[name]}</span>
                    </td>
                    <td className={css.r}>{nf(o.bandwidth)}</td>
                    <td className={css.r}>{o.cacheLinesPerRow.toFixed(2)}</td>
                    <td className={css.r}>{ms(o.spmvSeconds)}</td>
                    <td className={o.cacheLineGainVsNatural > 0 ? css.good : css.bad}>
                      {pct(o.cacheLineGainVsNatural)}
                    </td>
                    <td className={o.spmvGainVsNatural > 0 ? css.good : css.bad}>
                      {pct(o.spmvGainVsNatural)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* ---- the comparison that decides it -------------------------------- */}
      <section className={css.panel}>
        <h4 className={css.h4}>The only comparison that decides anything</h4>
        <p className={css.sub}>
          Locality gain on the real graph against the same ordering on the degree-matched
          rewiring. The excess is what biological structure contributed; without this column,
          every number above is just a statement that sparse matrices like being reordered.
        </p>
        <div className={css.verdicts}>
          {s.verdict.map((v) => {
            const width = Math.min(100, Math.abs(v.excess) * 100 * 1.4);
            return (
              <div key={v.ordering} className={css.vRow}>
                <span className={css.vName}>{v.ordering}</span>
                <span className={css.vReal}>{pct(v.realGain)}</span>
                <span className={css.vNull}>{pct(v.nullGain)}</span>
                <span className={css.vTrack}>
                  <span className={v.biologyHelps ? css.vBar : css.vBarBad}
                        style={{ width: `${width}%` }} />
                </span>
                <span className={v.biologyHelps ? css.good : css.bad}>
                  {v.excess >= 0 ? "+" : ""}{(v.excess * 100).toFixed(1)} pts
                </span>
                <span className={css.vVerdict}>
                  {v.biologyHelps ? "biology helps" : "no biological excess"}
                </span>
              </div>
            );
          })}
        </div>
      </section>

      <section className={css.classical}>
        <span className={css.kicker}>And the half that does not flatter the hypothesis</span>
        <p>{s.versusClassical.says}</p>
      </section>

      <p className={css.finding}>{s.finding}</p>

      <p className={css.provenance}>
        Built with {s.uses.join(", ")} from {s.input}. {nf(s.graph.associations)} gene-disease
        associations over {nf(s.graph.diseases)} diseases, of which{" "}
        {nf(s.graph.diseasesWithTwoOrMoreGenes)} name two or more genes and therefore create an
        edge. Timings are the best of several runs on one machine — the minimum, because it is
        the least contaminated by scheduling noise, and one machine, because that is the honest
        scope of the claim.
      </p>
    </div>
  );
}

function Row({ k, v, hot }: { k: string; v: string; hot?: boolean }) {
  return (
    <div className={hot ? css.rowHot : css.row}>
      <dt>{k}</dt>
      <dd>{v}</dd>
    </div>
  );
}
