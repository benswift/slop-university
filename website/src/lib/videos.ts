import { PDF_BASE } from "./pdfs";

// Video encodes and their covers live in the PDF bucket beside the PDFs, by
// file name (see the videos collection in content.config.ts).
export const videoUrl = (file: string): string => `${PDF_BASE}/${file}`;
