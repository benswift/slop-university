// Slop University horizontal lockup generator.
//
// The crest (a heater shield containing a steaming bowl) is drawn natively as a
// single gold-stroke `curve` (all subpaths share one stroke, no fills) so the
// whole lockup exports as vector when compiled to SVG -- embedding an external
// SVG via `image()` would rasterise it instead. The wordmark is Public Sans
// "Slop / University" (gold slash); typst's SVG export outlines the glyphs to
// paths, so the result is self-contained with no font dependency at use time.
//
//   typst compile lockup-gen.typ out.svg --input variant=black|white
//
// `build-all.sh` drives this for both variants and runs svgo. See NOTES.md.
#set page(width: auto, height: auto, margin: 0pt, fill: none)
#let variant = sys.inputs.at("variant", default: "black")
#let ink = if variant == "white" { white } else { rgb("#1a1a1a") }
#let gold = rgb("#b97d1c")

// 1 crest unit -> length (crest authored at 2cm tall over an 80x100 unit grid;
// the shield spans x[12,68] so its symmetry axis is at the box centre, u(40)).
#let u(n) = n * 0.02cm
#let stroke-spec = (paint: gold, thickness: u(2.9), cap: "round", join: "round")

#let crest = box(width: u(80), height: u(100), place(top + left, curve(
  stroke: stroke-spec,
  fill: none,
  // shield
  curve.move((u(12), u(12))),
  curve.line((u(68), u(12))),
  curve.line((u(68), u(42))),
  curve.cubic((u(68), u(62)), (u(56), u(78)), (u(40), u(88))),
  curve.cubic((u(24), u(78)), (u(12), u(62)), (u(12), u(42))),
  curve.close(),
  // steam (left, mid, right)
  curve.move((u(32), u(53))),
  curve.cubic((u(35), u(49)), (u(29), u(45)), (u(32), u(40))),
  curve.cubic((u(35), u(35)), (u(30), u(31)), (u(32), u(26))),
  curve.move((u(40), u(53))),
  curve.cubic((u(43), u(49)), (u(37), u(45)), (u(40), u(40))),
  curve.cubic((u(43), u(35)), (u(38), u(31)), (u(40), u(26))),
  curve.move((u(48), u(53))),
  curve.cubic((u(51), u(49)), (u(45), u(45)), (u(48), u(40))),
  curve.cubic((u(51), u(35)), (u(46), u(31)), (u(48), u(26))),
  // bowl body
  curve.move((u(26), u(60))),
  curve.cubic((u(27.5), u(71)), (u(52.5), u(71)), (u(54), u(60))),
  // bowl rim (ellipse approx, cx40 cy60 rx15 ry4)
  curve.move((u(55), u(60))),
  curve.cubic((u(55), u(62.209)), (u(48.285), u(64)), (u(40), u(64))),
  curve.cubic((u(31.715), u(64)), (u(25), u(62.209)), (u(25), u(60))),
  curve.cubic((u(25), u(57.791)), (u(31.715), u(56)), (u(40), u(56))),
  curve.cubic((u(48.285), u(56)), (u(55), u(57.791)), (u(55), u(60))),
  curve.close(),
)))

#set text(font: "Public Sans", fill: ink)
#grid(
  columns: 2,
  align: horizon,
  column-gutter: 0.30cm,
  crest,
  text(weight: "medium", size: 30pt)[Slop #h(1pt)#text(fill: gold)[\/]#h(1pt)
    University],
)
