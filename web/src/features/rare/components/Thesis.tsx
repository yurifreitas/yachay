/** The argument the measurements serve — with its register intact and its coverage audited.
 *
 *  THREE VIEWS, and the third is the one that matters.
 *
 *    The ladder     genotype to patient, one rung per scale, each saying what changes there
 *                   and whether this repository has anything at that height.
 *    The insights   eighteen claims, each carrying whether it is a founded claim or an open
 *                   research hypothesis, and whether anything here implements it.
 *    The register   what is established, what is still a hypothesis, and which metaphors are
 *                   being kept as metaphors on purpose.
 *
 *  WHY BUILD STATUS IS DRAWN AS PROMINENTLY AS THE CLAIM. A page that lists an ambitious
 *  architecture and lets the reader assume it exists is a brochure. Six of the eighteen
 *  insights here are marked "named, not built" and three are absent outright; showing that at
 *  the same weight as the claim is what makes the rest of the page worth believing.
 */
import { useMemo, useState } from "react";
import { thesis as t } from "../data/thesis";
import css from "./Thesis.module.css";

type View = "ladder" | "insights" | "register";

const VIEWS: { id: View; label: string; sub: string }[] = [
  { id: "ladder", label: "The ladder", sub: "genotype to patient, and where the repo reaches" },
  { id: "insights", label: "The claims", sub: "eighteen, each with its register and its status" },
  { id: "register", label: "Founded, hypothesis, metaphor", sub: "the separation, kept" },
];

/** Build status is a fact about this repository, so it gets status colour and always its word. */
const STATUS: Record<string, { cls: string; label: string }> = {
  built: { cls: "good", label: "built" },
  partial: { cls: "warn", label: "partial" },
  "named-only": { cls: "serious", label: "named, not built" },
  absent: { cls: "muted", label: "absent" },
};

const REGISTER_LABEL: Record<string, string> = {
  founded: "founded claim",
  hypothesis: "open hypothesis",
  metaphor: "metaphor",
};

