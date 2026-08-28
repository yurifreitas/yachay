/** The navigation model, written once.
 *
 *  Four pages had each grown their own copy of the same three declarations — a group list, a
 *  section list carrying a `group` key, and the derivation that turns one into the other.
 *  Four copies of a rule is four chances for it to disagree with itself, and the disagreement
 *  is invisible until a deep link opens a group that does not contain its own section.
 *
 *  So the shape lives here and the derivation lives in `useSectionNav`. A page now declares
 *  WHAT its sections are; it no longer restates HOW a section finds its group, how a group
 *  counts its sections, or where either is stored.
 */

import type { Text } from "../../i18n";

/** One panel. `badge` is a count or status shown after the label.
 *
 *  Labels are `Text`: either a translated pair or a bare string. A run's title arrives from
 *  the manifest and has one form; a section this application named has two. The type lets
 *  both travel the same path and be resolved once, at the point of rendering. */
export type NavSection = { id: string; label: Text; badge?: string };

/** A section as a page declares it: the same thing, plus which question it answers. */
export type NavSectionDef = NavSection & { group: string };

/** A question the page answers, stated as a question rather than as a category — the
 *  sections underneath are answers, and a reader arrives holding a question. */
export type NavGroupDef = { id: string; label: Text; question: Text };

/** The same group once the sections have been counted, so the depth of a group is visible
 *  from outside it: a group holding six sections says so before it is opened. */
export type NavGroup = NavGroupDef & { count: number };

/** What a page publishes to the shell so the sidebar can render the page's own interior.
 *
 *  The sidebar knows nothing about diseases, runs or documents; it renders this. That is the
 *  whole reason the three-level tree can exist in one component rather than in each page.
 */
export type NavTree = {
  /** Stable identity of the publishing page, so an unmounting page cannot clear a tree that
   *  the page replacing it has already published. */
  owner: string;
  groups: NavGroup[];
  sections: NavSectionDef[];
  /** The open section, and the group derived from it. */
  section: string;
  group: string;
  onSection: (id: string) => void;
  onGroup: (id: string) => void;
};
