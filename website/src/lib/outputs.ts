import type { CollectionEntry } from "astro:content";

export const presetLabels: Record<CollectionEntry<"outputs">["data"]["preset"], string> = {
  "research-poster": "Research poster",
  paper: "Research paper",
  strategy: "Strategic plan",
  "impact-report": "Impact report",
};

// The BibTeX rendered in every landing page's "Cite as" box. A human pasting
// this citation is exercising exactly the agency the piece contests.
export function bibtex(id: string, entry: CollectionEntry<"outputs">["data"]): string {
  const seed = entry.doi.split(".").at(-1) ?? id;
  const author = entry.authors.length > 0 ? entry.authors.join(" and ") : "Slop University";
  return [
    `@misc{slop_${seed},`,
    `  author       = {${author}},`,
    `  title        = {${entry.title}},`,
    `  year         = {${entry.date.getFullYear()}},`,
    `  publisher    = {Slop University},`,
    `  doi          = {${entry.doi}},`,
    `  url          = {https://slop.university/outputs/${id}/},`,
    `  version      = {${entry.version}},`,
    `  note         = {${presetLabels[entry.preset]}},`,
    `}`,
  ].join("\n");
}
