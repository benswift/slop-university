import type { APIRoute } from "astro";
import { type Orientation, orientations, signagePlaylist } from "../../lib/signage";

// The signage playlist as JSON, which a running screen fetches before each
// change (see [orientation].astro).
export function getStaticPaths() {
  return orientations.map((orientation) => ({ params: { orientation } }));
}

export const GET: APIRoute = async ({ params }) =>
  new Response(JSON.stringify(await signagePlaylist(params.orientation as Orientation)), {
    headers: { "Content-Type": "application/json" },
  });
