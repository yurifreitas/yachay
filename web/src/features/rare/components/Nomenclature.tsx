/** Names, and what they carry — the layer upstream of every statistic in this atlas.
 *
 *  This is not a humanities appendix. It closes a loop the data sections leave open:
 *
 *      a disease's NAME decides what a literature search finds
 *        → which decides what evidence is discoverable
 *          → which is the ascertainment bias measured at +0.236 next door
 *
 *  A disease renamed in 2022 has two literatures. A searcher who knows one name sees half
 *  the evidence, and the half they see is not a random half. That is a measurable
 *  consequence of an etymological fact, which is why the two sections belong together.
 */
import { nomenclature as n } from "../data/nomenclature";
import css from "./Nomenclature.module.css";

const FLAG = /DISPROVEN|ethical|racial|misdescrib/i;

export function Nomenclature() {
  return (
    <div className={css.root}>
      <div>
        <p className={css.premise}>
          {n.premise}
          <span className={css.chain}>
            <span className={css.chainStep}>a name</span>
            <span className={css.chainArrow}>→</span>
            <span className={css.chainStep}>what a search finds</span>
            <span className={css.chainArrow}>→</span>
            <span className={css.chainStep}>what evidence exists</span>
            <span className={css.chainArrow}>→</span>
            <span className={`${css.chainStep} ${css.chainEnd}`}>ascertainment bias +0.236</span>
          </span>
        </p>
      </div>

      {/* ---- taxonomy as stratigraphy --------------------------------------------- */}
      <section>
        <h4 className={css.eraName} style={{ marginBottom: "var(--sp-2)" }}>
          Six naming eras, all still in use at once
        </h4>
        <p className={css.story} style={{ maxWidth: "72ch", marginBottom: "var(--sp-6)" }}>
          Taxonomy is stratigraphic: every era left names behind and none of them were
          withdrawn. That is the real reason one disease carries four incompatible
          identifiers — MONDO, Orphanet, OMIM and ICD are not competing standards so much
          as sediment from different centuries.
        </p>
        <div className={css.eras}>
          {n.eras.map((e) => (
            <article key={e.id} className={css.era}>
              <span className={css.eraSpan}>{e.span}</span>
              <span className={css.eraName}>{e.name}</span>
              <span className={css.eraBasis}>{e.basis}</span>
              <span className={css.eraNote}>{e.note}</span>
            </article>
          ))}
        </div>
      </section>

      {/* ---- the reading key ------------------------------------------------------ */}
      <section>
        <h4 className={css.eraName} style={{ marginBottom: "var(--sp-2)" }}>
          Twelve word-parts that make most names readable
        </h4>
        <p className={css.story} style={{ maxWidth: "72ch", marginBottom: "var(--sp-4)" }}>
          Almost every term below is Greek or Latin compounding. Learning the parts turns a
          wall of nomenclature into something that can be parsed — and occasionally exposes
          the theory the name was built on.
        </p>
        <div className={css.roots}>
          {n.roots.map((r) => (
            <div key={r.part} className={css.root_}>
              <span className={css.part}>{r.part}</span>
              <span>
                <span className={css.means}>{r.means}</span>
                <br />
                <span className={css.origin}>{r.origin} · {r.example}</span>
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* ---- the cases ------------------------------------------------------------ */}
      <section>
        <h4 className={css.eraName} style={{ marginBottom: "var(--sp-2)" }}>
          {n.summary.cases} names, and what each one costs
        </h4>
        <p className={css.story} style={{ maxWidth: "76ch", marginBottom: "var(--sp-6)" }}>
          <strong>{n.summary.renamedForEthics}</strong> were renamed on ethical or racial
          grounds, <strong>{n.summary.namePreservesError}</strong> carry an error the field
          has since corrected, and one is a name for having no name at all.
        </p>
        <ul className={css.cases}>
          {n.names.map((c) => {
            const flagged = FLAG.test(c.verdict);
            return (
              <li key={c.id} className={`${css.case} ${flagged ? css.caseFlag : ""}`}>
                <div>
                  <div className={css.caseHead}>
                    <span className={css.caseName}>{c.current}</span>
                    <span className={`${css.verdict} ${flagged ? css.verdictWarn : ""}`}>
                      {c.verdict}
                    </span>
                  </div>
                  <p className={css.etym}>{c.etymology}</p>
                  <p className={css.story}>{c.story}</p>
                </div>
                <div>
                  <span className={css.consLabel}>What the name costs</span>
                  <p className={css.cons}>{c.consequence}</p>
                  <p className={css.confidence}>
                    confidence in the historical claim: {c.confidence}
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      </section>

      <p className={css.provenance}>
        <strong>Provenance.</strong> {n.provenance}
      </p>
    </div>
  );
}
