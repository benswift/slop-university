import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { parse, View } from "vega";
import { compile, type TopLevelSpec } from "vega-lite";

// The outputs content collection is the canonical record of published
// artefacts; the roster supplies the academic FTE denominator. Both are read
// at build time --- this page carries no hand-maintained data. The roster is
// resolved from the working directory (builds run from website/), because
// import.meta.url points into dist/.prerender at build time.
const rosterPath = resolve(process.cwd(), "../canon/roster.yml");

export function academicFte(): number {
  // One entry per `- id:` line; the roster is small and flat, so a line count
  // beats a YAML-parser dependency.
  const roster = readFileSync(rosterPath, "utf8");
  return roster.split("\n").filter((line) => /^\s*-\s+id:/.test(line)).length;
}

export function countBy<T>(items: T[], key: (item: T) => string): { key: string; count: number }[] {
  const counts = new Map<string, number>();
  for (const item of items) {
    const k = key(item);
    counts.set(k, (counts.get(k) ?? 0) + 1);
  }
  return [...counts.entries()].map(([k, count]) => ({ key: k, count }));
}

function outputsByYear(dates: Date[]): { key: string; count: number }[] {
  return countBy(dates, (d) => String(d.getFullYear())).toSorted((a, b) =>
    a.key.localeCompare(b.key),
  );
}

// Cumulative outputs climb monotonically, as the sector expects.
export function cumulativeByYear(dates: Date[]): { year: string; outputs: number }[] {
  let cumulative = 0;
  return outputsByYear(dates).map(({ key, count }) => {
    cumulative += count;
    return { year: key, outputs: cumulative };
  });
}

export function perFteByYear(dates: Date[], fte: number): { year: string; perFte: number }[] {
  return outputsByYear(dates).map(({ key, count }) => ({
    year: key,
    perFte: Number((count / fte).toFixed(2)),
  }));
}

// The slop palette for Vega-Lite --- theme colours, never library defaults.
const chartTheme = {
  gold: "#b97d1c",
  ink: "#1a1a1a",
  grey: "#6b6154",
  grid: "#e4ddd0",
  font: "Public Sans, sans-serif",
};

export const vlConfig = {
  background: "transparent",
  font: chartTheme.font,
  axis: {
    labelColor: chartTheme.grey,
    titleColor: chartTheme.grey,
    gridColor: chartTheme.grid,
    domainColor: chartTheme.grid,
    tickColor: chartTheme.grid,
    labelFontSize: 12,
    titleFontSize: 12,
  },
  view: { stroke: null },
  bar: { color: chartTheme.gold },
  line: { color: chartTheme.gold, strokeWidth: 2.5 },
  point: { color: chartTheme.gold, filled: true },
};

// Charts are compiled to static SVG at build time; no Vega runtime reaches
// the client. width/height become a viewBox so the SVG scales fluidly.
export async function chartSvg(spec: TopLevelSpec): Promise<string> {
  const view = new View(parse(compile(spec).spec), { renderer: "none" });
  const svg = await view.toSVG();
  view.finalize();
  if (svg.includes("viewBox")) return svg;
  const size = svg.match(/<svg[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"/);
  return size ? svg.replace("<svg", `<svg viewBox="0 0 ${size[1]} ${size[2]}"`) : svg;
}
