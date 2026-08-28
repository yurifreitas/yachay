/** What an approach physically requires: the instrument, the physics, the money, the people.
 *
 *  THREE VIEWS, because they answer three different questions and share one dataset.
 *
 *    Plans        given an approach, what has to happen in what order, what each stage is
 *                 gated on, what it costs to stand up, and what is actually known about
 *                 whether it works.
 *    Instruments  the capital ladder. Every instrument carries the physical reason it
 *                 cannot be substituted — and, where one exists, the cheaper route.
 *    Diagnostics  what the standard test misses, and the instrument that would not.
 *
 *  WHY THE COST IS DRAWN AS A BAND. A list price is not a transaction price, and these are
 *  engineering estimates good to about a factor of two. A bar from zero to a single number
 *  would claim a precision nobody has. So the ladder draws lo-to-hi as a dumbbell on a LOG
 *  axis — log because the range runs from a $60k booth to a $22M cleanroom, and on a linear
 *  axis every instrument except the cleanroom would be a smear against the left edge.
 *
 *  THE FTE COLUMN IS DELIBERATELY BESIDE THE MONEY. The scarce input in a rare-disease
 *  programme is usually not the machine. Reading the two columns together is the point of
 *  putting them in one row.
 */
import { useMemo, useState } from "react";
import { capability as cap } from "../data/capability";
import { capabilityMath as math } from "../data/capabilityMath";
import { prevalenceAudit as pa } from "../data/prevalenceAudit";
import type { Instrument } from "../capabilityModel";
import css from "./Capability.module.css";

type View = "plans" | "instruments" | "diagnostics" | "arithmetic";

const VIEWS: { id: View; label: string; sub: string }[] = [
  { id: "plans", label: "Approach plans", sub: "stages, gates, and what is known about efficacy" },
  { id: "instruments", label: "Instruments and cost", sub: "the physics, the capital, the people" },
  { id: "diagnostics", label: "Sharper diagnosis", sub: "what the standard test misses" },
  { id: "arithmetic", label: "The arithmetic", sub: "nothing authored — all of it computed" },
];

/** Log placement for the capital-per-patient ladder: cents to thousands. */
const PLO = 0.1;
const PHI = 2_000;
const pAt = (v: number) =>
  ((Math.log10(Math.min(Math.max(v, PLO), PHI)) - Math.log10(PLO)) /
    (Math.log10(PHI) - Math.log10(PLO))) * 100;
const PTICKS = [1, 10, 100, 1_000];
const small = (v: number) =>
  v >= 1000 ? "$" + Math.round(v / 1000) + "k"
  : v >= 10 ? "$" + Math.round(v)
  : v >= 1 ? "$" + v.toFixed(1)
  : "$" + v.toFixed(2);

/** Money, at the precision the estimate actually has. */
const usd = (v: number) =>
  v >= 1_000_000 ? `$${(v / 1_000_000).toFixed(v >= 10_000_000 ? 0 : 1)}M`
  : v >= 1_000 ? `$${Math.round(v / 1_000)}k`
  : `$${v}`;

const band = (lo: number, hi: number) => `${usd(lo)}–${usd(hi)}`;

/** Log placement for the capital ladder. */
const LO = 50_000;
const HI = 25_000_000;
const at = (v: number) =>
  ((Math.log10(Math.max(v, LO)) - Math.log10(LO)) / (Math.log10(HI) - Math.log10(LO))) * 100;

const TICKS = [100_000, 1_000_000, 10_000_000];

/** Thirteen instrument classes is more series than any palette can keep separable, so the
 *  colour encodes a FAMILY of five — what the instrument is pointed at — and the class stays
 *  as text on the card. Five hues stay distinguishable under colour-vision deficiency; thirteen
 *  do not, and a legend nobody can use is decoration. */
const FAMILY: Record<string, string> = {
  sequencing: "genome", genomics: "genome", molecular: "genome",
  cell: "cell", electrophysiology: "cell", imaging: "cell",
  analytical: "molecule", biophysics: "molecule", structural: "molecule",
  "clinical imaging": "patient", "clinical function": "patient",
  manufacture: "dose", facility: "dose",
};
const FAMILIES: { id: string; label: string }[] = [
  { id: "genome", label: "points at the genome" },
  { id: "cell", label: "points at the cell" },
  { id: "molecule", label: "points at the molecule" },
  { id: "patient", label: "points at the patient" },
  { id: "dose", label: "makes the dose" },
];

