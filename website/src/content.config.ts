import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";
import { definePageCollection } from "astro-theme-university/schemas";

// Free-form pages (colophon, agent-grown pages like people/ and schools/).
const pages = definePageCollection({ passthrough: true });

// One entry per published artefact. Written by the /publish pipeline; the
// per-output landing page and the DOI resolver route are generated from it.
const outputs = defineCollection({
  loader: glob({ pattern: "**/*.yml", base: "src/content/outputs" }),
  schema: z.object({
    title: z.string(),
    authors: z.array(z.string()).default([]),
    preset: z.enum(["research-poster", "paper", "strategy", "impact-report"]),
    school: z.string().optional(),
    date: z.coerce.date(),
    doi: z.string().regex(/^10\.5555\/slop\.[a-z0-9]+$/),
    summary: z.string(),
    topic: z.string(),
    pdf: z.string(),
    thumbnail: z.string().optional(),
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

export const collections = { pages, outputs, news };
