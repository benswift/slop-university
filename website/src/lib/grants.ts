import { getCollection, type CollectionEntry } from "astro:content";

// Join and formatting helpers over the funding collections: award events live
// in src/content/grants/ (written by the publish tick), the canon schemes they
// instantiate in canon/grants.yml (loaded as grantSchemes). There are no
// per-grant pages --- grants render on people profiles, output records, news
// posts, and the outputs dashboard.

export type Grant = CollectionEntry<"grants">;
export type GrantScheme = CollectionEntry<"grantSchemes">;

/** Awarded grants and prizes, newest first. */
export async function getGrants(): Promise<Grant[]> {
  return (await getCollection("grants")).toSorted(
    (a, b) => b.data.date.valueOf() - a.data.date.valueOf(),
  );
}

/** Grants held by a researcher (matched on name), newest first. */
export async function grantsByGrantee(name: string): Promise<Grant[]> {
  return (await getGrants()).filter((g) => g.data.grantees.includes(name));
}

export async function getSchemes(): Promise<GrantScheme[]> {
  return getCollection("grantSchemes");
}

/** The canon scheme a grant entry references by id, if any. */
export function schemeById(schemes: GrantScheme[], id: string): GrantScheme | undefined {
  return schemes.find((s) => s.id === id);
}

// Values are whole australian dollars. The full form serves records and lists;
// the compact form is for the dashboard's stat tile, where "$1,234,567" would
// overflow the tile column long before the fiction runs out of money.
const aud = new Intl.NumberFormat("en-AU", {
  style: "currency",
  currency: "AUD",
  maximumFractionDigits: 0,
});
const audCompact = new Intl.NumberFormat("en-AU", {
  style: "currency",
  currency: "AUD",
  notation: "compact",
  maximumFractionDigits: 1,
});

export function formatAud(value: number): string {
  return aud.format(value);
}

export function formatAudCompact(value: number): string {
  return audCompact.format(value);
}
