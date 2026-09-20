import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import {
  type Candidate,
  type CatalogueEntry,
  entrySchema,
  sourceSchema,
  validateCatalogue,
} from "../src/lib/catalogue";

const sourcesPath = resolve("src/data/sources.json");
const outputPath = resolve("src/data/catalogue.json");

const sources = sourceSchema.array().parse(JSON.parse(await readFile(sourcesPath, "utf8")));

// Previous run's entries, keyed by feed URL, so an unchanged course can be
// revalidated with a conditional request rather than refetched and reparsed.
const cached = new Map<string, CatalogueEntry>(
  entrySchema
    .array()
    .catch([])
    .parse(JSON.parse(await readFile(outputPath, "utf8").catch(() => "[]")))
    .map((entry) => [entry.apiUrl, entry]),
);

type Fetched = { candidate: Candidate; reused: boolean } | { apiUrl: string; error: string };

const results = await Promise.all(
  sources.map(async ({ apiUrl, sourceUrl }): Promise<Fetched> => {
    const previous = cached.get(apiUrl);
    try {
      const response = await fetch(apiUrl, {
        headers: previous?.etag ? { "If-None-Match": previous.etag } : {},
      });
      // 304: the body we already hold is still current, so reuse it verbatim.
      if (response.status === 304 && previous) {
        return {
          candidate: { apiUrl, sourceUrl, etag: previous.etag, feed: previous.feed },
          reused: true,
        };
      }
      if (!response.ok) return { apiUrl, error: `${response.status} ${response.statusText}` };
      const etag = response.headers.get("etag") ?? undefined;
      return { candidate: { apiUrl, sourceUrl, etag, feed: await response.json() }, reused: false };
    } catch (error) {
      return { apiUrl, error: (error as Error).message };
    }
  }),
);

const unreachable = results.filter((r): r is { apiUrl: string; error: string } => "error" in r);
const fetched = results.filter(
  (r): r is { candidate: Candidate; reused: boolean } => "candidate" in r,
);
const { entries, rejected } = validateCatalogue(fetched.map((r) => r.candidate));

// Only rewrite when something actually changed: an unchanged catalogue that
// rewrites itself every run produces a commit, a rebuild and a redeploy for
// nothing.
const next = `${JSON.stringify(entries, null, 2)}\n`;
const current = await readFile(outputPath, "utf8").catch(() => "");
const changed = next !== current;
if (changed) await writeFile(outputPath, next);

const reused = fetched.filter((r) => r.reused).length;
console.log(
  `${entries.length} course${entries.length === 1 ? "" : "s"} (${reused} unchanged, ${fetched.length - reused} refetched); catalogue ${changed ? "updated" : "unchanged"}.`,
);
for (const { apiUrl, error } of unreachable) console.log(`  unreachable: ${apiUrl} -> ${error}`);
for (const { apiUrl, reason } of rejected) console.log(`  rejected:    ${apiUrl} -> ${reason}`);
