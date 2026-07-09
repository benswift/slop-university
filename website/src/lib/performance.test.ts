import { describe, expect, it } from "vitest";
import { academicFte, chartSvg, cumulativeByDay } from "./performance";

const item = (date: string, series: string) => ({ date: new Date(date), series });

describe("cumulativeByDay", () => {
  it("accumulates each series independently, in day order", () => {
    expect(
      cumulativeByDay([
        item("2026-07-06", "posters"),
        item("2026-07-04", "papers"),
        item("2026-07-06", "papers"),
      ]),
    ).toEqual([
      { date: "2026-07-04", series: "papers", outputs: 1 },
      { date: "2026-07-06", series: "posters", outputs: 1 },
      { date: "2026-07-06", series: "papers", outputs: 2 },
    ]);
  });

  it("emits one point per day, carrying the day's final total", () => {
    const sameDay = [item("2026-07-08", "papers"), item("2026-07-08", "papers")];
    expect(cumulativeByDay(sameDay)).toEqual([
      { date: "2026-07-08", series: "papers", outputs: 2 },
    ]);
  });

  it("buckets by UTC day, so a date-only entry can't slip to the day before", () => {
    const [point] = cumulativeByDay([item("2026-07-04T00:00:00Z", "papers")]);
    expect(point.date).toBe("2026-07-04");
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
