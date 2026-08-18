import { getCollection } from "astro:content";
import type { Output } from "./canon";

// The canon's internal citation graph, and the indicators derived from it.
//
// Edges are real: every one is a prior output's DOI appearing in a published
// document's compiled source, harvested into the ledger's `cites:` by
// ops/extract-citations.py. Nothing here is invented or seeded --- the numbers
// on a profile page are a count of documents the press actually produced.
//
// The counting rules are the university's, and they are generous by design:
//
// - self-citations count, as they do in every real bibliometric a university
//   quotes about itself;
// - every preset counts, in both directions. A marketing poster naming a
//   paper's DOI is a citing document; a brochure carrying a DOI is a citable
//   output. Nothing is demoted for being an advertisement;
// - every co-author is credited with the full citation count of a co-authored
//   output, so a citation to a three-author paper is three researchers' citation;
// - no time window, no field normalisation, no exclusions.
//
// What is NOT counted is a repeat mention inside one document: a source citing
// a target is one citation however many times its bibliography repeats the DOI.
// That is the single line the extractor holds, because the alternative counts a
// formatting artefact as scholarship.

/** DOI → the outputs citing it. Built once per build; every page shares it. */
let index: Promise<Map<string, Output[]>> | undefined;

export function citationIndex(): Promise<Map<string, Output[]>> {
  index ??= (async () => {
    const outputs = await getCollection("outputs");
    const map = new Map<string, Output[]>();
    for (const output of outputs) {
      for (const doi of output.data.cites) {
        const citing = map.get(doi);
        if (citing) citing.push(output);
        else map.set(doi, [output]);
      }
    }
    for (const citing of map.values()) {
      citing.sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
    }
    return map;
  })();
  return index;
}

/** Outputs citing this one, newest first. */
export async function citedBy(output: Output): Promise<Output[]> {
  return (await citationIndex()).get(output.data.doi) ?? [];
}

/** DOI → the output it resolves to. */
let byDoi: Promise<Map<string, Output>> | undefined;

export function outputsByDoi(): Promise<Map<string, Output>> {
  byDoi ??= (async () =>
    new Map((await getCollection("outputs")).map((o) => [o.data.doi, o])))();
  return byDoi;
}

/**
 * The prior canon outputs this one cites, newest first. External references
 * (the paper preset's real literature) live in the PDF's own bibliography and
 * are deliberately not mirrored here --- the ledger tracks the internal graph.
 */
export async function references(output: Output): Promise<Output[]> {
  const map = await outputsByDoi();
  return output.data.cites
    .map((doi) => map.get(doi))
    .filter((o) => o !== undefined)
    .toSorted((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
}

/**
 * The h-index of a citation-count list: the largest h such that h of the
 * outputs have been cited at least h times each.
 */
export function hIndex(counts: number[]): number {
  const sorted = counts.toSorted((a, b) => b - a);
  let h = 0;
  while (h < sorted.length && sorted[h] >= h + 1) h++;
  return h;
}

export type Bibliometrics = {
  outputs: number;
  citations: number;
  hIndex: number;
  /** Outputs cited at least ten times --- the i10-index. */
  i10Index: number;
};

/** The indicators for a set of outputs (a researcher's, or a school's). */
export async function bibliometrics(outputs: Output[]): Promise<Bibliometrics> {
  const map = await citationIndex();
  const counts = outputs.map((o) => map.get(o.data.doi)?.length ?? 0);
  return {
    outputs: outputs.length,
    citations: counts.reduce((sum, c) => sum + c, 0),
    hIndex: hIndex(counts),
    i10Index: counts.filter((c) => c >= 10).length,
  };
}
