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
      llmsTxt: true,
    }),
    sitemap(),
  ],
});
