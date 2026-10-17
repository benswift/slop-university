// The Slop University video engine: one build for every templated video,
// driven by the video's spec.json, a list of beats in a fixed vocabulary.
// A run writes the script and the spec and never animation code, which is what
// lets a video be made unattended (skills/video/SKILL.md is the method, and
// lists the beats and their fields). fetch.py fills assets/ from the spec.
//
// A beat starts on its line (`line`, an index into the script's spoken lines)
// and holds until the next beat starts; `at` puts a cue on a word, as a word
// of the beat's line ("fence"), [line, word] or [line, word, nth]. Images are
// references, resolved to the files fetch.py writes:
//   { output: id }   the output's hero      { thumb: id }    its first page
//   { page: [id, n] } page n of its PDF      { person: id }   a person's hero
//   { headshot: id } a roster headshot      { file: "assets/x.png" }

import * as M from "./motion/motion.js";
import * as B from "./motion/brand.js";
import { lockups, logos } from "./brand/video/brand.js";

export const src = (ref) => {
  if (typeof ref === "string") return ref;
  if (ref.file) return ref.file;
  if (ref.output) return `assets/heroes/${ref.output}.avif`;
  if (ref.person) return `assets/people/${ref.person}.avif`;
  if (ref.thumb) return `assets/thumbs/${ref.thumb}.avif`;
  if (ref.headshot) return `assets/headshots/${ref.headshot}.jpg`;
  if (ref.page) return `assets/pages/${ref.page[0]}-p${ref.page[1]}.png`;
  throw new Error(`no image for ${JSON.stringify(ref)}`);
};

const COVER_AR = 1.414; // an A-series page, portrait
const LEAD = 0.25; // a beat arrives this far ahead of its line
const OUT = 0.45; // and clears this long before the next one arrives

const text = (parent, cls, s, style = {}) => {
  const d = M.el("div", { class: `layer ${cls}`, text: s }, parent);
  Object.assign(d.style, style);
  return d;
};

// a number as a promo says it: 2376 -> "2,376", 5710876 -> "$5.7 million"
export function figure(value, { format = "number", prefix = "", suffix = "" } = {}) {
  let s;
  if (format === "money") {
    s =
      value >= 1e6
        ? `$${(value / 1e6).toFixed(1)} million`
        : `$${Math.round(value).toLocaleString("en-AU")}`;
  } else if (format === "decimal") s = value.toFixed(1);
  else s = Math.round(value).toLocaleString("en-AU");
  return `${prefix}${s}${suffix}`;
}

// Load everything a spec needs before the build (the build itself is sync).
export async function prepare() {
  const root = document.getElementById("stage");
  const theme = root.dataset.theme === "light" ? "light" : "dark";
  const spec = await fetch("spec.json").then((r) => r.json());
  const people = await fetch("assets/people.json")
    .then((r) => (r.ok ? r.json() : {}))
    .catch(() => ({}));
  const refs = new Set();
  const walk = (x) => {
    if (x?.type === "pages") x.outputs.forEach((id) => refs.add(src({ thumb: id })));
    if (x?.type === "people") x.people.forEach((id) => refs.add(src({ headshot: id })));
    if (x && typeof x === "object") {
      if (["output", "person", "thumb", "headshot", "page", "file"].some((k) => k in x))
        refs.add(src(x));
      Object.values(x).forEach(walk);
    }
  };
  walk(spec.beats);
  const images = Object.fromEntries(
    await Promise.all([...refs].map(async (s) => [s, await B.image(s, "")])),
  );
  const assets = {
    theme,
    spec,
    people,
    images,
    logo: await B.image(logos[theme], "Slop University"),
    mark: await B.svgText(lockups[theme].src),
    lockup: lockups[theme],
  };
  return (tl, S, T) => build(tl, S, T, assets);
}

