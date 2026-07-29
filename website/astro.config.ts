import sitemap from "@astrojs/sitemap";
import { defineConfig } from "astro/config";
import universityTheme from "astro-theme-university";

export default defineConfig({
  site: "https://slop.university",
  // Pages build as directories, so every route URL ends in a slash. Saying so
  // explicitly makes Astro emit matching pagination links (/2/, not /2) ---
  // otherwise each Previous/Next click costs a 301 on GitHub Pages and
  // disagrees with the canonical URL the sitemap advertises.
  trailingSlash: "always",
  integrations: [
    universityTheme({
      name: "Slop University",
      brandCss: "astro-theme-slop/slop.css",
      // Every publish tick adds heroes, thumbnails and headshots to a site
      // deployed as a single Pages artifact against a hard 1 GB ceiling, so
      // bytes are the binding constraint. AVIF halves the image payload; its
      // ~8x encode cost is absorbed by the deploy workflow's transform cache,
      // which only re-encodes what actually changed.
      imageFormat: "avif",
      llmsTxt: true,
    }),
    sitemap(),
  ],
});
