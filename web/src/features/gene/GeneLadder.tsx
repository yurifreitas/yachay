import { useEffect, useState } from "react";
import { useT } from "../../i18n";
import { LADDER } from "../../i18n/ladder";
import css from "./GeneLadder.module.css";

/** ONE GENE FROM THE RESIDUE TO THE ORGAN SYSTEM, WITH THE COST OF EVERY STEP PRINTED.
 *
 *  Every multiscale figure in biology draws this ladder and implies the steps are free. They
 *  are not. `tools/scale_information.py` measured two of them — collapsing a disease's genes
 *  onto Reactome pathways keeps 22 % of what they said about organ system, onto cell types
 *  31 % — and the other four have never been measured by anybody here.
 *
 *  SO THE CONNECTORS CARRY THE NUMBER OR THE ADMISSION, and there is no third option. A
 *  connector with a retention shows it. A connector without one says *not measured* and gives
 *  the reason. A ladder that printed a plausible-looking figure at every rung would be
 *  precisely the failure this repository exists to refuse, and it would be invisible.
 *
 *  The residue rung is the one that earns the word "anatomy": the protein drawn to length,
 *  UniProt domains and transmembrane spans laid over it, and the ClinVar variant histogram
 *  underneath split by significance — so a reader sees where the pathogenic variants sit
 *  relative to the domains, on the same axis, at the same scale.
 */

type Rung = { id: string; label: string; count: number; detail: any };
type Transition = { from: string; to: string; retention: number | null; why: string };
type Gene = { rungs: Rung[]; transitions: Transition[] };
type Payload = { genes: Record<string, Gene>; says?: string; limits?: string[];
                 provenance?: string; generated?: string };

const URL = `${import.meta.env.BASE_URL}data/gene_ladder.json`;

let cache: Payload | null = null;
let inflight: Promise<Payload> | null = null;

export function prefetchLadder(): Promise<Payload> {
  if (cache) return Promise.resolve(cache);
  if (!inflight) {
    inflight = fetch(URL).then((r) => r.json())
      .then((j) => { cache = j; return j; })
      .catch(() => ({ genes: {} } as Payload));
  }
  return inflight;
}

const FEATURE_COLOURS: Record<string, string> = {
  domain: "dom", membrane: "mem", motif: "mot", active: "act", binding: "bind",
};

/* ------------------------------------------------------------------ the residue rung */

