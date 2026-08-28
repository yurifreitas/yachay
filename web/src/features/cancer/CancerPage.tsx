import { Suspense, lazy, useMemo } from "react";
import { useHashParam } from "../../lib/useHashParam";
import { useRemoteData } from "../../lib/useRemoteData";
import { identityScale } from "../../lib/palette";
import {
  DEFAULT_REGISTERED, LEVELS, LEVEL_LABEL, LEVEL_BLURB, cancellation, controls, footprints,
  gateInputs, ordered, privateCount, regate, type CancerLevel, type Gates, type Subgroup,
} from "../../lib/cancerModel";
import GateControls, { useGates } from "./GateControls";
import ChoiceGroup from "../../components/atoms/ChoiceGroup";
import { SectionHeading } from "../../components/molecules/SectionHeading";
import { useSectionNav, type NavGroupDef, type NavSectionDef } from "../../lib/nav";
import { CANCER } from "../../i18n/strings";
import s from "./CancerPage.module.css";

/** Split out: the genotype view carries its own model, its own stylesheet and a 78 kB
 *  dataset, and a reader who only wants the lineage answer should not download it. */
const GenotypeView = lazy(() => import("./GenotypeView"));

/** Grouped thousands, pinned to the page's own language rather than the reader's browser.
 *  `toLocaleString()` with no argument rendered 1242 as "1.242" under a pt-BR browser, which
 *  inside an English sentence reads as a decimal — a number that is wrong by a factor of a
 *  thousand and looks deliberate. The prose here is English; so is its number formatting. */
const fmt = (n: number) => n.toLocaleString("en-US");

/** Cancer, by subgroup — the section this repository should have had first.
 *
 *  DepMap is `sieve`'s reference application and the source of every calibration result it
 *  publishes, and until now the interface showed it scored as ONE POOL: 17,916 genes across
 *  1,178 cell lines with no regard for what cancer those lines are. That answers "what is
 *  broadly essential", which is the question whose top is 60 % pan-essential genes.
 *
 *  Everything here answers the other question — which gene does *this* cancer depend on that
 *  others do not — at three nested levels of subgroup that were sitting unread in Model.csv.
 *
 *  ON COLOUR. There are 24 lineages and 37 subtypes, and none of these panels asks the reader
 *  to rank 24 colours against each other. Colour is identity: find the subgroup you chose,
 *  recognise it in the next panel. Every mark is directly labelled and the hue only confirms
 *  — see `identityScale` in lib/palette.ts for why that permits a scale the six-hue
 *  categorical cap would not.
 */
/** THE PANELS WERE A SCROLL, AND A SCROLL IS NOT A STRUCTURE.
 *
 *  Every other page on this site states the questions it answers and lets a reader open one.
 *  This one stacked seven panels under a two-way switch, so the fifth panel was reachable
 *  only by scrolling past four others, could not be linked to, and announced nothing about
 *  itself from outside. The panels were already answering four distinct questions — how big
 *  the contrast is, what could have been detected at all, what one subgroup needs, and
 *  whether the positive controls came back — so those are the groups, and each panel is a
 *  section with its own URL.
 *
 *  The catalogue/genotype split becomes the top level rather than a control above the
 *  panels: they are two questions, not two views of one. "Melanoma" is a label someone
 *  assigned; "carries a damaging mutation in SMARCA4" is a property of the cell.
 */
const GROUPS: NavGroupDef[] = [
  { id: "catalogue", label: CANCER.gCatalogue, question: CANCER.qCatalogue },
  { id: "genotype", label: CANCER.gGenotype, question: CANCER.qGenotype },
];

const SECTIONS: NavSectionDef[] = [
  { id: "scale", label: CANCER.sScale, group: "catalogue" },
  { id: "power", label: CANCER.sPower, group: "catalogue" },
  { id: "subgroup", label: CANCER.sSubgroup, group: "catalogue" },
  { id: "shared", label: CANCER.sShared, group: "catalogue" },
  { id: "controls", label: CANCER.sControls, group: "catalogue" },
  { id: "genotype", label: CANCER.sGenotype, group: "genotype" },
];

