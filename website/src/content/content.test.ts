import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { parse as parseYaml } from "yaml";

// Dataset integrity: the publish pipeline writes news, outputs, and public
// artefacts as a unit, and grows the canon (people, schools) the site renders
// --- these checks catch a partial or hand-broken deposit, and prove the parts
// agree across the seams (roster ↔ schools ↔ outputs).

const contentDir = join(process.cwd(), "src/content");
const publicDir = join(process.cwd(), "public");
const canonDir = join(process.cwd(), "..", "canon");

const outputIds = readdirSync(join(contentDir, "outputs"))
  .filter((f) => f.endsWith(".yml"))
  .map((f) => f.replace(/\.yml$/, ""));

const outputs = outputIds.map(
  (id) => parseYaml(readFileSync(join(contentDir, "outputs", `${id}.yml`), "utf8")) as {
    authors?: string[];
    school?: string;
  },
);

const repoRoot = join(process.cwd(), "..");
const researchers = (
  parseYaml(readFileSync(join(canonDir, "roster.yml"), "utf8")) as {
    researchers: { id: string; name: string; school: string; headshot: string }[];
  }
).researchers;

const schoolDoc = parseYaml(readFileSync(join(canonDir, "schools.yml"), "utf8")) as Record<
  string,
  { name: string }[]
>;
const schoolNames = new Set((schoolDoc.schools ?? []).map((s) => s.name));
const allOrgNames = new Set(Object.values(schoolDoc).flat().map((o) => o.name));
const researcherNames = new Set(researchers.map((r) => r.name));

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

  it("credit only roster researchers", () => {
    for (const output of outputs) {
      for (const author of output.authors ?? []) {
        expect(researcherNames, `output author "${author}"`).toContain(author);
      }
    }
  });

  it("name a school that exists in the canon", () => {
    for (const output of outputs) {
      if (output.school) expect(schoolNames, output.school).toContain(output.school);
    }
  });
});

describe("roster", () => {
  it("affiliates every researcher to a real school", () => {
    for (const r of researchers) {
      expect(schoolNames, `${r.name} → ${r.school}`).toContain(r.school);
    }
  });

  it("has a headshot on disk for every researcher", () => {
    for (const r of researchers) {
      expect(existsSync(join(repoRoot, r.headshot)), `${r.name} headshot`).toBe(true);
    }
  });
});

// Keep allOrgNames referenced (units/labs/etc. are canon we may cross-check as
// the site grows); the assertion above already covers schools specifically.
void allOrgNames;
