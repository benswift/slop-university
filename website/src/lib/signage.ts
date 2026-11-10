import { getCollection } from "astro:content";
import { newestFirst } from "./chronology";
import { fullTitle } from "./outputs";
import { signagePdfUrl } from "./pdfs";
import { videoUrl } from "./videos";
import { thumbLargestUrl } from "./images";

// What an e-signage screen plays: the recent posters and the videos in its
// orientation, the videos shown between the posters. Built once per deploy; the signage page
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
  // the true orientation. Only posters with a dark render play: the screens
  // are black, and the early light posters predate the screen-native format.
  const posters = (await getCollection("outputs"))
    .filter(
      (entry) =>
        entry.data.preset === "research-poster" || entry.data.preset === "marketing-poster",
    )
    .filter((entry) => entry.data.pdfDark)
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

  // Signage is research-led: four research slots followed by one ad slot. The
  // pools are the whole archive, for variety; the player walks them by slot
  // number, so each publish shifts which poster lands where.
  const research = posters.filter((e) => e.data.preset === "research-poster");
  const marketing = posters.filter((e) => e.data.preset === "marketing-poster");

  const videos = (await getCollection("videos"))
    .toSorted((a, b) => a.id.localeCompare(b.id))
    .flatMap(({ data: { signage, title } }) => {
      const file = signage[orientation];
      return file ? [{ src: videoUrl(file), title }] : [];
    });

  return { research: research.map(poster), marketing: marketing.map(poster), videos };
}
