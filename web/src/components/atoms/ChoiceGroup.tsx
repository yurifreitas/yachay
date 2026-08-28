import { useCallback, useEffect, useRef } from "react";
import s from "./ChoiceGroup.module.css";

/** Pick one of N, where choosing re-renders the content below.
 *
 *  WHY THIS EXISTS. The cancer section shipped five controls carrying `role="tab"` inside a
 *  `role="tablist"`, with **no `role="tabpanel"` anywhere on the page**, no `aria-controls`,
 *  no ids, and no keyboard model. That is a broken contract, not a missing nicety: a screen
 *  reader announces "tab, 1 of 2" and there is nothing for the reader to move to, and the
 *  arrow keys a tablist promises do nothing. Declaring a role is a promise about behaviour.
 *
 *  These are not tabs. A tab swaps a panel that stays in the same place in the reading order;
 *  these choose which question is being asked and re-render the page beneath. That is a
 *  **radio group** — one selection, mutually exclusive, content follows — and it comes with a
 *  keyboard model that is actually implementable here:
 *
 *    · the group is ONE tab stop, not N (roving `tabindex`), so Tab moves past a 3-option
 *      switch in one press instead of three
 *    · arrow keys move the selection, wrapping at both ends
 *    · Home and End jump to the first and last option
 *
 *  Each option is a real `<button>`, so it keeps native activation, focus and hit-testing.
 */

export type Choice = { id: string; label: string; note?: string };

export default function ChoiceGroup(
  { choices, value, onChange, label, variant = "pill" }:
  {
    choices: Choice[];
    value: string;
    onChange: (id: string) => void;
    /** Names the group for assistive technology. Required — an unlabelled group of options
     *  is announced as bare buttons with no statement of what is being chosen. */
    label: string;
    variant?: "pill" | "card";
  },
) {
  const ref = useRef<HTMLDivElement>(null);
  /** Set only by the arrow keys. Focus must follow the selection when the KEYBOARD moved it,
   *  and must not be stolen when the selection changes for any other reason — a click
   *  elsewhere, a link with the state in it, a back button. */
  const followFocus = useRef(false);

  // After commit, not before. The first version moved focus inside a requestAnimationFrame
  // fired from the key handler, which races React's render: the frame can run while the DOM
  // still holds the previous selection, leaving focus on an unchecked option. An effect keyed
  // on `value` runs after the DOM matches the state, which is the only moment the right
  // element can be identified.
  useEffect(() => {
    if (!followFocus.current) return;
    followFocus.current = false;
    const i = choices.findIndex((c) => c.id === value);
    ref.current?.querySelectorAll<HTMLButtonElement>("button")[i]?.focus();
  }, [value, choices]);

  const onKeyDown = useCallback((e: React.KeyboardEvent) => {
    const keys = ["ArrowRight", "ArrowDown", "ArrowLeft", "ArrowUp", "Home", "End"];
    if (!keys.includes(e.key)) return;
    e.preventDefault();
    const i = choices.findIndex((c) => c.id === value);
    const last = choices.length - 1;
    const next =
      e.key === "Home" ? 0
      : e.key === "End" ? last
      : e.key === "ArrowRight" || e.key === "ArrowDown"
        ? (i + 1) % choices.length
        : (i - 1 + choices.length) % choices.length;
    // Move focus with the selection: in a radio group the two travel together, and a
    // selection that moves while focus stays behind is unnavigable without sight.
    followFocus.current = true;
    onChange(choices[next].id);
  }, [choices, value, onChange]);

  return (
    <div
      ref={ref}
      role="radiogroup"
      aria-label={label}
      className={variant === "card" ? s.cards : s.pills}
      onKeyDown={onKeyDown}
    >
      {choices.map((c) => {
        const on = c.id === value;
        return (
          <button
            key={c.id}
            type="button"
            role="radio"
            aria-checked={on}
            // Roving tabindex: only the selected option is in the tab order.
            tabIndex={on ? 0 : -1}
            className={on ? s.on : s.off}
            onClick={() => onChange(c.id)}
          >
            <span className={s.label}>{c.label}</span>
            {c.note && <span className={s.note}>{c.note}</span>}
          </button>
        );
      })}
    </div>
  );
}
