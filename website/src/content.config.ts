import { defineCollection } from "astro:content";
import { file, glob } from "astro/loaders";
import { z } from "astro/zod";
import { definePageCollection } from "astro-theme-university/schemas";
import { parse as parseYaml } from "yaml";

// The fiction's source of truth lives OUTSIDE this Astro project, in the repo's
// canon/ directory. These loaders read it in place (paths resolve relative to
// the project root, i.e. website/) --- canon is edited by the publish tick and
// the site re-renders. No mirroring, no drift.

// Researcher roster --- canon/roster.yml, an array nested under `researchers:`.
// The custom parser unwraps that key; each item's `id` becomes the entry id.
const people = defineCollection({
  loader: file("../canon/roster.yml", {
    parser: (text) => parseYaml(text).researchers,
  }),
  schema: z.object({
    name: z.string(),
    title: z.string(),
    school: z.string(), // full school name; resolved to a schools entry at render
    bio: z.string(),
    headshot: z.string(), // canon-root path; images resolved via lib/headshots.ts
    web: z.url().optional(),
    displayOrder: z.number().optional(),
  }),
});

// Org chart --- canon/schools.yml, grouped by section. The parser flattens the
// sections into one array, stamping each record with its `kind` and keeping the
// per-record `id` as the entry id.
const SCHOOL_SECTIONS = {
  schools: "school",
  units: "unit",
  labs: "lab",
  programs: "program",
  initiatives: "initiative",
  history: "history",
} as const;

const schools = defineCollection({
  loader: file("../canon/schools.yml", {
    parser: (text) => {
      const doc = parseYaml(text) as Record<string, Array<Record<string, unknown>>>;
      return Object.entries(SCHOOL_SECTIONS).flatMap(([section, kind]) =>
        (doc[section] ?? []).map((record) => ({ ...record, kind })),
      );
    },
  }),
  schema: z.object({
    name: z.string(),
    kind: z.enum(["school", "unit", "lab", "program", "initiative", "history"]),
    blurb: z.string().optional(),
    school: z.string().optional(), // parent school id (labs, programs, initiatives)
    acronym: z.string().optional(),
  }),
});

// Free-form pages (colophon, about, agent-grown pages).
const pages = definePageCollection({ passthrough: true });

// One entry per published artefact. Written by the /publish pipeline; the
// per-output landing page and the DOI resolver route are generated from it.
const outputs = defineCollection({
  loader: glob({ pattern: "**/*.yml", base: "src/content/outputs" }),
  schema: z.object({
    title: z.string(),
    subtitle: z.string().optional(),
    authors: z.array(z.string()).default([]),
    preset: z.enum(["research-poster", "paper", "brochure", "strategy", "impact-report"]),
    school: z.string().optional(),
    date: z.coerce.date(),
    doi: z.string().regex(/^10\.5555\/slop\.[a-z0-9]+$/),
    summary: z.string(),
    topic: z.string(),
    pdf: z.string(),
    pages: z.number().optional(),
    version: z.string().default("1.0"),
  }),
});

// Press releases; each references its output by collection id.
const news = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "src/content/news" }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    description: z.string().optional(),
    output: z.string().optional(),
  }),
});

export const collections = { pages, people, schools, outputs, news };
