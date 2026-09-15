import type { CollectionEntry } from "astro:content";

// `date` is the human-facing publication day and `publishedAt` the exact time
// the publish wrapper stamped. Sorting on the day alone leaves a busy day's
// entries in filename order, so every newest-first list sorts on the instant.
// Outputs and output-less news posts each carry their own (the content test
// enforces it); a post announcing an output takes its output's, so the two
// always sit together.

type Dated = { id: string; data: { date: Date; publishedAt?: Date } };

/** The instant an entry was published, falling back to its day. */
export function publishedTime(entry: Dated): number {
  return (entry.data.publishedAt ?? entry.data.date).getTime();
}

/** Newest-first comparator; ties break on id so the order is stable. */
export function newestFirst(a: Dated, b: Dated): number {
  return publishedTime(b) - publishedTime(a) || b.id.localeCompare(a.id);
}

type NewsEntry = CollectionEntry<"news">;
type OutputsById = Map<string, CollectionEntry<"outputs">>;

/** When a news post was published: its output's time if it announces one. */
export function newsPublishedAt(entry: NewsEntry, outputsById: OutputsById): Date {
  const output = entry.data.output ? outputsById.get(entry.data.output) : undefined;
  return output?.data.publishedAt ?? entry.data.publishedAt ?? entry.data.date;
}

/** News posts, newest first. */
export function sortNews(news: NewsEntry[], outputsById: OutputsById): NewsEntry[] {
  const time = new Map(news.map((n) => [n.id, newsPublishedAt(n, outputsById).getTime()]));
  return news.toSorted((a, b) => time.get(b.id)! - time.get(a.id)! || b.id.localeCompare(a.id));
}