/** Efficacy is a claim about evidence, so it gets status colour, never a series colour. */
const TONE: Record<string, string> = {
  demonstrated: css.good,
  "partially demonstrated": css.warn,
  "established mechanism, unmeasured programme benefit": css.warn,
  "unproven in humans": css.serious,
  "preclinical only": css.serious,
  unknown: css.muted,
};

export function Capability() {
  const [view, setView] = useState<View>("plans");
  const [pickPlan, setPickPlan] = useState(0);
  const byId = useMemo(
    () => Object.fromEntries(cap.instruments.map((i) => [i.id, i])) as Record<string, Instrument>,
    [],
  );
  const ladder = useMemo(
    () => [...cap.instruments].sort((a, b) => a.capexUSD[0] - b.capexUSD[0]),
    [],
  );
  const s = cap.summary;
  const plan = cap.plans[pickPlan];

  return (
    <div className={css.root}>
      <p className={css.premise}>{cap.premise}</p>

      <div className={css.counts}>
        <Stat v={String(s.instruments)} l="instruments"
              s={`${s.withCheaperRoute} state a cheaper route that would do`} />
        <Stat v={String(s.plans)} l="approach plans" s={`${s.planStages} gated stages`} />
        <Stat v={String(s.diagnostics)} l="sharper diagnostics"
              s="what the standard test misses, per disease" />
        <Stat v={band(s.cheapestPlanUSD, s.dearestPlanUSD)} l="plan capital, cheapest to dearest"
              s="a factor of twelve between the two ends" />
      </div>

      <nav className={css.tabs} aria-label="Capability views">
        {VIEWS.map((v) => (
          <button key={v.id} type="button" onClick={() => setView(v.id)}
                  className={v.id === view ? css.tabOn : css.tab} aria-current={v.id === view}>
            <span>{v.label}</span>
            <span className={css.tabSub}>{v.sub}</span>
          </button>
        ))}
      </nav>

      {/* ---- PLANS --------------------------------------------------------- */}
      {view === "plans" && (
        <div className={css.planWrap}>
          <nav className={css.planPick} aria-label="Choose an approach plan">
            {cap.plans.map((p, i) => (
              <button key={p.id} type="button" onClick={() => setPickPlan(i)}
                      className={i === pickPlan ? css.pickOn : css.pick} aria-current={i === pickPlan}>
                <span className={css.pickName}>{p.approach}</span>
                <span className={css.pickMeta}>{p.catalogueName}</span>
                <span className={`${css.pill} ${TONE[p.efficacy] ?? css.muted}`}>{p.efficacy}</span>
              </button>
            ))}
          </nav>

          {plan && (
            <article className={css.plan}>
              <header className={css.planHead}>
                <h4 className={css.planTitle}>{plan.approach}</h4>
                <p className={css.goal}>{plan.goal}</p>
              </header>

              <div className={css.ledger}>
                <Cell l="Capital to stand up" v={band(plan.capexUSD.lo, plan.capexUSD.hi)}
                      s={`${plan.instruments.length} instruments, list price, band not point`} />
                <Cell l="Operating, per year" v={usd(plan.opexUSDyr)}
                      s="service contracts plus consumables" />
                <Cell l="Siting" v={plan.sitingUSD ? usd(plan.sitingUSD) : "none material"}
                      s="shielding, floor loading, a quiet room" />
                <Cell l="People" v={`${plan.fte} FTE`}
                      s={`${plan.roles.length} distinct specialisms`} />
                <Cell l="Horizon" v={`${plan.horizonYears} yr`} s="to a first human readout" />
              </div>

              <section className={css.physics}>
                <span className={css.label}>The physical reason</span>
                <p>{plan.physics}</p>
              </section>

              {/* The stages ARE a sequence with gates, so they are numbered. */}
              <ol className={css.stages}>
                {plan.stages.map((st, i) => (
                  <li key={st.name} className={css.stage}>
                    <span className={css.stageN}>{String(i + 1).padStart(2, "0")}</span>
                    <div className={css.stageBody}>
                      <span className={css.stageName}>{st.name}</span>
                      <p className={css.stageDoes}>{st.does}</p>
                      <p className={css.gate}>
                        <span className={css.gateL}>Gate</span> {st.gate}
                      </p>
                      <div className={css.needs}>
                        {st.needs.length === 0 ? (
                          <span className={css.needNone}>no instrument — this stage is a decision</span>
                        ) : (
                          st.needs.map((n) => (
                            <span key={n} className={css.need}>
                              {byId[n]?.name ?? n}
                              <span className={css.needCost}>
                                {byId[n] ? band(byId[n].capexUSD[0], byId[n].capexUSD[1]) : ""}
                              </span>
                            </span>
                          ))
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ol>

              <section className={css.efficacy}>
                <span className={`${css.pill} ${TONE[plan.efficacy] ?? css.muted}`}>{plan.efficacy}</span>
                <p>{plan.efficacyEvidence}</p>
                <p className={css.note}>{plan.note}</p>
              </section>

              <div className={css.roleList}>
                {plan.roles.map((r) => <span key={r} className={css.role}>{r}</span>)}
              </div>
            </article>
          )}
        </div>
      )}

      {/* ---- INSTRUMENTS --------------------------------------------------- */}
      {view === "instruments" && (
        <div className={css.instWrap}>
          <section className={css.ladderPanel}>
            <h4 className={css.h4}>Capital, on a log axis, because the range is 400-fold</h4>
            <p className={css.sub}>
              Each row is one instrument, drawn from its low estimate to its high one. The
              width of the bar is the width of the uncertainty, not the size of the number.
              Colour is what the instrument is pointed at — five families, because thirteen
              classes is more hues than anyone can tell apart. The figure on the right is
              whole-time-equivalent staff, which is the column that is usually forgotten.
            </p>
            <div className={css.legend}>
              {FAMILIES.map((f) => (
                <span key={f.id} className={css.legendItem}>
                  <i className={css.swatch} data-f={f.id} /> {f.label}
                </span>
              ))}
            </div>
            <div className={css.ladder}>
              <div className={css.axis} aria-hidden="true">
                {TICKS.map((t) => (
                  <span key={t} className={css.tick} style={{ left: `${at(t)}%` }}>{usd(t)}</span>
                ))}
              </div>
              {ladder.map((i) => (
                <div key={i.id} className={css.rung}>
                  <span className={css.rungName}>{i.name}</span>
                  <span className={css.track}>
                    {TICKS.map((t) => (
                      <i key={t} className={css.gridline} style={{ left: `${at(t)}%` }} />
                    ))}
                    <span className={css.dumbbell} data-f={FAMILY[i.klass]}
                          style={{ left: `${at(i.capexUSD[0])}%`,
                                   width: `${Math.max(1.5, at(i.capexUSD[1]) - at(i.capexUSD[0]))}%` }} />
                  </span>
                  <span className={css.rungCost}>{band(i.capexUSD[0], i.capexUSD[1])}</span>
                  <span className={css.rungFte}>{i.fte} FTE</span>
                </div>
              ))}
            </div>
          </section>

          <div className={css.cards}>
            {ladder.map((i) => (
              <article key={i.id} className={css.card}>
                <header>
                  <span className={css.klass} data-f={FAMILY[i.klass]}>{i.klass}</span>
                  <h5 className={css.cardTitle}>{i.name}</h5>
                </header>
                <div className={css.cardMoney}>
                  <span><b>{band(i.capexUSD[0], i.capexUSD[1])}</b> capital</span>
                  <span>{usd(i.opexUSDyr)}/yr running</span>
                  {i.sitingUSD > 0 && <span>{usd(i.sitingUSD)} siting</span>}
                  <span>{i.fte} FTE</span>
                </div>
                <p className={css.cardPhysics}>{i.physics}</p>
                <p className={css.cardRow}><span className={css.label}>Measures</span> {i.measures}</p>
                <p className={css.cardRow}><span className={css.label}>Limit</span> {i.limit}</p>
                <p className={i.cheaperRoute ? css.cheaper : css.noCheaper}>
                  <span className={css.label}>Cheaper route</span>{" "}
                  {i.cheaperRoute ?? "none that answers the same question."}
                </p>
                <div className={css.roleList}>
                  {i.roles.map((r) => <span key={r} className={css.role}>{r}</span>)}
                </div>
              </article>
            ))}
          </div>
        </div>
      )}

      {/* ---- DIAGNOSTICS --------------------------------------------------- */}
      {view === "diagnostics" && (
        <div className={css.dxWrap}>
          {cap.diagnostics.map((d) => (
            <article key={d.catalogueName} className={css.dx}>
              <header className={css.dxHead}>
                <h5 className={css.cardTitle}>{d.catalogueName}</h5>
                <span className={css.dxCost}>{band(d.perTestUSD[0], d.perTestUSD[1])} per test</span>
              </header>
              <div className={css.dxCols}>
                <div>
                  <span className={css.label}>What is done now</span>
                  <p>{d.standard}</p>
                </div>
                <div className={css.dxMiss}>
                  <span className={css.label}>What it misses</span>
                  <p>{d.misses}</p>
                </div>
                <div className={css.dxSharp}>
                  <span className={css.label}>The sharper test</span>
                  <p>{d.sharper}</p>
                </div>
              </div>
              <p className={css.dxPhysics}>{d.physics}</p>
              <p className={css.dxChanges}>
                <span className={css.label}>Why it changes anything</span> {d.changesManagement}
              </p>
              <div className={css.needs}>
                {d.instruments.map((n) => (
                  <span key={n} className={css.need}>
                    {byId[n]?.name ?? n}
                    <span className={css.needCost}>
                      {byId[n] ? band(byId[n].capexUSD[0], byId[n].capexUSD[1]) : ""}
                    </span>
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      )}

      {/* ---- ARITHMETIC: derived, never authored ---------------------------- */}
      {view === "arithmetic" && (
        <div className={css.mathWrap}>
          <p className={css.premise}>{math.premise}</p>

          <section className={css.finding}>
            <span className={css.findingL}>
              What the arithmetic says, including where it cuts against this site
            </span>
            <p>{math.finding}</p>
          </section>

          {/* 1 - capital per patient */}
          <section className={css.ladderPanel}>
            <h4 className={css.h4}>Laboratory capital per prevalent patient, both ends of both bands</h4>
            <p className={css.sub}>
              The plan capital is a band and the Orphanet prevalence class is a band, so the
              quotient is a band: the low end divides the cheap plan by the large cohort, the
              high end divides the dear plan by the small one. Log axis, because the answer
              spans four decades. Every figure is an UPPER bound - the cohorts are under-counted,
              and the block below says by how much and why. The right-hand column is the cohort.
            </p>
            <div className={css.ladder}>
              <div className={css.axis} aria-hidden="true">
                {PTICKS.map((t) => (
                  <span key={t} className={css.tick} style={{ left: pAt(t) + "%" }}>{small(t)}</span>
                ))}
              </div>
              {math.capitalPerPatient.map((r) => (
                <div key={r.planId} className={css.rung}>
                  <span className={css.rungName}>{r.catalogueName}</span>
                  <span className={css.track}>
                    {PTICKS.map((t) => (
                      <i key={t} className={css.gridline} style={{ left: pAt(t) + "%" }} />
                    ))}
                    {r.capitalPerPatientUSD && (
                      <span
                        /* An unbounded high end is drawn open-ended rather than clipped to the
                           axis, because clipping it would read as a measured ceiling. */
                        className={r.capitalPerPatientUSD.hi === null ? css.dumbbellOpen : css.dumbbell}
                        data-f="dose"
                        style={{
                          left: pAt(r.capitalPerPatientUSD.lo) + "%",
                          width: Math.max(
                            1.5,
                            pAt(r.capitalPerPatientUSD.hi ?? PHI) - pAt(r.capitalPerPatientUSD.lo),
                          ) + "%",
                        }}
                      />
                    )}
                  </span>
                  <span className={css.rungCost}>
                    {r.capitalPerPatientUSD
                      ? small(r.capitalPerPatientUSD.lo) + "\u2013" +
                        (r.capitalPerPatientUSD.hi === null ? "\u221e" : small(r.capitalPerPatientUSD.hi))
                      : "no validated cohort"}
                  </span>
                  <span className={css.rungFte}>
                    {r.patients
                      ? Math.round(r.patients.lo / 1000) + "\u2013" + Math.round(r.patients.hi / 1000) + "k"
                      : "\u2014"}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* WAS AN AUTHORED BLOCK. It named two diseases from memory and said so. The audit
              below finds the same defect by reading all 17,108 Orphanet prevalence records,
              which is both larger and re-runnable. The authored version is gone rather than
              kept alongside: two accounts of the same problem is one account too many. */}
          <section className={css.disputed}>
            <h4 className={css.h4}>
              The cohort above was standing on one string per disease. It was never one number
            </h4>
            <p className={css.sub}>{pa.premise}</p>

            <div className={css.auditNums}>
              <Stat v={pa.scale.prevalenceRecords.toLocaleString("en-US")}
                    l="prevalence records"
                    s={`across ${pa.scale.disordersWithPrevalence.toLocaleString("en-US")} disorders, ${pa.scale.meanRecordsPerDisorder} each on average`} />
              <Stat v={`${Math.round(pa.mixedTypeDisorders.fraction * 100)}%`}
                    l="mix more than one KIND of measurement"
                    s={`${pa.mixedTypeDisorders.count.toLocaleString("en-US")} disorders carry two or more of point prevalence, birth prevalence, annual incidence or raw case counts`} />
              <Stat v={pa.typeDisagreements.count.toLocaleString("en-US")}
                    l="disagree five-fold or more"
                    s="birth figure against point-prevalence figure, in the same disorder" />
            </div>

            <div className={css.typeBars}>
              {Object.entries(pa.byType).map(([k, v]) => (
                <div key={k} className={css.typeRow}>
                  <span className={css.typeName}>{k}</span>
                  <span className={css.typeTrack}>
                    <span
                      className={css.typeBar}
                      data-f={k === "Point prevalence" ? "cell" : "molecule"}
                      style={{ width: (v / Math.max(...Object.values(pa.byType))) * 100 + "%" }}
                    />
                  </span>
                  <span className={css.typeN}>{v.toLocaleString("en-US")}</span>
                </div>
              ))}
            </div>
            <p className={css.cmpNote}>
              Point prevalence and prevalence at birth are different quantities, and for a
              disease that shortens life they diverge — that is not an error in the data, it is
              an error in reading it. The dashboard had been taking whichever record the
              collapse happened to keep.
            </p>

            <div className={css.watched}>
              {pa.watched.map((w) => (
                <div key={w.orpha} className={css.wRow}>
                  <span className={css.wName}>{w.name}</span>
                  <span className={css.wRecords}>{w.recordCount} records</span>
                  <span className={css.wTypes}>{w.typesPresent.join(" · ")}</span>
                  <span className={css.wCohort}>
                    {w.worldCohort
                      ? "validated point prevalence: " +
                        Math.round(w.worldCohort.lo / 1000).toLocaleString("en-US") + "k\u2013" +
                        Math.round(w.worldCohort.hi / 1000).toLocaleString("en-US") + "k"
                      : "no validated point-prevalence class"}
                  </span>
                </div>
              ))}
            </div>

            <p className={css.dispEffect}>{pa.finding}</p>
          </section>

          {/* WHAT THE CORRECTION MOVED. A correction whose size is hidden is just a second
              unexplained number, so the old reading stays beside the new one. */}
          {math.movement.length > 0 && (
            <section className={css.ladderPanel}>
              <h4 className={css.h4}>What rebuilding on the audited cohort actually moved</h4>
              <p className={css.sub}>{math.cohortSource}</p>
              <div className={css.moveList}>
                {math.movement.map((m) => (
                  <div key={m.catalogueName} className={css.moveRow}>
                    <span className={css.mvName}>{m.catalogueName}</span>
                    <span className={css.mvOld}>
                      {small(m.fromUSD.lo)}&ndash;{small(m.fromUSD.hi)}
                      <span className={css.mvTag}>from one collapsed string</span>
                    </span>
                    <span className={css.mvArrow} aria-hidden="true">&rarr;</span>
                    <span className={css.mvNew}>
                      {small(m.toUSD.lo)}&ndash;{m.toUSD.hi === null ? "unbounded" : small(m.toUSD.hi)}
                      <span className={css.mvTag}>
                        from {m.records} records, {m.basis}
                      </span>
                    </span>
                    <span className={css.mvFold}>
                      {m.folds.lo !== undefined && (
                        <b>{m.folds.lo < 1 ? Math.round(1 / m.folds.lo) + "x cheaper" : m.folds.lo + "x"}</b>
                      )}
                    </span>
                  </div>
                ))}
              </div>
              <p className={css.cmpNote}>
                Every one of these moved <strong>down</strong>: the collapsed string was
                systematically under-counting the cohort, so the site had been overstating what a
                programme costs per patient. My own hand-written flag on this tab named two of
                these diseases and guessed the direction right and the size wrong.
              </p>
            </section>
          )}

          {/* WHERE THE MEASURING HAPPENED. Not where disease is — where the field looked. */}
          <section className={css.ladderPanel}>
            <h4 className={css.h4}>
              The prevalence corpus, ranked by how closely a population has been examined
            </h4>
            <p className={css.sub}>{pa.geography.says}</p>
            <div className={css.geoCols}>
              <div>
                <span className={css.label}>Most looked at, records per 100M people</span>
                <div className={css.geoList}>
                  {pa.geography.byRate.slice(0, 10).map((g) => (
                    <div key={g.place} className={css.geoRow}>
                      <span className={css.geoName}>{g.place}</span>
                      <span className={css.geoTrack}>
                        <span className={css.geoBar} data-f="patient"
                              style={{ width: ((g.perHundredM ?? 0) / (pa.geography.byRate[0].perHundredM || 1)) * 100 + "%" }} />
                      </span>
                      <span className={css.geoN}>{Math.round(g.perHundredM ?? 0).toLocaleString("en-US")}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <span className={css.label}>Least looked at, same units, same corpus</span>
                <div className={css.geoList}>
                  {pa.geography.leastLookedAt.slice(0, 10).map((g) => (
                    <div key={g.place} className={css.geoRow}>
                      <span className={css.geoName}>{g.place}</span>
                      <span className={css.geoTrack}>
                        <span className={css.geoBar} data-f="dose"
                              style={{ width: Math.max(0.4, ((g.perHundredM ?? 0) / (pa.geography.byRate[0].perHundredM || 1)) * 100) + "%" }} />
                      </span>
                      <span className={css.geoN}>{(g.perHundredM ?? 0).toFixed(1)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            {pa.geography.absentEntirely.length > 0 && (
              <p className={css.absent}>
                <span className={css.label}>No prevalence record at all</span>{" "}
                {pa.geography.absentEntirely
                  .map((a) => a.place + " (" + a.populationM + "M)")
                  .join(" \u00b7 ")}
                . Between them that is{" "}
                {pa.geography.absentEntirely.reduce((n, a) => n + a.populationM, 0)
                  .toLocaleString("en-US")}{" "}
                million people about whom this corpus says nothing, which is a fact about the
                corpus and not about them.
              </p>
            )}
          </section>

          {/* 2 - the double count */}
          <section className={css.ladderPanel}>
            <h4 className={css.h4}>
              {math.sharing.instrumentSlotsAcrossPlans} instrument slots across the plans resolve
              to {math.sharing.distinctInstruments} distinct instruments
            </h4>
            <p className={css.sub}>
              Each plan was costed as if its programme bought everything it needs. Summing the
              plans, and then summing the union of distinct instruments, gives the difference -
              which is what a shared facility is worth, computed rather than advocated.
            </p>
            <div className={css.compare}>
              <div className={css.cmpRow}>
                <span className={css.cmpL}>Each programme buying its own</span>
                <span className={css.cmpTrack}>
                  <span className={css.cmpBar} data-f="patient" style={{ width: "100%" }} />
                </span>
                <span className={css.cmpV}>{usd(math.sharing.sumOfPlansUSD.hi)}</span>
              </div>
              <div className={css.cmpRow}>
                <span className={css.cmpL}>One shared facility, same capability</span>
                <span className={css.cmpTrack}>
                  <span
                    className={css.cmpBar}
                    data-f="cell"
                    style={{
                      width:
                        (math.sharing.unionOfInstrumentsUSD.hi / math.sharing.sumOfPlansUSD.hi) * 100 + "%",
                    }}
                  />
                </span>
                <span className={css.cmpV}>{usd(math.sharing.unionOfInstrumentsUSD.hi)}</span>
              </div>
            </div>
            <p className={css.cmpNote}>
              <strong>
                {usd(math.sharing.doubleCountedUSD.lo)}&ndash;{usd(math.sharing.doubleCountedUSD.hi)} is
                counted twice &mdash; {Math.round(math.sharing.doubleCountedFraction * 100)}% of the total.
              </strong>{" "}
              Ordered below by how many programmes want the same machine.
            </p>
            <div className={css.shareGrid}>
              {math.sharing.byInstrument.filter((i) => i.plans > 1).map((i) => (
                <div key={i.id} className={css.share}>
                  <span className={css.shareN}>{i.plans} plans</span>
                  <span className={css.shareName}>{i.name}</span>
                  <span className={css.shareWaste}>
                    {usd(i.wastedIfNotSharedUSD.lo)}&ndash;{usd(i.wastedIfNotSharedUSD.hi)} spent over again
                  </span>
                  <span className={css.shareWho}>{i.diseases.join(" \u00b7 ")}</span>
                </div>
              ))}
            </div>
          </section>

          {/* 3 - the queue */}
          <section className={css.ladderPanel}>
            <h4 className={css.h4}>How long one instrument would need to run the whole cohort once</h4>
            <p className={css.sub}>
              Cohort divided by realistic annual throughput. For most of these the answer is a
              fraction of one machine for a fraction of a year - the capacity exists and is not
              pointed here. One row is not like the others, and it is a manufacturing row rather
              than a diagnostic one.
            </p>
            <div className={css.queue}>
              {math.queue.map((q) => (
                <div key={q.planId} className={css.qRow}>
                  <span className={css.qName}>{q.catalogueName}</span>
                  <span className={css.qBottle}>{q.bottleneck}</span>
                  <span className={q.bottleneckYears > 5 ? css.qYearsBad : css.qYears}>
                    {q.bottleneckYears >= 1
                      ? Math.round(q.bottleneckYears).toLocaleString("en-US") + " instrument-years"
                      : Math.round(q.bottleneckYears * 52) + " weeks"}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* 4 - capital rank against cost-per-answer rank */}
          <section className={css.ladderPanel}>
            <h4 className={css.h4}>Expensive to own is not expensive to use</h4>
            <p className={css.sub}>
              Ranking the instruments by capital, and again by cost per answer, moves them. A
              positive move means dearer to buy than to use - it amortises. A negative move means
              the opposite: cheap to buy and costly per answer, because it runs rarely or its
              consumables dominate.
            </p>
            <div className={css.moves}>
              {math.capitalVsAnswer.slice(0, 8).map((m) => (
                <div key={m.id} className={css.move}>
                  <span className={css.moveName}>{m.name}</span>
                  <span className={css.moveCap}>#{m.rankByCapital} by capital</span>
                  <span className={css.moveArrow} aria-hidden="true">&rarr;</span>
                  <span className={css.moveAns}>#{m.rankByAnswer} by cost per answer</span>
                  <span className={m.move > 0 ? css.moveUp : css.moveDown}>
                    {m.move > 0 ? "+" + m.move : m.move} places
                  </span>
                  <span className={css.moveUnit}>{usd(m.costPerAnswerUSD)} per {m.unit}</span>
                </div>
              ))}
            </div>
          </section>

          <div className={css.assume}>
            <span className={css.label}>What this assumes, stated so it can be attacked</span>
            {Object.entries(math.assumptions)
              .filter(([, v]) => typeof v === "string")
              .map(([k, v]) => <p key={k}>{v as string}</p>)}
          </div>
        </div>
      )}

      <p className={css.provenance}>
        <strong>On these numbers.</strong> {cap.provenance}
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

function Cell({ l, v, s }: { l: string; v: string; s: string }) {
  return (
    <div className={css.cellBox}>
      <span className={css.cellL}>{l}</span>
      <span className={css.cellV}>{v}</span>
      <span className={css.cellS}>{s}</span>
    </div>
  );
}
