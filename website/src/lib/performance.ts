import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { parse, View } from "vega";
import { compile, type TopLevelSpec } from "vega-lite";
import { parse as parseYaml } from "yaml";

// The outputs content collection is the canonical record of published
// artefacts; the roster supplies the academic FTE denominator. Both are read
// at build time --- the outputs page carries no hand-maintained data. The
// roster is resolved from the working directory (builds run from website/),
// because import.meta.url points into dist/.prerender at build time.
const rosterPath = resolve(process.cwd(), "../canon/roster.yml");

export function academicFte(): number {
  // One FTE per roster researcher --- the same parse the people collection
  // loader does (see content.config.ts), so the denominator can't drift on a
  // formatting change the way a line-count regex could.
  const roster = parseYaml(readFileSync(rosterPath, "utf8")) as { researchers: unknown[] };
  return roster.researchers.length;
}

export interface SeriesPoint {
  date: string;
  series: string;
  outputs: number;
}

// Dates come out of the collection as UTC midnight (a date-only yml scalar), so
// bucket them in UTC too: a local-time accessor would slide an output into the
// previous day whenever the build machine sits west of Greenwich.
const day = (d: Date): string => d.toISOString().slice(0, 10);

// One cumulative point per day a series published, each series climbing
// monotonically on its own count --- the spec draws the flat stretches between
// a series' publication days, so days it sits out need no point of their own.
export function cumulativeByDay(items: { date: Date; series: string }[]): SeriesPoint[] {
  const running = new Map<string, number>();
  // Keyed by day and series: a second output on the same day updates the point
  // in place, leaving the day's final cumulative total at its first position.
  const points = new Map<string, SeriesPoint>();
  for (const { date, series } of items.toSorted((a, b) => a.date.valueOf() - b.date.valueOf())) {
    const outputs = (running.get(series) ?? 0) + 1;
    running.set(series, outputs);
    points.set(`${day(date)} ${series}`, { date: day(date), series, outputs });
  }
  return [...points.values()];
}

// The slop palette for Vega-Lite --- theme colours, never library defaults.
// Charts are static SVG baked at build time, so each spec renders twice (a
// light and a dark variant) and CSS shows the one matching the site theme.
const gold = "#b97d1c";

// Categorical series, in the same two-ink register as the brand package's
// `slop-categorical`: gold leads, then the ink (inverted to cream on the dark
// surface, where near-black would vanish), then the warm grey. Series also
// carry a stroke dash, so the lines stay separable without a third hue.
const categorical = {
  light: [gold, "#1a1a1a", "#6b6154"],
  dark: [gold, "#e4ddd0", "#a39887"],
};

export function vlConfig(mode: "light" | "dark") {
  const grey = mode === "dark" ? "#a39887" : "#6b6154";
  const grid = mode === "dark" ? "#3d3831" : "#e4ddd0";
  return {
    background: "transparent",
    font: "Public Sans, sans-serif",
    axis: {
      labelColor: grey,
      titleColor: grey,
      gridColor: grid,
      domainColor: grid,
      tickColor: grid,
      labelFontSize: 12,
      titleFontSize: 12,
      // 0 disables truncation; headless width estimates over-truncate the
      // labels otherwise.
      labelLimit: 0,
    },
    legend: { labelColor: grey, titleColor: grey, labelFontSize: 12, labelLimit: 0 },
    range: { category: categorical[mode] },
    view: { stroke: null },
    bar: { color: gold },
    line: { color: gold, strokeWidth: 2.5 },
    point: { color: gold, filled: true },
  };
}

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
