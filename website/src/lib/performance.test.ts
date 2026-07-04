import { describe, expect, it } from "vitest";
import { academicFte, chartSvg, countBy, cumulativeByYear, perFteByYear } from "./performance";

describe("countBy", () => {
  it("counts occurrences per key", () => {
    const counts = countBy(["a", "b", "a", "a"], (s) => s);
    expect(counts).toEqual([
      { key: "a", count: 3 },
      { key: "b", count: 1 },
    ]);
  });
});

describe("cumulativeByYear", () => {
  it("accumulates monotonically over sorted years", () => {
    const dates = [new Date("2027-03-01"), new Date("2026-07-04"), new Date("2027-11-20")];
    expect(cumulativeByYear(dates)).toEqual([
      { year: "2026", outputs: 1 },
      { year: "2027", outputs: 3 },
    ]);
  });
});

describe("perFteByYear", () => {
  it("divides yearly counts by FTE, rounded to 2 places", () => {
    const dates = [new Date("2026-01-01"), new Date("2026-06-01")];
    expect(perFteByYear(dates, 3)).toEqual([{ year: "2026", perFte: 0.67 }]);
  });
});

describe("academicFte", () => {
  it("counts the roster entries", () => {
    expect(academicFte()).toBeGreaterThan(0);
  });
});

describe("chartSvg", () => {
  it("renders a Vega-Lite spec to scalable SVG at build time", async () => {
    const svg = await chartSvg({
      data: { values: [{ x: "a", y: 1 }] },
      mark: "bar",
      encoding: {
        x: { field: "x", type: "ordinal" },
        y: { field: "y", type: "quantitative" },
      },
      width: 100,
      height: 100,
    });
    expect(svg).toContain("<svg");
    expect(svg).toContain("viewBox");
  });
});
