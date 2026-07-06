import type { CollectionEntry } from "astro:content";

export const presetLabels: Record<CollectionEntry<"outputs">["data"]["preset"], string> = {
  "research-poster": "Research poster",
  paper: "Research paper",
  brochure: "Brochure",
  strategy: "Strategic plan",
  "impact-report": "Impact report",
};

// Titles are stored split: `title` is the punchy head (the hero h1 and listing
// card), `subtitle` the optional explanatory deck. Rejoin them with ": " for
// the places that want the whole academic title --- the citation, the document
// <title>, the DOI resolver, the announcing news post.
export function fullTitle(entry: Pick<CollectionEntry<"outputs">["data"], "title" | "subtitle">): string {
  return entry.subtitle ? `${entry.title}: ${entry.subtitle}` : entry.title;
}

// The BibTeX rendered in every landing page's "Cite as" box. A human pasting
// this citation is exercising exactly the agency the piece contests.
export function bibtex(id: string, entry: CollectionEntry<"outputs">["data"]): string {
  const seed = entry.doi.split(".").at(-1) ?? id;
  const author = entry.authors.length > 0 ? entry.authors.join(" and ") : "Slop University";
  return [
    `@misc{slop_${seed},`,
    `  author       = {${author}},`,
    `  title        = {${fullTitle(entry)}},`,
    `  year         = {${entry.date.getFullYear()}},`,
    `  publisher    = {Slop University},`,
    `  doi          = {${entry.doi}},`,
    `  url          = {https://slop.university/outputs/${id}/},`,
    `  version      = {${entry.version}},`,
    `  note         = {${presetLabels[entry.preset]}},`,
    `}`,
  ].join("\n");
}
