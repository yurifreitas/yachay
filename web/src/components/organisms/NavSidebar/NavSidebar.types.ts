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
};

export type NavSidebarProps = {
  families: NavFamily[];
  views: NavView[];
  activeView: string;
  onView: (id: string) => void;
};
