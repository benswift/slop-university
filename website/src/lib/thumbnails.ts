import type { ImageMetadata } from "astro";

// Output thumbnails (the PDF's first page) are optimised through astro:assets,
// so they live under src/ rather than public/. The publish pipeline writes
// each as src/assets/outputs/thumbs/<output-id>.avif (basename === the output
// collection id), mirroring the canon headshots convention.
//
// The glob pattern must be a static string literal, so it lives here and
// nowhere else.
const thumbnails = import.meta.glob<{ default: ImageMetadata }>(
  "../assets/outputs/thumbs/*.avif",
  { eager: true },
);

/** Resolve an output id to its optimisable first-page thumbnail, if present. */
export function thumbnail(id: string): ImageMetadata | undefined {
  const hit = Object.entries(thumbnails).find(([path]) => path.endsWith(`/${id}.avif`));
  return hit?.[1].default;
}
