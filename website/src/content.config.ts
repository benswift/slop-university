import { defineCollection } from "astro:content";
import { file, glob } from "astro/loaders";
import { z } from "astro/zod";
import { definePageCollection } from "astro-theme-university/schemas";
import { parse as parseYaml } from "yaml";

// The fiction's source of truth lives OUTSIDE this Astro project, in the repo's
// canon/ directory. These loaders read it in place (paths resolve relative to
// the project root, i.e. website/) --- canon is edited by the publish tick and
// the site re-renders. No mirroring, no drift.

// One person, whether fictional researcher or real Vice-Chancellor, renders
// through the same profile page --- so both collections below share a schema.
const personSchema = z.object({
  name: z.string(),
  title: z.string(),
  school: z.string(), // full school/unit name; resolved to a schools entry at render
  email: z.string().regex(/^[a-z]+(\.[a-z]+)+@slop\.university$/), // id with dots; catch-all makes it real
  bio: z.string(),
  headshot: z.string(), // canon-root path; images resolved via lib/headshots.ts
  web: z.url().optional(),
  displayOrder: z.number().optional(),
});

// Researcher roster --- canon/roster.yml, an array nested under `researchers:`.
// The custom parser unwraps that key; each item's `id` becomes the entry id.
const people = defineCollection({
  loader: file("../canon/roster.yml", {
    parser: (text) => parseYaml(text).researchers,
  }),
  schema: personSchema,
});

// University leadership --- canon/leadership.yml, one entry: the real
// Vice-Chancellor. A SEPARATE collection rather than another key in the roster
// file, because every preset blueprint tells its run to draw authors from
// canon/roster.yml: kept apart, a real name cannot be rolled into an author
// line. getPeople() unions the two for the /people/ pages; nothing that
// resolves authors or grantees reads this collection.
const leadership = defineCollection({
  loader: file("../canon/leadership.yml", {
    parser: (text) => parseYaml(text).leadership,
  }),
  schema: personSchema,
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

// Funding schemes --- canon/grants.yml, an array nested under `schemes:`.
// The scheme (the recurring apparatus) is canon and never invented in a run;
// the award events instantiating it live in the grants collection below.
const grantSchemes = defineCollection({
  loader: file("../canon/grants.yml", {
    parser: (text) => parseYaml(text).schemes,
  }),
  schema: z.object({
    name: z.string(),
    kind: z.enum(["grant", "award", "prize"]),
    funder: z.string(), // full org unit name from canon/schools.yml
    blurb: z.string(),
  }),
});

// One entry per awarded grant or prize. Written by the /publish pipeline and
// announced via news (frontmatter `grant:`) --- there are no per-grant pages;
// the data renders on people profiles and the outputs dashboard.
const grants = defineCollection({
  loader: glob({ pattern: "**/*.yml", base: "src/content/grants" }),
  schema: z.object({
    name: z.string(), // the funded project's title, or the prize citation
    scheme: z.string(), // grantSchemes entry id
    date: z.coerce.date(),
    grantees: z.array(z.string()).min(1), // roster names, as in outputs.authors
    value: z.number().int().positive(), // whole australian dollars
    summary: z.string(),
  }),
});

// Free-form pages (colophon, about, agent-grown pages).
const pages = definePageCollection({ passthrough: true });

// Intrinsic dimensions of a pre-encoded image served from img.slop.university.
// Only dims are stored --- URLs derive from the entry id (see src/lib/images.ts,
// whose rung ladder mirrors ops/encode-images.py, the thing that encoded them).
const imageDims = z.object({
  width: z.number().int().positive(),
  height: z.number().int().positive(),
});

// One entry per published artefact. Written by the /publish pipeline; the
// per-output landing page and the DOI resolver route are generated from it.
const outputs = defineCollection({
  loader: glob({ pattern: "**/*.yml", base: "src/content/outputs" }),
  schema: z.object({
    title: z.string(),
    subtitle: z.string().optional(),
    authors: z.array(z.string()).default([]),
    preset: z.enum([
      "research-poster",
      "marketing-poster",
      "paper",
      "brochure",
      "strategy",
      "impact-report",
    ]),
    school: z.string().optional(),
    date: z.coerce.date(),
    // Exact publish time, supplied by the unattended wrapper. `date` remains
    // the human-facing publication date; signage uses this to order same-day
    // outputs consistently.
    publishedAt: z.coerce.date().optional(),
    doi: z.string().regex(/^10\.5555\/slop\.[a-z0-9]+$/),
    summary: z.string(),
    topic: z.string(),
    // The PDF's location is not stored: it is served from the bucket at
    // pdf.slop.university under the entry id (see src/lib/pdfs.ts), so a path
    // here could only ever agree or disagree with that.
    //
    // Whether a DARK render exists is a real fact, not derivable: it is
    // produced only for the poster-format presets (research-poster,
    // marketing-poster) so the e-signage screens show white-on-black, and
    // older outputs predate it. Consumers fall back to the light PDF.
    pdfDark: z.boolean().default(false),
    pages: z.number().optional(),
    version: z.string().default("1.0"),
    grants: z.array(z.string()).default([]), // grants entry ids funding this work
    // Like the PDF, the hero and thumbnail live in a bucket keyed by the entry
    // id; the dims are the one fact the site can't derive. thumb is required
    // (every output has a first page) --- the fail-closed hinge that makes a
    // half-migrated tree a build error, never a broken live site. hero is
    // optional in the schema but generated for every output.
    hero: imageDims.optional(),
    thumb: imageDims,
  }),
});

// Press releases; each references its output (or awarded grant) by
// collection id.
const news = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "src/content/news" }),
  schema: z.object({
    title: z.string(),
    subtitle: z.string().optional(),
    date: z.coerce.date(),
    description: z.string().optional(),
    output: z.string().optional(),
    grant: z.string().optional(),
    // Own-hero posts (grant awards, institutional notices) record their remote
    // hero's dims; posts announcing an output inherit that output's hero.
    hero: imageDims.optional(),
  }),
});

export const collections = {
  pages,
  people,
  leadership,
  schools,
  outputs,
  news,
  grants,
  grantSchemes,
};
