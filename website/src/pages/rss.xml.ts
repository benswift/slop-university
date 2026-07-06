import rss from "@astrojs/rss";
import type { APIContext } from "astro";
import { getCollection } from "astro:content";
import { siteConfig } from "../site-config";

// The news feed: every press release, newest first. Items link to the
// on-site news post; the feed reads straight, like everything else.
export async function GET(context: APIContext) {
  if (!context.site) throw new Error("astro.config.ts must set `site` for the RSS feed");
  const news = (await getCollection("news")).toSorted(
    (a, b) => b.data.date.valueOf() - a.data.date.valueOf(),
  );
  return rss({
    title: siteConfig.name,
    description: `News from the ${siteConfig.contact?.description ?? siteConfig.name}.`,
    site: context.site,
    items: news.map((entry) => ({
      title: entry.data.title,
      link: `/news/${entry.id}/`,
      pubDate: entry.data.date,
      description: entry.data.description,
    })),
  });
}
