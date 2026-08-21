import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { sourceSchema, validateCatalogue } from "../src/lib/catalogue";

const sourcesPath = resolve("src/data/sources.json");
const outputPath = resolve("src/data/catalogue.json");
const sources = sourceSchema.array().parse(JSON.parse(await readFile(sourcesPath, "utf8")));
const feeds = await Promise.all(
  sources.map(async ({ apiUrl }) => {
    const response = await fetch(apiUrl);
    if (!response.ok) throw new Error(`${apiUrl}: ${response.status} ${response.statusText}`);
    return response.json();
  }),
);
const catalogue = validateCatalogue(feeds);
await writeFile(outputPath, `${JSON.stringify(catalogue, null, 2)}\n`);
console.log(`Synced ${catalogue.length} course${catalogue.length === 1 ? "" : "s"}.`);