export function build(tl, S, T, A) {
  const P = S.portrait;
  const W = S.W;
  const H = S.H - S.captionH;
  const cx = W / 2;
  const cy = H / 2;
  const scene = S.root.querySelector(".scene");
  const img = (ref) => A.images[src(ref)].cloneNode();
  const beats = A.spec.beats.filter((b) => b.type !== "close");
  const close = A.spec.beats.find((b) => b.type === "close") ?? { type: "close" };
  const lastLine = T.lines.length - 1;

  // when beat k starts and must be gone by; a close on its line ends the last,
  // or its call to action lands on top of it
  const starts = beats.map((b) => Math.max(0, T.start(b.line) - LEAD));
  const closing =
    close.line != null ? Math.max(0, T.start(close.line) - LEAD) : T.end(lastLine) + 0.6;
  const ends = beats.map((_, k) => (k + 1 < beats.length ? starts[k + 1] : closing));
  const cueOf = (b, at, fallback) => {
    if (at == null) return fallback;
    if (typeof at === "number") return at;
    if (typeof at === "string") return T.word(b.line, at);
    return T.word(at[0], at[1], at[2] ?? 1);
  };

  beats.forEach((b, k) => {
    const t0 = starts[k];
    const t1 = ends[k] - OUT;
    const render = BEATS[b.type];
    if (!render) throw new Error(`unknown beat type ${b.type}`);
    const els = render({
      b,
      t0,
      t1,
      tl,
      S,
      T,
      A,
      P,
      W,
      H,
      cx,
      cy,
      scene,
      img,
      cue: (at, f) => cueOf(b, at, f ?? t0),
    });
    if (els?.length) M.vanish(tl, els, t1, { dur: 0.4 });
  });

  // ---- captions: one segment at a time, held across a short pause ----
  const band = M.el("div", { class: "captions" }, S.root);
  const cues = T.lines.flatMap((l) => l.segments);
  cues.forEach((c, n) => {
    const el = M.el("div", { class: "caption", text: c.caption }, band);
    M.set(el, { opacity: 0 });
    const next = cues[n + 1]?.start ?? Infinity;
    tl.set(el, { opacity: 1 }, c.start);
    tl.set(el, { opacity: 0 }, next - c.end < 1.2 ? next : c.end + 0.5);
  });

  // ---- the close: where to find the University, then the lockup ----
  let tLock = T.end(lastLine) + 1.2;
  if (close.cta) {
    const ways = close.cta === true ? CTA : close.cta;
    const step = P ? 230 : 200;
    const t = close.line != null ? T.start(close.line) : T.end(lastLine) + 0.4;
    const found = ways.map(([kind, where, word], k) => {
      const y = cy - ((ways.length - 1) * step) / 2 + k * step;
      const label = text(scene, "kicker", kind, { width: `${W}px`, textAlign: "center" });
      const value = text(scene, "resolver", where, { width: `${W}px`, textAlign: "center" });
      M.set(label, { x: 0, y: y - 50, opacity: 0 });
      M.set(value, { x: 0, y, opacity: 0 });
      const at = word && close.line != null ? T.word(close.line, word) - 0.2 : t + k * 0.5;
      M.appear(tl, [label, value], at, { dur: 0.45 });
      return [label, value];
    });
    const gone = T.end(lastLine) + 2.0;
    M.vanish(tl, found.flat(), gone, { dur: 0.5 });
    tLock = gone + 0.8;
  }
  const end = B.lockup(tl, S.root, S, { mark: A.mark, ...A.lockup, at: tLock }).el;
  tl.to(end, { opacity: 0 }, Number(S.root.dataset.duration) - 1.0, { dur: 0.8 });
}

const CTA = [
  ["Website", "slop.university", "website"],
  ["Bluesky", "@slop.university", "Bluesky"],
  ["Email", "outputs@slop.university", "email"],
];

