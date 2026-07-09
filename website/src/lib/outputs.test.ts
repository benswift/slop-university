import type { CollectionEntry } from "astro:content";
import { describe, expect, it } from "vitest";
import { bibtex, bibtexTokens, fullTitle, presetLabels } from "./outputs";

const entry: CollectionEntry<"outputs">["data"] = {
  title: "The Queue as Leading Indicator",
  authors: ["Casimir Beng", "Osei Vandermeer"],
  preset: "research-poster",
  school: "School of Continuous Improvement",
  date: new Date("2026-07-04"),
  doi: "10.5555/slop.sn9kzr",
  summary: "A two-year study.",
  topic: "coffee-cart queue lengths",
  pdf: "/outputs/pdf/slop-poster-x.pdf",
  version: "1.0",
};

describe("bibtex", () => {
  it("renders a complete @misc entry keyed by the DOI seed", () => {
    const cite = bibtex("slop-poster-x", entry);
    expect(cite).toContain("@misc{slop_sn9kzr,");
    expect(cite).toContain("author       = {Casimir Beng and Osei Vandermeer},");
    expect(cite).toContain("year         = {2026},");
    expect(cite).toContain("doi          = {10.5555/slop.sn9kzr},");
    expect(cite).toContain("url          = {https://slop.university/outputs/slop-poster-x/},");
    expect(cite).toContain("note         = {Research poster},");
  });

  it("falls back to the institution when there are no authors", () => {
    const cite = bibtex("slop-poster-x", { ...entry, authors: [] });
    expect(cite).toContain("author       = {Slop University},");
  });

  it("cites the full title, rejoining the subtitle", () => {
    const cite = bibtex("slop-poster-x", {
      ...entry,
      subtitle: "Coffee-Cart Waiting Times and Global-Ranking Trajectory",
    });
    expect(cite).toContain(
      "title        = {The Queue as Leading Indicator: Coffee-Cart Waiting Times and Global-Ranking Trajectory},",
    );
  });
});

describe("bibtexTokens", () => {
  const citation = bibtex("slop-poster-x", entry);
  const tokens = bibtexTokens(citation);

  it("reassembles the citation verbatim", () => {
    expect(tokens.map((t) => t.text).join("")).toBe(citation);
  });

  it("picks out the entry type and cite key", () => {
    expect(tokens).toContainEqual({ kind: "type", text: "@misc" });
    expect(tokens).toContainEqual({ kind: "key", text: "slop_sn9kzr" });
  });

  it("splits each field into a name and a braced value", () => {
    expect(tokens).toContainEqual({ kind: "field", text: "doi" });
    expect(tokens).toContainEqual({ kind: "value", text: "10.5555/slop.sn9kzr" });
  });

  it("leaves a value containing an equals sign or comma intact", () => {
    const tricky = bibtex("slop-poster-x", { ...entry, title: "A = B, mostly" });
    expect(bibtexTokens(tricky)).toContainEqual({ kind: "value", text: "A = B, mostly" });
  });
});

describe("fullTitle", () => {
  it("rejoins title and subtitle with ': '", () => {
    expect(
      fullTitle({
        title: "Reading the Drift Before the Workaround",
        subtitle: "Forecasting Exam-Integrity Vulnerability",
      }),
    ).toBe("Reading the Drift Before the Workaround: Forecasting Exam-Integrity Vulnerability");
  });

  it("returns the title alone when there is no subtitle", () => {
    expect(fullTitle({ title: "The Queue as Leading Indicator" })).toBe(
      "The Queue as Leading Indicator",
    );
  });
});

describe("presetLabels", () => {
  it("labels every preset the schema allows", () => {
    for (const preset of ["research-poster", "paper", "brochure", "strategy", "impact-report"] as const) {
      expect(presetLabels[preset]).toBeTruthy();
    }
  });
});
