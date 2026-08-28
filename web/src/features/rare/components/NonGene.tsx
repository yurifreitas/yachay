/** What fills the gene slot when there is no gene.
 *
 *  THE MATRIX IS THE ARGUMENT, and it is drawn one COLUMN at a time rather than all at once.
 *  Ten causal classes against seven pipeline slots is seventy cells of prose; rendered as a
 *  grid it is unreadable, and unreadable is the same as absent. So the slot is chosen and the
 *  ten classes answer it side by side, with the gene's own answer pinned at the top as the
 *  reference row. That turns a table nobody would read into a comparison anyone can: pick
 *  "carrier", and the answers run from "a person, in every cell" to "a region of tissue" to
 *  "an occupation" to "nobody, the exposure is over".
 *
 *  THE PHENOCOPY PAIRS ARE THE FALSIFIABLE PART. Each names an enzyme, receptor or mark where
 *  the two causal routes converge, so a reader who thinks the equivalence is a metaphor has
 *  something specific to check.
 */
import { useMemo, useState } from "react";
import { nongene as ng } from "../data/nongene";
import { nongeneMeasured as mm } from "../data/nongeneMeasured";
import css from "./NonGene.module.css";

type View = "slots" | "mechanisms" | "phenocopies" | "measured";

const VIEWS: { id: View; label: string; sub: string }[] = [
  { id: "slots", label: "The equivalence", sub: "seven slots, ten answers each" },
  { id: "mechanisms", label: "Mechanisms", sub: "how each causal unit actually does damage" },
  { id: "phenocopies", label: "Phenocopy pairs", sub: "two causes, one clinical endpoint" },
  { id: "measured", label: "What the catalogue can record",
    sub: "the authored classes, checked against the annotations" },
];

