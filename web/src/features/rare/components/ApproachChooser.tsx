/** Which approach fits *this* programme — a parameterised model that shows its work.
 *
 *  The atlas answers "what is known". This answers "given what I have, what should I do",
 *  which is the question a researcher actually arrives with. It is deliberately not an
 *  oracle: every weight is the user's, every rule is one sentence, and the output is a
 *  ranking *with its decomposition*, because a ranking without one is an opinion wearing a
 *  number.
 *
 *  Three states are kept distinct, which is the same discipline as the typed unknowns in
 *  the lexicon:
 *    scored high    — fits, and here is what carried it
 *    scored low     — considered, and here is what sank it
 *    RULED OUT      — a hard constraint makes it impossible, which is not a low score
 */
import { useMemo, useState } from "react";
import { EChart } from "../../../components/organisms/EChart";
import { chartInk, diverging, type Mode } from "../../../lib/palette";
import {
  DEFAULT_WEIGHTS, evaluate, leaderStability,
  type Params, type Weights,
} from "../approach";
import css from "./ApproachChooser.module.css";

const VARIANTS: { id: Params["variant"]; label: string }[] = [
  { id: "transition_snv", label: "Transition SNV (C>T, A>G)" },
  { id: "transversion_snv", label: "Transversion SNV" },
  { id: "small_indel", label: "Small indel" },
  { id: "large_deletion", label: "Large deletion" },
  { id: "repeat_expansion", label: "Repeat expansion" },
  { id: "splice", label: "Splice variant" },
  { id: "whole_gene_loss", label: "Whole-gene loss" },
];

const TISSUES: { id: Params["tissue"]; label: string }[] = [
  { id: "liver", label: "Liver" },
  { id: "cns", label: "CNS" },
  { id: "muscle", label: "Muscle" },
  { id: "eye", label: "Eye" },
  { id: "haematopoietic", label: "Blood" },
  { id: "systemic", label: "Systemic" },
];

const MECHANISMS: { id: Params["mechanism"]; label: string }[] = [
  { id: "loss_of_function", label: "Loss of function" },
  { id: "gain_of_function", label: "Toxic gain of function" },
  { id: "dominant_negative", label: "Dominant negative" },
];

const WEIGHT_LABELS: Record<keyof Weights, string> = {
  precision: "Addressing the exact lesion",
  delivery: "Reaching the tissue",
  speed: "Time to a construct",
  evidence: "Prior human data",
  reusability: "Carries to the next patient",
};

