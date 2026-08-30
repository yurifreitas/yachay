import { useMemo, useState } from "react";
import { useRovingRadio } from "../../lib/useRovingRadio";
import { useRemoteData } from "../../lib/useRemoteData";
import { useHashParam } from "../../lib/useHashParam";
import { useT, fill } from "../../i18n";
import { BROWSE } from "../../i18n/browse";
import { fmtInt } from "../../lib/scale";
import css from "./GeneBrowse.module.css";

/** A WAY IN THAT IS NOT A SEARCH BOX.
 *
 *  The navigator opened on a text field and four suggestions, which serves a reader who
 *  already knows the symbol. The people this is aimed at often do not. A curator wants every
 *  kinase. A therapy team wants the genes their cancer subgroup needs. A clinician wants the
 *  genes whose reports come back "uncertain", because those are the inconclusive ones.
 *  None of them can type their way there.
 *
 *  Six facets, every one of them a measurement already on disk: the UniProt domain family,
 *  the gnomAD constraint band, the DepMap cancer lineage, the ClinVar interpretation band,
 *  the expression breadth, and which route the gene breaks by. Nothing is authored.
 *
 *  SMALL CLASSES ARE PUBLISHED WITH THEIR SIZE. A browse surface that hides its eight-gene
 *  families is telling the reader the field is tidier than it is; the floor is stated and
 *  the number below it is reported.
 */

type FacetValue = { value: string; count: number; genes: string[] };
type Facets = {
  generated: string;
  premise: string;
  minMembers: number;
  maxMembers: number;
  facets: Record<string, {
    values: FacetValue[];
    distinct: number;
    offered: number;
    belowFloor: number;
  }>;
};

const KINDS = ["domain", "lineage", "constraint", "interpretation", "breadth", "route"] as const;
type Kind = (typeof KINDS)[number];

export function GeneBrowse({ onPick }: { onPick: (symbol: string) => void }) {
  const t = useT();
  const [kind, setKind] = useHashParam("f", "domain");
  const nav = useRovingRadio(KINDS as readonly string[], kind,
                             (k) => { setKind(k); setValue(""); setFilter(""); });
  const [value, setValue] = useHashParam("v", "");
  const [filter, setFilter] = useState("");

  const data = useRemoteData<Facets>("data/gene/facets.json");

  const block = data.state === "ready" ? data.data.facets[kind] : undefined;

  const shown = useMemo(() => {
    if (!block) return [];
    const q = filter.trim().toLowerCase();
    // A 304-family list needs its own filter. Not a search over genes — a search over the
    // NAMES of the classes, which is a different question and deserves a different field.
    return q ? block.values.filter((v) => v.value.toLowerCase().includes(q)) : block.values;
  }, [block, filter]);

  const chosen = block?.values.find((v) => v.value === value);

  if (data.state === "loading") return <div className={css.skeleton} role="status" />;
  if (data.state === "error") {
    return (
      <p className={css.absent}>
        {t(BROWSE.absent)} <code>python tools/gene_facets.py</code>
      </p>
    );
  }

  return (
    <section className={css.wrap}>
      <div className={css.head}>
        <h3 className={css.title}>{t(BROWSE.title)}</h3>
        <p className={css.lede}>{t(BROWSE.lede)}</p>
      </div>

      <div className={css.kinds} {...nav.group} aria-label={t(BROWSE.title)}>
        {KINDS.filter((k) => data.data.facets[k]?.values.length).map((k) => (
          <button
            key={k}
            type="button"
            {...nav.option(k)}
            className={k === kind ? css.kindOn : css.kind}
            onClick={() => { setKind(k); setValue(""); setFilter(""); }}
          >
            <span className={css.kindName}>{t(BROWSE.kind[k as Kind])}</span>
            <span className={css.kindCount}>{data.data.facets[k].offered}</span>
          </button>
        ))}
      </div>

      <p className={css.kindNote}>{t(BROWSE.note[kind as Kind] ?? BROWSE.note.domain)}</p>

      {block && block.values.length > 12 && (
        <input
          type="search"
          className={css.filter}
          placeholder={t(BROWSE.filterPlaceholder)}
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          aria-label={t(BROWSE.filterPlaceholder)}
        />
      )}

      <div className={css.split}>
        <ul className={css.values}>
          {shown.map((v) => {
            const peak = block?.values[0]?.count ?? 1;
            return (
              <li key={v.value}>
                <button
                  type="button"
                  className={v.value === value ? css.valueOn : css.value}
                  onClick={() => setValue(v.value === value ? "" : v.value)}
                  aria-pressed={v.value === value}
                >
                  <span className={css.valueName}>{v.value}</span>
                  {/* Length on a common baseline: which classes are big is the first thing
                      a reader wants from a list of 304, and a count alone makes them
                      compare four-digit numbers by eye. */}
                  <span className={css.valueTrack}>
                    <span className={css.valueBar}
                          style={{ width: `${(v.count / peak) * 100}%` }} />
                  </span>
                  <span className={css.valueCount}>{fmtInt(v.count)}</span>
                </button>
              </li>
            );
          })}
          {!shown.length && <li className={css.none}>{t(BROWSE.noMatch)}</li>}
        </ul>

        <div className={css.members}>
          {chosen ? (
            <>
              <p className={css.membersHead}>
                <strong>{chosen.value}</strong>{" "}
                {fill(t(BROWSE.showing), {
                  shown: fmtInt(chosen.genes.length), total: fmtInt(chosen.count),
                })}
              </p>
              <ul className={css.genes}>
                {chosen.genes.map((g) => (
                  <li key={g}>
                    <button type="button" className={css.gene} onClick={() => onPick(g)}>
                      {g}
                    </button>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className={css.pickOne}>{t(BROWSE.pickOne)}</p>
          )}
        </div>
      </div>

      {block && block.belowFloor > 0 && (
        <p className={css.floor}>
          {fill(t(BROWSE.belowFloor), {
            n: fmtInt(block.belowFloor), min: data.data.minMembers,
          })}
        </p>
      )}
    </section>
  );
}
