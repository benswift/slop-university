import type { APIRoute } from "astro";
import { publicationUri } from "../../lib/atproto";

// standard.site's domain verification: readers fetch this to confirm that the
// site.standard.publication record in the University's repo speaks for this
// domain (src/lib/atproto.ts).
export const GET: APIRoute = () =>
  new Response(publicationUri, { headers: { "Content-Type": "text/plain" } });
