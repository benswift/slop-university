// Output PDFs are served from a Tigris (fly.io S3-compatible) bucket fronted by
// pdf.slop.university, not from this site's public/ directory.
//
// They used to ship inside the GitHub Pages artifact, where they were both the
// largest category and the only unbounded one: 203 MB of a 533 MB artifact
// against Pages' hard 1 GB limit, growing ~0.6 MB per publish tick. Being
// committed, they grew .git permanently at the same rate. Moving them off
// removes both at once. `ops/bucket-sync.py` documents the bucket's two
// load-bearing properties (its own robots.txt, and CORS for the signage kiosk).
//
// The key is always the entry id, so nothing about the location is stored per
// entry --- there is exactly one place that knows where a PDF lives, and the
// publish tick cannot write a path that disagrees with it.
const PDF_BASE = "https://pdf.slop.university";

export const pdfUrl = (id: string): string => `${PDF_BASE}/${id}.pdf`;

// Dark-theme sibling, produced only for the poster presets (the e-signage
// screens show white-on-black). Entries flag its existence with `pdfDark: true`;
// older outputs predate it and consumers fall back to `pdfUrl`.
export const pdfDarkUrl = (id: string): string => `${PDF_BASE}/${id}-dark.pdf`;

// The URL the signage kiosk should fetch: the dark render when one exists.
export const signagePdfUrl = (id: string, hasDark: boolean | undefined): string =>
  hasDark ? pdfDarkUrl(id) : pdfUrl(id);
