import type { Text } from "../../../i18n";

export type NavView = {
  id: string;
  /** A run's label comes from its manifest and has one form; the domain pages have two. */
  label: Text;
  /** One line saying what is inside, shown under the label of the open view. */
  blurb: Text;
  /** Which family of views this belongs to — screens, domains, or the method itself. */
  family: string;
};

export type NavFamily = {
  id: string;
  label: Text;
  /** WHY A FAMILY NEEDS A SENTENCE TOO.
   *
   *  Every level below this one explains itself — a group states its question, a section
   *  states what it does not show, a view carries a blurb. The top level, the one a reader
   *  meets first and the only one that decides which of six screens they land on, was four
   *  bare words. "Domains" told a reader nothing about whether the answer they wanted was
   *  in there.
   *
   *  So a family says what kind of question it answers, and the answer names the reader
   *  rather than the method: people arrive holding a gene, a disease, or a doubt about
   *  whether any of this is sound. */
  question: Text;
};

export type NavSidebarProps = {
  families: NavFamily[];
  views: NavView[];
  activeView: string;
  onView: (id: string) => void;
};
