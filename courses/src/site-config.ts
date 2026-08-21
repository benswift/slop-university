import { slopBranding } from "astro-theme-slop";
import { defineSiteConfig } from "astro-theme-university/types";

export const siteConfig = defineSiteConfig({
  ...slopBranding,
  name: "Slop University",
  links: [{ text: "Programs and courses", href: "/" }],
  licence: "CC-BY-4.0",
});
