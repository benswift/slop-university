import { getCollection } from "astro:content";
import { formatAud, formatAudCompact } from "./grants";
import { presetSeries, seriesOrder } from "./outputs";
import { academicFte, chartSvg, performanceSpec, vlConfig } from "./performance";

export interface Dashboard {
  stats: { label: string; value: string | number }[];
  chart?: { label: string; light: string; dark: string };
}

async function build(): Promise<Dashboard> {
  const allOutputs = await getCollection("outputs");
  const allGrants = await getCollection("grants");
  const totalFunding = allGrants.reduce((sum, g) => sum + g.data.value, 0);

  const fte = academicFte();
  const stats = [
    { label: "Research outputs", value: allOutputs.length },
    {
      label: "Outputs per academic FTE",
      value: fte > 0 ? (allOutputs.length / fte).toFixed(2) : "—",
    },
    // The funding tiles arrive with the first award --- the repository predates
    // the university discovering research income.
    ...(totalFunding > 0
      ? [
          { label: "Funding awarded", value: formatAudCompact(totalFunding) },
          {
            label: "Research income per academic FTE",
            value: fte > 0 ? formatAud(totalFunding / fte) : "—",
          },
        ]
      : []),
  ];

  // The trend chart carries the whole build-time Vega-Lite pipeline (static SVG,
  // light/dark bake, slop palette). It renders twice; CSS shows the matching
  // theme. Outputs and funding stack as two panels sharing one day axis --- see
  // performanceSpec.
  const spec = performanceSpec(
    allOutputs.map((o) => ({ date: o.data.date, series: presetSeries[o.data.preset] })),
    allGrants.map((g) => ({ date: g.data.date, value: g.data.value })),
    seriesOrder,
  );
  const chart =
    allOutputs.length > 0
      ? {
          label:
            allGrants.length > 0
              ? "Cumulative research outputs by day split by output type, above cumulative research funding awarded on the same day axis"
              : "Cumulative research outputs by day, split by output type",
          light: await chartSvg({ ...spec, config: vlConfig("light") }),
          dark: await chartSvg({ ...spec, config: vlConfig("dark") }),
        }
      : undefined;

  return { stats, chart };
}

// The dashboard summarises the whole repository, never the active type filter,
// so every route that shows it shows the same tiles and the same SVG. Building
// it once per build makes that a property of the code rather than a thing four
// pages have to remember, and spares Vega six redundant renders.
let built: Promise<Dashboard> | undefined;

export function dashboard(): Promise<Dashboard> {
  return (built ??= build());
}