export function NonGene() {
  const [view, setView] = useState<View>("slots");
  const [slot, setSlot] = useState(ng.slots[0]?.id ?? "unit");
  const [open, setOpen] = useState<string | null>(ng.classes[0]?.id ?? null);

  const active = useMemo(() => ng.slots.find((s) => s.id === slot), [slot]);
  const b = ng.blindSpot;

  return (
    <div className={css.root}>
      <p className={css.premise}>{ng.premise}</p>

      {/* The cost of the architecture, as a number rather than a caveat. */}
      <section className={css.blind}>
        <div className={css.blindNum}>
          <span className={css.blindV}>{b.withoutGene.toLocaleString("en-US")}</span>
          <span className={css.blindL}>
            of {b.diseases.toLocaleString("en-US")} catalogued diseases have no causal gene
          </span>
          <span className={css.blindPct}>{(b.fractionWithoutGene * 100).toFixed(1)}%</span>
        </div>
        <p className={css.blindSays}>{b.says}</p>

        {/* The number above is true and was over-claimed. Measuring it is what found that,
            so the correction sits with the claim rather than in a footnote. */}
        <div className={css.correction}>
          <span className={css.correctionL}>Correction, from measuring it</span>
          <p>{mm.geneLessBreakdown.says}</p>
          <div className={css.split}>
            <span className={css.splitItem}>
              <b>{mm.geneLessBreakdown.withMendelianInheritance.toLocaleString("en-US")}</b>
              annotated Mendelian &mdash; the gene is simply not found yet
            </span>
            <span className={css.splitItem}>
              <b>{mm.geneLessBreakdown.withNonMendelianInheritance.toLocaleString("en-US")}</b>
              annotated non-Mendelian
            </span>
            <span className={css.splitItem}>
              <b>{mm.geneLessBreakdown.withNoInheritanceAnnotation.toLocaleString("en-US")}</b>
              no inheritance annotation at all &mdash; curation, not biology
            </span>
          </div>
        </div>
      </section>

      <nav className={css.tabs} aria-label="Non-gene views">
        {VIEWS.map((v) => (
          <button key={v.id} type="button" onClick={() => setView(v.id)}
                  className={v.id === view ? css.tabOn : css.tab} aria-current={v.id === view}>
            <span>{v.label}</span>
            <span className={css.tabSub}>{v.sub}</span>
          </button>
        ))}
      </nav>

      {/* ---- SLOTS: one column of the matrix at a time ---------------------- */}
      {view === "slots" && (
        <div className={css.slotWrap}>
          <nav className={css.slotPick} aria-label="Choose a pipeline slot">
            {ng.slots.map((s) => (
              <button key={s.id} type="button" onClick={() => setSlot(s.id)}
                      className={s.id === slot ? css.slotOn : css.slot} aria-current={s.id === slot}>
                <span className={css.slotName}>{s.name}</span>
                <span className={css.slotGene}>{s.gene}</span>
              </button>
            ))}
          </nav>

          {active && (
            <div className={css.column}>
              <header className={css.colHead}>
                <h4 className={css.colTitle}>{active.name}</h4>
                <p className={css.colNote}>{active.note}</p>
                <p className={css.reference}>
                  <span className={css.refL}>When the cause is a gene</span> {active.gene}
                </p>
              </header>
              <ul className={css.answers}>
                {ng.classes.map((c) => (
                  <li key={c.id} className={c.id === "idiopathic" ? css.answerNone : css.answer}>
                    <span className={css.answerUnit}>{c.name}</span>
                    <span className={css.answerText}>{c.slots[active.id]}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* ---- MECHANISMS ---------------------------------------------------- */}
      {view === "mechanisms" && (
        <div className={css.mechList}>
          {ng.classes.map((c) => {
            const isOpen = open === c.id;
            return (
              <article key={c.id} className={isOpen ? css.mechOpen : css.mech}>
                <button type="button" className={css.mechHead} aria-expanded={isOpen}
                        onClick={() => setOpen(isOpen ? null : c.id)}>
                  <span className={css.mechName}>{c.name}</span>
                  <span className={css.mechOne}>{c.oneLine}</span>
                  <span className={css.chev} aria-hidden="true">{isOpen ? "–" : "+"}</span>
                </button>
                {isOpen && (
                  <div className={css.mechBody}>
                    <p className={css.mechText}>{c.mechanism}</p>
                    <p className={css.fails}>
                      <span className={css.failsL}>Why the gene pipeline misses it</span>{" "}
                      {c.whyGeneThinkingFails}
                    </p>
                    <ul className={css.examples}>
                      {c.examples.map((e) => <li key={e}>{e}</li>)}
                    </ul>
                    {c.confidence !== "high" && (
                      <p className={css.conf}>{c.confidence}</p>
                    )}
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}

      {/* ---- PHENOCOPIES --------------------------------------------------- */}
      {view === "phenocopies" && (
        <div className={css.pheno}>
          <p className={css.sub}>
            Each pair reaches the same clinical picture from two different causal units, and
            names the enzyme, receptor or mark where they meet. That naming is what makes the
            equivalence checkable rather than a figure of speech.
          </p>
          {ng.phenocopies.map((p) => (
            <article key={p.nonGene} className={css.pair}>
              <div className={css.pairTop}>
                <span className={css.side}>
                  <span className={css.sideL}>Not a gene</span>
                  <span className={css.sideV}>{p.nonGene}</span>
                </span>
                <span className={css.converge} aria-hidden="true">→</span>
                <span className={css.middle}>
                  <span className={css.sideL}>Converges on</span>
                  <span className={css.middleV}>{p.convergesOn}</span>
                </span>
                <span className={css.converge} aria-hidden="true">←</span>
                <span className={css.side}>
                  <span className={css.sideL}>A gene</span>
                  <span className={css.sideV}>{p.genetic}</span>
                </span>
              </div>
              <p className={css.pairMech}>{p.mechanism}</p>
            </article>
          ))}
        </div>
      )}

      {/* ---- MEASURED: the authored classes, checked ----------------------- */}
      {view === "measured" && (
        <div className={css.measured}>
          <p className={css.premise}>{mm.premise}</p>

          <section className={css.finding}>
            <span className={css.findingL}>What the measurement found</span>
            <p>{mm.finding}</p>
          </section>

          <section className={css.mBlock}>
            <h4 className={css.h4}>
              The {mm.summary.classesWithNoVocabulary} classes the catalogue has no term for
            </h4>
            <p className={css.sub}>
              Not a low count &mdash; no term. The inheritance vocabulary is a vocabulary of
              inheritance, so these causes have nowhere to be written down at all.
            </p>
            <div className={css.zeroGrid}>
              {mm.unmeasurable.map((u) => {
                const cls = ng.classes.find((c) => c.id === u.seedClass);
                return (
                  <div key={u.seedClass} className={css.zero}>
                    <span className={css.zeroN}>0</span>
                    <span className={css.zeroName}>{cls ? cls.name : u.seedClass}</span>
                    <p>{u.why}</p>
                  </div>
                );
              })}
            </div>
          </section>

          <section className={css.mBlock}>
            <h4 className={css.h4}>
              The {mm.summary.classesWithFootprint} classes that do have a footprint
            </h4>
            <p className={css.sub}>
              Counted from the inheritance annotations, and split by whether a causal gene is
              known &mdash; because a mosaic disease with a known gene is still a disease the
              standard blood-sampling pipeline misses.
            </p>
            <div className={css.mGrid}>
              {mm.measured.map((m) => {
                const cls = ng.classes.find((c) => c.id === m.seedClass);
                return (
                  <article key={m.seedClass} className={css.mCard}>
                    <header>
                      <span className={css.mN}>{m.diseases.toLocaleString("en-US")}</span>
                      <span className={css.mName}>{cls ? cls.name : m.seedClass}</span>
                    </header>
                    <div className={css.mSplit}>
                      <span>{m.withGene} with a gene</span>
                      <span>{m.geneLess} without</span>
                    </div>
                    <ul className={css.mTerms}>
                      {m.terms.map((t) => (
                        <li key={t.term}>{t.name} <span className={css.mTermId}>{t.term}</span></li>
                      ))}
                    </ul>
                    <p className={css.mEx}>{m.examples.slice(0, 3).join(" \u00b7 ")}</p>
                  </article>
                );
              })}
            </div>
          </section>

          <section className={css.mBlock}>
            <h4 className={css.h4}>
              The whole inheritance vocabulary, in use, ordered by how much of the catalogue
              it carries
            </h4>
            <p className={css.sub}>
              {mm.summary.vocabularyTerms} terms are actually used across{" "}
              {mm.scale.withInheritanceAnnotation.toLocaleString("en-US")} annotated diseases.
              Two of them carry almost all of it, which is the shape of the field rather than
              the shape of biology.
            </p>
            <div className={css.vocab}>
              {mm.vocabulary.map((v) => (
                <div key={v.term} className={css.vRow}>
                  <span className={css.vName}>{v.name}</span>
                  <span className={css.vTrack}>
                    <span
                      className={v.mendelian ? css.vBarM : css.vBarN}
                      style={{ width: Math.max(0.4, (v.diseases / mm.vocabulary[0].diseases) * 100) + "%" }}
                    />
                  </span>
                  <span className={css.vN}>{v.diseases.toLocaleString("en-US")}</span>
                  <span className={css.vKind}>
                    {v.mendelian ? "Mendelian" : v.seedClass ? "non-Mendelian" : "modifier"}
                  </span>
                </div>
              ))}
            </div>
          </section>

          <p className={css.provenance}>
            <strong>Sources.</strong> Computed directly from {mm.inputs.join(", ")} &mdash; the
            files the ingest already downloads. Re-running the tool re-derives every figure on
            this view, and a changed annotation release changes them.
          </p>
        </div>
      )}

      <section className={css.failures}>
        <h4 className={css.h4}>How a non-gene cause disappears inside a gene-keyed database</h4>
        <div className={css.failGrid}>
          {ng.failureModes.map((f) => (
            <div key={f.id} className={css.fail}>
              <span className={css.failName}>{f.name}</span>
              <p>{f.says}</p>
            </div>
          ))}
        </div>
      </section>

      <p className={css.provenance}>
        <strong>On this layer.</strong> {ng.provenance}
      </p>
    </div>
  );
}
