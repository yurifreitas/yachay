import { useT } from "../../i18n";
import { INS } from "../../i18n/insights";
import { fmtInt, pct } from "../../lib/scale";
import type { GeneSearchIndex } from "./geneModel";
import css from "./Insights.module.css";

/** What the layers say when two of them are read at once.
 *
 *  THE GAP THIS FILLS. The navigator showed seven layers side by side and never said a word
 *  about what they mean together. But almost everything a person wants to know about a gene
 *  lives in a DISAGREEMENT between two measurements rather than inside either one — a gene
 *  under strong selection in people that no cell line needs, a gene every line needs that
 *  people break freely, a gene that clearly matters and whose variants nobody can classify.
 *
 *  EACH ONE IS A RULE WITH A STATED THRESHOLD, not a score. The rule is printed under the
 *  claim, with the count it caught and the population it was applied to. A reader who
 *  disagrees with a cut can see it and move it, which is the difference between an argument
 *  and an oracle — and the reason there is no composite anywhere on this page.
 */

const ORDER = [
  "selective", "organismal", "unreadable", "broadButSelective",
  "damageInDomains", "cultureArtefact",
] as const;

type Rule = { claim: string; reading: string; rule: string };

export function Insights(
  { found, scope, rules, caution }:
  {
    found?: string[];
    scope: GeneSearchIndex["scope"];
    rules: Record<string, Rule>;
    caution: string;
  },
) {
  const t = useT();
  const ins = scope.ins;
  const hits = ORDER.filter((k) => found?.includes(k));
  const missed = ORDER.filter((k) => !found?.includes(k) && rules[k]);

  return (
    <div className={css.wrap}>
      <p className={css.lede}>{t(INS.lede)}</p>

      {hits.length === 0 && (
        <p className={css.none}>{t(INS.none)}</p>
      )}

      {hits.map((k) => (
        <Observation
          key={k}
          id={k}
          rule={rules[k]}
          caught={ins?.byRule?.[k]}
          eligible={ins?.eligible?.[k]}
          on
        />
      ))}

      {/* THE RULES THAT DID NOT FIRE ARE LISTED TOO. A page that shows only the hits makes
          the reader believe the others were never asked — and "asked and did not fire" is a
          statement about the gene, which is the whole discipline of this site. */}
      {missed.length > 0 && (
        <section className={css.notFired}>
          <h4 className={css.notFiredTitle}>{t(INS.notFired)}</h4>
          <ul className={css.notFiredList}>
            {missed.map((k) => (
              <li key={k}>
                <span className={css.notFiredClaim}>{rules[k].claim}</span>
                <span className={css.notFiredRule}>{rules[k].rule}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className={css.caution}>{caution}</p>
    </div>
  );
}

function Observation(
  { id, rule, caught, eligible, on }:
  { id: string; rule: Rule; caught?: number; eligible?: number; on?: boolean },
) {
  const t = useT();
  return (
    <section className={on ? css.obsOn : css.obs} data-rule={id}>
      <div className={css.obsHead}>
        <h4 className={css.claim}>{rule.claim}</h4>
        {caught != null && (
          <span className={css.freq}>
            {fmtInt(caught)}
            {eligible ? ` · ${pct(caught / eligible, 1)} ${t(INS.ofEligible)}` : ""}
          </span>
        )}
      </div>
      <p className={css.reading}>{rule.reading}</p>
      {/* The rule itself, printed. Without it the claim is an assertion; with it the reader
          can disagree with the cut rather than with the conclusion. */}
      <p className={css.rule}>
        <span className={css.ruleLabel}>{t(INS.ruleLabel)}</span> {rule.rule}
      </p>
    </section>
  );
}
