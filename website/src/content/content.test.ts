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
    doi?: string;
    date?: string;
    grants?: string[];
  },
);

const grantIds = readdirSync(join(contentDir, "grants"))
  .filter((f) => f.endsWith(".yml"))
  .map((f) => f.replace(/\.yml$/, ""));

const grants = grantIds.map(
  (id) => parseYaml(readFileSync(join(contentDir, "grants", `${id}.yml`), "utf8")) as {
    scheme?: string;
    date?: string;
    grantees?: string[];
    value?: number;
  },
);

const grantDateById = new Map(grantIds.map((id, i) => [id, grants[i].date]));

// Output publication dates by id, for the news-precedes-output check below.
// The yaml core schema keeps `date:` as an ISO string, so dates compare
// lexicographically.
const outputDateById = new Map(outputIds.map((id, i) => [id, outputs[i].date]));

const newsFiles = readdirSync(join(contentDir, "news")).filter((f) => /\.mdx?$/.test(f));

const repoRoot = join(process.cwd(), "..");
const researchers = (
  parseYaml(readFileSync(join(canonDir, "roster.yml"), "utf8")) as {
    researchers: { id: string; name: string; school: string; headshot: string }[];
  }
).researchers;

const schoolDoc = parseYaml(readFileSync(join(canonDir, "schools.yml"), "utf8")) as Record<
  string,
  { id: string; name: string }[]
>;

const schemes = (
  parseYaml(readFileSync(join(canonDir, "grants.yml"), "utf8")) as {
    schemes: { id: string; name: string; funder: string }[];
  }
).schemes;
const schemeIds = new Set(schemes.map((s) => s.id));
const schoolNames = new Set((schoolDoc.schools ?? []).map((s) => s.name));
const allOrgNames = new Set(Object.values(schoolDoc).flat().map((o) => o.name));
const researcherNames = new Set(researchers.map((r) => r.name));

// Name → URL-slug maps, mirroring the render-time resolvers in lib/canon.ts
// (personIdByName, schoolIdByName). The output landing page links each author
// to /people/<id>/ and the school to /schools/<id>/; these maps let the tests
// below prove every such cross-link resolves to exactly one canon page rather
// than silently degrading to plain text on a name mismatch or an id rename.
function nameToId(records: { id: string; name: string }[]): Map<string, string[]> {
  const map = new Map<string, string[]>();
  for (const r of records) map.set(r.name, [...(map.get(r.name) ?? []), r.id]);
  return map;
}
const researcherIdByName = nameToId(researchers);
const schoolIdByName = nameToId(schoolDoc.schools ?? []);

describe("news entries", () => {
  it("reference an existing outputs entry", () => {
    for (const file of newsFiles) {
      const frontmatter = readFileSync(join(contentDir, "news", file), "utf8");
      const ref = frontmatter.match(/^output:\s*(\S+)\s*$/m);
      if (ref) expect(outputIds).toContain(ref[1]);
    }
  });

  it("carry a hero: an output post inherits its output's, any other has its own", () => {
    // Mirrors newsPostHero() in lib/heroes.ts. A post announcing an output
    // shows that output's hero; a grant award or an institutional notice
    // announces none, so it must ship src/assets/heroes/news/<id>.avif.
    const assetsDir = join(contentDir, "..", "assets", "heroes");
    for (const file of newsFiles) {
      const id = file.replace(/\.mdx?$/, "");
      const output = readFileSync(join(contentDir, "news", file), "utf8").match(
        /^output:\s*(\S+)\s*$/m,
      )?.[1];
      const hero = output
        ? join(assetsDir, "outputs", `${output}.avif`)
        : join(assetsDir, "news", `${id}.avif`);
      expect(existsSync(hero), `${id} hero (${hero})`).toBe(true);
    }
  });

  it("carry a filename date prefix that matches the frontmatter date", () => {
    for (const file of newsFiles) {
      const frontmatter = readFileSync(join(contentDir, "news", file), "utf8");
      const date = frontmatter.match(/^date:\s*"?(\d{4}-\d{2}-\d{2})"?\s*$/m)?.[1];
      expect(date, `${file} frontmatter date`).toBe(file.slice(0, 10));
    }
  });

  it("announce no earlier than the output they reference", () => {
    for (const file of newsFiles) {
      const frontmatter = readFileSync(join(contentDir, "news", file), "utf8");
      const ref = frontmatter.match(/^output:\s*(\S+)\s*$/m);
      if (!ref) continue;
      const newsDate = frontmatter.match(/^date:\s*"?(\d{4}-\d{2}-\d{2})"?\s*$/m)?.[1];
      const outputDate = outputDateById.get(ref[1]);
      expect(newsDate, `${file} frontmatter date`).toBeDefined();
      expect(outputDate, `${ref[1]} date`).toBeDefined();
      if (!newsDate || !outputDate) continue;
      expect(
        newsDate >= outputDate,
        `${file} (${newsDate}) predates its output ${ref[1]} (${outputDate})`,
      ).toBe(true);
    }
  });

  it("reference an existing grant entry", () => {
    for (const file of newsFiles) {
      const frontmatter = readFileSync(join(contentDir, "news", file), "utf8");
      const ref = frontmatter.match(/^grant:\s*(\S+)\s*$/m);
      if (ref) expect(grantIds).toContain(ref[1]);
    }
  });

  it("announce no earlier than the grant they reference", () => {
    for (const file of newsFiles) {
      const frontmatter = readFileSync(join(contentDir, "news", file), "utf8");
      const ref = frontmatter.match(/^grant:\s*(\S+)\s*$/m);
      if (!ref) continue;
      const newsDate = frontmatter.match(/^date:\s*"?(\d{4}-\d{2}-\d{2})"?\s*$/m)?.[1];
      const grantDate = grantDateById.get(ref[1]);
      expect(newsDate, `${file} frontmatter date`).toBeDefined();
      expect(grantDate, `${ref[1]} date`).toBeDefined();
      if (!newsDate || !grantDate) continue;
      expect(
        newsDate >= grantDate,
        `${file} (${newsDate}) predates its grant ${ref[1]} (${grantDate})`,
      ).toBe(true);
    }
  });
});

