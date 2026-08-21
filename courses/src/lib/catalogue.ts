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
  nodes: z.array(z.unknown()),
  edges: z.array(z.unknown()),
});

export const sourceSchema = z.strictObject({
  apiUrl: z.url(),
  sourceUrl: z.url(),
});

export type CourseFeed = z.infer<typeof courseSchema>;
export type CourseSource = z.infer<typeof sourceSchema>;

export function validateCatalogue(feeds: unknown[]): CourseFeed[] {
  const parsed = feeds.map((feed) => courseSchema.parse(feed));
  const seen = new Set<string>();
  for (const feed of parsed) {
    const { code, level } = feed.course;
    if (Number(code[4]) !== level) throw new Error(`${code}: level does not match code`);
    if (seen.has(code))
      throw new Error(`${code}: duplicate course code; reroll the last three digits`);
    seen.add(code);
  }
  return parsed.toSorted((a, b) => a.course.code.localeCompare(b.course.code));
}
