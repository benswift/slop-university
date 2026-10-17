// A ten-second card for one output: its hero image under the cream scrim with
// the title block over it, then the closing lockup. No voice; output.json is
// the output it shows. The same build serves both aspects.

import * as M from "./kit/motion/motion.js";
import * as B from "./kit/motion/brand.js";
import { lockups, logos } from "./kit/brand/video/brand.js";

const OUTPUT = await fetch("output.json").then((r) => r.json());
const HERO = await B.image("assets/hero.avif", OUTPUT.title);
const LOGO = await B.image(logos.light, "Slop University");
const MARK = await B.svgText(lockups.light.src);

const T_OUT = 6.2;
const T_LOCKUP = 7.4;

export function build(tl, S) {
  const scene = S.root.querySelector(".scene");
  B.backdrop(tl, S, { photos: [HERO], at: [0.1], out: T_OUT });
  const hero = B.titleBlock(scene, S, {
    logo: LOGO,
    title: OUTPUT.title,
    tagline: OUTPUT.subtitle,
    byline: OUTPUT.byline,
  });
  M.appear(tl, hero.el, 0.5, { dur: 0.8 });
  M.vanish(tl, hero.el, T_OUT - 0.2, { dur: 0.6 });
  const end = B.lockup(tl, S.root, S, { mark: MARK, ...lockups.light, at: T_LOCKUP }).el;
  tl.to(end, { opacity: 0 }, Number(S.root.dataset.duration) - 1.0, { dur: 0.8 });
}