export default function CancerPage() {
  const { section, group: mode } = useSectionNav({
    owner: "cancer", groups: GROUPS, sections: SECTIONS, initial: "scale",
  });
  const [level, setLevel] = useHashParam("level", "lineage");
  const [pick, setPick] = useHashParam("group", "");

  const lin = useRemoteData<CancerLevel>("data/cancer_subgroups_lineage.json");
  // keepPrevious: changing the level is a filter on the same question, not a new page.
  const cur = useRemoteData<CancerLevel>(`data/cancer_subgroups_${level}.json`,
                                         { keepPrevious: true });
  const sub = useRemoteData<CancerLevel>("data/cancer_subgroups_subtype.json");

  if (cur.state === "loading") return <Skeleton />;
  if (cur.state === "error") {
    return (
      <section className={s.page}>
        <p className={s.error}>
          Could not load the subgroup analysis ({cur.message}). It is written by{" "}
          <code>python tools/cancer_subgroups.py</code> and converted by{" "}
          <code>npm run data</code>.
        </p>
      </section>
    );
  }

  const data = cur.data;
  const registered = (data as { gates?: { registered?: typeof DEFAULT_REGISTERED } })
    .gates?.registered ?? DEFAULT_REGISTERED;
  const groups = ordered(data);
  const stale = cur.state === "ready" && cur.stale === true;
  const chosen = groups.find((g) => g.subgroup === pick) ?? groups[0];
  const split =
    lin.state === "ready" && sub.state === "ready" ? cancellation(lin.data, sub.data) : null;

  return (
    <section className={s.page} aria-busy={stale || undefined}>
      {/* The header follows the mode. Leaving the catalogue title and premise standing over
          the genotype answer would have described one analysis while showing another. */}
      <header className={s.head}>
        <p className={s.eyebrow}>
          {mode === "genotype"
            ? "Stage 0 · Stage 2 · Stage 3 · DepMap 24Q2"
            : "Stage 2 · Stage 3 · DepMap 24Q2"}
        </p>
        <h2>
          {mode === "genotype"
            ? "What a mutation makes a cell need"
            : "What each cancer needs that the others do not"}
        </h2>
        <p className={s.lede}>
          {mode === "genotype"
            ? "A catalogue label is a name someone assigned; a damaging mutation is a "
              + "property of the cell, and it is the grouping a target programme acts on. "
              + "Two confounds sit between that question and its answer — lineage and "
              + "mutational burden — and both are measured here rather than disclaimed."
            : data.premise}
        </p>
      </header>

      <SectionHeading />

      {mode === "genotype" ? (
        <Suspense fallback={<div className={s.skelPanel} />}>
          <GenotypeView />
        </Suspense>
      ) : (
        <>
          {/* The level is the SCOPE of every catalogue panel, not a control belonging to one
              of them, so it stays put while the sections change underneath it. Moving it
              inside a panel would have made the reader re-choose it on the way to each. */}
          <LevelSwitch level={level} setLevel={setLevel} scale={data.scale} stale={stale} />

          {section === "scale" && (
            <>
              <Kpis data={data} />
              {split && <Cancellation split={split} />}
            </>
          )}

          {section === "power" && <Power groups={groups} chosen={chosen} onPick={setPick} />}

          {section === "subgroup" && (
            <>
              {/* The plane in "What could be detected at all" is where a subgroup is
                  normally chosen. Arriving here by link, there was nothing to choose with
                  and the panel showed whichever subgroup happened to sort first — a page
                  about one subgroup with no way to say which. */}
              <SubgroupPicker groups={groups} chosen={chosen} onPick={setPick} />
              <Gated group={chosen} level={level} registered={registered} />
            </>
          )}

          {section === "shared" && <Shared data={data} />}

          {section === "controls" && <Controls data={data} />}
        </>
      )}
    </section>
  );
}

/* ------------------------------------------------------------------ KPI row */