describe("outputs entries", () => {
  it("point at a PDF that exists under public/", () => {
    for (const id of outputIds) {
      const entry = readFileSync(join(contentDir, "outputs", `${id}.yml`), "utf8");
      for (const match of entry.matchAll(/^pdf:\s*(\/\S+)\s*$/gm)) {
        expect(existsSync(join(publicDir, match[1])), `${id}: ${match[1]}`).toBe(true);
      }
    }
  });

  it("have a first-page thumbnail on disk (optimised via src/, not public/)", () => {
    // The publish pipeline writes each output's thumbnail to
    // src/assets/outputs/thumbs/<id>.avif so astro:assets optimises it.
    for (const id of outputIds) {
      const thumb = join(contentDir, "..", "assets", "outputs", "thumbs", `${id}.avif`);
      expect(existsSync(thumb), `${id} thumbnail`).toBe(true);
    }
  });

  it("mint a unique DOI per entry", () => {
    const dois = outputs.map((o, i) => {
      expect(o.doi, `${outputIds[i]} doi`).toBeDefined();
      return o.doi;
    });
    expect(new Set(dois).size).toBe(dois.length);
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

  it("credit authors that each resolve to exactly one /people/ page", () => {
    for (const output of outputs) {
      for (const author of output.authors ?? []) {
        expect(researcherIdByName.get(author), `author "${author}" → /people/`).toHaveLength(1);
      }
    }
  });

  it("name a school that resolves to exactly one /schools/ page", () => {
    for (const output of outputs) {
      if (output.school) {
        expect(schoolIdByName.get(output.school), `${output.school} → /schools/`).toHaveLength(1);
      }
    }
  });

  it("attach only grants that exist", () => {
    for (const output of outputs) {
      for (const grant of output.grants ?? []) {
        expect(grantIds, `attached grant "${grant}"`).toContain(grant);
      }
    }
  });

  it("postdate every grant they attach", () => {
    outputs.forEach((output, i) => {
      for (const grant of output.grants ?? []) {
        const grantDate = grantDateById.get(grant);
        if (!output.date || !grantDate) continue;
        expect(
          output.date >= grantDate,
          `${outputIds[i]} (${output.date}) predates its grant ${grant} (${grantDate})`,
        ).toBe(true);
      }
    });
  });
});

describe("grant entries", () => {
  it("reference a scheme defined in canon/grants.yml", () => {
    grants.forEach((grant, i) => {
      expect(grant.scheme, `${grantIds[i]} scheme`).toBeDefined();
      if (grant.scheme) expect(schemeIds, `${grantIds[i]} scheme`).toContain(grant.scheme);
    });
  });

  it("name grantees that each resolve to exactly one /people/ page", () => {
    for (const grant of grants) {
      for (const grantee of grant.grantees ?? []) {
        expect(researcherIdByName.get(grantee), `grantee "${grantee}" → /people/`).toHaveLength(1);
      }
    }
  });

  it("carry a filename date prefix that matches the frontmatter date", () => {
    grantIds.forEach((id, i) => {
      expect(grants[i].date, `${id} date`).toBe(id.slice(0, 10));
    });
  });

  it("record a positive whole-dollar value", () => {
    grants.forEach((grant, i) => {
      expect(Number.isInteger(grant.value) && (grant.value ?? 0) > 0, `${grantIds[i]} value`).toBe(
        true,
      );
    });
  });
});

describe("grant schemes", () => {
  it("are funded by an org unit that exists in the canon", () => {
    for (const scheme of schemes) {
      expect(allOrgNames, `${scheme.name} funder "${scheme.funder}"`).toContain(scheme.funder);
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
