import sitemap from "@astrojs/sitemap";
import { defineConfig } from "astro/config";
import universityTheme from "astro-theme-university";

export default defineConfig({
  site: "https://courses.slop.university",
  output: "static",
  trailingSlash: "always",
  integrations: [
    universityTheme({
      name: "Slop University Courses",
      brandCss: "astro-theme-slop/slop.css",
      imageFormat: "avif",
      llmsTxt: true,
      search: false,
    }),
    sitemap(),
  ],
});
