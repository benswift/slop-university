import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { parse as parseYaml } from "yaml";

// Dataset integrity: the publish pipeline writes news, outputs, and public
// artefacts as a unit, and grows the canon (people, schools) the site renders
// --- these checks catch a partial or hand-broken deposit, and prove the parts
// agree across the seams (roster ↔ schools ↔ outputs).

const contentDir = join(process.cwd(), "src/content");
const canonDir = join(process.cwd(), "..", "canon");

const outputIds = readdirSync(join(contentDir, "outputs"))
  .filter((f) => f.endsWith(".yml"))
  .map((f) => f.replace(/\.yml$/, ""));

const outputs = outputIds.map(
  (id) =>
    parseYaml(readFileSync(join(contentDir, "outputs", `${id}.yml`), "utf8")) as {
      authors?: string[];
      school?: string;
      doi?: string;
      date?: string;
      grants?: string[];
      cites?: string[];
      preset?: string;
      pdfDark?: boolean;
      hero?: { width: number; height: number };
      thumb?: { width: number; height: number };
    },
);

const grantIds = readdirSync(join(contentDir, "grants"))
  .filter((f) => f.endsWith(".yml"))
  .map((f) => f.replace(/\.yml$/, ""));

const grants = grantIds.map(
  (id) =>
    parseYaml(readFileSync(join(contentDir, "grants", `${id}.yml`), "utf8")) as {
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

// University leadership --- the one real person in the canon, held in a file of
// his own so no run drawing authors "from canon/roster.yml" can reach him.
const leadership = (
  parseYaml(readFileSync(join(canonDir, "leadership.yml"), "utf8")) as {
    leadership: { id: string; name: string; school: string; headshot: string }[];
  }
).leadership;

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
const unitNames = new Set((schoolDoc.units ?? []).map((s) => s.name));
const allOrgNames = new Set(
  Object.values(schoolDoc)
    .flat()
    .map((o) => o.name),
);
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

  it("carry a hero: an output post inherits its output's, any other records its own dims", () => {
    // Mirrors the news pages' hero resolution. A post announcing an output
    // shows that output's remote hero; a grant award or an institutional
    // notice announces none, so it must record its own remote hero's dims in
    // frontmatter (the encoded rungs live in the img bucket, keyed by id ---
    // see src/lib/images.ts).
    for (const file of newsFiles) {
      const id = file.replace(/\.mdx?$/, "");
      const frontmatter = readFileSync(join(contentDir, "news", file), "utf8");
      const output = frontmatter.match(/^output:\s*(\S+)\s*$/m)?.[1];
      if (output) continue; // inherits the output's hero, checked below
      expect(/^hero:\s*$/m.test(frontmatter), `${id} hero dims`).toBe(true);
    }
  });

  it("promote at most one quote to a pull-quote blockquote", () => {
    // comms.md sets the first roster quote as a blockquote and leaves any
    // later one inline. Two blockquotes turn the release into a pull-quote
    // gallery, which the genre it imitates never does.
    for (const file of newsFiles) {
      const body = readFileSync(join(contentDir, "news", file), "utf8").split(/^---$/m)[2] ?? "";
      const blocks = body.split(/\n\s*\n/).filter((p) => p.trimStart().startsWith(">"));
      expect(blocks.length, `${file} pull-quotes`).toBeLessThanOrEqual(1);
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
  // The PDF itself lives in the bucket (src/lib/pdfs.ts), so its presence is
  // not something this suite can check offline --- that guarantee is the
  // publish wrapper's, which uploads before it pushes and aborts the tick if
  // the upload fails. What stays checkable here is that no entry stores a
  // location: a stray `pdf:` key would be silently ignored by the schema and
  // would read as authoritative to the next person editing an entry.
  it("store no PDF path --- the location is derived from the entry id", () => {
    for (const id of outputIds) {
      const entry = readFileSync(join(contentDir, "outputs", `${id}.yml`), "utf8");
      expect(entry, `${id} stores a stale pdf path`).not.toMatch(/^pdf:/m);
      expect(entry, `${id} stores a stale pdfDark path`).not.toMatch(/^pdfDark:\s*\//m);
    }
  });

  // A dark render is only ever produced for the poster presets (the e-signage
  // screens show white-on-black); a flag on anything else means the tick wrote
  // a fact that has no file behind it.
  it("only flag a dark render on the poster presets", () => {
    for (const [i, output] of outputs.entries()) {
      if (!output.pdfDark) continue;
      expect(
        ["research-poster", "marketing-poster"],
        `${outputIds[i]} flags pdfDark on a ${output.preset}`,
      ).toContain(output.preset);
    }
  });

  it("record positive intrinsic dims for the remote thumbnail (and hero when present)", () => {
    // The publish pipeline encodes each output's thumbnail and hero into the
    // img bucket and records only their dims here; the site derives every URL
    // and the srcset rung list from these numbers (src/lib/images.ts mirrors
    // ops/encode-images.py). Zero or missing dims would silently break that
    // derivation, so they are load-bearing content.
    for (let i = 0; i < outputs.length; i++) {
      const output = outputs[i];
      expect(output.thumb, `${outputIds[i]} thumb dims`).toBeDefined();
      expect(output.thumb?.width ?? 0, `${outputIds[i]} thumb width`).toBeGreaterThan(0);
      expect(output.thumb?.height ?? 0, `${outputIds[i]} thumb height`).toBeGreaterThan(0);
      if (output.hero) {
        expect(output.hero.width, `${outputIds[i]} hero width`).toBeGreaterThan(0);
        expect(output.hero.height, `${outputIds[i]} hero height`).toBeGreaterThan(0);
      }
    }
  });

  it("no longer ship per-tick image assets in the repo", () => {
    // Tripwire against an agent following a stale publish skill: the per-tick
    // image families moved to the img bucket, and these directories must not
    // quietly come back (they were the artifact-ceiling problem).
    const assetsDir = join(contentDir, "..", "assets");
    for (const dir of ["heroes/outputs", "heroes/news", "outputs/thumbs"]) {
      expect(existsSync(join(assetsDir, dir)), `${dir} resurrected`).toBe(false);
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

  // The internal citation graph (`cites:`, harvested by
  // ops/extract-citations.py) is load-bearing content: the roster's citation
  // counts and h-indices are counted straight off these edges, so a dangling
  // or impossible edge would inflate an indicator with nothing behind it.
  describe("citation edges", () => {
    const doiToId = new Map(outputs.map((o, i) => [o.doi, outputIds[i]]));

    it("cite a DOI that resolves to a published output", () => {
      outputs.forEach((output, i) => {
        for (const doi of output.cites ?? []) {
          expect(doiToId.get(doi), `${outputIds[i]} cites ${doi}`).toBeDefined();
        }
      });
    });

    it("cite each output at most once, and never themselves", () => {
      outputs.forEach((output, i) => {
        const cites = output.cites ?? [];
        expect(new Set(cites).size, `${outputIds[i]} repeats a citation`).toBe(cites.length);
        expect(cites, `${outputIds[i]} cites itself`).not.toContain(output.doi);
      });
    });

    it("postdate every output they cite", () => {
      outputs.forEach((output, i) => {
        for (const doi of output.cites ?? []) {
          const cited = outputs[outputIds.indexOf(doiToId.get(doi) ?? "")];
          if (!output.date || !cited?.date) continue;
          expect(
            output.date >= cited.date,
            `${outputIds[i]} (${output.date}) cites ${doi} (${cited.date}), which postdates it`,
          ).toBe(true);
        }
      });
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

// The Vice-Chancellor is the one real person in the canon. These checks are the
// mechanical half of the rule that keeps him out of the fiction's output: he
// renders a profile page like anyone else, but the institution never credits
// him with work it generated.
describe("leadership", () => {
  it("holds exactly one entry, kept out of the roster file", () => {
    expect(leadership).toHaveLength(1);
    for (const l of leadership) {
      expect(
        researchers.map((r) => r.id),
        `${l.id} in roster.yml`,
      ).not.toContain(l.id);
      expect(researcherNames, `${l.name} in roster.yml`).not.toContain(l.name);
    }
  });

  it("affiliates to a real org unit and has a headshot on disk", () => {
    for (const l of leadership) {
      expect(unitNames, `${l.name} → ${l.school}`).toContain(l.school);
      expect(existsSync(join(repoRoot, l.headshot)), `${l.name} headshot`).toBe(true);
    }
  });

  it("is never credited as an author on any output", () => {
    for (const l of leadership) {
      for (const output of outputs) {
        expect(output.authors ?? [], `output author "${l.name}"`).not.toContain(l.name);
      }
    }
  });

  it("never holds a grant or prize", () => {
    for (const l of leadership) {
      for (const grant of grants) {
        expect(grant.grantees ?? [], `grantee "${l.name}"`).not.toContain(l.name);
      }
    }
  });
});
