import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

// Dataset integrity: the publish pipeline writes news, outputs, and public
// artefacts as a unit --- these checks catch a partial or hand-broken deposit.

const contentDir = join(process.cwd(), "src/content");
const publicDir = join(process.cwd(), "public");

const outputIds = readdirSync(join(contentDir, "outputs"))
  .filter((f) => f.endsWith(".yml"))
  .map((f) => f.replace(/\.yml$/, ""));

describe("news entries", () => {
  it("reference an existing outputs entry", () => {
    for (const file of readdirSync(join(contentDir, "news"))) {
      const frontmatter = readFileSync(join(contentDir, "news", file), "utf8");
      const ref = frontmatter.match(/^output:\s*(\S+)\s*$/m);
      if (ref) expect(outputIds).toContain(ref[1]);
    }
  });
});

describe("outputs entries", () => {
  it("point at artefacts that exist under public/", () => {
    for (const id of outputIds) {
      const entry = readFileSync(join(contentDir, "outputs", `${id}.yml`), "utf8");
      for (const match of entry.matchAll(/^(?:pdf|thumbnail):\s*(\/\S+)\s*$/gm)) {
        expect(existsSync(join(publicDir, match[1])), `${id}: ${match[1]}`).toBe(true);
      }
    }
  });
});
