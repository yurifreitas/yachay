import { useT, fill } from "../../i18n";
import { WORLD } from "../../i18n/world";
import { fmt, fmtInt, pct } from "../../lib/scale";
import { loeufBand, vusIsMeaningful, VUS_MIN_VARIANTS, type WorldRecord } from "./worldModel";
import type { GeneSearchIndex } from "./geneModel";
import css from "./GenePage.module.css";

/** The four panels built from public catalogues nothing here had read per gene.
 *
 *  Kept in their own file because they answer a different kind of question from the rest of
 *  the navigator. Everything else on the page is something THIS repository measured; these
 *  are things the world already knew and had never been brought together next to a screen
 *  result. The separation is not cosmetic — the provenance line under each says which.
 */

type Props = { world?: WorldRecord; scope: GeneSearchIndex["scope"] };

/* --------------------------------------------------------------------- form */

export function Form({ world }: Props) {
  const t = useT();
  const p = world?.prot;
  if (!p) return <p className={css.absentPanel}>{t(WORLD.aForm)}</p>;

  // STRING writes "Full protein name; then the function." The two are different registers and
  // the split is what makes the paragraph readable rather than a wall.
  const [name, ...rest] = p.note.split(";");
  const body = rest.join(";").trim();

  return (
    <div className={css.block}>
      <p className={css.sub}>{t(WORLD.formLede)}</p>
      <h4 className={css.protName}>{name.trim()}</h4>
      {body && <p className={css.protNote}>{body}</p>}
      {p.size != null && (
        <div className={css.facts}>
          <Fact k={t(WORLD.formSize)} v={fmtInt(p.size)} s={t(WORLD.formSizeSub)} />
        </div>
      )}
    </div>
  );
}

/* --------------------------------------------------------------- constraint */

export function ConstraintPanel({ world }: Props) {
  const t = useT();
  const c = world?.con;
  if (!c) return <p className={css.absentPanel}>{t(WORLD.aConstraint)}</p>;

  const band = loeufBand(c.loeuf);
  const bandText = band === "constrained" ? WORLD.bandConstrained
    : band === "middling" ? WORLD.bandMiddling
    : band === "tolerant" ? WORLD.bandTolerant : null;

  return (
    <div className={css.block}>
      <p className={css.sub}>{t(WORLD.constraintLede)}</p>

      <div className={css.facts}>
        <Fact k={t(WORLD.cLoeuf)} v={c.loeuf != null ? fmt(c.loeuf, 2) : "—"}
              s={t(WORLD.cLoeufSub)}
              tone={band === "constrained" ? "warn" : undefined} />
        <Fact k={t(WORLD.cOe)} v={c.oe != null ? fmt(c.oe, 2) : "—"}
              s={fill(t(WORLD.cOeSub), { obs: fmtInt(c.lofObs), exp: fmt(c.lofExp, 1) })} />
        <Fact k={t(WORLD.cPli)} v={c.pLI != null ? fmt(c.pLI, 2) : "—"} s={t(WORLD.cPliSub)} />
        <Fact k={t(WORLD.cMisZ)} v={c.misZ != null ? fmt(c.misZ, 1) : "—"} s={t(WORLD.cMisZSub)} />
      </div>

      {bandText && (
        <p className={css.note} data-tone={band === "constrained" ? "warn" : "info"}>
          {t(bandText)}
        </p>
      )}

      {/* THE CAUTION IS NOT A FOOTNOTE. Reading LOEUF as a pathogenicity score is the
          commonest misuse of gnomAD, and a number printed without it invites exactly that. */}
      <p className={css.caution}>{t(WORLD.constraintCaution)}</p>
    </div>
  );
}

/* --------------------------------------------------------------- expression */

