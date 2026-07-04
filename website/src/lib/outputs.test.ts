import type { CollectionEntry } from "astro:content";
import { describe, expect, it } from "vitest";
import { bibtex, presetLabels } from "./outputs";

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
});

describe("presetLabels", () => {
  it("labels every preset the schema allows", () => {
    for (const preset of ["research-poster", "paper", "strategy", "impact-report"] as const) {
      expect(presetLabels[preset]).toBeTruthy();
    }
  });
});
