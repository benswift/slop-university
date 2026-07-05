import { getCollection, type CollectionEntry } from "astro:content";

// Cross-reference helpers over the canon-backed collections. People and schools
// are loaded from canon/ (see content.config.ts); these keep the join logic ---
// person → school, school → researchers, entity → outputs --- in one place so
// the pages stay declarative.

export type Person = CollectionEntry<"people">;
export type School = CollectionEntry<"schools">;
export type Output = CollectionEntry<"outputs">;

/** Roster, ordered by explicit displayOrder then name. */
export async function getPeople(): Promise<Person[]> {
  return (await getCollection("people")).toSorted(
    (a, b) =>
      (a.data.displayOrder ?? Number.MAX_SAFE_INTEGER) -
        (b.data.displayOrder ?? Number.MAX_SAFE_INTEGER) ||
      a.data.name.localeCompare(b.data.name),
  );
}

export async function getSchools(): Promise<School[]> {
  return getCollection("schools");
}

/** The id (URL slug) of the top-level school with this full name, if any. */
export function schoolIdByName(schools: School[], name: string): string | undefined {
  return schools.find((s) => s.data.kind === "school" && s.data.name === name)?.id;
}

/** Researchers affiliated to a school (matched on the school's full name). */
export function researchersOf(people: Person[], schoolName: string): Person[] {
  return people.filter((p) => p.data.school === schoolName);
}

/** Published outputs credited to a researcher (matched on name), newest first. */
export async function outputsByAuthor(name: string): Promise<Output[]> {
  return (await getCollection("outputs"))
    .filter((o) => o.data.authors.includes(name))
    .toSorted((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
}

/** Published outputs attributed to a school (by full name), newest first. */
export async function outputsBySchool(name: string): Promise<Output[]> {
  return (await getCollection("outputs"))
    .filter((o) => o.data.school === name)
    .toSorted((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
}
