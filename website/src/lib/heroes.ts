import type { ImageMetadata } from "astro";

// Page hero banners, all optimised through astro:assets. Three families, each
// resolved by the entry id (basename === id), mirroring the headshots
// convention. Heroes are landscape (16:9). A missing hero resolves to
// undefined and the layout falls back to a plain heading --- so pages render
// before their art exists, and the publish agent can grow the set over time.
//
// Each glob pattern must be a static string literal, so they all live here.
//
//   - output heroes: website content, under src/assets/heroes/outputs/
//   - person + school heroes: canon-derived (like canon/headshots/), so they
//     sit in canon/ and the publish tick can regenerate them
// Standalone page heroes (index pages etc.), keyed by a stable name:
// src/assets/heroes/<name>.avif. Non-recursive, so it never collides with the
// outputs/ subfamily below.
const pageHeroes = import.meta.glob<{ default: ImageMetadata }>("../assets/heroes/*.avif", {
  eager: true,
});
const outputHeroes = import.meta.glob<{ default: ImageMetadata }>(
  "../assets/heroes/outputs/*.avif",
  { eager: true },
);
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

/** Landscape hero for an output landing / listing card, if present. */
export function outputHero(id: string): ImageMetadata | undefined {
  return resolve(outputHeroes, id);
}

/** Landscape hero for a researcher's profile, generated from their headshot. */
export function personHero(id: string): ImageMetadata | undefined {
  return resolve(personHeroes, id);
}

/** Landscape hero for a school's profile / listing card, if present. */
export function schoolHero(id: string): ImageMetadata | undefined {
  return resolve(schoolHeroes, id);
}
