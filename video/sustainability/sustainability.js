// Lighter by Design: the Slop University sustainability film (HORIZONS, Venice,
// 2026). Landscape only. Every cue lands on a word of the script
// (video/scripts/sustainability.md) through T.word. assets/ is filled by
// fetch-assets.py; the four clips are Veo renders kept there, placed as media
// clips in index.html. The figures are frozen at 9 November 2026 and come from
// analysis/sustainability/ (estimate.py and its data/); the monthly series is
// Claude energy from tokens3d.json against outputs published by month.

import * as M from "./kit/motion/motion.js";
import * as B from "./kit/motion/brand.js";
import * as C from "./kit/motion/canvas.js";
import { lockups, logos } from "./kit/brand/video/brand.js";

const THEME = "light";
const DATA = await fetch("assets/outputs.json").then((r) => r.json());
const LOGO = await B.image(logos[THEME], "Slop University");
const MARK = await B.svgText(lockups[THEME].src);
const AR = 1.414;
// the clips' playable lengths (video.py mix rewrites every data-duration to the video's)
const CLIP_S = { quad: 6, hall: 6 };

// the figures, frozen at 9 November 2026
const FIG = {
  outputs: 3221,
  perStaff: 224,
  go8PerStaff: 1.5,
  tokensB: 41.8, // 40.5 B cache-read + 1.08 B cache-write + 230 M output + 7 M input
  images: 8759,
  mwh: 3.3,
  kgPerOutput: 0.39,
  sectorKg: 16000,
  totalT: 1.27,
  // Claude energy per output (kWh), outputs published, and Claude energy (kWh), by month
  months: [
    ["Jul", 1.175, 485, 570],
    ["Aug", 1.088, 519, 565],
    ["Sep", 0.958, 715, 685],
    ["Oct", 0.514, 1135, 584],
  ],
  filmKwh: 20, // provisional, as in the script
  // TODO(source): one return economy flight Canberra–Venice, t CO2 (ICAO); drawn
  // unlabelled until sourced, so only "more than the University" is shown
  flightT: 2.0,
};

const SOURCES = {
  outputs: "Outputs published 4 July – 9 November 2026 · slop.university/outputs",
  perStaff:
    "3,221 outputs ÷ 41 researchers ÷ 128 days × 365 · Go8 (ANU, Melbourne, Sydney, UNSW, Monash): 75,034 works ÷ 48,777 staff, 2025 (OpenAlex; annual reports)",
  kwh: "3,299 kWh ÷ 3,221 outputs · Claude tokens × Wh per token (Couch 2026) · images: Replicate GPU-seconds × 700 W · PUE 1.2 · a 1.7 L kettle from 20 °C ≈ 0.2 kWh",
  kg: "3,299 kWh × 384 g/kWh (US grid 2025, Ember) ÷ 3,221 outputs · sector: Go8 2025 and LERU 2023–24 emissions ÷ OpenAlex works (members' reports)",
  months: "Claude energy ÷ outputs published, by month: July 1.18 kWh, October 0.51 kWh",
  thesis:
    "Ten theses, 128–169 pages, 1–3 hours each · thesis runs' Claude tokens × Couch 2026 × PUE 1.2 × 384 g/kWh = 12.8 kWh, 4.9 kg",
  phd: "Achten, Almeida & Muys 2013, Ecological Indicators 34, 352–355: one PhD project, 21.5 t CO2e",
  total:
    "3,299 kWh × 384 g/kWh = 1,267 kg CO2e, 4 July – 9 November 2026 · flight: ICAO carbon emissions calculator, return, economy",
  counted:
    "40.5 B cache-read, 1.08 B cache-write, 230 M output and 7 M input tokens · 8,759 Replicate images · analysis/sustainability/estimate.py",
  reread: "Cache reads: 62% of Claude energy, at an assumed 39 Wh per million tokens",
  rebound: "Claude energy by month: July 570 kWh for 485 outputs; October 584 kWh for 1,135",
  film: "85 s of generated video (every trial) × 3.4 MJ per 5 s (an open model; MIT Technology Review 2025) × PUE 1.2 ≈ 19 kWh · this film's tokens ≈ 3 kWh · renders and audio < 1 kWh",
};

const text = (parent, cls, s, style = {}) => {
  const d = M.el("div", { class: `layer ${cls}`, text: s }, parent);
  Object.assign(d.style, style);
  return d;
};
const img = (parent, src, w, h, cls = "page") => {
  const i = M.el("img", { src, alt: "", class: `layer ${cls}` }, parent);
  Object.assign(i.style, { width: `${w}px`, height: `${h}px` });
  return i;
};
const svgBox = (parent, x, y, w, h, vb = `0 0 ${w} ${h}`) => {
  const s = M.svg("svg", { class: "layer", width: w, height: h, viewBox: vb });
  s.style.overflow = "visible";
  parent.appendChild(s);
  M.set(s, { x, y });
  return s;
};
const widthOf = (el) => el.getBoundingClientRect().width;
const fmtInt = (n) => Math.round(n).toLocaleString("en-AU");