export function ApproachChooser() {
  const [p, setP] = useState<Params>({
    variant: "transition_snv",
    tissue: "cns",
    cdsKb: 3.2,
    patients: 4,
    monthsToAct: 12,
    mechanism: "loss_of_function",
  });
  const [w, setW] = useState<Weights>(DEFAULT_WEIGHTS);
  const [open, setOpen] = useState<string | null>(null);

  const verdicts = useMemo(() => evaluate(p, w), [p, w]);
  const stability = useMemo(() => leaderStability(p, w), [p, w]);
  const scored = verdicts.filter((v) => v.score !== null);
  const ruledOut = verdicts.filter((v) => v.score === null);
  const focus = verdicts.find((v) => v.approach.id === open) ?? scored[0];

  const set = <K extends keyof Params>(k: K, v: Params[K]) => setP((s) => ({ ...s, [k]: v }));

  /** Contribution breakdown: a diverging bar, because the quantity is signed and the
   *  question is "what pushed this up and what pulled it down". */
  const build = useMemo(
    () => (mode: Mode) => {
      const ink = chartInk(mode);
      const div = diverging(mode);
      const pos = div[div.length - 2];
      const neg = div[1];
      const rows = (focus?.criteria ?? []).map((c) => ({
        name: c.label,
        value: c.raw * (w[c.key] ?? 1),
        why: c.why,
      }));
      return {
        animation: false,
        grid: { left: 178, right: 40, top: 10, bottom: 34 },
        tooltip: {
          trigger: "item",
          formatter: (o: { dataIndex: number }) =>
            `<strong>${rows[o.dataIndex].name}</strong><br/>${rows[o.dataIndex].why}`,
          extraCssText: "max-width:320px;white-space:normal;line-height:1.5",
        },
        xAxis: {
          type: "value",
          min: -1.6, max: 1.6,
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: ink.grid } },
          axisLabel: { color: ink.muted, fontSize: 11 },
          name: "pulls against  ←     → carries it",
          nameLocation: "middle",
          nameGap: 24,
          nameTextStyle: { color: ink.muted, fontSize: 11 },
        },
        yAxis: {
          type: "category",
          data: rows.map((r) => r.name),
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { color: ink.text, fontSize: 12 },
        },
        series: [
          {
            type: "bar",
            barWidth: 16,
            itemStyle: {
              borderRadius: 3,
              color: (o: { value: number }) => (o.value >= 0 ? pos : neg),
            },
            label: {
              show: true,
              position: "right",
              formatter: (o: { value: number }) => (o.value >= 0 ? "+" : "") + o.value.toFixed(2),
              color: ink.muted,
              fontSize: 11,
            },
            data: rows.map((r) => r.value),
          },
        ],
      };
    },
    [focus, w]
  );

  return (
    <div className={css.root}>
      {/* ---- parameters ------------------------------------------------------- */}
      <aside className={css.panel} aria-label="Programme parameters">
        <h4 className={css.panelTitle}>Your programme</h4>

        <Select label="Variant class" value={p.variant} options={VARIANTS}
                onChange={(v) => set("variant", v)} />
        <Select label="Target tissue" value={p.tissue} options={TISSUES}
                onChange={(v) => set("tissue", v)} />
        <Select label="Disease mechanism" value={p.mechanism} options={MECHANISMS}
                onChange={(v) => set("mechanism", v)} />

        <Slider label="Coding sequence" value={p.cdsKb} min={0.5} max={12} step={0.1}
                unit="kb" onChange={(v) => set("cdsKb", v)}
                hint={p.cdsKb > 4.7 ? "beyond single-AAV capacity" : "fits a single AAV"} />
        <Slider label="Patients known worldwide" value={p.patients} min={1} max={200} step={1}
                unit="" onChange={(v) => set("patients", v)}
                hint={p.patients <= 12 ? "n-of-1 territory" : "a conventional cohort"} />
        <Slider label="Months until intervention must begin" value={p.monthsToAct}
                min={3} max={60} step={1} unit="mo" onChange={(v) => set("monthsToAct", v)}
                hint={p.monthsToAct <= 12 ? "urgent" : "time to develop"} />

        <h4 className={css.panelTitle}>What matters to you</h4>
        <p className={css.panelNote}>
          These are weights, not facts. Move them and watch the ranking — if it flips
          easily, the model is telling you the answer is not robust.
        </p>
        {(Object.keys(w) as (keyof Weights)[]).map((k) => (
          <Slider key={k} label={WEIGHT_LABELS[k]} value={w[k]} min={0} max={2} step={0.1}
                  unit="×" onChange={(v) => setW((s) => ({ ...s, [k]: v }))} />
        ))}
      </aside>

      {/* ---- ranking ---------------------------------------------------------- */}
      <div className={css.results}>
        <div className={css.stability}>
          {stability.stable ? (
            <><span className={css.stableTag}>robust</span> The leader survives moving any
            single weight by ±0.5.</>
          ) : (
            <><span className={css.fragileTag}>fragile</span> The leader changes if you move{" "}
              {stability.flips.join(", ")}. Treat the ranking as a shortlist, not a choice.</>
          )}
        </div>

        <ol className={css.list}>
          {scored.map((v, i) => (
            <li key={v.approach.id}>
              <button
                type="button"
                className={focus?.approach.id === v.approach.id ? css.rowOn : css.row}
                onClick={() => setOpen(v.approach.id)}
                aria-expanded={focus?.approach.id === v.approach.id}
              >
                <span className={css.rank}>{i + 1}</span>
                <span className={css.rowMain}>
                  <span className={css.name}>{v.approach.name}</span>
                  <span className={css.note}>{v.approach.note}</span>
                </span>
                <ScoreBar score={v.score!} />
              </button>
            </li>
          ))}
        </ol>

        {ruledOut.length > 0 && (
          <div className={css.ruled}>
            <h4 className={css.ruledTitle}>Ruled out — not scored low, impossible</h4>
            <ul className={css.ruledList}>
              {ruledOut.map((v) => (
                <li key={v.approach.id}>
                  <span className={css.ruledName}>{v.approach.name}</span>
                  <span className={css.ruledWhy}>{v.ruledOutBy}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* ---- why -------------------------------------------------------------- */}
      {focus && focus.score !== null && (
        <section className={css.why}>
          <h4 className={css.whyTitle}>
            Why <strong>{focus.approach.name}</strong> scores {Math.round(focus.score)}
          </h4>
          <p className={css.whySub}>
            Each bar is one criterion, already multiplied by your weight. Hover a bar for the
            rule behind it — there are no hidden terms.
          </p>
          <EChart
            build={build}
            height={230}
            deps={[focus, w]}
            ariaLabel={`Contribution breakdown for ${focus.approach.name}: ${focus.criteria
              .map((c) => `${c.label} ${(c.raw * (w[c.key] ?? 1)).toFixed(2)}`)
              .join(", ")}`}
          />
        </section>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- small pieces */

function ScoreBar({ score }: { score: number }) {
  const pctOf = (v: number) => `${Math.abs(v) / 2}%`;
  return (
    <span className={css.scoreWrap}>
      <span className={css.scoreTrack}>
        <span className={css.scoreZero} />
        <span
          className={score >= 0 ? css.scorePos : css.scoreNeg}
          style={{ width: pctOf(score), [score >= 0 ? "left" : "right"]: "50%" }}
        />
      </span>
      <span className={css.scoreNum}>{score >= 0 ? "+" : ""}{Math.round(score)}</span>
    </span>
  );
}

function Select<T extends string>({
  label, value, options, onChange,
}: { label: string; value: T; options: { id: T; label: string }[]; onChange: (v: T) => void }) {
  return (
    <label className={css.field}>
      <span className={css.fieldLabel}>{label}</span>
      <select className={css.select} value={value} onChange={(e) => onChange(e.target.value as T)}>
        {options.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
      </select>
    </label>
  );
}

function Slider({
  label, value, min, max, step, unit, onChange, hint,
}: {
  label: string; value: number; min: number; max: number; step: number;
  unit: string; onChange: (v: number) => void; hint?: string;
}) {
  return (
    <label className={css.field}>
      <span className={css.fieldLabel}>
        {label}
        <span className={css.fieldValue}>{value}{unit && ` ${unit}`}</span>
      </span>
      <input className={css.range} type="range" min={min} max={max} step={step} value={value}
             onChange={(e) => onChange(Number(e.target.value))} />
      {hint && <span className={css.hint}>{hint}</span>}
    </label>
  );
}
