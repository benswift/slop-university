import { z } from "zod";

export const courseSchema = z.strictObject({
  schemaVersion: z.literal(1),
  canonicalUrl: z.url(),
  course: z.strictObject({
    code: z.string().regex(/^SLOP([1-4]|[6-8])\d{3}$/),
    title: z.string().min(1),
    session: z.string().min(1),
    year: z.number().int(),
    level: z.union([
      z.literal(1),
      z.literal(2),
      z.literal(3),
      z.literal(4),
      z.literal(6),
      z.literal(7),
      z.literal(8),
    ]),
    startDate: z.iso.date(),
    endDate: z.iso.date(),
    description: z.string().min(80).max(300),
    tags: z.array(z.string().min(2).max(24)).min(1).max(3),
    learningOutcomes: z.array(z.string()),
  }),
  // astro-course-university emits this alongside the course record. Feeds are
  // strict so an unmodelled field is caught rather than silently dropped, which
  // is also why it has to be declared here the moment the producer emits it.
  timezone: z.string().optional(),
  nodes: z.array(z.unknown()),
  edges: z.array(z.unknown()),
});

export const sourceSchema = z.strictObject({
  apiUrl: z.url(),
  sourceUrl: z.url(),
});

// The checked-in catalogue keeps each feed next to the source it came from and
// the ETag it was served with, so the next sync can revalidate with a
// conditional request instead of refetching every body.
export const entrySchema = z.strictObject({
  apiUrl: z.url(),
  sourceUrl: z.url(),
  etag: z.string().optional(),
  feed: courseSchema,
});

export type CourseFeed = z.infer<typeof courseSchema>;
export type CourseSource = z.infer<typeof sourceSchema>;
export type CatalogueEntry = z.infer<typeof entrySchema>;

export interface Candidate {
  apiUrl: string;
  sourceUrl: string;
  etag?: string;
  feed: unknown;
}

export interface Rejection {
  apiUrl: string;
  reason: string;
}

/**
 * Validate candidate feeds into catalogue entries.
 *
 * One bad feed must not cost the whole cohort its catalogue, so a rejection is
 * returned rather than thrown. Course codes are the catalogue's primary key ---
 * a duplicate cannot be rendered or resolved to a canonical URL, so the second
 * claimant is rejected and named instead of overwriting the first.
 */
export function validateCatalogue(candidates: Candidate[]): {
  entries: CatalogueEntry[];
  rejected: Rejection[];
} {
  const entries: CatalogueEntry[] = [];
  const rejected: Rejection[] = [];
  const claimed = new Map<string, string>();

  for (const { apiUrl, sourceUrl, etag, feed } of candidates) {
    const parsed = courseSchema.safeParse(feed);
    if (!parsed.success) {
      const reason = parsed.error.issues
        .map((issue) => `${issue.path.join(".") || "(root)"}: ${issue.message}`)
        .join("; ");
      rejected.push({ apiUrl, reason });
      continue;
    }

    const { code, level } = parsed.data.course;
    if (Number(code[4]) !== level) {
      rejected.push({ apiUrl, reason: `${code}: level does not match code` });
      continue;
    }

    const priorClaim = claimed.get(code);
    if (priorClaim !== undefined) {
      rejected.push({
        apiUrl,
        reason: `${code}: duplicate course code, already claimed by ${priorClaim}; reroll the last three digits`,
      });
      continue;
    }

    claimed.set(code, apiUrl);
    entries.push({ apiUrl, sourceUrl, ...(etag !== undefined && { etag }), feed: parsed.data });
  }

  return {
    entries: entries.toSorted((a, b) => a.feed.course.code.localeCompare(b.feed.course.code)),
    rejected,
  };
}
