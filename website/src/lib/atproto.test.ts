import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { z } from "astro/zod";
import { parse as parseYaml } from "yaml";
import { documentRkey, documentUri, publicationUri } from "./atproto";
import constants from "./atproto.json";
import { presetLabels } from "./outputs";

const outputsDir = join(process.cwd(), "src/content/outputs");
const outputs = readdirSync(outputsDir)
  .filter((f) => f.endsWith(".yml"))
  .map((f) => ({
    id: f.replace(/\.yml$/, ""),
    publishedAt: new Date(
      z
        .object({ publishedAt: z.string() })
        .parse(parseYaml(readFileSync(join(outputsDir, f), "utf8"))).publishedAt,
    ),
  }));

const TID = /^[2-7a-j][2-7a-z]{12}$/;

describe("ATproto record keys", () => {
  it("agree with the vectors ops/sync-atproto.py checks itself against", () => {
    for (const v of constants.vectors) {
      expect(documentRkey(v.id, new Date(v.publishedAt))).toBe(v.rkey);
    }
  });

  it("are well-formed TIDs, unique across every output", () => {
    const rkeys = outputs.map((o) => documentRkey(o.id, o.publishedAt));
    for (const rkey of rkeys) expect(rkey).toMatch(TID);
    expect(new Set(rkeys).size).toBe(rkeys.length);
  });

  it("build AT-URIs in the University's repo", () => {
    expect(constants.publicationRkey).toMatch(TID);
    expect(publicationUri).toMatch(
      /^at:\/\/did:plc:[a-z0-9]+\/site\.standard\.publication\/[2-7a-z]{13}$/,
    );
    expect(documentUri(outputs[0].id, outputs[0].publishedAt)).toMatch(
      /^at:\/\/did:plc:[a-z0-9]+\/site\.standard\.document\/[2-7a-z]{13}$/,
    );
  });
});

describe("the university.slop.defs lexicon", () => {
  // Every published preset needs an outputClass token, or its documents carry
  // a class the University's own vocabulary does not list.
  it("has an outputClass token for every preset", () => {
    const defs = z
      .object({
        defs: z.record(z.string(), z.object({ type: z.string() }).loose()).and(
          z.object({
            outputClass: z.object({ knownValues: z.array(z.string()) }).loose(),
          }),
        ),
      })
      .parse(
        JSON.parse(
          readFileSync(join(process.cwd(), "..", "lexicons/university/slop/defs.json"), "utf8"),
        ),
      );
    for (const preset of Object.keys(presetLabels)) {
      const token = preset.replace(/-([a-z])/g, (_, c: string) => c.toUpperCase());
      expect(defs.defs[token]?.type, preset).toBe("token");
      expect(defs.defs.outputClass.knownValues).toContain(`university.slop.defs#${token}`);
    }
  });
});
