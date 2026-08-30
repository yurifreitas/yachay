import { useCallback, useEffect, useRef } from "react";

/** The radio-group contract, for controls that keep their own markup.
 *
 *  WHY THIS EXISTS. Seven places on this site shipped `role="tab"` inside a `role="tablist"`
 *  with **no `role="tabpanel"` anywhere**, no `aria-controls`, no ids and no keyboard model.
 *  Declaring a role is a promise about behaviour: a screen reader announces "tab, 3 of 5" and
 *  offers to move to the panel, and there is no panel; a tablist promises arrow keys, and the
 *  arrows did nothing. That is worse than plain buttons, because plain buttons make no
 *  promise they then break.
 *
 *  None of them are tabs. A tab swaps a labelled panel that keeps its place in the reading
 *  order; these choose which question is being asked and re-render the content beneath. That
 *  is a radio group.
 *
 *  `ChoiceGroup` already implements this correctly and owns its own markup and styling. These
 *  seven do not want its markup — each has its own chips, rules or view switch with its own
 *  CSS — so what they need is the CONTRACT without the presentation. Copying the key handling
 *  into five components would be five chances for it to drift; this is the same behaviour as
 *  one hook.
 *
 *  WHAT THE CONTRACT IS:
 *    · the group is ONE tab stop, not N — roving `tabindex`, so Tab moves past a five-option
 *      switch in a single press instead of five
 *    · arrow keys move the selection, wrapping at both ends
 *    · Home and End jump to first and last
 *    · focus follows the selection ONLY when a key moved it, never when a click, a link or a
 *      back button changed it — stealing focus on someone else's navigation is its own bug
 */
export function useRovingRadio<T extends string>(
  ids: readonly T[],
  value: T,
  onChange: (id: T) => void,
) {
  const ref = useRef<HTMLDivElement>(null);
  const followFocus = useRef(false);

  // After commit, not before. Moving focus from inside the key handler races React's render:
  // the DOM can still hold the previous selection when the frame runs, leaving focus on an
  // unchecked option. An effect keyed on `value` runs once the DOM matches the state, which
  // is the only moment the right element can be identified.
  useEffect(() => {
    if (!followFocus.current) return;
    followFocus.current = false;
    const i = ids.indexOf(value);
    if (i >= 0) ref.current?.querySelectorAll<HTMLButtonElement>("button")[i]?.focus();
  }, [value, ids]);

  const onKeyDown = useCallback((e: React.KeyboardEvent) => {
    const keys = ["ArrowRight", "ArrowDown", "ArrowLeft", "ArrowUp", "Home", "End"];
    if (!keys.includes(e.key) || ids.length < 2) return;
    e.preventDefault();
    const i = Math.max(0, ids.indexOf(value));
    const last = ids.length - 1;
    const next =
      e.key === "Home" ? 0
      : e.key === "End" ? last
      : e.key === "ArrowRight" || e.key === "ArrowDown"
        ? (i + 1) % ids.length
        : (i - 1 + ids.length) % ids.length;
    followFocus.current = true;
    onChange(ids[next]);
  }, [ids, value, onChange]);

  return {
    /** Spread onto the container. It supplies the role and the key handling; the CALLER
     *  supplies `aria-label`, because only the caller knows what is being chosen and an
     *  unlabelled group is announced as bare buttons. */
    group: { ref, role: "radiogroup" as const, onKeyDown },
    /** Spread onto each option button, in the same order as `ids`. */
    option: (id: T) => ({
      role: "radio" as const,
      "aria-checked": id === value,
      tabIndex: id === value ? 0 : -1,
    }),
  };
}