// ---------------------------------------------------------------- the beats
// Each takes the beat and its window [t0, t1] and returns what to clear at t1.
const BEATS = {
  // the opening: a full-frame image under the scrim, with the title block
  hero({ b, t0, t1, tl, S, A, scene, img, cue }) {
    const bg = B.backdrop(tl, S, { photos: [img(b.image)], at: [Math.max(0.1, t0)], out: t1 });
    const block = B.titleBlock(scene, S, {
      logo: A.logo.cloneNode(),
      title: b.title,
      tagline: b.tagline,
      byline: b.byline,
    });
    M.appear(tl, block.el, Math.max(0.4, t0 + 0.3), { dur: 0.8 });
    M.vanish(tl, block.el, cue(b.clear, t1 - 0.6), { dur: 0.6 });
    return [];
  },

  // a line of display type, its key phrase in gold
  statement({ b, t0, tl, P, W, cy, scene, cue }) {
    const box = text(scene, "statement", "", { width: `${W - (P ? 140 : 360)}px` });
    if (b.kicker) M.el("div", { class: "kicker", text: b.kicker }, box);
    const line = M.el("div", { class: "statement-text" }, box);
    const [pre, post] = b.highlight ? b.text.split(b.highlight) : [b.text, null];
    line.append(pre);
    if (post != null) {
      M.el("span", { class: "gold", text: b.highlight }, line);
      line.append(post);
    }
    M.set(box, { x: P ? 70 : 180, y: cy - box.offsetHeight / 2, opacity: 0 });
    M.appear(tl, box, cue(b.at, t0), { dur: 0.6 });
    return [box];
  },

  // one big number counting up to its value, or two or three side by side
  stat(ctx) {
    return BEATS.stats({ ...ctx, b: { ...ctx.b, items: [ctx.b] } });
  },
  stats({ b, t0, tl, P, W, cy, scene, cue }) {
    const n = b.items.length;
    const colW = P ? W - 120 : Math.min(560, (W - 240) / n);
    const rowH = P ? 330 : 0;
    const els = b.items.map((it, k) => {
      const box = text(scene, "stat", "", { width: `${colW}px` });
      const num = M.el("div", { class: "stat-num", text: figure(it.value, it) }, box);
      M.el("div", { class: "stat-label", text: it.label }, box);
      const x = P ? 60 : (W - n * colW) / 2 + k * colW;
      const y = P ? cy - (n * rowH) / 2 + k * rowH + 40 : cy - 110;
      M.set(box, { x, y, opacity: 0 });
      const at = cue(it.at, t0 + k * 0.6);
      M.appear(tl, box, at, { dur: 0.5 });
      const dur = it.count === false ? 0 : 1.4;
      if (dur) {
        const e = M.ease("out-cubic");
        tl.draw((t) => {
          const p = M.clamp((t - at) / dur, 0, 1);
          num.textContent = figure(it.value * e(p), it);
        });
      }
      return box;
    });
    return els;
  },

  // a page or a figure from the output: `image`, cropped to `crop`
  // ([x, y, w, h] as fractions of the image), then pushed in on each of
  // `focus` ({ at, box: [x, y, w, h] } in the same fractions)
  figure({ b, t0, tl, S, P, W, H, scene, img, cue }) {
    const im = img(b.image);
    const [fx, fy, fw, fh] = b.crop ?? [0, 0, 1, 1];
    const iw = im.naturalWidth * fw;
    const ih = im.naturalHeight * fh;
    const maxW = W - (P ? 120 : 260);
    const maxH = H - (b.label ? 200 : 120);
    const s = Math.min(maxW / iw, maxH / ih);
    const bw = iw * s;
    const bh = ih * s;
    const frame = M.el("div", { class: "layer figure-frame" }, scene);
    Object.assign(frame.style, { width: `${bw}px`, height: `${bh}px` });
    const inner = M.layer(frame, 0, 0);
    inner.appendChild(im);
    Object.assign(im.style, {
      width: `${im.naturalWidth * s}px`,
      height: `${im.naturalHeight * s}px`,
      maxWidth: "none",
    });
    M.set(inner, {
      x: -fx * im.naturalWidth * s,
      y: -fy * im.naturalHeight * s,
      transformOrigin: "0 0",
    });
    const top = (H - bh - (b.label ? 80 : 0)) / 2;
    M.set(frame, { x: (W - bw) / 2, y: top, opacity: 0 });
    M.appear(tl, frame, cue(b.at, t0), { dur: 0.6, scale: 0.97 });
    const els = [frame];
    if (b.label) {
      const label = text(scene, "label", b.label, { width: `${W}px`, textAlign: "center" });
      M.set(label, { x: 0, y: top + bh + 28, opacity: 0 });
      M.appear(tl, label, cue(b.at, t0) + 0.3, { dur: 0.5 });
      els.push(label);
    }
    for (const f of b.focus ?? []) {
      // the focus box, in display pixels of the full image, filling the frame
      const [x, y, w, h] = f.box;
      const z = Math.min(1 / ((w / fw) * 1.08), 1 / ((h / fh) * 1.08), 4);
      const px = (x + w / 2) * im.naturalWidth * s;
      const py = (y + h / 2) * im.naturalHeight * s;
      tl.to(inner, { x: bw / 2 - px * z, y: bh / 2 - py * z, scale: z }, cue(f.at), {
        dur: 0.9,
        ease: "in-out-cubic",
      });
    }
    return els;
  },

  // covers dropping into a grid: `outputs`, a list of output ids
  pages({ b, t0, t1, tl, P, W, H, scene, cue, img }) {
    const ids = b.outputs;
    const cw = b.big ? (P ? 300 : 260) : P ? 150 : 140;
    const ch = cw * COVER_AR;
    const gap = 14;
    const cols = Math.min(ids.length, Math.floor((W - 80 + gap) / (cw + gap)));
    const rows = Math.min(Math.ceil(ids.length / cols), Math.floor((H - 60 + gap) / (ch + gap)));
    const gx = (W - (cols * (cw + gap) - gap)) / 2;
    const gy = (H - (rows * (ch + gap) - gap)) / 2;
    const covers = ids.slice(0, cols * rows).map((id, i) => {
      const c = img({ thumb: id });
      c.classList.add("layer", "page");
      scene.appendChild(c);
      Object.assign(c.style, { width: `${cw}px`, height: `${ch}px` });
      M.set(c, {
        x: gx + (i % cols) * (cw + gap),
        y: gy + Math.floor(i / cols) * (ch + gap),
        opacity: 0,
      });
      return c;
    });
    const a = cue(b.at, t0);
    const z = cue(b.until, Math.min(t1 - 0.5, a + 3));
    const order = covers.map((_, i) => i).sort((p, q) => M.hash(p) - M.hash(q));
    order.forEach((i, k) => {
      const at = a + (z - a) * Math.sqrt(k / covers.length);
      tl.fromTo(covers[i], { opacity: 0, y: "-=24" }, { opacity: 1, y: "+=24" }, at, {
        dur: 0.3,
        ease: "out-quad",
      });
    });
    return covers;
  },

  // the people behind it: headshots with name and title; one person large
  people({ b, t0, tl, P, W, H, cx, cy, scene, cue, img, A }) {
    const ids = b.people;
    const one = ids.length === 1;
    const size = one
      ? P
        ? 520
        : 440
      : P
        ? ids.length <= 2
          ? 380
          : 260
        : Math.min(ids.length <= 3 ? 380 : 300, (W - 200) / ids.length - 40);
    const cols = one ? 1 : P ? Math.min(2, ids.length) : ids.length;
    const rows = Math.ceil(ids.length / cols);
    const cellW = one ? size : P ? (W - 120) / cols : size + 40;
    const cellH = size + (one ? 230 : 150);
    const gx = (W - cols * cellW) / 2;
    const gy = (H - rows * cellH) / 2;
    return ids.map((id, i) => {
      const who = A.people[id] ?? { name: id, title: "" };
      const card = M.layer(scene, 0, 0);
      const face = img({ headshot: id });
      face.classList.add("headshot");
      Object.assign(face.style, { width: `${size}px`, height: `${size}px` });
      card.appendChild(face);
      Object.assign(face.style, {
        position: "absolute",
        left: `${(cellW - size) / 2}px`,
        top: "0px",
      });
      text(card, one ? "person-name big" : "person-name", who.name, {
        width: `${cellW}px`,
        top: `${size + 22}px`,
      });
      text(card, "person-title", one ? `${who.title}\n${who.school}` : who.title, {
        width: `${cellW}px`,
        top: `${size + (one ? 96 : 70)}px`,
      });
      M.set(card, { x: gx + (i % cols) * cellW, y: gy + Math.floor(i / cols) * cellH, opacity: 0 });
      const at = Array.isArray(b.at) && typeof b.at[0] !== "number" ? b.at[i] : b.at;
      M.appear(tl, card, cue(at, t0 + i * 0.35), { dur: 0.5 });
      return card;
    });
  },

  // two to four points, one after another
  cards({ b, t0, tl, P, W, H, scene, cue }) {
    const w = P ? W - 140 : Math.min(1300, W - 300);
    const rows = b.items.map((it) => (it.text ? (P ? 230 : 170) : P ? 160 : 120));
    const x = (W - w) / 2;
    let y = (H - rows.reduce((a, r) => a + r, 0)) / 2;
    return b.items.map((it, k) => {
      const card = text(scene, "card", "", { width: `${w}px` });
      M.el("div", { class: "card-num", text: String(k + 1).padStart(2, "0") }, card);
      const body = M.el("div", { class: "card-body" }, card);
      M.el("div", { class: "card-title", text: it.title }, body);
      if (it.text) M.el("div", { class: "card-text", text: it.text }, body);
      M.set(card, { x, y, opacity: 0 });
      y += rows[k];
      M.appear(tl, card, cue(it.at, t0 + k * 0.8), { dur: 0.5 });
      return card;
    });
  },
};
