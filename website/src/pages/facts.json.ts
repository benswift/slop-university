import { getCollection } from "astro:content";
import type { APIRoute } from "astro";
import { getSchools, outputsByAuthor, outputsBySchool } from "../lib/canon";
import { newestFirst } from "../lib/chronology";
import { bibliometrics, citationIndex } from "../lib/citations";
import { fullTitle } from "../lib/outputs";
import { academicFte } from "../lib/performance";

// The University's numbers as the site itself counts them: the whole
// institution, each school and each researcher, with their outputs, citations,
// h- and i10-indices and funding. A video run reads it (video/ via
// skills/video/) to pick the metrics a promo leads with, so a number on screen
// is always one the site shows. Built with the site, never written by hand.
export const GET: APIRoute = async () => {
  const outputs = (await getCollection("outputs")).toSorted(newestFirst);
  const grants = await getCollection("grants");
  const cited = await citationIndex();
  const citations = (doi: string) => cited.get(doi)?.length ?? 0;
  const brief = (o: (typeof outputs)[number]) => ({
    id: o.id,
    title: fullTitle(o.data),
    preset: o.data.preset,
    date: o.data.date.toISOString().slice(0, 10),
    citations: citations(o.data.doi),
  });
  const funding = (names: string[]) => {
    const awarded = grants.filter((g) => g.data.grantees.some((n) => names.includes(n)));
    return { grants: awarded.length, funding: awarded.reduce((sum, g) => sum + g.data.value, 0) };
  };
  const topCited = (list: typeof outputs) =>
    list
      .filter((o) => citations(o.data.doi) > 0)
      .toSorted((a, b) => citations(b.data.doi) - citations(a.data.doi))
      .slice(0, 5)
      .map(brief);

  const people = await getCollection("people");
  const researchers = await Promise.all(
    people.map(async (p) => {
      const own = await outputsByAuthor(p.data.name);
      return {
        id: p.id,
        name: p.data.name,
        title: p.data.title,
        school: p.data.school,
        ...(await bibliometrics(own)),
        ...funding([p.data.name]),
        coauthors: new Set(own.flatMap((o) => o.data.authors)).size - (own.length > 0 ? 1 : 0),
        topCited: topCited(own),
        recent: own.slice(0, 5).map(brief),
      };
    }),
  );

  const schools = await Promise.all(
    (await getSchools())
      .filter((s) => s.data.kind === "school")
      .map(async (s) => {
        const own = await outputsBySchool(s.data.name);
        const staff = people.filter((p) => p.data.school === s.data.name);
        return {
          id: s.id,
          name: s.data.name,
          researchers: staff.length,
          ...(await bibliometrics(own)),
          ...funding(staff.map((p) => p.data.name)),
          topCited: topCited(own),
        };
      }),
  );

  const byPreset: Record<string, number> = {};
  for (const o of outputs) byPreset[o.data.preset] = (byPreset[o.data.preset] ?? 0) + 1;
  const total = grants.reduce((sum, g) => sum + g.data.value, 0);

  const university = {
    ...(await bibliometrics(outputs)),
    byPreset,
    researchers: people.length,
    schools: schools.length,
    academicFte: academicFte(),
    outputsPerFte: outputs.length / academicFte(),
    grants: grants.length,
    funding: total,
    first: outputs.at(-1)?.data.date.toISOString().slice(0, 10),
    topCited: topCited(outputs),
    recent: outputs.slice(0, 10).map(brief),
  };

  return new Response(JSON.stringify({ university, schools, researchers }, null, 1), {
    headers: { "Content-Type": "application/json" },
  });
};
