import { createHash } from "node:crypto";
import constants from "./atproto.json";

// The AT-URIs of the University's standard.site records, which
// ops/sync-atproto.py writes and this site advertises (the
// /.well-known/site.standard.publication endpoint and each output page's
// <link rel="site.standard.document">). A document's record key is derived
// from its entry rather than stored, so the two implementations must agree:
// both check themselves against the vectors in atproto.json.

const B32 = "234567abcdefghijklmnopqrstuvwxyz";

/** A TID: 53 bits of microseconds since the epoch, then a 10-bit clock id. */
export const tid = (ms: number, clockId: number): string => {
  let value = ((BigInt(ms) * 1000n) << 10n) | BigInt(clockId);
  let out = "";
  for (let i = 0; i < 13; i++) {
    out = B32[Number(value & 31n)] + out;
    value >>= 5n;
  }
  return out;
};

export const documentRkey = (id: string, publishedAt: Date): string => {
  const digest = createHash("sha256").update(id).digest();
  return tid(publishedAt.getTime(), digest.readUInt16BE(0) >> 6);
};

export const publicationUri = `at://${constants.did}/site.standard.publication/${constants.publicationRkey}`;

export const documentUri = (id: string, publishedAt: Date): string =>
  `at://${constants.did}/site.standard.document/${documentRkey(id, publishedAt)}`;
