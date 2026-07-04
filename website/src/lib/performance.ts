import { readFileSync } from "node:fs";
import { resolve } from "node:path";

// The publish ledger is the canonical outputs manifest (repo root, written by
// every /publish run); the roster supplies the academic FTE denominator. Both
// are read at build time --- this page carries no hand-maintained data.
// Resolved from the working directory (builds run from website/), because
// import.meta.url points into dist/.prerender at build time.
const ledgerPath = resolve(process.cwd(), "../data/publish-ledger.json");
const rosterPath = resolve(process.cwd(), "../canon/roster.yml");

export interface LedgerRun {
  date: string;
  preset: string;
  doi: string;
  output: string;
  school: string;
}

export function readLedger(): LedgerRun[] {
  const parsed = JSON.parse(readFileSync(ledgerPath, "utf8")) as { runs: LedgerRun[] };
  return parsed.runs;
}

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

// The slop palette for Vega-Lite --- theme colours, never library defaults.
export const chartTheme = {
  gold: "#b97d1c",
  ink: "#1a1a1a",
  grey: "#6b6154",
  grid: "#e4ddd0",
  font: "Public Sans, sans-serif",
};

export function vlConfig() {
  return {
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
}
