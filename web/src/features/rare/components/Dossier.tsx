/** One disease, assembled from every source the atlas ingests — and nothing invented.
 *
 *  WHAT IS HERE AND WHERE IT COMES FROM
 *    identity, signs, inheritance   HPO annotations + hp.obo
 *    genes                          HPO gene-to-disease
 *    prevalence, onset age          Orphanet
 *    cell axis                      Human Protein Atlas single-cell
 *    current state                  ClinicalTrials.gov, queried live and cached
 *
 *  WHAT IS DELIBERATELY ABSENT. No severity score, no burden index, no composite. Those
 *  need value judgements this project has no basis for, and inventing one would be the
 *  fabrication the whole atlas argues against. Human impact appears as onset age, sign
 *  frequency WITH its denominator, and trial activity. The reader does the weighing.
 *
 *  WHAT THIS PANEL SHOWS IS HOW MUCH IS KNOWN, NOT HOW OFTEN IT HAPPENS. It used to draw
 *  one bar per sign, and for Duchenne it drew FOURTEEN IDENTICAL BARS reading "1/1 ·
 *  21%–100%" — because every quantified sign of Duchenne in HPO comes from a single
 *  patient. A 100% point estimate on n=1 with an interval covering four fifths of the
 *  scale is not a measurement, and rendering it like one was this dashboard committing
 *  the exact error the rest of the project exists to catch.
 *
 *  So the encoding is the EVIDENCE GRADE, computed in tools/dossier.py:
 *
 *    quantified   a fraction with a real denominator  -> a bar, with its Wilson interval
 *    single-case  a fraction of one patient           -> NO bar. A chip saying "1 patient"
 *    class        an unquantified frequency class     -> a hatched band spanning its range
 *    none         no frequency recorded at all        -> listed, not hidden
 *
 *  A single-case sign gets no bar on purpose. There is no length that honestly represents
 *  it: its interval is almost the whole axis, and drawing that as a full-width bar reads
 *  as certainty about a symptom that is universal rather than as one case report.
 */
import { useMemo, useState } from "react";
import { dossiers as data } from "../data/dossiers";
import { barriers as bar } from "../data/barriers";
import { evidenceAtlas as field } from "../data/evidenceAtlas";
import { wilson } from "../evidence";
import type { Evidence } from "../dossierModel";
import css from "./Dossier.module.css";

const nf = (v: number) => v.toLocaleString("en-US");
const pct = (v: number) => `${Math.round(v * 100)}%`;

/** HPO frequency classes, as the ranges they actually are. */
const CLASS_RANGE: Record<string, [number, number]> = {
  Obligate: [1, 1],
  "Very frequent": [0.8, 0.99],
  Frequent: [0.3, 0.79],
  Occasional: [0.05, 0.29],
  "Very rare": [0.01, 0.04],
  Excluded: [0, 0],
};

/** The four grades, in the order they are worth trusting. Labels are short because they
 *  appear as filter chips; the long-form definition ships on the record itself
 *  (`evidenceGrades`) and is shown as the title attribute rather than invented here. */
const GRADES: { id: Evidence; label: string }[] = [
  { id: "quantified", label: "Estimated from a series" },
  { id: "single-case", label: "One patient" },
  { id: "class", label: "A class, no denominator" },
  { id: "none", label: "No frequency at all" },
];

