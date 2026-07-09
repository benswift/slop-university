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
  total: number;
}

// Dates come out of the collection as UTC midnight (a date-only yml scalar), so
// bucket them in UTC too: a local-time accessor would slide an output into the
// previous day whenever the build machine sits west of Greenwich.
const day = (d: Date): string => d.toISOString().slice(0, 10);

// One cumulative point per day a series moved, each series climbing
// monotonically on its own running total --- one count per item by default, or
// the item's `value` (grant dollars) when given. The spec draws the flat
// stretches between a series' active days, so days it sits out need no point
// of their own.
export function cumulativeByDay(
  items: { date: Date; series: string; value?: number }[],
): SeriesPoint[] {
  const running = new Map<string, number>();
  // Keyed by day and series: a second item on the same day updates the point
  // in place, leaving the day's final cumulative total at its first position.
  const points = new Map<string, SeriesPoint>();
  for (const { date, series, value } of items.toSorted(
    (a, b) => a.date.valueOf() - b.date.valueOf(),
  )) {
    const total = (running.get(series) ?? 0) + (value ?? 1);
    running.set(series, total);
    points.set(`${day(date)} ${series}`, { date: day(date), series, total });
  }
  return [...points.values()];
}

// The repository deposits daily, so the x axis is a day-resolution UTC scale
// (matching how the collections store their dates). tickMinStep is in
// scale-domain units --- one day of milliseconds --- so a short range can't
// sprout sub-day ticks, and a long one still gets however many day-aligned
// ticks Vega thinks fit.
const dayAxis = { format: "%d %b", tickMinStep: 24 * 60 * 60 * 1000 };

// step-after holds each series flat between its own deposits rather than
// sloping between them, which is what a cumulative total actually does.
const cumulativeLine = { type: "line", point: true, interpolate: "step-after" } as const;

// Outputs (counts) and funding (dollars) can't share a y axis, so they stack as
// two panels of one concat spec resolving x as a *shared* scale: one union
// domain, one set of ticks, and `align: "all"` puts both plot areas on the same
// grid however wide each panel's y-axis labels turn out to be. The funding
// panel only appears once there's an award to draw.
//
// Kept here rather than inline in the page: the two-panel spec is enough of a
// union type to blow out TS's inference inside .astro frontmatter.
export function performanceSpec(
  outputs: { date: Date; series: string }[],
  grants: { date: Date; value: number }[],
  seriesDomain: readonly string[],
): TopLevelSpec {
  // Funding is awarded rarely --- often a single deposit, landing wherever it
  // falls on the outputs axis. Seeding the series at zero on the first output's
  // day makes the line climb from the axis origin instead of hanging in space
  // as one detached point. cumulativeByDay adds `value`, so a zero contributes
  // no dollars; it only pins the series' start.
  const firstDay = outputs.reduce<Date | undefined>(
    (earliest, o) => (!earliest || o.date < earliest ? o.date : earliest),
    undefined,
  );
  const funding = [
    ...(firstDay ? [{ date: firstDay, series: "funding", value: 0 }] : []),
    ...grants.map((g) => ({ date: g.date, series: "funding", value: g.value })),
  ];

  const outputsPanel = {
    data: { values: cumulativeByDay(outputs) },
    mark: cumulativeLine,
    encoding: {
      // With a shared scale the "Date" title belongs under the bottom panel,
      // so the outputs panel only carries one when it stands alone.
      x: {
        field: "date",
        type: "temporal" as const,
        scale: { type: "utc" as const },
        title: grants.length > 0 ? null : "Date",
        axis: dayAxis,
      },
      y: {
        field: "total",
        type: "quantitative" as const,
        title: "Cumulative outputs",
        scale: { zero: true },
        axis: { tickMinStep: 1 },
      },
      // Colour and dash encode the same field with the same (null) title, so
      // Vega-Lite merges them into a single legend.
      color: {
        field: "series",
        type: "nominal" as const,
        title: null,
        scale: { domain: [...seriesDomain] },
        legend: { orient: "top-left" as const },
      },
      strokeDash: {
        field: "series",
        type: "nominal" as const,
        title: null,
        // Vega's default dashes are too fine to read at this stroke width.
        scale: { domain: [...seriesDomain], range: [[1, 0], [6, 3], [2, 2]] },
      },
    },
    width: 640,
    height: 200,
  };

  // A single series takes the config's gold line, so it needs no legend.
  const fundingPanel = {
    data: { values: cumulativeByDay(funding) },
    mark: cumulativeLine,
    encoding: {
      x: {
        field: "date",
        type: "temporal" as const,
        scale: { type: "utc" as const },
        title: "Date",
        axis: dayAxis,
      },
      y: {
        field: "total",
        type: "quantitative" as const,
        title: "Cumulative funding (A$)",
        scale: { zero: true },
        axis: { format: "$,.0f" },
      },
    },
    width: 640,
    height: 200,
  };

  return {
    concat: grants.length > 0 ? [outputsPanel, fundingPanel] : [outputsPanel],
    columns: 1,
    align: "all",
    spacing: 32,
    resolve: { scale: { x: "shared" } },
  };
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