export function build(tl, S, T) {
  const root = getComputedStyle(S.root);
  const ink = root.getPropertyValue("--video-text").trim();
  const gold = root.getPropertyValue("--video-accent").trim();
  const ground = root.getPropertyValue("--video-ground").trim();
  const W = S.W;
  const H = S.H - S.captionH; // 890
  const cx = W / 2;
  const scene = S.root.querySelector(".scene");
  const w = (i, word, nth) => T.word(i, word, nth);
  const counter = (el, from, to, t0, dur, f = fmtInt, e = "out-cubic") =>
    tl.draw((t) => {
      el.textContent = f(from + (to - from) * C.phase(t, t0, dur, e));
    });

  // ---- the clips (index.html places them in time; here their opacity) ----
  const clip = (id) => document.getElementById(id);
  const [press, quad, stillQuad, server, hall, stillHall, heroScrim] = [
    "clip-press",
    "clip-quad",
    "still-quad",
    "clip-server",
    "clip-hall",
    "still-hall",
    "hero-scrim",
  ].map(clip);
  // the media clips' times must agree with the voice
  const expect = [
    [quad, w(7, "How") - 0.2],
    [server, w(12, "artwork.") - 0.1],
    [hall, w(18, "never") - 0.1],
  ];
  for (const [el, t] of expect)
    if (Math.abs(Number(el.dataset.start) - t) > 0.25)
      throw new Error(`${el.id} starts at ${el.dataset.start}, the voice wants ${t.toFixed(2)}`);
  M.set([quad, stillQuad, server, hall, stillHall], { opacity: 0 });

  // ---- recurring: the source line, the fine print, the QR code ----
  const source = (s, t0, t1) => {
    const d = text(scene, "source", s);
    M.set(d, { x: 60, y: H - 30 - 54, opacity: 0 });
    tl.to(d, { opacity: 1 }, t0, { dur: 0.4 });
    tl.to(d, { opacity: 0 }, t1, { dur: 0.3 });
    return d;
  };

  const fineLH = 36;
  const fineBottom = H - 52;
  const fines = [];
  const fine = (s, at) => {
    const d = text(scene, "fine", s);
    const x = W - 60 - widthOf(d);
    M.set(d, { x, y: fineBottom, opacity: 0 });
    for (const f of fines) tl.to(f, { y: `-=${fineLH}` }, at, { dur: 0.35, ease: "in-out-quad" });
    M.appear(tl, d, at, { dur: 0.4, y: 12 });
    fines.push(d);
    return d;
  };

  const qrSmall = M.layer(scene, W - 60 - 222, 40, "qr");
  M.el("img", { src: "assets/qr.svg", alt: "" }, qrSmall);
  M.el("div", { class: "qr-label", text: "slop.university/sustainability" }, qrSmall);
  M.set(qrSmall, { opacity: 0 });
  const qrWindows = [
    [w(2, "That's"), w(3, "carbon")],
    [w(7, "How"), w(8, "Each")],
    [w(11, "Since"), w(11, "Venice.") + 1.2],
    [w(13, "We"), w(13, "website.") + 0.8],
    [w(16, "Each"), w(17, "outputs.") + 0.4],
  ];
  for (const [a, b] of qrWindows) {
    tl.to(qrSmall, { opacity: 1 }, a, { dur: 0.5 });
    tl.to(qrSmall, { opacity: 0 }, b, { dur: 0.4 });
  }

  // ---- 0: the press, the title block ----
  M.set(press, { opacity: 1 });
  M.set(heroScrim, { opacity: 1 });
  tl.to([press, heroScrim], { opacity: 0 }, T.start(1) - 0.9, { dur: 0.8, ease: "in-cubic" });
  const hero = B.titleBlock(scene, S, {
    logo: LOGO,
    title: "Lighter by Design",
    tagline: "The Slop University Sustainability Initiative",
    byline: "slop.university/sustainability",
  });
  M.appear(tl, hero.el, 0.4, { dur: 0.8 });
  M.vanish(tl, hero.el, w(0, "lighter"), { dur: 0.6 });

  // ---- 1: the grid, the count, the kinds ----
  const cw = 104;
  const ch = cw * AR;
  const gap = 10;
  const cols = Math.floor((W - 60 + gap) / (cw + gap));
  const rows = Math.floor((H - 40 + gap) / (ch + gap));
  const gx = (W - (cols * (cw + gap) - gap)) / 2;
  const gy = (H - (rows * (ch + gap) - gap)) / 2;
  const grid = M.layer(scene, 0, 0);
  const covers = [];
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++) {
      const n = covers.length % DATA.grid.length;
      const i = img(grid, `assets/thumbs/${String(n).padStart(3, "0")}.avif`, cw, ch);
      M.set(i, { x: gx + c * (cw + gap), y: gy + r * (ch + gap), opacity: 0 });
      covers.push(i);
    }
  const order = covers.map((_, i) => i).sort((a, b) => M.hash(a) - M.hash(b));
  const g0 = w(1, "Since");
  const g1 = w(1, "outputs.");
  order.forEach((i, k) => {
    tl.fromTo(
      covers[i],
      { opacity: 0, y: "-=28" },
      { opacity: 1, y: "+=28" },
      g0 + (g1 - g0) * Math.sqrt(k / covers.length),
      { dur: 0.3, ease: "out-quad" },
    );
  });
  const plate = text(scene, "count-plate", "", { width: "900px" });
  const plateNum = M.el("div", { class: "count-num", text: "0" }, plate);
  M.el("div", { class: "kicker", text: "research outputs since July" }, plate);
  M.set(plate, { x: cx - 450, y: H / 2 - 120, opacity: 0 });
  M.appear(tl, plate, w(1, "our") - 0.2, { dur: 0.5, scale: 0.94 });
  counter(plateNum, 0, FIG.outputs, w(1, "forty-one"), g1 + 0.6 - w(1, "forty-one"));
  M.vanish(tl, plate, w(1, "Papers,") - 0.3, { dur: 0.3 });
  tl.to(covers, { opacity: 0.12 }, w(1, "Papers,") - 0.3, { dur: 0.5 });

  const kindH = 300;
  const kinds = ["paper", "poster", "thesis", "strategy", "film"].map((k) => ({
    k,
    w: kindH / DATA.kinds[k].ratio,
  }));
  const kgap = 44;
  let kx = (W - (kinds.reduce((s, k) => s + k.w, 0) + kgap * (kinds.length - 1))) / 2;
  const kindWords = ["Papers,", "posters,", "theses,", "strategies,", "films."];
  const kindEls = kinds.map((k, i) => {
    const e = img(scene, `assets/kinds/${k.k}.avif`, k.w, kindH);
    M.set(e, { x: kx, y: H / 2 - kindH / 2 - 30, opacity: 0 });
    kx += k.w + kgap;
    M.appear(tl, e, w(1, kindWords[i]), { dur: 0.45, scale: 0.88, y: 30 });
    return e;
  });
  source(SOURCES.outputs, w(1, "our"), T.start(2) - 0.5);
  M.vanish(tl, kindEls, T.start(2) - 0.5, { dur: 0.4 });
  tl.to(covers, { opacity: 0 }, T.start(2) - 0.5, { dur: 0.4 });

  // ---- 2: 224 against 1.5 ----
  const stat = (num, label, x, color, tNum, tLabel) => {
    const d = M.layer(scene, x - 330, 210);
    d.style.width = "660px";
    d.style.textAlign = "center";
    const n = M.el("div", { class: "big-num", text: num }, d);
    n.style.color = color;
    const l = M.el("div", { class: "num-label", text: label }, d);
    M.set([n, l], { opacity: 0 });
    M.appear(tl, n, tNum, { dur: 0.5, scale: 0.9 });
    M.appear(tl, l, tLabel, { dur: 0.45 });
    return d;
  };
  const s1 = stat(
    String(FIG.perStaff),
    "outputs per staff member, per year",
    cx - 400,
    gold,
    w(2, "two"),
    w(2, "staff"),
  );
  const s2 = stat(
    String(FIG.go8PerStaff),
    "at Australia's leading research universities",
    cx + 400,
    ink,
    w(2, "one"),
    w(2, "Australia's"),
  );
  source(SOURCES.perStaff, w(2, "two"), T.start(3) - 0.4);
  M.vanish(tl, [s1, s2], T.start(3) - 0.4, { dur: 0.4 });

  // ---- 3, 4: one output, its meter, five kettles ----
  const one = img(scene, "assets/kinds/paper.avif", 300, 300 * AR);
  M.set(one, { x: 470, y: 90, opacity: 0 });
  M.appear(tl, one, w(3, "Every"), { dur: 0.6, scale: 0.9 });
  const mH = 300 * AR;
  const meter = svgBox(scene, 850, 90, 90, mH);
  const fill = M.svg("rect", { x: 0, y: 0, width: 90, height: mH, fill: gold }, meter);
  M.set(fill, { transformOrigin: "50% 100%", scaleY: 0 });
  M.svg(
    "rect",
    { x: 1.5, y: 1.5, width: 87, height: mH - 3, fill: "none", stroke: ink, "stroke-width": 3 },
    meter,
  );
  M.set(meter, { opacity: 0 });
  M.appear(tl, meter, w(3, "carbon"), { dur: 0.5 });
  const measured = text(scene, "measured", "Measured*");
  M.set(measured, { x: 1000, y: 150, opacity: 0 });
  M.appear(tl, measured, w(3, "measured"), { dur: 0.5 });
  fine("*estimated", w(3, "measured") + 0.15);

  tl.to(fill, { scaleY: 1 }, w(4, "one"), { dur: 1.3, ease: "out-cubic" });
  const kwh = text(scene, "mid-num", "1 kWh", { color: gold });
  M.set(kwh, { x: 1000, y: 300, opacity: 0 });
  M.appear(tl, kwh, w(4, "kilowatt"), { dur: 0.5 });
  fine("*average of all outputs", w(4, "electricity."));
  const kettlePath =
    "M 22 86 L 78 86 L 72 44 Q 50 34 28 44 Z M 28 56 L 8 40 M 34 42 Q 50 8 66 42 M 46 34 L 54 34";
  const kettles = Array.from({ length: 5 }, (_, i) => {
    const s = svgBox(scene, 450 + i * 175, 610, 140, 140, "0 0 100 100");
    const p = M.svg(
      "path",
      {
        d: kettlePath,
        fill: "none",
        stroke: ink,
        "stroke-width": 4,
        "stroke-linejoin": "round",
        "stroke-linecap": "round",
      },
      s,
    );
    M.prepDraw([p]);
    return p;
  });
  M.drawOn(tl, kettles, w(4, "About"), 0.5, (w(4, "kettles.") - w(4, "About")) / 4);
  source(SOURCES.kwh, w(4, "one"), T.start(5) - 0.4);
  M.vanish(
    tl,
    [one, meter, measured, kwh, ...kettles.map((p) => p.ownerSVGElement)],
    T.start(5) - 0.4,
    { dur: 0.4 },
  );

  // ---- 5: 0.4 kg against 16 t, and the pull-back ----
  const base = 700;
  const k0 = 300 / FIG.kgPerOutput;
  const k1 = 560 / FIG.sectorKg;
  const tGrow = w(5, "four");
  const tSec = w(5, "leading");
  const tSecEnd = w(5, "Australia,") + 0.6;
  const zA = w(5, "sixteen");
  const zB = zA + 2.2;
  const zOut = T.start(6) - 0.4;
  const ticks = [
    [1, "1 kg"],
    [10, "10 kg"],
    [100, "100 kg"],
    [1000, "1 t"],
    [10000, "10 t"],
  ];
  const bars = C.canvas(
    tl,
    scene,
    (ctx, t) => {
      const z = C.phase(t, zA, zB - zA, "in-out-quad");
      const k = Math.exp(Math.log(k0) + (Math.log(k1) - Math.log(k0)) * z);
      ctx.font = '400 26px "Public Sans"';
      ctx.textBaseline = "middle";
      for (const [v, lab] of ticks) {
        const y = base - v * k;
        if (y < 30 || y > base - 20) continue;
        ctx.globalAlpha = C.phase(t, zA, 0.4) * 0.8;
        ctx.fillStyle = ink;
        ctx.fillRect(560, y, 760, 1);
        ctx.fillText(lab, 440, y);
      }
      ctx.globalAlpha = 1;
      ctx.fillStyle = ink;
      ctx.fillRect(560, base, 760, 2);
      const grow = C.phase(t, tGrow, 0.8, "out-cubic");
      const ho = FIG.kgPerOutput * k * grow;
      ctx.fillStyle = gold;
      ctx.fillRect(720, base - Math.max(ho, grow > 0 ? 3 : 0), 140, Math.max(ho, grow > 0 ? 3 : 0));
      ctx.font = '300 44px "Public Sans"';
      ctx.textAlign = "center";
      if (grow > 0.5) ctx.fillText("0.4 kg", 790, base - Math.max(ho, 3) - 34);
      const sec = C.phase(t, tSec, tSecEnd - tSec, "in-quad");
      const hs = FIG.sectorKg * sec * k;
      ctx.fillStyle = ink;
      if (sec > 0) ctx.fillRect(1020, Math.max(base - hs, -10), 140, Math.min(hs, base + 10));
      if (sec > 0.98 && base - hs > 70) ctx.fillText("16 t", 1090, base - hs - 34);
      ctx.textAlign = "left";
    },
    { x: 0, y: 0, w: W, h: H },
  );
  M.set(bars.el, { opacity: 0 });
  tl.to(bars.el, { opacity: 1 }, T.start(5), { dur: 0.3 });
  const tags = text(scene, "tag", "per output: ours, and leading universities'");
  M.set(tags, { x: 560, y: base + 24, opacity: 0 });
  M.appear(tl, tags, w(5, "leading"), { dur: 0.4 });
  fine("*US grid, 2025 average", w(5, "carbon"));
  fine("*theirs counts buildings, travel and teaching", w(5, "sixteen") + 0.3);
  source(SOURCES.kg, w(5, "four"), zOut);
  tl.to([bars.el, tags], { opacity: 0 }, zOut, { dur: 0.4 });

  // ---- 6 (and 16): per output, by month ----
  const months = M.layer(scene, 0, 0);
  M.set(months, { opacity: 0 });
  const mBase = 620;
  const mScale = 330 / FIG.months[0][1];
  const mStep = 330;
  const mBarW = 120;
  const mchart = svgBox(months, 0, 0, W, H);
  M.svg("rect", { x: cx - 2 * mStep, y: mBase, width: 4 * mStep, height: 2, fill: ink }, mchart);
  const mBars = FIG.months.map(([mon, kwhPer], i) => {
    const mx = cx + (i - 1.5) * mStep;
    const h = kwhPer * mScale;
    const r = M.svg(
      "rect",
      { x: mx - mBarW / 2, y: mBase - h, width: mBarW, height: h, fill: gold },
      mchart,
    );
    M.set(r, { transformOrigin: "50% 100%", scaleY: 0 });
    const lab = text(months, "tag", mon, { width: "200px", textAlign: "center" });
    M.set(lab, { x: mx - 100, y: mBase + 16 });
    const val = text(months, "tag", `${kwhPer.toFixed(2)} kWh`, {
      width: "240px",
      textAlign: "center",
      color: ink,
    });
    M.set(val, { x: mx - 120, y: mBase - h - 50, opacity: 0 });
    return { r, val, mx, h, i };
  });
  const tM0 = w(6, "Since");
  const tM1 = w(6, "fallen");
  tl.to(months, { opacity: 1 }, T.start(6), { dur: 0.4 });
  mBars.forEach(({ r, val, i }) => {
    const at = tM0 + ((tM1 - tM0) * i) / 3;
    tl.to(r, { scaleY: 1 }, at, { dur: 0.6, ease: "out-cubic" });
    M.appear(tl, val, at + 0.3, { dur: 0.4, y: 10 });
  });
  const perOutput = text(months, "kicker", "energy per output", {
    width: `${W}px`,
    textAlign: "center",
  });
  M.set(perOutput, { x: 0, y: 120, opacity: 0 });
  M.appear(tl, perOutput, T.start(6) + 0.2, { dur: 0.4 });
  fine("*per output, July to October", w(6, "output"));
  source(SOURCES.months, tM0, T.start(7) - 0.4);
  tl.to(months, { opacity: 0 }, T.start(7) - 0.4, { dur: 0.3 });

  // ---- 7: the quad empties ----
  const tQ = Number(quad.dataset.start);
  tl.to(quad, { opacity: 1 }, tQ, { dur: 0.4 });
  tl.set(stillQuad, { opacity: 1 }, tQ + CLIP_S.quad - 0.1);
  tl.to([quad, stillQuad], { opacity: 0 }, T.start(8) - 0.3, { dur: 0.4 });
  // the fine print steps aside while the clip plays
  tl.to([...fines], { opacity: 0 }, tQ - 0.2, { dur: 0.3 });
  tl.to([...fines], { opacity: 1 }, T.start(8) - 0.2, { dur: 0.4 });

  // ---- 8, 9: the theses, and a human PhD ----
  const tw = 96;
  const tx0 = (W - (10 * tw + 9 * 16)) / 2;
  const theses = DATA.theses.map((_, i) => {
    const e = img(scene, `assets/theses/${i}.avif`, tw, tw * AR);
    M.set(e, { x: tx0 + i * (tw + 16), y: 60, opacity: 0 });
    return e;
  });
  tl.to(theses, { opacity: 1 }, w(8, "doctoral"), { dur: 0.4, stagger: 0.08 });
  const pick = theses[3];
  const ours = { x: 400, y: 250, s: 300 / tw };
  tl.to(pick, { x: ours.x, y: ours.y, scale: ours.s }, w(8, "hundred"), {
    dur: 0.9,
    ease: "in-out-cubic",
  });
  tl.to(
    theses.filter((e) => e !== pick),
    { opacity: 0 },
    w(8, "hundred"),
    { dur: 0.5 },
  );
  const pages = text(scene, "tag", "about 140 pages");
  M.set(pages, { x: ours.x, y: ours.y + 300 * AR + 16, opacity: 0 });
  M.appear(tl, pages, w(8, "pages."), { dur: 0.4 });

  const clockAt = (parent, x, y, R) => {
    const s = svgBox(
      parent,
      x - R - 10,
      y - R - 10,
      2 * R + 20,
      2 * R + 20,
      `${-R - 10} ${-R - 10} ${2 * R + 20} ${2 * R + 20}`,
    );
    M.svg("circle", { r: R, fill: ground, stroke: ink, "stroke-width": 3 }, s);
    for (let k = 0; k < 12; k++) {
      const a = (k * Math.PI) / 6;
      M.svg(
        "line",
        {
          x1: Math.sin(a) * (R - 18),
          y1: -Math.cos(a) * (R - 18),
          x2: Math.sin(a) * (R - 6),
          y2: -Math.cos(a) * (R - 6),
          stroke: ink,
          "stroke-width": 3,
        },
        s,
      );
    }
    const hand = (len, width, color) => {
      const l = M.svg(
        "line",
        {
          x1: 0,
          y1: 0,
          x2: 0,
          y2: -len,
          stroke: color,
          "stroke-width": width,
          "stroke-linecap": "square",
        },
        s,
      );
      M.set(l, { transformOrigin: "50% 100%" });
      return l;
    };
    const hour = hand(R * 0.5, 7, ink);
    const minute = hand(R - 26, 5, gold);
    M.svg("circle", { r: 7, fill: gold }, s);
    M.set(s, { opacity: 0 });
    return { el: s, hour, minute };
  };
  const tc = clockAt(scene, 1000, 360, 110);
  M.appear(tl, tc.el, w(8, "Each"), { dur: 0.5, scale: 0.9 });
  const tH0 = w(8, "two");
  const tH1 = T.wordEnd(8, "write,") + 0.4;
  tl.to(tc.minute, { rotation: 720 }, tH0, { dur: tH1 - tH0, ease: "in-out-quad" });
  tl.to(tc.hour, { rotation: 60 }, tH0, { dur: tH1 - tH0, ease: "in-out-quad" });
  const thesisKg = text(scene, "big-num", "4.9 kg", { color: gold });
  M.set(thesisKg, { x: 1180, y: 290, opacity: 0 });
  M.appear(tl, thesisKg, w(8, "five"), { dur: 0.5, scale: 0.9 });
  fine("*unexamined", w(8, "dioxide.") + 0.2);
  source(SOURCES.thesis, w(8, "Each"), T.start(9) - 0.3);

  // a human PhD beside ours, and its bar out of the frame
  const t9 = T.start(9);
  M.vanish(tl, [tc.el, pages], t9 - 0.3, { dur: 0.3 });
  tl.to(thesisKg, { x: 1165, y: 625, scale: 0.4 }, t9, { dur: 0.6, ease: "in-out-cubic" });
  const human = svgBox(scene, 760, ours.y, 300, 300 * AR);
  M.svg("rect", { x: 0, y: 0, width: 300, height: 300 * AR, fill: ink }, human);
  M.svg("rect", { x: 30, y: 60, width: 240, height: 8, fill: ground }, human);
  M.svg("rect", { x: 30, y: 84, width: 180, height: 8, fill: ground }, human);
  M.set(human, { opacity: 0 });
  M.appear(tl, human, w(9, "human"), { dur: 0.5, scale: 0.94 });
  const humanTag = text(scene, "tag", "a human PhD");
  M.set(humanTag, { x: 760, y: ours.y + 300 * AR + 16, opacity: 0 });
  M.appear(tl, humanTag, w(9, "PhD"), { dur: 0.4 });
  const pb = svgBox(scene, 1200, 0, 300, 700);
  M.svg("rect", { x: 0, y: 696, width: 110, height: 4, fill: gold }, pb);
  const theirBar = M.svg("rect", { x: 160, y: -20, width: 110, height: 720, fill: ink }, pb);
  M.svg("rect", { x: -20, y: 700, width: 320, height: 2, fill: ink }, pb);
  M.set(theirBar, { transformOrigin: "50% 100%", scaleY: 0 });
  M.set(pb, { opacity: 0 });
  tl.to(pb, { opacity: 1 }, w(9, "human"), { dur: 0.3 });
  tl.to(theirBar, { scaleY: 1 }, w(9, "twenty-one"), { dur: 1.0, ease: "in-cubic" });
  const phdT = text(scene, "mid-num", "21.5 t");
  M.set(phdT, { x: 1500, y: 120, opacity: 0 });
  M.appear(tl, phdT, w(9, "tonnes,"), { dur: 0.4 });
  const years = text(scene, "tag", "over four years");
  M.set(years, { x: 1500, y: 240, opacity: 0 });
  M.appear(tl, years, w(9, "four"), { dur: 0.4 });
  fine("*one study, 2013", w(9, "PhD") + 0.2);
  source(SOURCES.phd, w(9, "human"), T.start(10) - 0.4);
  M.vanish(tl, [pick, thesisKg, human, humanTag, pb, phdT, years], T.start(10) - 0.4, { dur: 0.4 });

  // ---- 10: the researchers, lit as the hand passes ----
  const hs = 108;
  const hg = 12;
  const hcols = 11;
  const hx = (W - (hcols * (hs + hg) - hg)) / 2;
  const hy = 110;
  const cc = { x: cx, y: hy + (4 * (hs + hg) - hg) / 2 };
  const t10a = w(10, "starts");
  const t10b = T.wordEnd(10, "done.");
  const heads = DATA.headshots.map((id, i) => {
    const x = hx + (i % hcols) * (hs + hg);
    const y = hy + Math.floor(i / hcols) * (hs + hg);
    const e = img(scene, `assets/headshots/${id}.jpg`, hs, hs, "headshot");
    M.set(e, { x, y, opacity: 0 });
    tl.to(e, { opacity: 0.3 }, T.start(10) + 0.02 * i, { dur: 0.4 });
    const a = (Math.atan2(x + hs / 2 - cc.x, -(y + hs / 2 - cc.y)) + 2 * Math.PI) % (2 * Math.PI);
    const at = t10a + ((t10b - t10a) * a) / (2 * Math.PI);
    tl.to(e, { opacity: 1 }, at, { dur: 0.15 });
    tl.to(e, { opacity: 0.3 }, at + 0.7, { dur: 0.6 });
    return e;
  });
  const sweep = svgBox(scene, cc.x, cc.y, 1, 1, "0 0 1 1");
  const sweepHand = M.svg(
    "line",
    { x1: 0, y1: 0, x2: 0, y2: -760, stroke: gold, "stroke-width": 6 },
    sweep,
  );
  M.svg("circle", { r: 10, fill: gold }, sweep);
  M.set(sweepHand, { transformOrigin: "50% 100%" });
  M.set(sweep, { opacity: 0 });
  tl.to(sweep, { opacity: 1 }, t10a - 0.3, { dur: 0.3 });
  tl.to(sweepHand, { rotation: 360 }, t10a, { dur: t10b - t10a, ease: "linear" });
  M.vanish(tl, [...heads, sweep], T.start(11) - 0.4, { dur: 0.4 });

  // ---- 11: the whole University against one flight ----
  const fBase = 640;
  const fScale = 280 / FIG.flightT;
  const fb = svgBox(scene, 140, 0, 400, 700);
  M.svg("rect", { x: 0, y: fBase, width: 360, height: 2, fill: ink }, fb);
  const uniBar = M.svg(
    "rect",
    { x: 30, y: fBase - FIG.totalT * fScale, width: 120, height: FIG.totalT * fScale, fill: gold },
    fb,
  );
  const flightBar = M.svg(
    "rect",
    {
      x: 300,
      y: fBase - FIG.flightT * fScale,
      width: 120,
      height: FIG.flightT * fScale,
      fill: ink,
    },
    fb,
  );
  M.set([uniBar, flightBar], { transformOrigin: "50% 100%", scaleY: 0 });
  M.set(fb, { opacity: 0 });
  tl.to(fb, { opacity: 1 }, T.start(11), { dur: 0.3 });
  tl.to(uniBar, { scaleY: 1 }, w(11, "one"), { dur: 0.8, ease: "out-cubic" });
  tl.to(flightBar, { scaleY: 1 }, w(11, "flight"), { dur: 0.8, ease: "out-cubic" });
  const uniT = text(scene, "mid-num", "1.3 t", { color: gold });
  M.set(uniT, { x: 150, y: fBase - FIG.totalT * fScale - 120, opacity: 0 });
  M.appear(tl, uniT, w(11, "three"), { dur: 0.4 });
  const fTags = [
    ["the University, since July", 150, fBase + 16],
    ["one return flight", 430, fBase + 56],
  ].map(([s, x, y]) => {
    const d = text(scene, "tag", s);
    M.set(d, { x, y, opacity: 0 });
    return d;
  });
  M.appear(tl, fTags[0], w(11, "University"), { dur: 0.4 });
  M.appear(tl, fTags[1], w(11, "flight"), { dur: 0.4 });
  const vce = { x: 820, y: 230 };
  const cbr = { x: 1320, y: 580 };
  const map = svgBox(scene, 0, 0, W, H);
  const arcs = [
    `M ${cbr.x} ${cbr.y} Q ${(cbr.x + vce.x) / 2 + 60} ${vce.y - 160} ${vce.x} ${vce.y}`,
    `M ${vce.x} ${vce.y} Q ${(cbr.x + vce.x) / 2 - 60} ${cbr.y + 120} ${cbr.x} ${cbr.y}`,
  ].map((d) =>
    M.svg(
      "path",
      { d, fill: "none", stroke: ink, "stroke-width": 3, "stroke-dasharray": "0" },
      map,
    ),
  );
  M.prepDraw(arcs);
  for (const p of [vce, cbr]) M.svg("circle", { cx: p.x, cy: p.y, r: 10, fill: gold }, map);
  const places = [
    ["Venice", vce.x - 60, vce.y - 64],
    ["Canberra", cbr.x - 70, cbr.y + 22],
  ].map(([s, x, y]) => {
    const d = text(scene, "tag", s);
    M.set(d, { x, y, opacity: 0 });
    return d;
  });
  M.set(map, { opacity: 0 });
  tl.to(map, { opacity: 1 }, w(11, "Less"), { dur: 0.3 });
  M.appear(tl, places, w(11, "Less"), { dur: 0.4 });
  M.drawOn(tl, arcs, w(11, "return"), 0.8, 0.8, "in-out-cubic");
  fine("*economy class, CO2 only", w(11, "flight") + 0.3);
  source(SOURCES.total, w(11, "one"), T.start(12) - 0.2);
  M.vanish(tl, [fb, uniT, ...fTags, map, ...places], w(12, "real.") - 0.3, { dur: 0.3 });

  // ---- 12: the fine print fills the frame; the server room; the clock ----
  const tReal = w(12, "real.");
  fines.forEach((f, k) => {
    tl.to(f, { x: 260, y: 70 + k * 88, scale: 2.0 }, tReal + 0.05 * k, {
      dur: 1.0,
      ease: "in-out-cubic",
    });
  });
  const tArt = Number(server.dataset.start);
  tl.set(fines, { opacity: 0 }, tArt);
  tl.set(server, { opacity: 1 }, tArt);
  const tTimer = w(12, "timer.");
  tl.set(server, { opacity: 0 }, tTimer);
  const big = clockAt(scene, cx, H / 2, 170);
  tl.set(big.el, { opacity: 1 }, tTimer);
  // a tick a second from "timer" until the clock leaves
  const tClockOut = T.start(15) - 0.4;
  for (let t = tTimer + 0.3, n = 1; t < tClockOut; t += 1, n++)
    tl.to(big.minute, { rotation: n * 6 }, t, { dur: 0.12, ease: "out-back(1.4)" });

  // ---- 13, 14: what was counted, what it came to, what wasn't ----
  const t13 = T.start(13);
  tl.to(big.el, { x: 220 - 180, scale: 0.85 }, t13 - 0.2, { dur: 0.8, ease: "in-out-cubic" });
  const tok = text(scene, "mid-num", "0");
  const tokL = text(scene, "tag", "tokens read and written");
  M.set(tok, { x: 640, y: 70, opacity: 0 });
  M.set(tokL, { x: 644, y: 176, opacity: 0 });
  M.appear(tl, [tok, tokL], w(13, "token"), { dur: 0.4 });
  counter(tok, 0, FIG.tokensB, w(13, "token"), 1.6, (v) => `${v.toFixed(1)} billion`);
  const ims = text(scene, "mid-num", "0");
  const imsL = text(scene, "tag", "images made");
  M.set(ims, { x: 640, y: 240, opacity: 0 });
  M.set(imsL, { x: 644, y: 346, opacity: 0 });
  M.appear(tl, [ims, imsL], w(13, "images"), { dur: 0.4 });
  counter(ims, 0, FIG.images, w(13, "images"), 1.4);
  const arrows = svgBox(scene, 640, 400, 200, 120);
  const arrow = M.svg(
    "path",
    {
      d: "M 80 0 L 80 100 M 60 80 L 80 100 L 100 80",
      fill: "none",
      stroke: gold,
      "stroke-width": 5,
    },
    arrows,
  );
  M.prepDraw([arrow]);
  M.drawOn(tl, [arrow], w(13, "turned"), 0.6);
  const mwh = text(scene, "big-num", `${FIG.mwh} MWh`, { color: gold });
  M.set(mwh, { x: 640, y: 520, opacity: 0 });
  M.appear(tl, mwh, w(13, "energy"), { dur: 0.5, scale: 0.92 });
  source(SOURCES.counted, w(13, "token"), T.start(15) - 0.4);
  const excl = [
    ["*excludes model training", "training"],
    ["*excludes hardware", "chips"],
    ["*excludes water", "water"],
  ].map(([s, word], i) => {
    const d = text(scene, "fine", s, { textAlign: "left" });
    M.set(d, { x: 1340, y: 580 + i * 44, opacity: 0 });
    M.appear(tl, d, w(14, word), { dur: 0.4, y: 10 });
    return d;
  });
  M.vanish(tl, [big.el, tok, tokL, ims, imsL, arrows, mwh, ...excl], tClockOut, { dur: 0.4 });

  // ---- 15: the same text, read again and again ----
  const loop = svgBox(scene, 0, 0, W, H);
  const lc = { x: cx, y: 400 };
  const lr = { x: 560, y: 230 };
  const traces = [0, 1, 2].map((i) => {
    const e = M.svg(
      "ellipse",
      {
        cx: lc.x,
        cy: lc.y,
        rx: lr.x - i * 14,
        ry: lr.y - i * 10,
        fill: "none",
        stroke: gold,
        "stroke-width": 4,
        opacity: 0.45 + 0.25 * i,
      },
      loop,
    );
    return e;
  });
  M.prepDraw(traces);
  M.svg(
    "rect",
    { x: lc.x - lr.x - 110, y: lc.y - 80, width: 220, height: 160, fill: ink },
    loop,
  );
  const modelL = text(scene, "kicker", "model", { color: ground });
  M.set(modelL, { x: lc.x - lr.x - 50, y: lc.y - 18, opacity: 0 });
  const doc = M.layer(scene, 0, 0);
  const docSvg = svgBox(doc, -50, -64, 100, 128);
  M.svg(
    "rect",
    { x: 0, y: 0, width: 100, height: 128, fill: ground, stroke: ink, "stroke-width": 3 },
    docSvg,
  );
  for (let k = 0; k < 6; k++)
    M.svg(
      "rect",
      { x: 14, y: 18 + k * 17, width: k % 3 === 2 ? 46 : 72, height: 6, fill: ink },
      docSvg,
    );
  M.set([loop, doc], { opacity: 0 });
  const t15a = T.start(15) + 0.3;
  const t15b = T.end(15) + 0.6;
  tl.to(loop, { opacity: 1 }, T.start(15), { dur: 0.3 });
  tl.to(modelL, { opacity: 1 }, T.start(15), { dur: 0.3 });
  tl.to(doc, { opacity: 1 }, T.start(15), { dur: 0.3 });
  // three passes, each faster: the angle runs on a curve that steepens
  const loops = 3;
  tl.sample(
    doc,
    t15a,
    t15b - t15a,
    (p) => {
      const a = Math.PI + 2 * Math.PI * loops * p ** 1.6;
      return { x: lc.x + Math.cos(a) * lr.x, y: lc.y + Math.sin(a) * lr.y };
    },
    { ease: "linear", step: 0.004 },
  );
  traces.forEach((e, i) => {
    const p0 = (i / loops) ** (1 / 1.6);
    const p1 = ((i + 1) / loops) ** (1 / 1.6);
    tl.to(e, { strokeDashoffset: 0 }, t15a + (t15b - t15a) * p0, {
      dur: (t15b - t15a) * (p1 - p0),
      ease: "linear",
    });
  });
  source(SOURCES.reread, w(15, "energy"), T.start(16) - 0.4);
  M.vanish(tl, [loop, modelL, doc], T.start(16) - 0.4, { dur: 0.4 });

  // ---- 16: per output down, by month; the outputs widen each bar to its total ----
  const t16 = T.start(16);
  tl.to(months, { opacity: 1 }, t16, { dur: 0.4 });
  const tWide = w(16, "made");
  mBars.forEach(({ r, val, mx, i }) => {
    const nw = ((mBarW * FIG.months[i][2]) / FIG.months[0][2]) * 0.9;
    tl.to(r, { scaleX: nw / mBarW }, tWide, {
      dur: 1.0,
      ease: "in-out-cubic",
    });
    tl.to(val, { opacity: 0 }, tWide - 0.3, { dur: 0.3 });
    const tot = text(months, "tag", `${FIG.months[i][3]} kWh in all`, {
      width: "300px",
      textAlign: "center",
      color: "var(--video-accent-2)",
    });
    M.set(tot, { x: mx - 150, y: mBase + 56, opacity: 0 });
    M.appear(tl, tot, w(16, "twice"), { dur: 0.4, y: 10 });
  });
  const mKick = text(months, "kicker", "outputs per month × energy per output", {
    width: `${W}px`,
    textAlign: "center",
  });
  M.set(mKick, { x: 0, y: 170, opacity: 0 });
  tl.to(perOutput, { opacity: 0 }, tWide - 0.3, { dur: 0.3 });
  M.appear(tl, mKick, tWide, { dur: 0.4 });
  source(SOURCES.rebound, w(16, "use"), T.start(17) - 0.4);
  tl.to(months, { opacity: 0 }, T.start(17) - 0.4, { dur: 0.4 });

  // ---- 17: this film, counted too ----
  const frames = [
    "assets/stills/document-press.jpg",
    "assets/stills/campus-quad.jpg",
    "assets/kinds/paper.avif",
    "assets/stills/server-room.jpg",
    "assets/stills/lecture-hall-empty-dark.jpg",
    "assets/kinds/film.avif",
  ];
  const fw = 200;
  const fh = 112;
  const fx0 = (W - (frames.length * (fw + 14) - 14)) / 2;
  const strip = frames.map((src, i) => {
    const e = img(scene, src, fw, fh);
    e.style.objectFit = "cover";
    M.set(e, { x: fx0 + i * (fw + 14), y: 100, opacity: 0 });
    return e;
  });
  tl.to(strip, { opacity: 1 }, T.start(17), { dur: 0.3, stagger: 0.1 });
  const fmW = frames.length * (fw + 14) - 14;
  const fm = svgBox(scene, fx0, 290, fmW, 60);
  const fmFill = M.svg("rect", { x: 0, y: 0, width: fmW, height: 60, fill: gold }, fm);
  M.svg(
    "rect",
    { x: 1.5, y: 1.5, width: fmW - 3, height: 57, fill: "none", stroke: ink, "stroke-width": 3 },
    fm,
  );
  M.set(fmFill, { transformOrigin: "0 50%", scaleX: 0 });
  M.set(fm, { opacity: 0 });
  tl.to(fm, { opacity: 1 }, w(17, "Making"), { dur: 0.3 });
  tl.to(fmFill, { scaleX: 1 }, w(17, "took"), { dur: 1.4, ease: "out-cubic" });
  const filmK = text(scene, "mid-num", `about ${FIG.filmKwh} kWh`, { color: gold });
  M.set(filmK, { x: fx0, y: 380, opacity: 0 });
  M.appear(tl, filmK, w(17, "twenty"), { dur: 0.4 });
  const fcw = 50;
  const fcs = Array.from({ length: FIG.filmKwh }, (_, i) => {
    const e = img(
      scene,
      `assets/thumbs/${String((i * 7) % DATA.grid.length).padStart(3, "0")}.avif`,
      fcw,
      fcw * AR,
    );
    M.set(e, { x: fx0 + i * (fcw + 8), y: 520, opacity: 0 });
    return e;
  });
  const tC0 = w(17, "As");
  const tC1 = T.wordEnd(17, "outputs.");
  fcs.forEach((e, i) =>
    tl.fromTo(
      e,
      { opacity: 0, y: "-=24" },
      { opacity: 1, y: "+=24" },
      tC0 + ((tC1 - tC0) * i) / fcs.length,
      { dur: 0.25 },
    ),
  );
  source(SOURCES.film, w(17, "Making"), T.start(18) - 0.4);
  M.vanish(tl, [...strip, fm, filmK, ...fcs], T.start(18) - 0.4, { dur: 0.4 });

  // ---- 18: the gold sliver alone; the empty theatre ----
  const sliver = svgBox(scene, cx - 70, 0, 140, H);
  M.svg("rect", { x: -400, y: 640, width: 940, height: 2, fill: ink, opacity: 0.4 }, sliver);
  M.svg("rect", { x: 0, y: 634, width: 140, height: 6, fill: gold }, sliver);
  const sliverT = text(scene, "tag", "0.4 kg per output", {
    width: "400px",
    textAlign: "center",
    color: "var(--video-accent-2)",
  });
  M.set(sliverT, { x: cx - 200, y: 570, opacity: 0 });
  M.set(sliver, { opacity: 0 });
  M.appear(tl, [sliver, sliverT], w(18, "greenest"), { dur: 0.6 });
  const tHall = Number(hall.dataset.start);
  tl.set([sliver, sliverT], { opacity: 0 }, tHall);
  tl.set(hall, { opacity: 1 }, tHall);
  const tHallOut = T.start(19) - 0.2;
  if (tHall + CLIP_S.hall - 0.1 < tHallOut) tl.set(stillHall, { opacity: 1 }, tHall + CLIP_S.hall - 0.1);
  tl.to([hall, stillHall], { opacity: 0 }, T.start(19) - 0.2, { dur: 0.3 });

  // ---- 19: back into the sizzle, still running ----
  const t19 = T.start(19);
  tl.to(covers, { opacity: 1 }, t19, { dur: 0.3, stagger: 1.0 / covers.length });
  const plate2 = text(scene, "count-plate", "", { width: "900px" });
  const plate2Num = M.el("div", { class: "count-num", text: fmtInt(FIG.outputs) }, plate2);
  M.el("div", { class: "kicker", text: "research outputs since July" }, plate2);
  M.set(plate2, { x: cx - 450, y: H / 2 - 120, opacity: 0 });
  M.appear(tl, plate2, t19 + 0.4, { dur: 0.4, scale: 0.94 });
  counter(
    plate2Num,
    FIG.outputs,
    FIG.outputs + 9,
    t19 + 0.6,
    T.start(20) - t19 - 1.2,
    fmtInt,
    "linear",
  );
  tl.to([...covers, plate2], { opacity: 0 }, T.start(20) - 0.5, { dur: 0.5 });

  // ---- 20: the address and its QR code, then the lockup ----
  const t20 = T.start(20);
  const qrBig = M.layer(scene, cx - 520, 140);
  const qrImg = M.el("img", { src: "assets/qr.svg", alt: "" }, qrBig);
  Object.assign(qrImg.style, { display: "block", width: "420px", height: "420px" });
  const url = text(scene, "url", "slop.university/sustainability");
  M.set(url, { x: cx - 40, y: 300, opacity: 0 });
  const urlK = text(scene, "kicker", "the full sustainability report");
  M.set(urlK, { x: cx - 36, y: 250, opacity: 0 });
  M.set(qrBig, { opacity: 0 });
  M.appear(tl, [qrBig, urlK, url], t20, { dur: 0.5 });
  const tLock = T.end(20) + 2.0 + 6.0;
  M.vanish(tl, [qrBig, urlK, url], tLock - 0.6, { dur: 0.5 });

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
  const end = B.lockup(tl, S.root, S, { mark: MARK, ...lockups[THEME], at: tLock }).el;
  tl.to(end, { opacity: 0 }, Number(S.root.dataset.duration) - 1.0, { dur: 0.8 });
}
