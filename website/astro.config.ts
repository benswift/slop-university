import sitemap from "@astrojs/sitemap";
import { defineConfig } from "astro/config";
import universityTheme from "astro-theme-university";

export default defineConfig({
  site: "https://slop.university",
  integrations: [
    universityTheme({
      name: "Slop University",
      defaultLayout: "src/layouts/PageLayout.astro",
      brandCss: "/src/styles/slop.css",
      llmsTxt: true,
    }),
    sitemap(),
  ],
});