function ResidueTrack({ detail }: { detail: any }) {
  const tt = useT();
  const length: number = detail.length ?? 0;
  const bins: number = detail.bins ?? 0;
  const hist = detail.hist ?? {};
  const features: { kind: string; start: number; end: number; label: string }[] =
    detail.features ?? [];
  const [hover, setHover] = useState<number | null>(null);

  const series = ["pathogenic", "uncertain", "benign", "conflicting"]
    .filter((k) => Array.isArray(hist[k]));
  if (!bins || series.length === 0) return null;

  const totals = Array.from({ length: bins }, (_, i) =>
    series.reduce((s, k) => s + (hist[k][i] ?? 0), 0));
  const max = Math.max(...totals, 1);
  const span = length || bins;

  return (
    <div className={css.residue}>
      {/* The protein, to length, with its features laid over it. */}
      <div className={css.protein}>
        {features.map((f, i) => (
          <span
            key={i}
            className={`${css.feature} ${css[FEATURE_COLOURS[f.kind] ?? "dom"]}`}
            style={{ left: `${(100 * f.start) / span}%`,
                     width: `${Math.max(0.4, (100 * (f.end - f.start)) / span)}%` }}
            title={`${f.label} · ${f.kind} · ${f.start}–${f.end}`}
          />
        ))}
      </div>

      {/* The variants, on the SAME axis, so position is comparable by eye. */}
      <div className={css.hist} onMouseLeave={() => setHover(null)}>
        {Array.from({ length: bins }, (_, i) => (
          <span key={i} className={css.histCol}
                data-hot={hover === i || undefined}
                onMouseEnter={() => setHover(i)}>
            {series.map((k) => (
              <span key={k}
                    className={`${css.histSeg} ${css[k]}`}
                    style={{ height: `${(100 * (hist[k][i] ?? 0)) / max}%` }} />
            ))}
          </span>
        ))}
      </div>

      <div className={css.residueFoot}>
        {hover != null
          ? <>
              <strong>{tt(LADDER.around)} {Math.round((hover / bins) * span)}</strong>
              {series.map((k) => (hist[k][hover] ? (
                <span key={k} className={css.chip}>
                  <span className={`${css.dot} ${css[k]}`} /> {hist[k][hover]} {k}
                </span>
              ) : null))}
            </>
          : <span className={css.hint}>
              {length ? `${length} ${tt(LADDER.residues)} · ` : ""}
              {features.length} {tt(LADDER.features)} · {totals.reduce((a, b) => a + b, 0)}{" "}
              {tt(LADDER.placed)}
            </span>}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ the ladder */

export default function GeneLadder({ gene }: { gene?: string }) {
  const tt = useT();
  const [data, setData] = useState<Payload | null>(cache);
  const [pick, setPick] = useState<string>(gene ?? "NF2");

  useEffect(() => {
    let alive = true;
    prefetchLadder().then((d) => { if (alive) setData(d); });
    return () => { alive = false; };
  }, []);

  if (!data) return <div className={css.skeleton} style={{ height: 560 }} aria-hidden />;
  const names = Object.keys(data.genes ?? {}).sort();
  if (names.length === 0) return null;
  const rec = data.genes[pick] ?? data.genes[names[0]];

  const byId = Object.fromEntries(rec.rungs.map((r) => [r.id, r]));
  const measured = rec.transitions.filter((t) => t.retention != null);

  /** The connector between two rungs. It carries the number or the admission — never a gap. */
  function Step({ t }: { t: Transition }) {
    return (
      <div className={css.step} data-measured={t.retention != null || undefined}>
        <span className={css.stepLine} aria-hidden />
        {t.retention != null
          ? <span className={css.stepVal}>
              {(100 * t.retention).toFixed(0)} % <em>{tt(LADDER.kept)}</em>
            </span>
          : <span className={css.stepNone}>{tt(LADDER.notMeasured)}</span>}
        <span className={css.stepWhy}>{t.why}</span>
      </div>
    );
  }

  const stepFor = (from: string) => rec.transitions.find((t) => t.from === from);

  return (
    <div className={css.wrap}>
      <div className={css.controls}>
        <span className={css.controlK}>{tt(LADDER.pick)}</span>
        {names.map((g) => (
          <button key={g} type="button"
                  className={`${css.chipBtn} ${pick === g ? css.chipOn : ""}`}
                  aria-pressed={pick === g}
                  onClick={() => setPick(g)}>{g}</button>
        ))}
      </div>

      <p className={css.lede}>
        <strong>{tt(LADDER.lede1)}</strong> {tt(LADDER.lede2)}{" "}
        <span className={css.ledeCount}>{measured.length} {tt(LADDER.ofSix)}</span>
      </p>

      {/* residue */}
      <section className={css.rung}>
        <header className={css.rungHead}>
          <span className={css.rungK}>{tt(LADDER.rResidue)}</span>
          <span className={css.rungN}>{byId.residue?.count ?? 0}</span>
        </header>
        <ResidueTrack detail={{ ...byId.residue?.detail,
                                length: byId.protein?.detail?.length }} />
      </section>

      <Step t={{ from: "residue", to: "protein", retention: null,
                 why: stepFor("residue")?.why ?? "" }} />

      {/* protein */}
      <section className={css.rung}>
        <header className={css.rungHead}>
          <span className={css.rungK}>{tt(LADDER.rProtein)}</span>
          <span className={css.rungN}>{byId.protein?.detail?.length ?? "—"} aa</span>
        </header>
        <div className={css.constraint}>
          {Object.entries(byId.protein?.detail?.constraint ?? {})
            .filter(([, v]) => typeof v === "number")
            .map(([k, v]) => (
              <span key={k} className={css.stat}>
                <em>{String(v)}</em><span>{k}</span>
              </span>
            ))}
        </div>
        <p className={css.note}>{byId.protein?.detail?.note}</p>
      </section>

      <Step t={stepFor("protein")!} />

      {/* interaction */}
      <section className={css.rung}>
        <header className={css.rungHead}>
          <span className={css.rungK}>{tt(LADDER.rInteraction)}</span>
          <span className={css.rungN}>{byId.interaction?.count ?? 0}</span>
        </header>
        <div className={css.chips}>
          {(byId.interaction?.detail?.partners ?? []).map((p: any) => (
            <span key={p.gene} className={css.partner}
                  style={{ opacity: 0.45 + 0.55 * ((p.score - 700) / 300) }}>
              {p.gene}
            </span>
          ))}
        </div>
      </section>

      <Step t={rec.transitions.find((t) => t.from === "gene" && t.to === "pathway")!} />

      {/* pathway */}
      <section className={css.rung}>
        <header className={css.rungHead}>
          <span className={css.rungK}>{tt(LADDER.rPathway)}</span>
          <span className={css.rungN}>{byId.pathway?.count ?? 0}</span>
        </header>
        <div className={css.chips}>
          {(byId.pathway?.detail?.names ?? []).map((n: string) => (
            <span key={n} className={css.chipFlat}>{n}</span>
          ))}
          {(byId.pathway?.count ?? 0) === 0 && (
            <span className={css.empty}>{tt(LADDER.noPathway)}</span>
          )}
        </div>
      </section>

      <Step t={rec.transitions.find((t) => t.from === "gene" && t.to === "cell_type")!} />

      {/* cell type */}
      <section className={css.rung}>
        <header className={css.rungHead}>
          <span className={css.rungK}>{tt(LADDER.rCell)}</span>
          <span className={css.rungN}>{byId.cell_type?.count ?? 0}</span>
        </header>
        <div className={css.chips}>
          {(byId.cell_type?.detail?.names ?? []).map((n: string) => (
            <span key={n} className={css.chipFlat}>{n}</span>
          ))}
        </div>
      </section>

      <Step t={stepFor("cell_type")!} />

      {/* organ system */}
      <section className={css.rung}>
        <header className={css.rungHead}>
          <span className={css.rungK}>{tt(LADDER.rSystem)}</span>
          <span className={css.rungN}>{byId.organ_system?.count ?? 0}</span>
        </header>
        <div className={css.systems}>
          {(byId.organ_system?.detail?.names ?? []).map((n: string) => {
            const ret = byId.organ_system?.detail?.retention?.[n];
            return (
              <span key={n} className={css.system}>
                {n}
                {ret != null && (
                  <em title={tt(LADDER.retentionTip)}>{(100 * ret).toFixed(0)} %</em>
                )}
              </span>
            );
          })}
        </div>
        <p className={css.note}>{tt(LADDER.systemNote)}</p>
      </section>

      <p className={css.saysNote}>{data.says}</p>
    </div>
  );
}