export function Dossier() {
  const [pick, setPick] = useState(0);
  // Which evidence grades are visible. All four by default: the whole argument of this
  // panel is that the weak grades are the majority, and defaulting to the strong ones
  // would hide the finding behind a filter.
  const [grades, setGrades] = useState<Set<Evidence>>(
    () => new Set(GRADES.map((g) => g.id))
  );
  const d = data.dossiers[pick];

  const signs = useMemo(() => {
    if (!d) return [];
    return d.signs.map((s) => {
      // A denominator counts as one only above 1. `n = 1` still has arithmetic — the
      // Wilson interval is computed and shown — but it never becomes a bar.
      const hasN = s.evidence === "quantified";
      const [lo, hi] =
        s.n && s.k !== null && s.k !== undefined
          ? wilson(s.k as number, s.n as number)
          : [null, null];
      // An HPO frequency CLASS is a range: "Frequent" means 30-79%. Drawing its floor as a
      // solid bar made every such sign look identical, which is what the rendered page
      // showed. A class now draws as a hatched BAND spanning its range, so a wide band
      // reads as "we barely know" rather than as a value.
      const band = !hasN && s.frequency ? CLASS_RANGE[s.frequency] : undefined;
      return { ...s, lo, hi, hasN, band };
    });
  }, [d]);

  const visible = useMemo(
    () => signs.filter((sg) => grades.has(sg.evidence)),
    [signs, grades]
  );

  if (!d) return null;
  const t = d.trials;
  const topStatuses = Object.entries(t.byStatus).slice(0, 5);

  return (
    <div className={css.root}>
      {/* ---- picker ---------------------------------------------------------- */}
      <nav className={css.picker} aria-label="Choose a disease">
        {data.dossiers.map((x, i) => (
          <button
            key={x.orpha || x.name}
            type="button"
            className={i === pick ? css.pickOn : css.pick}
            onClick={() => setPick(i)}
            aria-current={i === pick}
          >
            <span>{x.name}</span>
            <span className={css.pickMeta}>
              {x.geneCount} gene{x.geneCount === 1 ? "" : "s"} ·{" "}
              {x.trials.recruitingCount} recruiting
            </span>
          </button>
        ))}
      </nav>

      {/* ---- record ---------------------------------------------------------- */}
      <article className={css.record}>
        <header>
          <h4 className={css.title}>{d.name}</h4>
          <div className={css.ids}>
            {d.orpha && <span className={css.id}>{d.orpha}</span>}
            {d.omim && <span className={css.id}>{d.omim}</span>}
            {d.inheritance.map((i) => <span key={i} className={css.id}>{i}</span>)}
          </div>
        </header>

        <div className={css.tiles}>
          <Tile label="Causal genes" value={nf(d.geneCount)}
                sub={d.genes.slice(0, 6).join(", ") + (d.genes.length > 6 ? " …" : "")} />
          <Tile
            label="Prevalence, rarest band on record"
            value={d.rarestBand ?? "not stated"}
            sub={
              d.prevalenceBands > 1
                ? `and ${d.prevalenceBands - 1} other band${d.prevalenceBands > 2 ? "s" : ""} — see below`
                : `${d.prevalenceRecords} record${d.prevalenceRecords === 1 ? "" : "s"}, one band`
            }
          />
          <Tile label="Onset" value={d.onsetAges[0] ?? "not stated"}
                sub={d.onsetAges.slice(1).join(" · ") || "Orphanet age-of-onset record"} />
          <Tile label="Signs recorded" value={nf(d.signCount)}
                sub={`${d.signsWithDenominator} carry a denominator`} />
          <Tile label="Trials on record" value={nf(t.total)}
                sub={`${t.recruitingCount} recruiting or about to`} />
        </div>

        {d.naming.lostToTheName > 0 && (
          <p className={css.naming}>
            <strong>The name costs {nf(d.naming.lostToTheName)} trials.</strong> Querying the
            registry with the catalogue&rsquo;s formal name,{" "}
            <em>{d.naming.catalogueName}</em>, returns{" "}
            <strong>{nf(d.naming.catalogueHits)}</strong> studies. Querying it with{" "}
            <em>{d.naming.registryName}</em> returns{" "}
            <strong>{nf(d.naming.registryHits)}</strong>. Same disease, same registry,
            different word — this is the two-literatures claim from the naming tab, as a
            live number rather than an argument.
          </p>
        )}

        {/* THE PREVALENCE SPREAD. This block exists because the tile above used to be a
            single band beside an unrelated list of countries, and for Duchenne that meant
            the page displayed "1-9 / 1 000 000 · Canada · Denmark · Egypt" — a band
            reported only by South Africa, next to a country that reported a rate two
            orders of magnitude higher. The bands and their places are now paired at the
            source, so the disagreement is the thing on screen. */}
        {d.prevalenceSpread.length > 1 && (
          <section className={css.spread}>
            <div className={css.spreadHead}>
              <h4 className={css.h4}>
                Recorded at {d.prevalenceBands} different rates, depending on who was counted
              </h4>
              <p className={css.sub}>
                {nf(d.prevalenceRecords)} Orphanet prevalence records spanning{" "}
                <strong>{d.prevalenceSpanBands}</strong> bands. This disorder is one of the{" "}
                <strong>386 of 525</strong> measured in more than one country whose
                prevalence class disagrees across them — the population axis, on one
                disease.
              </p>
            </div>
            <ol className={css.bands}>
              {d.prevalenceSpread.map((b) => {
                // Position on the rarity scale, from the analysis, NOT from the row's
                // index. Sorting put "Unknown" last, and using the index gave it the
                // widest fill — drawing the absence of a measurement as the commonest
                // rate. An unordered value gets no length at all.
                const steps = 6;
                const frac = b.ordered && b.rank !== null ? (b.rank + 1) / steps : 0;
                return (
                  <li key={b.band} className={css.bandRow}>
                    <span className={b.ordered ? css.bandName : css.bandNameOff}>
                      {b.band}
                    </span>
                    <span className={css.bandRail}>
                      {b.ordered ? (
                        <span
                          className={css.bandFill}
                          style={{ width: `${frac * 100}%`, opacity: 0.4 + 0.6 * frac }}
                        />
                      ) : (
                        <span className={css.bandNone} title="not on the rarity scale" />
                      )}
                    </span>
                    <span className={css.bandPlaces}>{b.places.join(" · ")}</span>
                  </li>
                );
              })}
            </ol>
          </section>
        )}

        {/* ---------------------------------------------------------------------------
            WHAT IT ATTACKS. The signs rolled up the HPO `is_a` graph to the top-level
            organ systems. Until this existed the panel had 39 facts and no structure, and
            a flat list cannot answer the first question anyone asks about a disease.

            The second column is the one worth the screen space: how much of each system is
            actually QUANTIFIED. For Duchenne every system comes out at zero, including the
            cardiovascular one — where four of the five recorded signs have no frequency at
            all, in the organ that causes most of the deaths.
        ---------------------------------------------------------------------------- */}
        {d.systems.length > 0 && (
          <section className={css.spread}>
            <div className={css.spreadHead}>
              <h4 className={css.h4}>What it attacks, and where nobody has counted</h4>
              <p className={css.sub}>
                {d.signCount} signs rolled up the HPO <code>is_a</code> graph onto{" "}
                <strong>{d.systemsMeta.count}</strong> organ systems.{" "}
                {d.systemsMeta.quantifiedSystems === 0 ? (
                  <strong>
                    Not one of them has a single sign estimated from a real series.
                  </strong>
                ) : (
                  <>
                    <strong>{d.systemsMeta.quantifiedSystems}</strong> carry at least one
                    quantified sign; <strong>{d.systemsMeta.describedButUnquantified}</strong>{" "}
                    are described and never counted.
                  </>
                )}{" "}
                {d.systemsMeta.note}
              </p>
            </div>
            <ol className={css.systems}>
              {d.systems.map((sy) => (
                <li key={sy.id} className={css.systemRow}>
                  <span className={css.systemName} title={sy.examples.join(" · ")}>
                    {sy.name.replace(/^Abnormality of (the )?/, "")}
                  </span>
                  <span className={css.systemCount}>{sy.signs}</span>
                  {/* The same four-grade encoding as the sign panel, so one system can be
                      compared with another and with the disease as a whole. */}
                  <span className={css.systemBar}>
                    {GRADES.map((g) =>
                      sy.byEvidence[g.id] > 0 ? (
                        <span
                          key={g.id}
                          className={`${css.profileSeg} ${css[`ev_${g.id.replace("-", "_")}`]}`}
                          style={{ width: `${(sy.byEvidence[g.id] / sy.signs) * 100}%` }}
                          title={`${sy.byEvidence[g.id]} ${g.label.toLowerCase()}`}
                        />
                      ) : null
                    )}
                  </span>
                  <span className={css.systemExamples}>{sy.examples.join(" · ")}</span>
                </li>
              ))}
            </ol>
          </section>
        )}

        {/* ---------------------------------------------------------------------------
            COULD ANY OF IT HAVE FOUND ANYTHING. Every other view of the trial record
            counts studies, which answers "is anyone trying". This asks the question the
            rest of this library exists to ask — whether the observation count is large
            enough for the estimate to mean anything. It is Stage 2, applied to the
            clinical record instead of to a screen.
        ---------------------------------------------------------------------------- */}
        {d.trials.power.medianInterventionalEnrolment !== null && (
          <section className={css.spread}>
            <div className={css.spreadHead}>
              <h4 className={css.h4}>Could the trials have found anything?</h4>
              <p className={css.sub}>
                A count of trials says whether anyone is trying. It does not say whether the
                studies were large enough to detect a treatment that works — which is the
                question this library exists to ask, here asked of the clinical record.
              </p>
            </div>

            <div className={css.powerRow}>
              <PowerStat
                label="Median interventional trial"
                value={`${nf(d.trials.power.medianInterventionalEnrolment)} patients`}
                note={`across ${nf(d.trials.power.interventionalWithEnrolment)} trials that state an enrolment`}
              />
              <PowerStat
                label="Smallest effect it could detect"
                value={`${d.trials.power.medianMDE?.toFixed(2)} SD`}
                note="at 80 % power, two-sided α 0.05 — and this is a floor"
                tone={(d.trials.power.medianMDE ?? 0) > 0.8 ? "under" : undefined}
              />
              <PowerStat
                label="Trials that cannot see a large effect"
                value={`${nf(d.trials.power.belowLargeEffect)} of ${nf(d.trials.power.interventionalWithEnrolment)}`}
                note="a large effect is 0.8 SD by Cohen's convention"
                tone="under"
              />
              <PowerStat
                label="Effort still moving"
                value={`${nf(d.trials.trajectory.startedLastFiveYears)} since ${(d.trials.trajectory.lastYear ?? 0) - 4}`}
                note={`record runs ${d.trials.trajectory.firstYear}–${d.trials.trajectory.lastYear}`}
              />
            </div>

            <p className={css.assumption}>
              <strong>Read this before quoting it.</strong> {d.trials.power.assumption}{" "}
              {d.trials.power.trialsWithoutEnrolment > 0 && (
                <>
                  {nf(d.trials.power.trialsWithoutEnrolment)} of {nf(d.trials.total)} studies
                  state no enrolment at all and are excluded rather than imputed.
                </>
              )}
            </p>

            <div className={css.modality}>
              <span className={css.modalityLabel}>What is being tried</span>
              <div className={css.chips}>
                {Object.entries(d.trials.byModality)
                  .slice(0, 10)
                  .map(([k, v]) => (
                    <span key={k} className={css.chip}>
                      {k} <strong>{nf(v)}</strong>
                    </span>
                  ))}
              </div>
            </div>
          </section>
        )}

        <div className={css.pair}>
          {/* ---- signs ------------------------------------------------------- */}
          <section className={css.panel}>
            <h4 className={css.h4}>What it does, and how well anyone knows</h4>

            {/* THE HEADLINE IS GENERATED, NOT WRITTEN. It reads differently for each
                disease because the evidence profile differs, and for most of this
                portfolio it is an admission rather than a summary. */}
            <p className={css.verdict}>
              {d.evidence.quantified === 0 ? (
                <>
                  <strong>
                    Not one of the {nf(d.signCount)} recorded signs is estimated from more
                    than a single patient.
                  </strong>{" "}
                  {d.evidence["single-case"] > 0 && (
                    <>
                      {nf(d.evidence["single-case"])} come from one case each,{" "}
                    </>
                  )}
                  {nf(d.evidence.class)} carry only an unquantified class, and{" "}
                  {nf(d.evidence.none)} have no frequency recorded at all. The symptom list
                  is a list; it is not a distribution.
                </>
              ) : (
                <>
                  <strong>
                    {nf(d.evidence.quantified)} of {nf(d.signCount)} signs carry a real
                    denominator
                  </strong>
                  , with a median series of{" "}
                  <strong>{nf(d.medianDenominator ?? 0)}</strong> patients.{" "}
                  {nf(d.evidence["single-case"])} rest on a single case,{" "}
                  {nf(d.evidence.class)} on a class with no denominator, and{" "}
                  {nf(d.evidence.none)} on nothing at all.
                </>
              )}
            </p>

            {/* AGAINST THE FIELD, NOT IN ISOLATION. A per-disease figure invites the reader
                to conclude that this particular disease was neglected. The catalogue-wide
                measurement says otherwise, and the comparison is the honest frame: the
                scarcity is a property of how the field records phenotype. */}
            <p className={css.fieldCompare}>
              Across the whole catalogue —{" "}
              <strong>{nf(field.profile.annotations)}</strong> annotations over{" "}
              <strong>{nf(field.profile.diseasesWithPhenotypeAnnotations)}</strong> diseases —
              only <strong>{Math.round(field.profile.shareWithAQuantifiedSign * 100)}%</strong>{" "}
              have even one sign estimated from a real series, and where a denominator exists
              the median is <strong>{field.profile.denominators.median} patients</strong>.
              This disease is not unusual; the scarcity is the field&rsquo;s.
            </p>

            {/* The profile as a proportion, so the shape is read before any single row. */}
            <div className={css.profile} role="img"
                 aria-label={GRADES.map((g) => `${d.evidence[g.id]} ${g.label}`).join(", ")}>
              {GRADES.map((g) =>
                d.evidence[g.id] > 0 ? (
                  <span
                    key={g.id}
                    className={`${css.profileSeg} ${css[`ev_${g.id.replace("-", "_")}`]}`}
                    style={{ width: `${(d.evidence[g.id] / d.signCount) * 100}%` }}
                    title={`${d.evidence[g.id]} — ${d.evidenceGrades[g.id]}`}
                  />
                ) : null
              )}
            </div>

            <div className={css.gradeChips} role="group" aria-label="Filter signs by evidence">
              {GRADES.map((g) => (
                <button
                  key={g.id}
                  type="button"
                  aria-pressed={grades.has(g.id)}
                  disabled={d.evidence[g.id] === 0}
                  title={d.evidenceGrades[g.id]}
                  className={grades.has(g.id) ? css.gradeOn : css.grade}
                  onClick={() => {
                    const next = new Set(grades);
                    if (next.has(g.id)) next.delete(g.id);
                    else next.add(g.id);
                    // Never allow all four off: an empty panel teaches nothing, and the
                    // reader almost certainly meant "only this one".
                    setGrades(next.size ? next : new Set([g.id]));
                  }}
                >
                  <span className={`${css.dot} ${css[`ev_${g.id.replace("-", "_")}`]}`} />
                  {g.label}
                  <span className={css.gradeCount}>{nf(d.evidence[g.id])}</span>
                </button>
              ))}
            </div>

            <ul className={css.signs}>
              {visible.map((sg) => (
                <li key={sg.id} className={`${css.sign} ${sg.hasN ? "" : css.classy}`}>
                  <span className={css.signName} title={sg.name}>{sg.name}</span>
                  <span className={css.signBar}>
                    {/* A bar is drawn ONLY for a real denominator. */}
                    {sg.hasN && sg.point !== null && sg.point !== undefined && (
                      <span className={css.signPoint}
                            style={{ width: `${Math.max(2, (sg.point as number) * 100)}%` }} />
                    )}
                    {sg.hasN && sg.lo !== null && (
                      <span className={css.signCI}
                            style={{
                              left: `${(sg.lo as number) * 100}%`,
                              width: `${Math.max(2, ((sg.hi as number) - (sg.lo as number)) * 100)}%`,
                            }} />
                    )}
                    {sg.band && (
                      <span className={css.signBand}
                            style={{
                              left: `${sg.band[0] * 100}%`,
                              width: `${Math.max(3, (sg.band[1] - sg.band[0]) * 100)}%`,
                            }} />
                    )}
                    {/* Single case: the interval it actually has, drawn as the near-whole
                        axis it covers, with no point estimate to mistake for a rate. */}
                    {sg.evidence === "single-case" && sg.lo !== null && (
                      <span className={css.signVoid}
                            style={{
                              left: `${(sg.lo as number) * 100}%`,
                              width: `${((sg.hi as number) - (sg.lo as number)) * 100}%`,
                            }} />
                    )}
                  </span>
                  <span className={css.signFreq}>
                    {sg.evidence === "quantified"
                      ? `${sg.k}/${sg.n} · ${pct(sg.lo as number)}\u2013${pct(sg.hi as number)}`
                      : sg.evidence === "single-case"
                      ? `1 patient · ${pct(sg.lo as number)}\u2013${pct(sg.hi as number)}`
                      : sg.band
                      ? `${pct(sg.band[0])}\u2013${pct(sg.band[1])}`
                      : "no frequency"}
                  </span>
                </li>
              ))}
            </ul>

            {visible.length < signs.length && (
              <p className={css.sub}>
                {nf(signs.length - visible.length)} sign
                {signs.length - visible.length === 1 ? "" : "s"} hidden by the filter above.
              </p>
            )}
          </section>

          {/* ---- current state ------------------------------------------------ */}
          <section className={css.panel}>
            <h4 className={css.h4}>Current state</h4>
            <p className={css.sub}>
              Live from ClinicalTrials.gov, cached so the artefact is reproducible. Trial
              activity is not efficacy — a hundred studies can mean a hundred failures — but
              it is the only observable, current signal of whether anyone is trying.
            </p>
            <div className={css.chips}>
              {topStatuses.map(([k, v]) => (
                <span key={k} className={css.chip}>{k.replace(/_/g, " ").toLowerCase()} {v}</span>
              ))}
            </div>
            <div className={css.chips}>
              {Object.entries(t.byIntervention).slice(0, 6).map(([k, v]) => (
                <span key={k} className={css.chip}>{k.toLowerCase()} {v}</span>
              ))}
            </div>
            <ul className={css.trialRows}>
              {t.recruiting.map((r) => (
                <li key={r.nctId} className={css.trial}>
                  <span className={css.nct}>{r.nctId}</span>
                  <span className={css.trialTitle}>{r.title}</span>
                  <span className={css.trialPhase}>
                    {r.phase?.replace(/PHASE/g, "Ph ") ?? "n/a"}
                    {r.enrollment ? ` · n=${r.enrollment}` : ""}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        </div>

        {/* ---- cell axis ------------------------------------------------------ */}
        {Object.keys(d.cells).length > 0 && (
          <section className={css.panel}>
            <h4 className={css.h4}>Where the genes live</h4>
            <p className={css.sub}>
              For each causal gene: the cell type of highest single-cell expression, and how
              many of the {154} measured types express it at all. A gene expressed almost
              everywhere causes disease in one place — the morphogenesis gap.
            </p>
            <ul className={css.signs}>
              {Object.entries(d.cells).slice(0, 12).map(([gene, c]) => (
                <li key={gene} className={css.sign}>
                  <span className={css.signName}>
                    <strong>{gene}</strong> — {c.topCell}
                  </span>
                  <span className={css.signBar}>
                    <span className={css.signPoint}
                          style={{ width: `${Math.round((c.expressedIn / 154) * 100)}%` }} />
                  </span>
                  <span className={css.signFreq}>{c.expressedIn}/154</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {(() => {
          const b = bar.diseases.find((x) => x.catalogueName === d.name);
          if (!b) return null;
          return (
            <>
              <section className={css.panel}>
                <h4 className={css.h4}>What is actually stopping a therapy</h4>
                <p className={css.mechanism}>{b.mechanism}</p>
                <ul className={css.barrierList}>
                  {b.barriers.map((x, i) => (
                    <li key={i} className={css.barrier}>
                      <span className={`${css.kind} ${css[x.kind] ?? ""}`}>{x.kind}</span>
                      <span>
                        <span className={css.barrierWhat}>{x.what}</span>
                        <span className={css.barrierWhy}>{x.why}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              </section>

              <section className={css.panel}>
                <h4 className={css.h4}>Modern routes that exist and are little used here</h4>
                <p className={css.sub}>
                  Each names why it fits AND why it is not used, so the entry is a hypothesis
                  rather than an exhortation. That something is <em>underused</em> is a
                  judgement, and the confidence line says so.
                </p>
                <div className={css.underused}>
                  {b.underused.map((u) => (
                    <article key={u.approach} className={css.alt}>
                      <span className={css.altName}>{u.approach}</span>
                      <div>
                        <span className={css.altL}>Why it fits</span>
                        <p className={css.altT}>{u.why_it_fits}</p>
                      </div>
                      <div>
                        <span className={css.altL}>Why it is not used</span>
                        <p className={css.altT}>{u.why_not_used}</p>
                      </div>
                      <span className={css.altConf}>
                        confidence in the &ldquo;underused&rdquo; judgement: {u.confidence}
                      </span>
                    </article>
                  ))}
                </div>
              </section>
            </>
          );
        })()}

        <section className={css.panel}>
          <h4 className={css.h4}>The theories a strategy gets chosen from</h4>
          <p className={css.sub}>{bar.premise}</p>
          <div className={css.theories}>
            {bar.theories.map((t) => (
              <article key={t.id} className={css.theory}>
                <span className={css.theoryField}>{t.field}</span>
                <span className={css.theoryName}>{t.name}</span>
                <span className={css.theorySays}>{t.says}</span>
                <span className={css.theoryDecides}>{t.decides}</span>
              </article>
            ))}
          </div>
        </section>

        <p className={css.caveat}>
          <strong>What is deliberately absent.</strong> {data.caveat}
          <br /><br />
          <strong>On the barrier layer.</strong> {bar.provenance}
        </p>
      </article>
    </div>
  );
}

function PowerStat({
  label, value, note, tone,
}: { label: string; value: string; note: string; tone?: "under" }) {
  return (
    <div className={css.powerStat}>
      <span className={css.tileLabel}>{label}</span>
      <span className={`${css.powerValue} ${tone ? css[tone] : ""}`}>{value}</span>
      <span className={css.tileNote}>{note}</span>
    </div>
  );
}

function Tile({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className={css.tile}>
      <span className={css.tileL}>{label}</span>
      <span className={css.tileV}>{value}</span>
      <span className={css.tileS}>{sub}</span>
    </div>
  );
}