function Kpis({ data }: { data: CancerLevel }) {
  const c = controls(data);
  const back = c.filter((x) => x.rank !== null).length;
  const tiles = [
    { n: data.scale.subgroups, label: "subgroups", note: `at least 8 screened lines` },
    {
      n: data.scale.powered, label: "can detect 0.8 SD",
      note: `${data.scale.underpowered} cannot, and are marked rather than dropped`,
      tone: "good" as const,
    },
    {
      n: data.scale.panEssentialDropped, label: "pan-essentials removed",
      note: "Stage 3, before ranking rather than after", tone: "warn" as const,
    },
    {
      n: c.length ? `${back}/${c.length}` : "—", label: "positive controls back",
      note: "textbook lineage dependencies, recovered blind",
    },
  ];
  return (
    <div className={s.kpis}>
      {tiles.map((t) => (
        <div key={t.label} className={s.kpi} data-tone={t.tone}>
          <span className={s.kpiN}>{typeof t.n === "number" ? fmt(t.n) : t.n}</span>
          <span className={s.kpiL}>{t.label}</span>
          <span className={s.kpiNote}>{t.note}</span>
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------ the finding that justifies the level switch */

function Cancellation({ split }: { split: NonNullable<ReturnType<typeof cancellation>> }) {
  return (
    <div className={s.finding}>
      <p className={s.findingTag}>Why the grouping is the analysis</p>
      <h3>
        Pooled <strong>Lung</strong> has {split.pooled.lines} screened lines — the best-powered
        subgroup here — and returns <strong>nothing</strong>.
      </h3>
      <p>
        Split at the subtype level, both halves light up, each with the genes its biology
        predicts. They were cancelling: a dependency present in one half and absent in the
        other averages to no difference from everything else. A null result at the coarse
        level is not evidence of no dependency; it can be evidence of the wrong grouping.
      </p>
      <div className={s.splitRow}>
        {split.parts.map((p) => (
          <div key={p.subgroup} className={s.splitCard}>
            <span className={s.splitName}>{p.subgroup}</span>
            <span className={s.splitMeta}>{p.lines} lines · {p.hitCount} hits</span>
            <span className={s.splitGenes}>
              {p.hits.slice(0, 5).map((h) => h.gene).join(" · ")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ level switch */

function LevelSwitch(
  { level, setLevel, scale, stale }:
  { level: string; setLevel: (v: string) => void; scale: CancerLevel["scale"];
    stale: boolean },
) {
  return (
    <div className={s.levels}>
      <ChoiceGroup
        label="Subgroup level"
        value={level}
        onChange={setLevel}
        choices={LEVELS.map((l) => ({ id: l, label: LEVEL_LABEL[l] }))}
      />
      {/* Busy, not blank: the previous level stays readable and is marked as such. */}
      <p className={s.staleNote} role="status" aria-live="polite">
        {stale ? `Loading the ${LEVEL_LABEL[level].toLowerCase()} level — the figures below
          are still the previous one.` : ""}
      </p>
      <p className={s.levelNote}>
        {LEVEL_BLURB[level]} Each level re-runs the whole contrast — {fmt(scale.genesAfterStage3)} genes against {fmt(scale.lines)} lines — because a
        subgroup&rsquo;s comparison set is every line outside it, and that set changes when the
        grouping does.
      </p>
    </div>
  );
}

/* A list, not a chart: 24 lineages need a control that stays one line tall above a panel
   whose subject is a single one of them. */
function SubgroupPicker(
  { groups, chosen, onPick }:
  { groups: Subgroup[]; chosen: Subgroup; onPick: (v: string) => void },
) {
  return (
    <div className={s.levels}>
      <label className={s.pickerLabel}>
        Subgroup{" "}
        <select value={chosen.subgroup} onChange={(e) => onPick(e.target.value)}>
          {groups.map((g) => (
            <option key={g.subgroup} value={g.subgroup}>
              {g.subgroup} ({fmt(g.lines)} lines)
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

/* --------------------------------------------------- panel 1: what could be seen at all */

function Power(
  { groups, chosen, onPick }:
  { groups: Subgroup[]; chosen: Subgroup; onPick: (v: string) => void },
) {
  const colours = useMemo(
    () => identityScale(groups.map((g) => g.subgroup)), [groups]);
  const maxLines = Math.max(...groups.map((g) => g.lines));

  return (
    <section className={s.panel}>
      <h3>Which subgroups could detect anything, and which only look empty</h3>
      <p className={s.sub}>
        Bar length is the smallest effect the subgroup&rsquo;s size can detect, from{" "}
        <code>sieve.stages.power</code>. Below the marked line a subgroup can see a large
        effect; above it, an empty result means the screen could not resolve one — not that
        none exists. Click to inspect.
      </p>
      <ul className={s.powerList}>
        {groups.map((g) => (
          <li key={g.subgroup}>
            <button
              className={g.subgroup === chosen.subgroup ? s.rowOn : s.row}
              onClick={() => onPick(g.subgroup)}
              aria-pressed={g.subgroup === chosen.subgroup}
            >
              <span className={s.swatch} style={{ background: colours[g.subgroup] }} />
              <span className={s.rowName}>{g.subgroup}</span>
              <span className={s.rowBarWrap}>
                <span
                  className={s.rowBar}
                  style={{ width: `${(g.lines / maxLines) * 100}%`,
                           background: colours[g.subgroup] }}
                />
              </span>
              <span className={s.rowNum}>{g.lines}</span>
              <span className={g.powered ? s.floorOk : s.floorBad}>
                {g.detectableFloor?.toFixed(2) ?? "—"}
              </span>
              <span className={g.hitCount ? s.hits : s.hitsNone}>
                {g.powered
                  ? `${g.hitCount} hit${g.hitCount === 1 ? "" : "s"}`
                  : "underpowered"}
              </span>
            </button>
          </li>
        ))}
      </ul>
      <p className={s.axisNote}>
        columns: screened lines · smallest detectable effect (SD) · result
      </p>
    </section>
  );
}

/** The gates and the panel they govern, kept adjacent: a control whose effect is off-screen
 *  is a control nobody trusts. */
function Gated(
  { group, level, registered }:
  { group: Subgroup; level: string; registered: typeof DEFAULT_REGISTERED },
) {
  const [gates, set, dirty, reset] = useGates(registered);
  const { rows, total } = regate(group, gates);
  return (
    <>
      <GateControls gates={gates} set={set} dirty={dirty} reset={reset} reg={registered}
                    kept={rows.length} total={total} rows={gateInputs(group)} />
      <Detail group={group} level={level} rows={rows} gates={gates} dirty={dirty} />
    </>
  );
}

/* ------------------------------------------- panel 2: the chosen subgroup, both ends shown */

function Detail(
  { group, level, rows, gates, dirty }:
  { group: Subgroup; level: string; rows: Subgroup["hits"]; gates: Gates; dirty: boolean },
) {
  const span = useMemo(() => {
    const all = rows.flatMap((h) => [h.meanInGroup, h.meanElsewhere]);
    // Padded by 4 % at each end: without it the gene at the maximum lands at left:100% and
    // is drawn half outside the track.
    const lo = Math.min(0, ...all), hi = Math.max(1, ...all), pad = (hi - lo) * 0.04;
    return { lo: lo - pad, hi: hi + pad };
  }, [rows]);
  const x = (v: number) => ((v - span.lo) / (span.hi - span.lo)) * 100;

  return (
    <section className={s.panel}>
      <h3>
        {group.subgroup}
        <span className={s.badge}>{LEVEL_LABEL[level]}</span>
        {dirty && <span className={s.badgeMoved}>re-gated</span>}
      </h3>
      <p className={s.sub}>{group.says}</p>

      {rows.length === 0 ? (
        <p className={s.empty}>
          {dirty
            ? "Nothing clears the gates as you have set them. Widen a threshold, or restore "
              + "the registered values above \u2014 an empty list at settings chosen after "
              + "seeing the data says something about the settings, not about this subgroup."
            : group.powered
            ? "No gene cleared the gates here. With this many lines the screen could have "
              + "resolved a large effect, so this is a measured absence rather than a blind spot."
            : "Nothing to draw, and nothing to conclude: this subgroup is too small to have "
              + "detected a large effect had one been present."}
        </p>
      ) : (
        <>
          <p className={s.sub}>
            Each row is a dumbbell: the hollow end is the gene&rsquo;s mean dependency{" "}
            <em>everywhere else</em>, the filled end is its mean <em>inside this subgroup</em>.
            Both ends are drawn because the gap alone does not make a target — the filled end
            must also be a real dependency. That is the Stage 0 gate, and it is here because
            an earlier version of this analysis lacked it and ranked genes the rest of the
            panel depended on more.
          </p>
          <ul className={s.dumbbells}>
            {rows.map((h) => (
              <li key={h.gene}>
                <span className={s.gene}>{h.gene}</span>
                <span className={s.track}>
                  <span className={s.zero} style={{ left: `${x(gates.floor)}%` }} />
                  <span
                    className={s.link}
                    style={{
                      left: `${Math.min(x(h.meanElsewhere), x(h.meanInGroup))}%`,
                      width: `${Math.abs(x(h.meanInGroup) - x(h.meanElsewhere))}%`,
                    }}
                  />
                  <span className={s.dotOpen} style={{ left: `${x(h.meanElsewhere)}%` }}
                        title={`elsewhere ${h.meanElsewhere.toFixed(3)}`} />
                  <span className={s.dotFull} style={{ left: `${x(h.meanInGroup)}%` }}
                        title={`in group ${h.meanInGroup.toFixed(3)}`} />
                </span>
                <span className={s.d}>{h.d.toFixed(2)}</span>
                <span className={s.q}>
                  q&nbsp;{h.q < 1e-4 ? h.q.toExponential(0) : h.q.toFixed(4)}
                </span>
              </li>
            ))}
          </ul>
          <p className={s.axisNote}>
            dashed line: the {gates.floor.toFixed(2)} dependency floor a filled end must clear · columns: Cohen&rsquo;s
            d, then the Benjamini&ndash;Hochberg q within this subgroup
          </p>
        </>
      )}
    </section>
  );
}

/* ---------------------------------------- panel 3: private to a cancer, or shared across */

function Shared({ data }: { data: CancerLevel }) {
  const shared = useMemo(() => footprints(data).slice(0, 14), [data]);
  const priv = useMemo(() => privateCount(data), [data]);
  const colours = useMemo(
    () => identityScale(data.results.map((r) => r.subgroup)), [data]);

  if (!shared.length) {
    return (
      <section className={s.panel}>
        <h3>Private or shared</h3>
        <p className={s.empty}>
          Every hit at this level appears in exactly one subgroup, so there is no shared
          structure to draw.
        </p>
      </section>
    );
  }

  return (
    <section className={s.panel}>
      <h3>Private to one cancer, or shared across several</h3>
      <p className={s.sub}>
        A target list cannot answer this on its own, and the difference decides what a therapy
        would have to be selective against. <strong>{priv}</strong> genes are private to a
        single subgroup; these {shared.length} recur, which puts them closer to a pathway than
        to a lineage vulnerability.
      </p>
      <ul className={s.shared}>
        {shared.map((f) => (
          <li key={f.gene}>
            <span className={s.gene}>{f.gene}</span>
            <span className={s.chips}>
              {f.groups.map((g) => (
                <span
                  key={g.subgroup} className={s.chip}
                  style={{ borderColor: colours[g.subgroup] }}
                >
                  <span className={s.chipDot} aria-hidden="true"
                        style={{ background: colours[g.subgroup] }} />
                  {g.subgroup} <b>{g.d.toFixed(1)}</b>
                </span>
              ))}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

/* --------------------------------------------------------------- panel 4: the controls */

function Controls({ data }: { data: CancerLevel }) {
  const rows = controls(data);
  if (!rows.length) return null;
  const back = rows.filter((r) => r.rank !== null).length;
  return (
    <section className={s.panel}>
      <h3>Positive controls, reported whole</h3>
      <p className={s.sub}>
        Textbook lineage dependencies named in the analysis before it ran, checked on every
        run. <strong>{back} of {rows.length}</strong> came back. The {rows.length - back} that
        did not are listed with their result rather than folded into a pass rate, because a
        single percentage would let a specific failure read as noise.
      </p>
      <table className={s.table}>
        <thead>
          <tr><th>Subgroup</th><th>Control</th><th>Rank in the shortlist</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={`${r.subgroup}-${r.gene}`}>
              <td>{r.subgroup}</td>
              <td><code>{r.gene}</code></td>
              <td className={r.rank === null ? s.miss : s.got}>
                {r.rank === null ? "not recovered" : `#${r.rank + 1}`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function Skeleton() {
  return (
    <div className={s.page} role="status" aria-live="polite">
      <span className="visually-hidden">Loading the subgroup analysis</span>
      <div className={s.skelHead} />
      <div className={s.skelKpis}>{[0, 1, 2, 3].map((i) => <div key={i} />)}</div>
      <div className={s.skelPanel} />
    </div>
  );
}
