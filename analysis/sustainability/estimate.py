#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Energy and carbon of Slop University's outputs, 4 July to 9 November 2026.

First-pass central estimate for the sustainability video and page. The raw
counts were gathered by one-off scripts, not kept, and their aggregates are in
`data/`: Claude tokens summed once per `message.id` as `ops/run-usage.py` does,
per transcript directory and model (`tokens3.json`) and per day
(`tokens3d.json`); Replicate's prediction list (`repl.log`); ElevenLabs usage
(`el_*.json`); rendered video durations (`mp4.csv`). They are pasted here as
constants; replace them with live reads before the figures are published.

Conversion factors, all estimates:

- Claude: Wh per million tokens from Simon Couch (Jan 2026), back-solved from
  Epoch AI's GPT-4o estimate; cache rates guessed from pricing ratios.
  Anthropic publishes no energy figures.
  https://www.simonpcouch.com/blog/2026-01-20-cc-impact/
  https://epoch.ai/gradient-updates/how-much-energy-does-chatgpt-use
- Images: Replicate `predict_time` on one 700 W accelerator (H100 SXM board
  power). Replicate's history starts 2026-08-11 and the account is shared with
  other projects, so every image-model prediction is counted as ours.
- PUE 1.2 (between hyperscale ~1.1 and the Uptime 2025 average 1.54).
- Grid 384 gCO2e/kWh, the 2025 US power-sector average (Ember).
"""

from collections.abc import Mapping

WH_PER_MTOK = {"inp": 390, "cr": 39, "cc": 490, "out": 1950}

CLAUDE_ALL = {
    "inp": 7_009_812,
    "cr": 40_476_355_055,
    "cc": 1_078_106_125,
    "out": 230_090_730,
}
CLAUDE_PIPELINE = {
    "inp": 1_477_398 + 259_939 + 14_046,
    "cr": 20_173_161_324 + 14_068_675_024 + 1_184_802_191,
    "cc": 389_575_901 + 482_539_713 + 48_796_462,
    "out": 90_735_683 + 93_450_896 + 18_713_308,
}
CLAUDE_THESES = {
    "inp": 14_046,
    "cr": 1_184_802_191,
    "cc": 48_796_462,
    "out": 18_713_308,
}
GROK = {"inp": 44_000_000, "cr": 766_000_000, "cc": 0, "out": 5_460_000}

IMAGE_PREDICT_S = 352_408 + 5_415 + 7_186 + 13_252 + 162
IMAGES = 7_802 + 302 + 434 + 215 + 6
ACCELERATOR_W = 700
LOCAL_KWH = 50  # rendering and builds on weddle, a guess
OTHER_KWH = 10  # TTS, music, hosting, a guess

PUE = 1.2
G_PER_KWH = 384
OUTPUTS = 3_221
THESES = 10
STAFF = 41
DAYS = 128


def kwh(tokens: Mapping[str, float]) -> float:
    return sum(tokens[k] / 1e6 * WH_PER_MTOK[k] for k in WH_PER_MTOK) / 1000


def main() -> None:
    claude, grok = kwh(CLAUDE_ALL), kwh(GROK)
    images = IMAGE_PREDICT_S * ACCELERATOR_W / 3.6e6
    facility = (claude + grok + images + LOCAL_KWH + OTHER_KWH) * PUE
    kg = facility * G_PER_KWH / 1000
    thesis = kwh(CLAUDE_THESES) * PUE / THESES
    upper = (
        sum(
            CLAUDE_ALL[k] / 1e6 * (WH_PER_MTOK["inp"] if k == "cr" else WH_PER_MTOK[k])
            for k in WH_PER_MTOK
        )
        / 1000
    )
    print(
        f"Claude {claude:,.0f} kWh (pipeline {kwh(CLAUDE_PIPELINE):,.0f}), Grok {grok:,.0f}, "
        f"images {images:,.0f} ({images * 1000 / IMAGES:.1f} Wh each)"
    )
    print(f"total {facility:,.0f} kWh, {kg:,.0f} kg CO2e")
    print(f"per output {facility / OUTPUTS:.2f} kWh, {kg / OUTPUTS * 1000:.0f} g")
    print(f"per thesis {thesis:.1f} kWh, {thesis * G_PER_KWH / 1000:.1f} kg")
    print(f"outputs per staff member per year {OUTPUTS / STAFF * 365 / DAYS:.0f}")
    print(f"upper bound, cache reads at the input rate: Claude {upper:,.0f} kWh")


if __name__ == "__main__":
    main()
