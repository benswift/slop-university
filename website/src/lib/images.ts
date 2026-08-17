import type { RemoteImage } from "astro-theme-university";

// Mirrors pdfs.ts: nothing but dimensions is stored per entry — every URL
// derives from the entry id. The rung ladders and the ≤-source-width filter
// are duplicated, deliberately and exactly, in ops/encode-images.py, which
// encoded the objects these URLs point at. Change one, change both. When no
// ladder rung fits (source narrower than the smallest rung), both sides fall
// back to a single rung at the source width.
//
// The hero ladder serves two renderers: Hero (sizes 100vw) and Card (the
// grid's ~24rem columns pick the 800 rung at 2x DPR). Don't "optimise" the
// card widths separately — the rungs a card can pick from are whatever the
// encoder shipped.
const IMG_BASE = "https://img.slop.university";
const HERO_WIDTHS = [800, 1600, 2560];
const THUMB_WIDTHS = [320, 640, 960];

export interface ImageDims {
  width: number;
  height: number;
}

const rungs = (widths: number[], sourceWidth: number): number[] => {
  const fit = widths.filter((w) => w <= sourceWidth);
  return fit.length > 0 ? fit : [sourceWidth];
};

const remote = (prefix: string, id: string, dims: ImageDims, widths: number[]): RemoteImage => {
  const rs = rungs(widths, dims.width);
  const url = (w: number) => `${IMG_BASE}/${prefix}/${id}-${w}.avif`;
  return {
    // src is the largest rung (rungs never returns empty; the ?? only
    // narrows the type); width/height stay the source's — same aspect ratio,
    // and the attrs only exist for layout stability.
    src: url(rs.at(-1) ?? dims.width),
    width: dims.width,
    height: dims.height,
    srcset: rs.map((w) => `${url(w)} ${w}w`).join(", "),
  };
};

export const outputHero = (id: string, dims: ImageDims | undefined): RemoteImage | undefined =>
  dims && remote("heroes/outputs", id, dims, HERO_WIDTHS);

export const newsHero = (id: string, dims: ImageDims | undefined): RemoteImage | undefined =>
  dims && remote("heroes/news", id, dims, HERO_WIDTHS);

export const thumbnail = (id: string, dims: ImageDims): RemoteImage =>
  remote("thumbs", id, dims, THUMB_WIDTHS);

/** Largest thumb rung URL — the signage kiosk's pre-JS first frame. */
export const thumbLargestUrl = (id: string, dims: ImageDims): string => {
  const rs = rungs(THUMB_WIDTHS, dims.width);
  return `${IMG_BASE}/thumbs/${id}-${rs.at(-1) ?? dims.width}.avif`;
};

/** The pre-encoded og card (JPEG, width ≤1200, encoded at publish time).
 *  A RemoteImage so it can go straight into the theme's `socialImage`, which
 *  passes a remote source through untouched --- these are already the exact
 *  recipe the card wants (ops/encode-images.py), so re-encoding is pointless
 *  and the origin has no build-time pipeline to do it with anyway. */
export const ogImage = (kind: "outputs" | "news", id: string, dims: ImageDims): RemoteImage => {
  const width = Math.min(1200, dims.width);
  // round half-up, mirrored in encode-images.py og_dims()
  const height = Math.floor((dims.height * width) / dims.width + 0.5);
  return { src: `${IMG_BASE}/og/${kind}/${id}.jpg`, width, height };
};
