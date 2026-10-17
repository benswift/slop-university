import { getCollection } from "astro:content";
import { newestFirst } from "./chronology";
import { fullTitle } from "./outputs";
import { signagePdfUrl } from "./pdfs";
import { videoUrl } from "./videos";
import { thumbLargestUrl } from "./images";

// What an e-signage screen plays: the recent posters in its orientation and
// the videos it shows between them. Built once per deploy; the signage page
// embeds it for its first poster and fetches it again from
// /signage/<orientation>.json before every change, so a long-running screen
// picks up a deploy without reloading.

export type Orientation = "landscape" | "portrait";
export type Poster = { pdf: string; thumb: string; width: number; height: number; title: string };
export type Video = { src: string; title: string };
export type Playlist = { research: Poster[]; marketing: Poster[]; videos: Video[] };

export const orientations: Orientation[] = ["landscape", "portrait"];

export async function signagePlaylist(orientation: Orientation): Promise<Playlist> {
  const isLandscape = orientation === "landscape";

  // Orientation isn't a schema field of its own, but the first-page thumbnail
  // is rendered from the PDF page, so the thumb dims every entry records carry
  // the true orientation.
  const posters = (await getCollection("outputs"))
    .filter(
      (entry) =>
        entry.data.preset === "research-poster" || entry.data.preset === "marketing-poster",
    )
    .filter(({ data: { thumb } }) =>
      isLandscape ? thumb.width >= thumb.height : thumb.height > thumb.width,
    )
    .toSorted(newestFirst);

  const poster = (entry: (typeof posters)[number]): Poster => ({
    pdf: signagePdfUrl(entry.id, entry.data.pdfDark),
    thumb: thumbLargestUrl(entry.id, entry.data.thumb),
    width: entry.data.thumb.width,
    height: entry.data.thumb.height,
    title: fullTitle(entry.data),
  });

  // Signage is research-led: four research slots followed by one ad slot. Keep
  // a bounded recent pool so a screen changes regularly without resurrecting
  // old material from deep in the archive.
  const research = posters.filter((e) => e.data.preset === "research-poster").slice(0, 12);
  const marketing = posters.filter((e) => e.data.preset === "marketing-poster").slice(0, 6);

  const videos = (await getCollection("videos"))
    .toSorted((a, b) => a.id.localeCompare(b.id))
    .map((entry) => ({
      src: videoUrl(entry.data.signage[orientation]),
      title: entry.data.title,
    }));

  return { research: research.map(poster), marketing: marketing.map(poster), videos };
}
