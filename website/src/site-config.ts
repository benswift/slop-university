import { defineSiteConfig } from "astro-theme-university/types";
// The Slop University branding preset — the web mirror of the
// slop-university-brand typst package, extracted so other sites can wear the
// identity. Spread into the site config (and from there into BaseLayout);
// never import astro-theme-anu here.
import { slopBranding } from "astro-theme-slop";

export const siteConfig = defineSiteConfig({
  ...slopBranding,
  name: "Slop University",

  links: [
    { text: "News", href: "/" },
    { text: "People", href: "/people/" },
    { text: "Schools", href: "/schools/" },
    { text: "Outputs", href: "/outputs/" },
    { text: "About", href: "/about/" },
  ],

  // Outputs are CC BY 4.0 — the open-access repository default; reuse
  // requires a human choosing to attribute Slop University.
  licence: "CC-BY-4.0",

  contact: {
    description: "Office of Research Outputs",
    email: "outputs@slop.university",
  },

  // The one out-of-fiction page on the site, plus the news feed.
  legalLinks: [
    { text: "About this project", href: "/colophon/" },
    { text: "RSS", href: "/rss.xml" },
  ],
});
