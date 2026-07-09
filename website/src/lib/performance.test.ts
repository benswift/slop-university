import { describe, expect, it } from "vitest";
import { academicFte, chartSvg, cumulativeByDay, performanceSpec } from "./performance";

const item = (date: string, series: string) => ({ date: new Date(date), series });

// performanceSpec returns a concat spec; narrowing keeps the assertions off `any`.
const panels = (spec: ReturnType<typeof performanceSpec>) => ("concat" in spec ? spec.concat : []);

describe("cumulativeByDay", () => {
  it("accumulates each series independently, in day order", () => {
    expect(
      cumulativeByDay([
        item("2026-07-06", "posters"),
        item("2026-07-04", "papers"),
        item("2026-07-06", "papers"),
      ]),
    ).toEqual([
      { date: "2026-07-04", series: "papers", total: 1 },
      { date: "2026-07-06", series: "posters", total: 1 },
      { date: "2026-07-06", series: "papers", total: 2 },
    ]);
  });

  it("emits one point per day, carrying the day's final total", () => {
    const sameDay = [item("2026-07-08", "papers"), item("2026-07-08", "papers")];
    expect(cumulativeByDay(sameDay)).toEqual([{ date: "2026-07-08", series: "papers", total: 2 }]);
  });

  it("accumulates item values when given, for the funding series", () => {
    expect(
      cumulativeByDay([
        { ...item("2026-07-04", "funding"), value: 48750 },
        { ...item("2026-07-06", "funding"), value: 1200 },
      ]),
    ).toEqual([
      { date: "2026-07-04", series: "funding", total: 48750 },
      { date: "2026-07-06", series: "funding", total: 49950 },
    ]);
  });

  it("buckets by UTC day, so a date-only entry can't slip to the day before", () => {
    const [point] = cumulativeByDay([item("2026-07-04T00:00:00Z", "papers")]);
    expect(point.date).toBe("2026-07-04");
  });
});

describe("performanceSpec", () => {
  const outputs = [item("2026-07-04", "papers"), item("2026-07-09", "posters")];
  const grants = [{ date: new Date("2026-07-09"), value: 47285 }];

  it("stacks the funding panel under the outputs panel on one shared x scale", () => {
    const spec = performanceSpec(outputs, grants, ["papers", "posters"]);
    expect(panels(spec)).toHaveLength(2);
    expect(spec).toMatchObject({ columns: 1, align: "all", resolve: { scale: { x: "shared" } } });
  });

  it("seeds the funding series at zero on the first output's day", () => {
    const spec = performanceSpec(outputs, grants, ["papers", "posters"]);
    const [, funding] = panels(spec);
    expect(funding).toMatchObject({
      data: {
        values: [
          { date: "2026-07-04", series: "funding", total: 0 },
          { date: "2026-07-09", series: "funding", total: 47285 },
        ],
      },
    });
  });

  it("drops the funding panel until an award exists, keeping the date axis titled", () => {
    const spec = performanceSpec(outputs, [], ["papers", "posters"]);
    expect(panels(spec)).toHaveLength(1);
    expect(panels(spec)[0]).toMatchObject({ encoding: { x: { title: "Date" } } });
  });

  it("titles only the bottom panel's date axis when both panels render", () => {
    const [outputsPanel, funding] = panels(performanceSpec(outputs, grants, ["papers"]));
    expect(outputsPanel).toMatchObject({ encoding: { x: { title: null } } });
    expect(funding).toMatchObject({ encoding: { x: { title: "Date" } } });
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
