// Welcome to Slop University: the colophon as a video. One build serves both aspects;
// every cue lands on a word of the script (video/scripts/colophon.md) through
// T.word. assets/ is filled by fetch-assets.py: the colophon hero, real output
// covers and the roster's headshots. A stage with data-theme="light" is the
// cream cut (its composition links kit/kit-light.css).

import * as M from "./kit/motion/motion.js";
import * as B from "./kit/motion/brand.js";
import { lockups, logos } from "./kit/brand/video/brand.js";

const THEME = document.getElementById("stage").dataset.theme === "light" ? "light" : "dark";
const DATA = await fetch("assets/outputs.json").then((r) => r.json());
const HERO = await B.image("assets/hero.avif", "Slop University");
const LOGO = await B.image(logos[THEME], "Slop University");
const MARK = await B.svgText(lockups[THEME].src);
const CREST = new URL("../assets/slop-crest.svg", new URL(logos[THEME])).href;
const COVER_AR = 1.414;

const cover = (parent, n, w, cls = "") => {
  const img = M.el(
    "img",
    {
      src: `assets/thumbs/${String(n % DATA.outputs.length).padStart(3, "0")}.avif`,
      class: `layer page ${cls}`.trim(),
    },
    parent,
  );
  Object.assign(img.style, { width: `${w}px`, height: `${w * COVER_AR}px` });
  return img;
};

const text = (parent, cls, s, style = {}) => {
  const d = M.el("div", { class: `layer ${cls}`, text: s }, parent);
  Object.assign(d.style, style);
  return d;
};

// centre a fixed-size box on a point
const centre = (el, x, y, w, h) => M.set(el, { x: x - w / 2, y: y - h / 2 });