export function Thesis() {
  const [view, setView] = useState<View>("ladder");
  const [open, setOpen] = useState<number | null>(null);
  const byStatus = useMemo(() => t.summary.insightsByStatus, []);
  const s = t.summary;

  return (
    <div className={css.root}>
      <p className={css.premise}>{t.premise}</p>

      <section className={css.oneLine}>
        <span className={css.oneLineL}>The thesis in one line</span>
        <p className={css.oneLineV}>{t.oneLine}</p>
        <p className={css.deepest}>{t.deepest}</p>
      </section>

      <div className={css.counts}>
        <Stat v={String(s.foundedClaims)} l="founded claims" s="established in their fields" />
        <Stat v={String(s.openHypotheses)} l="open hypotheses"
              s="research questions, not results" />
        <Stat v={String(s.metaphorsRetired)} l="metaphors kept as metaphors"
              s="including two the author retired outright" />
        <Stat v={`${byStatus["named-only"] ?? 0} + ${byStatus.absent ?? 0}`}
              l="claims not implemented here"
              s={`of ${s.insights} — named or absent, said plainly`} />
      </div>

      <nav className={css.tabs} aria-label="Thesis views">
        {VIEWS.map((v) => (
          <button key={v.id} type="button" onClick={() => setView(v.id)}
                  className={v.id === view ? css.tabOn : css.tab} aria-current={v.id === view}>
            <span>{v.label}</span>
            <span className={css.tabSub}>{v.sub}</span>
          </button>
        ))}
      </nav>

      {/* ---- THE LADDER ---------------------------------------------------- */}
      {view === "ladder" && (
        <div className={css.ladder}>
          <p className={css.sub}>
            One rung per scale. Each says what actually changes at that height, what this
            repository holds there, and — where it holds nothing — what is missing. The rungs
            are numbered because they genuinely are ordered: a perturbation enters at the top
            and every rung below is downstream of it.
          </p>
          {t.scales.map((r, i) => {
            const st = STATUS[r.status] ?? STATUS.absent;
            return (
              <article key={r.id} className={css.rung}>
                <span className={css.rungN}>{String(i + 1).padStart(2, "0")}</span>
                <span className={css.spine} aria-hidden="true" />
                <div className={css.rungBody}>
                  <header className={css.rungHead}>
                    <h4 className={css.rungName}>{r.name}</h4>
                    <span className={css.unit}>unit: {r.unit}</span>
                    <span className={`${css.pill} ${css[st.cls]}`}>{st.label}</span>
                  </header>
                  <p className={css.changes}>{r.whatChanges}</p>
                  <p className={css.artifact}>
                    <span className={css.label}>In this repository</span> {r.repoArtifact}
                  </p>
                  {r.gap && (
                    <p className={css.gap}>
                      <span className={css.gapL}>Gap</span> {r.gap}
                    </p>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}

      {/* ---- THE CLAIMS ---------------------------------------------------- */}
      {view === "insights" && (
        <div className={css.claims}>
          {t.insights.map((c) => {
            const st = STATUS[c.status] ?? STATUS.absent;
            const isOpen = open === c.n;
            return (
              <article key={c.n} className={isOpen ? css.claimOpen : css.claim}>
                <button type="button" className={css.claimHead} aria-expanded={isOpen}
                        onClick={() => setOpen(isOpen ? null : c.n)}>
                  <span className={css.claimN}>{String(c.n).padStart(2, "0")}</span>
                  <span className={css.claimTitle}>{c.title}</span>
                  <span className={c.register === "founded" ? css.regFounded : css.regHypothesis}>
                    {REGISTER_LABEL[c.register]}
                  </span>
                  <span className={`${css.pill} ${css[st.cls]}`}>{st.label}</span>
                </button>
                {isOpen && (
                  <div className={css.claimBody}>
                    <p className={css.statement}>{c.statement}</p>
                    <p className={css.note}>
                      <span className={css.label}>Status here</span> {c.note}
                    </p>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}

      {/* ---- THE REGISTER -------------------------------------------------- */}
      {view === "register" && (
        <div className={css.regWrap}>
          <p className={css.sub}>
            The separation below is the author&rsquo;s own, and the argument for keeping it is
            that it <em>strengthens</em> the project. A thesis that marks its own speculation is
            harder to dismiss than one that does not.
          </p>

          <section className={css.regBlock} data-kind="founded">
            <h4 className={css.h4}>Established in their fields</h4>
            <p className={css.regNote}>
              None of this has to be invented for the project to be worth doing. The novelty is
              in the composition, not in the components.
            </p>
            <ul className={css.regList}>
              {t.register.founded.map((x) => <li key={x}>{x}</li>)}
            </ul>
          </section>

          <section className={css.regBlock} data-kind="hypothesis">
            <h4 className={css.h4}>Open research hypotheses</h4>
            <p className={css.regNote}>
              Stated as questions because that is what they are. Each could turn out false
              without damaging the rest.
            </p>
            <ul className={css.regList}>
              {t.register.hypothesis.map((x) => <li key={x}>{x}</li>)}
            </ul>
          </section>

          <section className={css.regBlock} data-kind="metaphor">
            <h4 className={css.h4}>Metaphors, kept as metaphors</h4>
            <p className={css.regNote}>
              Useful for thinking and not for claiming. Two of these the author retired outright
              once the vocabulary turned out not to exist in the literature — which is the
              behaviour that makes the rest of the register credible.
            </p>
            <ul className={css.regList}>
              {t.register.metaphor.map((x) => <li key={x}>{x}</li>)}
            </ul>
          </section>

          <section className={css.supplied}>
            <h4 className={css.h4}>Supplied by the author, not verified here</h4>
            <p className={css.regNote}>
              Context the author brought, kept separate from anything this repository measured.
              Nothing below was checked by any file in this project.
            </p>
            <div className={css.supGrid}>
              {t.supplied.map((x) => (
                <div key={x.claim} className={css.sup}>
                  <p className={css.supClaim}>{x.claim}</p>
                  <p className={x.status.includes("NOT VERIFIED") ? css.supUnver : css.supOk}>
                    {x.status}
                  </p>
                </div>
              ))}
            </div>
          </section>

          <section className={css.theses}>
            <div>
              <span className={css.label}>The scientific thesis</span>
              <p>{t.thesisScientific}</p>
            </div>
            <div>
              <span className={css.label}>The computational thesis underneath it</span>
              <p>{t.thesisComputational}</p>
            </div>
          </section>

          <section className={css.arch}>
            <h4 className={css.h4}>The architecture, and the loop it closes</h4>
            <div className={css.archList}>
              {t.architecture.map((a) => (
                <div key={a.layer} className={css.archRow}>
                  <span className={css.archName}>{a.layer}</span>
                  <span className={css.archHolds}>{a.holds}</span>
                  <span className={css.archNote}>{a.note}</span>
                </div>
              ))}
            </div>
            <div className={css.loop}>
              {t.loop.map((step, i) => (
                <span key={step} className={css.loopStep}>
                  {step}
                  {i < t.loop.length - 1 && <span className={css.loopArrow} aria-hidden="true">→</span>}
                </span>
              ))}
              <span className={css.loopBack} aria-hidden="true">↺</span>
            </div>
          </section>
        </div>
      )}

      <p className={css.provenance}>
        <strong>On this layer.</strong> {t.provenance}
      </p>
    </div>
  );
}

function Stat({ v, l, s }: { v: string; l: string; s: string }) {
  return (
    <div className={css.stat}>
      <span className={css.statV}>{v}</span>
      <span className={css.statL}>{l}</span>
      <span className={css.statS}>{s}</span>
    </div>
  );
}