export function ExpressionPanel({ world, scope }: Props) {
  const t = useT();
  const e = world?.exp;
  if (!e) return <p className={css.absentPanel}>{t(WORLD.aExpression)}</p>;

  const total = scope.world?.expression?.cellTypes ?? 0;
  const floor = scope.world?.expression?.floor ?? 1;
  const peak = Math.max(...e.top.map((x) => x.nCPM), 1);

  return (
    <div className={css.block}>
      <p className={css.sub}>{t(WORLD.expressionLede)}</p>

      <div className={css.facts}>
        <Fact k={t(WORLD.eBreadth)} v={fmtInt(e.typesAbove)}
              s={fill(t(WORLD.eBreadthSub), { total: fmtInt(total), floor })} />
        <Fact k={t(WORLD.ePeak)} v={e.top[0]?.cell ?? "—"}
              s={e.top[0] ? `${fmt(e.top[0].nCPM, 1)} nCPM` : ""} />
      </div>

      {/* A bar per cell type, on a common baseline. The question is "how much more here than
          there", which is a length comparison — the encoding people read most accurately. */}
      <ul className={css.cells}>
        {e.top.map((row) => (
          <li key={row.cell}>
            <span className={css.cellName}>{row.cell}</span>
            <span className={css.cellTrack}>
              <span className={css.cellBar} style={{ width: `${(row.nCPM / peak) * 100}%` }} />
            </span>
            <span className={css.cellVal}>{fmt(row.nCPM, 1)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ----------------------------------------------------------------- variants */

export function VariantsPanel({ world }: Props) {
  const t = useT();
  const c = world?.clin;
  if (!c) return <p className={css.absentPanel}>{t(WORLD.aVariants)}</p>;

  const meaningful = vusIsMeaningful(c);
  const parts = [
    { k: "pathogenic", n: c.pathogenic, cls: css.segPath },
    { k: "uncertain", n: c.uncertain, cls: css.segVus },
    { k: "conflicting", n: c.conflicting, cls: css.segConf },
    { k: "benign", n: c.benign, cls: css.segBenign },
    { k: "other", n: c.other, cls: css.segOther },
  ].filter((p) => p.n > 0);

  return (
    <div className={css.block}>
      <p className={css.sub}>{t(WORLD.variantsLede)}</p>

      <div className={css.facts}>
        <Fact k={t(WORLD.vTotal)} v={fmtInt(c.total)} s="ClinVar · GRCh38" />
        <Fact k={t(WORLD.vPathogenic)} v={fmtInt(c.pathogenic)} s={t(WORLD.vPathogenicSub)} />
        <Fact k={t(WORLD.vUncertain)} v={fmtInt(c.uncertain)} s={t(WORLD.vShare)}
              tone={meaningful && c.vusShare > 0.5 ? "warn" : undefined} />
        <Fact k={t(WORLD.vBenign)} v={fmtInt(c.benign)} s={t(WORLD.vBenignSub)} />
      </div>

      {/* One bar, whole, in proportion. A pie would put the same five numbers in the encoding
          people read worst; stacked on a common baseline the VUS block is impossible to miss,
          which is the point of the panel. */}
      <div className={css.stack} role="img"
           aria-label={`${c.total} variants: ${c.pathogenic} pathogenic, ${c.uncertain} uncertain, ${c.benign} benign`}>
        {parts.map((p) => (
          <span key={p.k} className={p.cls} style={{ width: `${(p.n / c.total) * 100}%` }}
                title={`${p.k}: ${fmtInt(p.n)}`} />
        ))}
      </div>

      {meaningful ? (
        <div className={css.vus}>
          <p className={css.vusHead}>
            {fill(t(WORLD.vusHeadline), { pct: pct(c.vusShare, 0) })}
          </p>
          <p className={css.vusBody}>{t(WORLD.vusExplain)}</p>
        </div>
      ) : (
        <p className={css.caution}>
          {fill(t(WORLD.vusTooFew), { n: fmtInt(c.total), min: VUS_MIN_VARIANTS })}
        </p>
      )}
    </div>
  );
}

/* --------------------------------------------------------------------- part */

function Fact({ k, v, s, tone }: { k: string; v: string; s: string; tone?: "good" | "warn" }) {
  return (
    <div className={css.fact} data-tone={tone}>
      <span className={css.factK}>{k}</span>
      <span className={css.factV}>{v}</span>
      <span className={css.factS}>{s}</span>
    </div>
  );
}