export function build(tl, S, T) {
  const P = S.portrait;
  const token = (name) => getComputedStyle(S.root).getPropertyValue(name).trim();
  const C = {
    ground: token("--video-ground"),
    ink: token("--video-text"),
    gold: token("--video-accent"),
  };
  const W = S.W;
  const H = S.H - S.captionH; // the scene
  const cx = W / 2;
  const cy = H / 2;
  const scene = S.root.querySelector(".scene");
  const w = (i, word) => T.word(i, word);

  // ---- 0: the hero and the title block ----
  B.backdrop(tl, S, { photos: [HERO], at: [0.1], out: T.start(1) - 1.2 });
  const hero = B.titleBlock(scene, S, {
    logo: LOGO,
    title: "Welcome to Slop University",
    tagline: "By Ben Swift",
    byline: "slop.university",
  });
  M.appear(tl, hero.el, 0.4, { dur: 0.8 });
  M.vanish(tl, hero.el, w(0, "never"), { dur: 0.6 });

  // ---- 1: a timer, and a cover dropping in on every tick ----
  const cw = P ? 116 : 112;
  const ch = cw * COVER_AR;
  const gap = 12;
  const cols = Math.floor((W - 60 + gap) / (cw + gap));
  const rows = Math.floor((H - 40 + gap) / (ch + gap));
  const gx = (W - (cols * (cw + gap) - gap)) / 2;
  const gy = (H - (rows * (ch + gap) - gap)) / 2;
  const grid = M.layer(scene, 0, 0);
  const covers = [];
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++) {
      const img = cover(grid, covers.length, cw);
      M.set(img, { x: gx + c * (cw + gap), y: gy + r * (ch + gap), opacity: 0 });
      covers.push(img);
    }
  // the ticks quicken: the gap between drops shrinks as the grid fills
  const t0 = w(1, "research");
  const t1 = w(1, "timer");
  const order = covers.map((_, i) => i).sort((a, b) => M.hash(a) - M.hash(b));
  order.forEach((i, k) => {
    const at = t0 + (t1 - t0) * Math.sqrt(k / covers.length);
    tl.fromTo(covers[i], { opacity: 0, y: "-=28" }, { opacity: 1, y: "+=28" }, at, {
      dur: 0.3,
      ease: "out-quad",
    });
  });

  const R = 120;
  const clock = M.svg("svg", {
    class: "layer",
    width: 2 * R + 20,
    height: 2 * R + 20,
    viewBox: `${-R - 10} ${-R - 10} ${2 * R + 20} ${2 * R + 20}`,
  });
  scene.appendChild(clock);
  centre(clock, cx, cy, 2 * R + 20, 2 * R + 20);
  M.svg("circle", { r: R, fill: C.ground, stroke: C.ink, "stroke-width": 3 }, clock);
  for (let k = 0; k < 12; k++) {
    const a = (k * Math.PI) / 6;
    M.svg(
      "line",
      {
        x1: Math.sin(a) * (R - 18),
        y1: -Math.cos(a) * (R - 18),
        x2: Math.sin(a) * (R - 6),
        y2: -Math.cos(a) * (R - 6),
        stroke: C.ink,
        "stroke-width": 3,
      },
      clock,
    );
  }
  const hand = M.svg(
    "line",
    {
      x1: 0,
      y1: 12,
      x2: 0,
      y2: -R + 26,
      stroke: C.gold,
      "stroke-width": 6,
      "stroke-linecap": "square",
    },
    clock,
  );
  M.set(hand, { transformOrigin: "50% 89%" });
  M.svg("circle", { r: 7, fill: C.gold }, clock);
  M.set(clock, { opacity: 0 });
  M.appear(tl, clock, t0 - 0.4, { dur: 0.5, scale: 0.9 });
  tl.sample(hand, t0, t1 - t0, (p) => ({ rotation: 360 * 5 * p * p }), { ease: "linear" });

  const count = text(scene, "count-plate", "", { width: `${P ? 760 : 900}px` });
  M.el("div", { class: "count-num", text: DATA.total.toLocaleString("en-AU") }, count);
  M.el("div", { class: "kicker", text: "outputs published" }, count);
  centre(count, cx, cy, P ? 760 : 900, 230);
  M.set(count, { opacity: 0 });
  M.vanish(tl, clock, t1, { dur: 0.3 });
  M.appear(tl, count, t1 + 0.35, { dur: 0.5, scale: 0.92 });
  M.vanish(tl, count, T.start(2) - 0.4, { dur: 0.4 });
  tl.to(covers, { opacity: 0.12 }, T.start(2) - 0.4, { dur: 0.6, ease: "in-out-quad" });

  // ---- 2: the four proxies ----
  const proxies = M.layer(scene, 0, 0);
  const box = 230; // each proxy's square, before its scale
  const PS = P ? 1.15 : 1.35; // in the row
  const LS = P ? 0.85 : 1.0; // on the loop
  const out = M.layer(proxies);
  cover(out, 7, 140).style.left = `${(box - 140) / 2}px`;
  const crest = M.layer(proxies);
  const crestImg = M.el("img", { src: CREST, alt: "" }, crest);
  Object.assign(crestImg.style, {
    position: "absolute",
    height: "190px",
    left: `${(box - 190 * 0.83) / 2}px`,
    top: "10px",
  });
  const doi = M.layer(proxies);
  const doiBox = M.el("div", { class: "doi-box" }, doi);
  M.el("div", { class: "kicker", text: "DOI" }, doiBox);
  M.el("div", { text: "10.5555/" }, doiBox);
  M.el("div", { text: "slop.7vh3fg" }, doiBox);
  const cite = M.layer(proxies);
  cover(cite, 12, 76).style.top = "50px";
  const citer = cover(cite, 31, 76);
  Object.assign(citer.style, { left: `${box - 76}px`, top: "50px" });
  const arrow = M.svg(
    "svg",
    { width: box, height: box, style: "position:absolute;left:0;top:0;overflow:visible" },
    cite,
  );
  M.svg(
    "path",
    {
      d: `M ${box - 86} ${50 + 54} L 88 ${50 + 54} M 104 ${50 + 42} L 88 ${50 + 54} L 104 ${50 + 66}`,
      fill: "none",
      stroke: C.gold,
      "stroke-width": 4,
    },
    arrow,
  );

  const items = [out, crest, doi, cite];
  const names = ["an output", "a crest", "a DOI", "a citation"];
  const words = ["output", "crest", "DOI", "citation"];
  const labels = items.map((it, i) => {
    const l = text(it, "kicker", names[i], {
      top: `${box + 26}px`,
      width: `${box}px`,
      textAlign: "center",
    });
    return l;
  });
  // a row in landscape, two by two in portrait
  const rowAt = (i) =>
    P
      ? { x: cx + (i % 2 ? 1 : -1) * 250, y: cy + (i < 2 ? -300 : 220) }
      : { x: cx + (i - 1.5) * 430, y: cy - 50 };
  items.forEach((it, i) => {
    const p = rowAt(i);
    M.set(it, { x: p.x - (PS * box) / 2, y: p.y - (PS * box) / 2, scale: PS, opacity: 0 });
    M.appear(tl, it, w(2, words[i]), { dur: 0.45, scale: 0.85 });
  });

  // ---- 3: the four feed each other, with nobody home ----
  const tLoop = w(3, "machinery");
  const LR = P ? 330 : 300;
  const loopAt = (i) => {
    const a = (i * Math.PI) / 2;
    return { x: cx + Math.sin(a) * LR * (P ? 0.9 : 1.25), y: cy - Math.cos(a) * LR };
  };
  tl.to(labels, { opacity: 0 }, tLoop - 0.3, { dur: 0.3 });
  items.forEach((it, i) => {
    const p = loopAt(i);
    tl.to(it, { x: p.x - (LS * box) / 2, y: p.y - (LS * box) / 2, scale: LS }, tLoop, {
      dur: 0.9,
      ease: "in-out-cubic",
    });
  });
  // the loop: an ellipse through the four, drawn on, with a gold bead running round
  const rx = LR * (P ? 0.9 : 1.25);
  const loop = M.svg("svg", { class: "layer", width: W, height: H, viewBox: `0 0 ${W} ${H}` });
  proxies.insertBefore(loop, proxies.firstChild);
  const ring = M.svg(
    "ellipse",
    { cx, cy, rx, ry: LR, fill: "none", stroke: C.gold, "stroke-width": 3 },
    loop,
  );
  M.prepDraw([ring]);
  M.drawOn(tl, [ring], tLoop + 0.6, 1.0, 0, "in-out-cubic");
  const bead = M.svg("circle", { cx: 0, cy: 0, r: 11, fill: C.gold }, loop);
  M.set(bead, { opacity: 0 });
  const tRun = tLoop + 1.6;
  const tEnd = T.end(3) + 0.6;
  tl.set(bead, { opacity: 1 }, tRun);
  tl.sample(
    bead,
    tRun,
    tEnd - tRun,
    (p) => {
      const a = p * 2 * Math.PI * 2.5;
      return { x: cx + Math.sin(a) * rx, y: cy - Math.cos(a) * LR };
    },
    { ease: "linear", step: 0.005 },
  );
  // an empty chair at the centre
  const chair = M.svg("svg", { class: "layer", width: 120, height: 150, viewBox: "0 0 120 150" });
  proxies.appendChild(chair);
  centre(chair, cx, cy - 20, 120, 150);
  const seat = M.svg(
    "path",
    {
      d: "M 25 10 L 25 85 L 95 85 M 25 85 L 25 140 M 95 85 L 95 140 M 25 58 L 95 58",
      fill: "none",
      stroke: C.ink,
      "stroke-width": 5,
      "stroke-linecap": "square",
    },
    chair,
  );
  M.prepDraw([seat]);
  M.drawOn(tl, [seat], w(3, "no"), 0.8);
  const name = M.el("img", { src: logos[THEME], alt: "Slop University", class: "layer" }, proxies);
  name.style.height = "52px";
  M.set(name, { x: cx - (52 * 278.24) / 43.09 / 2, y: cy + 80, opacity: 0 });
  M.appear(tl, name, w(3, "open."), { dur: 0.5 });
  M.vanish(tl, proxies, T.start(4) - 0.6, { dur: 0.5 });

  // ---- 4: the reserved prefix ----
  const doiBig = text(scene, "doi-big", "", { width: `${W}px`, textAlign: "center" });
  const prefix = M.el("span", { text: "10.5555" }, doiBig);
  M.el("span", { text: "/slop.7vh3fg" }, doiBig);
  M.set(doiBig, { x: 0, y: cy - (P ? 160 : 150), opacity: 0 });
  M.appear(tl, doiBig, w(4, "DOIs"), { dur: 0.5 });
  tl.to(prefix, { color: C.gold }, w(4, "reserved"), { dur: 0.4 });
  const reserved = text(scene, "kicker", "reserved for testing", {
    width: `${W}px`,
    textAlign: P ? "center" : "left",
  });
  M.set(reserved, { x: P ? 0 : (W - 1160) / 2 + 6, y: cy - (P ? 40 : 4), opacity: 0 });
  M.appear(tl, reserved, w(4, "test"), { dur: 0.4 });
  const resolver = text(scene, "resolver", "slop.university/doi/", {
    width: `${W}px`,
    textAlign: "center",
  });
  M.set(resolver, { x: 0, y: cy + (P ? 150 : 140), opacity: 0 });
  const down = M.svg("svg", { class: "layer", width: 40, height: 90, viewBox: "0 0 40 90" });
  scene.appendChild(down);
  centre(down, cx, cy + (P ? 95 : 85), 40, 90);
  const shaft = M.svg(
    "path",
    {
      d: "M 20 5 L 20 80 M 8 66 L 20 80 L 32 66",
      fill: "none",
      stroke: C.gold,
      "stroke-width": 4,
    },
    down,
  );
  M.prepDraw([shaft]);
  M.drawOn(tl, [shaft], w(4, "resolve"), 0.5);
  M.appear(tl, resolver, w(4, "only"), { dur: 0.45 });
  M.vanish(tl, [doiBig, reserved, down, resolver], T.start(5) - 0.5, { dur: 0.45 });

  // ---- 5: the researchers, none of whom exists ----
  const hs = 140;
  const hg = 16;
  const hcols = P ? 6 : 10;
  const hrows = Math.ceil(DATA.headshots.length / hcols);
  const hx = (W - (hcols * (hs + hg) - hg)) / 2;
  const hy = (H - (hrows * (hs + hg) - hg)) / 2;
  const heads = DATA.headshots.map((id, i) => {
    const d = M.layer(scene, hx + (i % hcols) * (hs + hg), hy + Math.floor(i / hcols) * (hs + hg));
    const img = M.el("img", { src: `assets/headshots/${id}.jpg`, alt: "", class: "page" }, d);
    Object.assign(img.style, { width: `${hs}px`, height: `${hs}px`, display: "block" });
    M.set(d, { opacity: 0 });
    return d;
  });
  const t5 = w(5, "researchers");
  heads.forEach((d, i) =>
    M.appear(tl, d, t5 + (i * (w(5, "checked") - t5)) / heads.length, { dur: 0.35, y: 16 }),
  );
  const ticks = heads.map((d) => {
    const s = M.svg(
      "svg",
      {
        width: 40,
        height: 40,
        viewBox: "0 0 40 40",
        style: `position:absolute;left:${hs - 46}px;top:${hs - 46}px`,
      },
      d,
    );
    M.svg("circle", { cx: 20, cy: 20, r: 18, fill: C.gold }, s);
    M.svg(
      "path",
      { d: "M 11 21 L 18 28 L 30 13", fill: "none", stroke: C.ground, "stroke-width": 4 },
      s,
    );
    M.set(s, { opacity: 0 });
    return s;
  });
  tl.to(ticks, { opacity: 1 }, w(5, "checked"), {
    dur: 0.2,
    stagger: (w(5, "every") - w(5, "checked")) / ticks.length,
  });

  // ---- 6: one real person, at the top ----
  const t6 = T.start(6);
  const bs = P ? 0.72 : 0.5; // the headshots' scale in the band
  const bcols = P ? 8 : 19;
  const bstep = (hs + hg) * bs;
  const brows = Math.ceil(heads.length / bcols);
  const bx = (W - (bcols * bstep - hg * bs)) / 2;
  const by = H - 40 - brows * bstep;
  tl.to(ticks, { opacity: 0 }, t6, { dur: 0.3 });
  heads.forEach((d, i) =>
    tl.to(
      d,
      { x: bx + (i % bcols) * bstep, y: by + Math.floor(i / bcols) * bstep, scale: bs },
      t6 + 0.2,
      { dur: 0.9, ease: "in-out-cubic" },
    ),
  );
  const vc = text(scene, "vc-box", "", { width: `${P ? 640 : 560}px` });
  M.el("div", { class: "kicker", text: "Vice-Chancellor" }, vc);
  M.el("div", { class: "vc-name", text: "Ben Swift" }, vc);
  M.set(vc, { x: cx - (P ? 320 : 280), y: 50, opacity: 0 });
  M.appear(tl, vc, w(6, "artist"), { dur: 0.5 });
  const wire = M.svg("svg", { class: "layer", width: W, height: H, viewBox: `0 0 ${W} ${H}` });
  scene.insertBefore(wire, vc);
  const stem = M.svg(
    "path",
    {
      d: `M ${cx} 210 L ${cx} ${by - 24} M ${bx} ${by - 24} L ${W - bx} ${by - 24}`,
      fill: "none",
      stroke: C.ink,
      "stroke-width": 2,
    },
    wire,
  );
  M.prepDraw([stem]);
  M.drawOn(tl, [stem], w(6, "Vice-Chancellor."), 0.9);
  // the output streams past the chart, through none of it
  const stream = M.layer(scene, 0, 0);
  const sw = 96;
  const sy = P ? 520 : 300;
  const tS = w(6, "no");
  for (let k = 0; k < 10; k++) {
    const c = cover(stream, 40 + k, sw);
    const yk = sy + (M.hash(k) - 0.5) * (P ? 260 : 120);
    tl.fromTo(
      c,
      { x: -sw - 20, y: yk, opacity: 1 },
      { x: W + 20, y: yk, opacity: 1 },
      tS - 0.4 + k * 0.15,
      { dur: 1.8, ease: "linear", immediate: false },
    );
    M.set(c, { opacity: 0, x: -sw - 20, y: yk });
  }
  M.vanish(tl, [vc, wire, ...heads], T.start(7) - 0.4, { dur: 0.4 });

  // ---- 7: the system ----
  const t7 = T.start(7);
  tl.to(covers, { opacity: 1 }, t7 + 0.1, {
    dur: 0.4,
    stagger: 1.4 / covers.length,
    ease: "out-quad",
  });
  tl.to(covers, { opacity: 0 }, T.end(7) + 0.2, { dur: 0.8, ease: "in-cubic" });

  // ---- 8: where to find the University, one line on each ----
  const ways = [
    ["Website", "slop.university", "website,"],
    ["Bluesky", "@slop.university", "Bluesky,"],
    ["Email", "outputs@slop.university", "email."],
  ];
  const step = P ? 230 : 200;
  const found = ways.map(([kind, where, word], k) => {
    const y = cy - step + k * step;
    const label = text(scene, "kicker", kind, { width: `${W}px`, textAlign: "center" });
    const value = text(scene, "resolver", where, { width: `${W}px`, textAlign: "center" });
    M.set(label, { x: 0, y: y - 50, opacity: 0 });
    M.set(value, { x: 0, y: y, opacity: 0 });
    M.appear(tl, [label, value], w(8, word) - 0.2, { dur: 0.45 });
    return [label, value];
  });
  M.vanish(tl, found.flat(), T.end(8) + 2.0, { dur: 0.5 });

  // ---- captions: one segment at a time, held across a short pause ----
  const band = M.el("div", { class: "captions" }, S.root);
  const cues = T.lines.flatMap((l) => l.segments);
  cues.forEach((cue, n) => {
    const c = M.el("div", { class: "caption", text: cue.caption }, band);
    M.set(c, { opacity: 0 });
    const next = cues[n + 1]?.start ?? Infinity;
    tl.set(c, { opacity: 1 }, cue.start);
    tl.set(c, { opacity: 0 }, next - cue.end < 1.2 ? next : cue.end + 0.5);
  });

  // ---- the lockup ----
  const tLock = T.end(8) + 2.8;
  const end = B.lockup(tl, S.root, S, { mark: MARK, ...lockups[THEME], at: tLock }).el;
  tl.to(end, { opacity: 0 }, Number(S.root.dataset.duration) - 1.0, { dur: 0.8 });
}
