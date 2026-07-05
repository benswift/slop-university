import type { SiteConfig } from "astro-theme-university/types";
import { defineSiteConfig } from "astro-theme-university/types";
import slopCrest from "./assets/branding/slop-crest.svg";
import slopLogo from "./assets/branding/slop-horizontal-gold-black.svg";
import slopLogoDark from "./assets/branding/slop-horizontal-gold-white.svg";

// The Slop University branding preset — the web mirror of the
// slop-university-brand typst package. Spread into the site config (and from
// there into BaseLayout); never import astro-theme-anu here.
export const slopBranding: Partial<SiteConfig> = {
  logo: slopLogo,
  logoDark: slopLogoDark,
  favicon: slopCrest,
};

export const siteConfig = defineSiteConfig({
  ...slopBranding,
  name: "Slop University",

  links: [
    { text: "News", href: "/" },
    { text: "People", href: "/people/" },
    { text: "Schools", href: "/schools/" },
    { text: "Research outputs", href: "/outputs/" },
    { text: "Research performance", href: "/research-performance/" },
    { text: "About", href: "/about/" },
  ],

  // Outputs are CC BY 4.0 — the open-access repository default; reuse
  // requires a human choosing to attribute Slop University.
  licence: "CC-BY-4.0",

  contact: {
    description: "Office of Research Outputs",
    email: "outputs@slop.university",
  },

  // The one out-of-fiction page on the site.
  legalLinks: [{ text: "About this project", href: "/colophon/" }],
});
