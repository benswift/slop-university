import type { ImageMetadata } from "astro";

// Hero banners for the SLOW-GROWING families, optimised through astro:assets
// and resolved by entry id (basename === id), mirroring the headshots
// convention. Heroes are landscape (16:9). A missing hero resolves to
// undefined and the layout falls back to a plain heading --- so pages render
// before their art exists.
//
// The per-tick families (output heroes, news heroes, thumbnails) do NOT live
// here any more: the publish pipeline pre-encodes them into the
// img.slop.university bucket and the site derives their URLs from recorded
// dims --- see src/lib/images.ts.
//
// Each glob pattern must be a static string literal, so they all live here.
//
//   - page heroes (index pages etc.), keyed by a stable name:
//     src/assets/heroes/<name>.avif. Non-recursive, so it never collided with
//     the migrated outputs/ and news/ subdirectories.
//   - person + school heroes: canon-derived (like canon/headshots/), so they
//     sit in canon/ and the publish tick can regenerate them
const pageHeroes = import.meta.glob<{ default: ImageMetadata }>("../assets/heroes/*.avif", {
  eager: true,
});
const personHeroes = import.meta.glob<{ default: ImageMetadata }>(
  "../../../canon/heroes/people/*.avif",
  { eager: true },
);
const schoolHeroes = import.meta.glob<{ default: ImageMetadata }>(
  "../../../canon/heroes/schools/*.avif",
  { eager: true },
);

function resolve(
  glob: Record<string, { default: ImageMetadata }>,
  id: string,
): ImageMetadata | undefined {
  const hit = Object.entries(glob).find(([path]) => path.endsWith(`/${id}.avif`));
  return hit?.[1].default;
}

/** Landscape hero for a standalone page (e.g. an index), keyed by name. */
export function pageHero(name: string): ImageMetadata | undefined {
  return resolve(pageHeroes, name);
}

/** Landscape hero for a researcher's profile, generated from their headshot. */
export function personHero(id: string): ImageMetadata | undefined {
  return resolve(personHeroes, id);
}

/** Landscape hero for a school's profile / listing card, if present. */
export function schoolHero(id: string): ImageMetadata | undefined {
  return resolve(schoolHeroes, id);
}
