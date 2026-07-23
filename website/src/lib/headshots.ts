import type { ImageMetadata } from "astro";

// Roster headshots live outside src/, in the repo's canon/headshots/. They fall
// inside Vite's fs-allow list (canon/ and website/ share the repo .git root),
// so import.meta.glob can reach them and astro:assets optimises the result ---
// no copying into public/ required.
//
// This is the ONE place the ../ depth to canon/ is written down. The glob
// pattern must be a static string literal, so it is defined here and nowhere
// else. Basenames equal the roster `id` (verity-marris.jpg → verity-marris).
const headshots = import.meta.glob<{ default: ImageMetadata }>("../../../canon/headshots/*.jpg", {
  eager: true,
});

/** Resolve a roster researcher id to its optimizable headshot, if present. */
export function headshot(id: string): ImageMetadata | undefined {
  const hit = Object.entries(headshots).find(([path]) => path.endsWith(`/${id}.jpg`));
  return hit?.[1].default;
}
