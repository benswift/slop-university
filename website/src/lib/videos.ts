import { getCollection } from "astro:content";
import { PDF_BASE } from "./pdfs";

// Video encodes and their covers live in the PDF bucket beside the PDFs, by
// file name (see the videos collection in content.config.ts).
export const videoUrl = (file: string): string => `${PDF_BASE}/${file}`;

/** The video about an output or a person, if there is one. */
export async function videoAbout(about: "output" | "person", id: string) {
  const found = (await getCollection("videos")).filter((v) => v.data[about] === id && v.data.web);
  return found.toSorted((a, b) => b.id.localeCompare(a.id))[0]?.data;
}
