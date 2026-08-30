import { useEffect, useMemo } from "react";
import { useHashParam } from "../useHashParam";
import { useNavPublish } from "./NavContext";
import type { NavGroup, NavGroupDef, NavSectionDef, NavTree } from "./types";

export type SectionNavSpec = {
  /** Identifies the publishing page. Also the key under which nothing else may clear it. */
  owner: string;
  groups: NavGroupDef[];
  sections: NavSectionDef[];
  /** The section a bare link to the page opens on. Defaults to the first declared. */
  initial?: string;
  /** URL parameter carrying the open section. One page per view, so "s" everywhere. */
  param?: string;
};

/** One page's interior navigation: derived, linkable, and published to the shell.
 *
 *  THE GROUP IS DERIVED, NOT STORED. Two sources of truth for one position is how a deep link
 *  ends up selecting a group that does not contain the section it opened. Deriving the group
 *  from the section makes that state unrepresentable rather than merely unlikely.
 *
 *  The section lives in the URL, so every panel in the site is a link someone can send, and a
 *  refresh lands where the reader was rather than at the top.
 */
export function useSectionNav(spec: SectionNavSpec) {
  const { owner, groups, sections, param = "s" } = spec;
  const initial = spec.initial ?? sections[0]?.id ?? "";

  const [section, setSection] = useHashParam(param, initial);

  const groupOf = useMemo(
    () => Object.fromEntries(sections.map((s) => [s.id, s.group])) as Record<string, string>,
    [sections],
  );
  const group = groupOf[section] ?? groups[0]?.id ?? "";

  const counted = useMemo<NavGroup[]>(
    () => groups.map((g) => ({ ...g, count: sections.filter((s) => s.group === g.id).length })),
    [groups, sections],
  );

  const inGroup = useMemo(
    () => sections.filter((s) => s.group === group),
    [sections, group],
  );

  /** Choosing a question opens its first answer. A group is a place to stand, not a
   *  destination, so selecting one and then showing nothing would be a dead end. */
  const onGroup = useMemo(
    () => (id: string) => {
      const first = sections.find((s) => s.group === id);
      if (first) setSection(first.id);
    },
    [sections, setSection],
  );

  /** THE ORDER IS AN ARGUMENT, AND NOTHING LET A READER WALK IT.
   *
   *  Every page's `SECTIONS` array is authored in a deliberate sequence — the rare atlas
   *  comments say so out loud: *look at one disease, then at what stops it, then at what it
   *  would physically take.* Twenty-nine sections carried that order and the only way to
   *  follow it was to hunt the next label in a rail, across a group boundary, by name.
   *
   *  So the sequence becomes navigable. Derived from the same array, so it cannot disagree
   *  with the rail, and flat across groups because the argument does not stop at a group.
   */
  const index = sections.findIndex((s) => s.id === section);
  const prev = index > 0 ? sections[index - 1] : null;
  const next = index >= 0 && index < sections.length - 1 ? sections[index + 1] : null;

  const go = useMemo(
    () => (delta: -1 | 1) => {
      const target = delta < 0 ? prev : next;
      if (target) setSection(target.id);
    },
    [prev, next, setSection],
  );

  /** `[` and `]` rather than the arrows: arrows scroll, and a page that eats them from a
   *  reader halfway down a table has broken something more important than it fixed. Ignored
   *  while a field has focus or a modifier is held, so a shortcut never outranks typing. */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const el = e.target as HTMLElement | null;
      if (el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName))) return;
      if (e.key === "[") { e.preventDefault(); go(-1); }
      if (e.key === "]") { e.preventDefault(); go(1); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go]);

  const tree = useMemo<NavTree>(
    () => ({ owner, groups: counted, sections, section, group, onSection: setSection, onGroup }),
    [owner, counted, sections, section, group, setSection, onGroup],
  );

  const publish = useNavPublish();
  useEffect(() => {
    publish(tree, owner);
    return () => publish(null, owner);
  }, [publish, tree, owner]);

  return { section, setSection, group, onGroup, groups: counted, inGroup, tree,
           prev, next, go, groupOf };
}
