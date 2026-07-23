import type { CollectionEntry } from "astro:content";

export type Preset = CollectionEntry<"outputs">["data"]["preset"];

export const presetLabels: Record<Preset, string> = {
  "research-poster": "Research poster",
  "marketing-poster": "Marketing poster",
  paper: "Research paper",
  brochure: "Brochure",
  strategy: "Strategic plan",
  "impact-report": "Impact report",
};

// Short forms for the type badge on output cards, where the icon already
// carries the "research artefact" sense and the pill has to stay narrow. The
// long labels above still cover the citation note and the metadata table.
export const presetBadgeLabels: Record<Preset, string> = {
  ...presetLabels,
  "research-poster": "Poster",
  "marketing-poster": "Ad",
  paper: "Paper",
};

// The trend chart on the outputs index plots one line per series, and the type
// filter facets on those same three series --- a pill and a legend entry always
// name the same set. Papers and posters carry the repository, so they each get
// a line; the institutional genres are pooled, and any preset added later joins
// the pool rather than stranding a one-point line on the chart.
export const seriesOrder = ["Research papers", "Research posters", "Other outputs"] as const;

export type OutputSeries = (typeof seriesOrder)[number];

export const presetSeries: Record<Preset, OutputSeries> = {
  paper: "Research papers",
  "research-poster": "Research posters",
  "marketing-poster": "Other outputs",
  brochure: "Other outputs",
  strategy: "Other outputs",
  "impact-report": "Other outputs",
};

// The URL segment each series filters under: /outputs/type/<slug>/. Slugs are
// part of the site's public surface (they're linked, crawled, and bookmarked),
// so they're spelled out here rather than derived from the display label --- a
// reworded legend entry must not silently move a page.
export const seriesSlugs: Record<OutputSeries, string> = {
  "Research papers": "papers",
  "Research posters": "posters",
  "Other outputs": "other",
};

// Cards per page. Shared by the unfiltered index and the facet routes so a
// filtered view paginates on the same rhythm as the one it was filtered from.
export const PAGE_SIZE = 12;

export interface SeriesFacet {
  series: OutputSeries;
  slug: string;
  count: number;
}

// The facets the type filter offers, in `seriesOrder`. A series with no outputs
// is left out: the facet route is only built where there's something to show,
// so a pill for an empty series would link at a 404.
export function seriesFacets(outputs: { preset: Preset }[]): SeriesFacet[] {
  return seriesOrder
    .map((series) => ({
      series,
      slug: seriesSlugs[series],
      count: outputs.filter((o) => presetSeries[o.preset] === series).length,
    }))
    .filter((facet) => facet.count > 0);
}

// iconoir glyph per preset, for the type badge on output cards. Names must be
// valid iconoir icons (the theme's Icon component adds the `iconoir:` prefix).
export const presetIcons: Record<Preset, string> = {
  "research-poster": "presentation",
  "marketing-poster": "megaphone",
  paper: "journal-page",
  brochure: "book",
  strategy: "strategy",
  "impact-report": "reports",
};

// Titles are stored split: `title` is the punchy head (the hero h1 and listing
// card), `subtitle` the optional explanatory deck. Rejoin them with ": " for
// the places that want the whole academic title --- the citation, the document
// <title>, the DOI resolver, the announcing news post.
export function fullTitle(
  entry: Pick<CollectionEntry<"outputs">["data"], "title" | "subtitle">,
): string {
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

export type BibtexTokenKind = "type" | "key" | "field" | "value" | "punct" | "plain";

export interface BibtexToken {
  kind: BibtexTokenKind;
  text: string;
}

// `@misc{slop_sn9kzr,`
const ENTRY_LINE = /^(@\w+)(\{)(.+)(,)$/;
// `  author       = {Casimir Beng},`
const FIELD_LINE = /^(\s+)(\w+)(\s*)(=)(\s*)(\{)(.*)(\},?)$/;

// Colour the citation without shipping a highlighter: `bibtex()` above emits a
// known shape, so tokenise it back apart and let the template wrap each token in
// a span. The `plain` tokens (indentation, newlines) carry no span, and the
// concatenated token text is byte-identical to the input --- the copy button
// hands the browser that same plain string, not this DOM.
export function bibtexTokens(citation: string): BibtexToken[] {
  const tokens: BibtexToken[] = [];
  const push = (kind: BibtexTokenKind, text: string) => text && tokens.push({ kind, text });

  citation.split("\n").forEach((line, i) => {
    if (i > 0) push("plain", "\n");

    const entry = ENTRY_LINE.exec(line);
    if (entry) {
      const [, type, brace, key, comma] = entry;
      push("type", type);
      push("punct", brace);
      push("key", key);
      push("punct", comma);
      return;
    }

    const field = FIELD_LINE.exec(line);
    if (field) {
      const [, indent, name, preGap, equals, postGap, open, value, close] = field;
      push("plain", indent);
      push("field", name);
      push("plain", preGap);
      push("punct", equals);
      push("plain", postGap);
      push("punct", open);
      push("value", value);
      push("punct", close);
      return;
    }

    // The closing brace, and anything a future field shape throws at us.
    push("punct", line);
  });

  return tokens;
}
