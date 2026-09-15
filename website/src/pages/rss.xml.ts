import rss from "@astrojs/rss";
import type { APIContext } from "astro";
import { getCollection } from "astro:content";
import { siteConfig } from "../site-config";
import { newsPublishedAt, sortNews } from "../lib/chronology";

// The news feed: every press release, newest first. Items link to the
// on-site news post; the feed reads straight, like everything else.
export async function GET(context: APIContext) {
  if (!context.site) throw new Error("astro.config.ts must set `site` for the RSS feed");
  const outputs = new Map((await getCollection("outputs")).map((o) => [o.id, o]));
  const news = sortNews(await getCollection("news"), outputs);
  return rss({
    title: siteConfig.name,
    description: `News from the ${siteConfig.contact?.description ?? siteConfig.name}.`,
    site: context.site,
    items: news.map((entry) => ({
      title: entry.data.title,
      link: `/news/${entry.id}/`,
      pubDate: newsPublishedAt(entry, outputs),
      description: entry.data.description,
    })),
  });
}
