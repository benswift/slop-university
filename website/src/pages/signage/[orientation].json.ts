import type { APIRoute } from "astro";
import { isOrientation, orientations, signagePlaylist } from "../../lib/signage";

// The signage playlist as JSON, which a running screen fetches before each
// change (see [orientation].astro).
export function getStaticPaths() {
  return orientations.map((orientation) => ({ params: { orientation } }));
}

export const GET: APIRoute = async ({ params }) => {
  const { orientation } = params;
  if (!isOrientation(orientation)) {
    return new Response(`Unknown signage orientation: ${String(orientation)}`, { status: 404 });
  }
  return new Response(JSON.stringify(await signagePlaylist(orientation)), {
    headers: { "Content-Type": "application/json" },
  });
};
