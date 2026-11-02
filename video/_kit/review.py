#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "numpy", "pyloudnorm", "pyyaml", "scipy", "soundfile", "typer"]
# ///
"""The mechanical review of a templated video: the faults the contact sheets
cannot show, measured, so a run can fail closed on them without a human
listening. skills/video/SKILL.md step 6 runs it after `render`.

    review.py <id>             # every check; writes out/<id>/review.json, exits 1 on a failure
    review.py <id> --offline   # skip the transcript (no ElevenLabs call); never a pass
    review.py --corpus         # every committed video, offline, one line each (calibration)

The checks, and what each was set against (the memory notes on the October
2026 batch, where every one of these was found by ear or eye):

- levels: each segment of assets/mix.wav against the narrator's median
  segment, in LUFS (0.2 s blocks). A researcher's ElevenLabs voice can come
  back 3--28 dB off the narrator, and mix sets one gain for the whole track.
- tails: the end of every segment of assets/voice.wav. Dead air (a run 30 dB
  under the segment's speech that runs to its end), a click or blip after a
  gap, and a sub-120 Hz rumble that a high-pass shows the voice has stopped
  under. Zeroed gaps (the hand fix) are digital silence and pass.
- transcript: ElevenLabs Scribe on assets/voice.wav, compared word by word
  with the captions. Catches mishearings, a trim that ate a final consonant
  ("lapse" heard as "lap"), a supplied article, a dropped stretch. Numbers
  compare as values ("three hundred and twelve" is 312) and roster names are
  wildcards, since Scribe misspells an invented name without the take being
  wrong.
- phrases: the spoken lines and the on-screen text against the burnt phrases
  of skills/publish/comms.md and the stock phrases of skills/video/SKILL.md.
- sources: an explainer's stat values, quotes and spoken numbers (above ten,
  or with a fraction) against its output's PDF text; a promo's stat values
  against website/dist/facts.json when the site is built.
- beats: every beat holds at least three seconds, and every cue lands at
  least a second before its beat clears (a late cue is cleared unseen). The
  arithmetic is beats.js's own (LEAD, OUT, `from`, `at`).
- frames: the drafts at 4 fps, the caption band cropped off; a frame with
  nothing on it while a line plays is a blank.

review.json records each check's findings and the hashes of the files it read,
so the lander can tell a review of these sources from a stale one.
"""

import difflib
import hashlib
import json
import os
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Annotated

import httpx
import numpy as np
import pyloudnorm
import soundfile
import typer
import yaml
from scipy.signal import butter, sosfilt

VIDEO = Path(__file__).resolve().parent.parent
ROOT = VIDEO.parent
OUT = VIDEO / "out"
API = "https://api.elevenlabs.io/v1"
STT_MODEL = "scribe_v2"  # and the cache key, both as video.py has them

# beats.js
LEAD = 0.25
OUT_GAP = 0.45

# thresholds; the docstring says where each came from
LEVEL_FAIL_LU = 3.0
LEVEL_WARN_LU = 2.0
DEAD_AIR_DB = 30.0
DEAD_AIR_WARN_S = 0.3
DEAD_AIR_FAIL_S = 0.5
TAIL_ALLOWANCE_S = 0.05
BLIP_GAP_S = 0.12
BLIP_MAX_S = 0.3
FRICATIVE_HZ = 4000  # above this, sound after a gap is a final "s", not a blip
RUMBLE_S = 0.5
MIN_HOLD_S = 3.0
MIN_HOLD_FAIL_S = 2.5
CUE_MARGIN_S = 1.0
BLANK_STD = 4.0  # grey levels, of the frame above the caption band
BLANK_MIN_S = 1.0  # a changeover clears for ~0.45 s by design (beats.js OUT)
FPS = 4

app = typer.Typer(add_completion=False)


# --- words and numbers ---------------------------------------------------

ONES = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
]
TENS = ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
SMALL = {w: n for n, w in enumerate(ONES)} | {
    w: 20 + 10 * n for n, w in enumerate(TENS)
}
SCALES = {"thousand": 1_000, "million": 1_000_000, "billion": 1_000_000_000}
TOKEN_RE = re.compile(r"\d+(?:\.\d+)?|[a-z]+")


def tokens(text: str) -> list[str]:
    """Words as script and transcript compare: lower case, apostrophes dropped,
    hyphens split, symbols spelt, and every run of number words one value."""
    t = text.lower().replace("’", "'").replace("'", "")
    t = re.sub(r"(?<=\d),(?=\d{3})", "", t)
    t = re.sub(
        r"\$\s*(\d+(?:\.\d+)?)(\s*(?:thousand|million|billion))?", r"\1\2 dollars", t
    )
    t = t.replace("%", " per cent ").replace("percent", "per cent")
    return numbers(TOKEN_RE.findall(t))


def numbers(words: list[str]) -> list[str]:
    """Collapse each run of number words (or a numeral and its scale) into one
    token holding its value: "a hundred and eighty-one thousand" is 181000."""
    out: list[str] = []
    i = 0
    while i < len(words):
        value, j = parse_number(words, i)
        if j > i:
            out.append(fmt(value))
            i = j
        else:
            out.append(words[i])
            i += 1
    return out


def is_numberish(w: str) -> bool:
    return (
        w in SMALL
        or w in SCALES
        or w == "hundred"
        or bool(re.fullmatch(r"\d+(\.\d+)?", w))
    )


def parse_number(w: list[str], i: int) -> tuple[float, int]:
    """The number starting at w[i], and the index after it (i when none)."""
    total, cur, seen, j = 0.0, 0.0, False, i
    while j < len(w):
        x = w[j]
        nxt = w[j + 1] if j + 1 < len(w) else ""
        if x == "a" and not seen and nxt in ("hundred", *SCALES):
            cur, seen, j = 1, True, j + 1
            continue
        # "and" joins only after a hundred or a scale: "three hundred and twelve"
        if x == "and" and seen and nxt in SMALL and cur % 100 == 0 and (cur or total):
            j += 1
            continue
        if re.fullmatch(r"\d+(\.\d+)?", x):
            if seen:
                break
            cur, seen = float(x), True
        elif x in SMALL:
            v = SMALL[x]
            last = cur % 100
            if seen and cur in (19, 20) and v >= 10:
                # a year said in pairs: "twenty twenty-four", "nineteen ninety"
                cur, seen = cur * 100 + v, True
                j += 1
                continue
            if seen and (
                (v >= 20 and last != 0)
                or (v < 20 and last != 0 and (last % 10 != 0 or last < 20 or v >= 10))
            ):
                break
            if seen and cur != int(cur):
                break
            cur, seen = cur + v, True
        elif x == "hundred" and seen:
            cur *= 100
        elif x in SCALES and seen:
            total += cur * SCALES[x]
            cur = 0
        elif x == "point" and seen and nxt in SMALL and SMALL[nxt] < 10:
            digits = ""
            j += 1
            while j < len(w) and w[j] in SMALL and SMALL[w[j]] < 10:
                digits += str(SMALL[w[j]])
                j += 1
            cur += float("0." + digits)
            continue
        else:
            break
        j += 1
    return total + cur, j if seen else i


def fmt(v: float) -> str:
    return str(int(v)) if v == int(v) else f"{v:g}"


SPELLINGS = [
    (r"isation", "ization"),
    (r"is(e|ed|es|ing)$", r"iz\1"),
    (r"ys(e|ed|es|ing)$", r"yz\1"),
    (r"our(s|ed|ing|ite|ites|able)?$", r"or\1"),
    (r"tre(s)?$", r"ter\1"),
    (r"ogue(s)?$", r"og\1"),
    (r"ence$", "ense"),
    (r"ll(ed|ing|er|ers)$", r"l\1"),
    (r"enor(s)?$", r"ener\1"),
]


def us_spelling(w: str) -> str:
    for pat, rep in SPELLINGS:
        w = re.sub(pat, rep, w)
    return w


def same_word(a: str, b: str) -> bool:
    """Equal, or the same word in Australian and US spelling (Scribe writes
    "center" for the script's "centre"). Nothing fuzzier: "ticked" heard as
    "ticket" is a real mishearing."""
    return a == b or us_spelling(a) == us_spelling(b)


# --- inputs --------------------------------------------------------------


def sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def roster_words() -> set[str]:
    """Every word of every roster name, and its possessive."""
    roster = yaml.safe_load((ROOT / "canon" / "roster.yml").read_text())
    words = {t for p in roster["researchers"] for t in tokens(p["name"])}
    return words | {w + "s" for w in words}


def segments(timing: dict) -> list[dict]:
    """Every spoken segment, with its line, speaker, caption and words."""
    return [
        {
            **s,
            "line": n,
            "speaker": line.get("speaker"),
            "words": [
                w for w in line["words"] if s["start"] - 0.01 <= w["start"] < s["end"]
            ],
        }
        for n, line in enumerate(timing["lines"])
        for s in line["segments"]
    ]


def read_mono(path: Path) -> tuple[np.ndarray, int]:
    x, rate = soundfile.read(path, dtype="float32", always_2d=True)
    return x.mean(axis=1), rate


def centroid(x: np.ndarray, rate: int) -> float:
    """Spectral centroid in Hz: a final "s" sits at 6--7 kHz, a breath at 2--3,
    a voiced blip under 1."""
    if len(x) < 64:
        return 0.0
    mag = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    freqs = np.fft.rfftfreq(len(x), 1 / rate)
    return float((mag * freqs).sum() / (mag.sum() + 1e-12))


def frame_db(x: np.ndarray, rate: int) -> np.ndarray:
    hop = rate // 100
    f = x[: len(x) // hop * hop].reshape(-1, hop)
    return 20 * np.log10(np.sqrt(np.mean(f**2, axis=1)) + 1e-9)


# --- the checks ----------------------------------------------------------
#
# Each returns a list of findings: {"level": "fail" | "warn", "at": seconds or
# None, "detail": str}.


def check_levels(proj: Path, timing: dict) -> list[dict]:
    x, rate = read_mono(proj / "assets" / "mix.wav")
    meter = pyloudnorm.Meter(rate, block_size=0.2)
    segs = []
    for s in segments(timing):
        a, b = int(s["start"] * rate), int(s["end"] * rate)
        if b - a < int(0.25 * rate):
            continue
        segs.append((s, float(meter.integrated_loudness(x[a:b]))))
    narrator = [v for s, v in segs if not s["speaker"] and np.isfinite(v)]
    ref = float(np.median(narrator if narrator else [v for _, v in segs]))
    found = []
    for s, v in segs:
        off = v - ref
        if abs(off) >= LEVEL_WARN_LU:
            who = s["speaker"] or "narrator"
            found.append(
                {
                    "level": "fail" if abs(off) >= LEVEL_FAIL_LU else "warn",
                    "at": s["start"],
                    "detail": f"line {s['line']} ({who}) {off:+.1f} LU against the narrator's median"
                    f" ({v:.1f} vs {ref:.1f} LUFS): {s['caption'][:60]!r}",
                }
            )
    return found


def check_tails(proj: Path, timing: dict) -> list[dict]:
    x, rate = read_mono(proj / "assets" / "voice.wav")
    high = sosfilt(butter(4, 120, "highpass", fs=rate, output="sos"), x)
    found = []
    for s in segments(timing):
        a, b = int(s["start"] * rate), int(s["end"] * rate)
        seg = x[a:b]
        if len(seg) < rate // 2:
            continue
        db = frame_db(seg, rate)
        loud = float(np.percentile(db, 95))
        # digital silence is a gap someone zeroed by hand: a pause, not a fault
        zero = db < -120
        quiet = (db < loud - DEAD_AIR_DB) & ~zero
        allow = int(TAIL_ALLOWANCE_S * 100)
        # the trailing quiet run, allowing the trim's fade at the very end and
        # stepping over zeroed frames
        end = len(db) - 1
        while end > 0 and (zero[end] or (not quiet[end] and len(db) - 1 - end < allow)):
            end -= 1
        run = 0
        while end - run >= 0 and quiet[end - run]:
            run += 1
        gap = run / 100
        where = s["start"] + (end - run + 1) / 100
        label = (
            f"line {s['line']} ({s['speaker'] or 'narrator'}), {s['caption'][-40:]!r}"
        )
        if gap >= DEAD_AIR_WARN_S:
            found.append(
                {
                    "level": "fail" if gap >= DEAD_AIR_FAIL_S else "warn",
                    "at": round(where, 2),
                    "detail": f"{gap:.2f} s of dead air ending the segment: {label}",
                }
            )
        # a blip: sound at speech level after a gap, once the last word has
        # begun (a gap before it is only a pause between words)
        last_word = max((w["start"] for w in s["words"]), default=s["start"])
        k0 = max(0, int((last_word - s["start"]) * 100))
        q = (db < loud - DEAD_AIR_DB) | zero
        n = int(BLIP_GAP_S * 100)
        for k in range(k0, len(db) - n):
            if q[k : k + n].all():
                after = db[k + n :]
                tail_audio = seg[(k + n) * (rate // 100) :]
                hz = centroid(tail_audio, rate)
                # a blip is short: more than BLIP_MAX_S of sound is the word going on
                sound = int((after > loud - 20).sum())
                if 3 <= sound <= BLIP_MAX_S * 100 and hz < FRICATIVE_HZ:
                    found.append(
                        {
                            "level": "fail",
                            "at": round(s["start"] + k / 100, 2),
                            "detail": f"a click or blip ({sound * 10} ms, centroid {hz:.0f} Hz) after a"
                            f" {BLIP_GAP_S:.2f}+ s gap in the last word: {label}",
                        }
                    )
                break
        # rumble: the voice has stopped above 120 Hz but the take runs on below it
        hdb = frame_db(high[a:b], rate)
        hq = (hdb < float(np.percentile(hdb, 95)) - DEAD_AIR_DB) | zero
        hrun = 0
        while hrun < len(hq) and hq[len(hq) - 1 - hrun]:
            hrun += 1
        rumble = (
            int((~quiet[len(db) - hrun :] & ~zero[len(db) - hrun :]).sum())
            if hrun
            else 0
        )
        if rumble / 100 >= RUMBLE_S:
            found.append(
                {
                    "level": "fail",
                    "at": round(s["end"] - hrun / 100, 2),
                    "detail": f"{rumble / 100:.2f} s of sub-120 Hz rumble after the last word: {label}",
                }
            )
    return found


def transcribe(audio: Path) -> list[dict]:
    """Scribe's words for audio, cached where video.py caches its transcripts."""
    key = hashlib.sha256(audio.read_bytes() + STT_MODEL.encode()).hexdigest()[:16]
    cached = OUT / "_stt-cache" / f"{key}.json"
    if not cached.is_file():
        with audio.open("rb") as f:
            r = httpx.post(
                f"{API}/speech-to-text",
                headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
                data={
                    "model_id": STT_MODEL,
                    "language_code": "en",
                    "timestamps_granularity": "word",
                    "tag_audio_events": "false",
                },
                files={"file": (audio.name, f)},
                timeout=600,
            )
        r.raise_for_status()
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(r.json()))
    return [w for w in json.loads(cached.read_text())["words"] if w["type"] == "word"]


def compare(
    script: list[tuple[str, int]], heard: list[tuple[str, float]], names: set[str]
) -> list[dict]:
    """Where the transcript departs from the script, as findings."""
    a = [t for t, _ in script]
    b = [t for t, _ in heard]
    found = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(
        None, a, b, autojunk=False
    ).get_opcodes():
        if op == "equal":
            continue
        said, got = a[i1:i2], b[j1:j2]
        if "".join(said) == "".join(got):
            continue  # "per cent" and "percent", "C M I" and "CMI"
        if op == "replace" and len(said) == len(got) and all(map(same_word, said, got)):
            continue
        if said and all(t in names for t in said) and len(got) <= len(said) + 2:
            continue  # an invented name, spelt Scribe's way
        line = script[min(i1, len(script) - 1)][1]
        at = heard[min(j1, len(heard) - 1)][1] if heard else None
        ctx = " ".join(a[max(0, i1 - 3) : i2 + 3])
        found.append(
            {
                "level": "fail",
                "at": at,
                "detail": f"line {line}: script {' '.join(said) or '(nothing)'!r}, heard "
                f"{' '.join(got) or '(nothing)'!r}, in {ctx!r}",
            }
        )
    return found


def check_transcript(proj: Path, timing: dict) -> list[dict]:
    script = [
        (t, n)
        for n, line in enumerate(timing["lines"])
        for t in tokens(line["caption"])
    ]
    words = transcribe(proj / "assets" / "voice.wav")
    # tokenised as one text, so a number Scribe splits across words still collapses
    heard: list[tuple[str, float]] = []
    for w in words:
        heard += [(t, w["start"]) for t in TOKEN_RE.findall(w["text"].lower())]
    collapsed = tokens(" ".join(w["text"] for w in words))
    starts = [s for _, s in heard] or [0.0]
    heard = [(t, starts[min(k, len(starts) - 1)]) for k, t in enumerate(collapsed)]
    return compare(script, heard, roster_words())


def burnt_phrases() -> list[tuple[str, re.Pattern]]:
    """The burnt list of comms.md and the stock phrases of the video skill, as
    patterns ("…" matches any short run of words)."""
    comms = (ROOT / "skills" / "publish" / "comms.md").read_text()
    block = comms.split("Phrases burnt by past overuse", 1)[1]
    block = block.split("\n\n", 2)[1]
    found = re.findall(r'^- "([^"]+)"', block, flags=re.MULTILINE)
    skill = (ROOT / "skills" / "video" / "SKILL.md").read_text()
    stock = re.search(r"No stock phrases \((.*?)\)", skill, flags=re.DOTALL)
    found += re.findall(r'"([^"]+)"', stock.group(1)) if stock else []
    out = []
    for p in found:
        parts = [re.escape(x.strip()) for x in re.split(r"…|\.\.\.", p) if x.strip()]
        pat = r"\b" + r"\b.{0,80}?\b".join(parts)
        out.append((p, re.compile(pat.replace(r"\ ", r"\s+"), re.IGNORECASE)))
    return out


def visible_text(spec: dict) -> list[tuple[str, str]]:
    """Every string a beat puts on screen, with where it came from."""
    out = []
    for k, b in enumerate(spec.get("beats", [])):
        for key in ("text", "title", "tagline", "kicker", "label"):
            if isinstance(b.get(key), str):
                out.append((f"beat {k} {key}", b[key]))
        for it in b.get("items", []) or []:
            for key in ("title", "text", "label"):
                if isinstance(it.get(key), str):
                    out.append((f"beat {k} item {key}", it[key]))
    return out


def check_phrases(proj: Path, timing: dict, spec: dict) -> list[dict]:
    texts = [(f"line {n}", line["caption"]) for n, line in enumerate(timing["lines"])]
    texts += visible_text(spec)
    found = []
    for where, text in texts:
        for phrase, pat in burnt_phrases():
            if pat.search(text):
                found.append(
                    {
                        "level": "fail",
                        "at": None,
                        "detail": f"{where} uses the burnt phrase {phrase!r}: {text[:80]!r}",
                    }
                )
    return found


def pdf_text(path: Path) -> str:
    """The PDF's text in reading order (-layout interleaves columns), with
    ligatures unfolded and soft hyphens, and the line breaks after them, gone."""
    t = subprocess.run(
        ["pdftotext", str(path), "-"], capture_output=True, text=True, check=True
    ).stdout
    t = unicodedata.normalize("NFKC", t)
    return re.sub(r"\u00ad\s*", "", t)


def flat(text: str) -> str:
    """Text for verbatim matching: line-break hyphens joined, quotes and dashes
    unified, punctuation and spacing gone."""
    t = unicodedata.normalize("NFKC", text)
    t = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", t)
    t = t.replace("’", "'").replace("‘", "'")
    return " ".join(re.findall(r"[a-z0-9]+", t.lower().replace("'", "")))


def stat_values(spec: dict) -> list[tuple[int, float]]:
    out = []
    for k, b in enumerate(spec.get("beats", [])):
        kind = b.get("type")
        items = [b] if kind == "stat" else b.get("items", []) if kind == "stats" else []
        for it in items:
            if "value" in it:
                shown = f"{it.get('prefix', '')}{it['value']}".replace(",", "")
                num = re.search(r"\d+(?:\.\d+)?", shown)
                out.append((k, float(num.group()) if num else float(it["value"])))
    return out


def number_set(text: str) -> set[float]:
    return {float(t) for t in tokens(text) if re.fullmatch(r"\d+(\.\d+)?", t)}


def sourced(v: float, known: set[float]) -> bool:
    """Whether v is a number the source has, as given or rounded: a script says
    "a hundred and fifty-five litres" of a table's 155.3, and "almost twenty-two
    thousand" or "more than two hundred and twelve thousand" of 21,946 and
    212,406 (a round figure, either way, to its own last non-zero digit)."""
    place = 1
    if v == int(v) and v >= 100:
        while v % (place * 10) == 0:
            place *= 10

    def near(x: float) -> bool:
        if abs(x - v) < 1e-9 or round(x) == v or round(x, 1) == v or round(x, 2) == v:
            return True
        return place > 1 and (x // place) * place <= v <= (x // place + 1) * place

    return any(near(x) for x in known)


def own_words(beat: dict) -> bool:
    """A quote over a researcher's hero is them speaking, in their own words;
    any other quote is the source's, and must be its words exactly."""
    image = beat.get("image")
    return isinstance(image, dict) and "person" in image


def check_sources(proj: Path, timing: dict, spec: dict) -> list[dict]:
    def fail(detail: str, at: float | None = None) -> dict:
        return {"level": "fail", "at": at, "detail": detail}

    if spec.get("kind") == "promo":
        facts = ROOT / "website" / "dist" / "facts.json"
        if not facts.is_file():
            return [
                fail(
                    "a promo's numbers come from website/dist/facts.json: build the site first"
                )
            ]
        known = {float(v) for v in re.findall(r"\d+(?:\.\d+)?", facts.read_text())}
        return [
            fail(f"beat {k}'s stat {fmt(v)} is not in facts.json")
            for k, v in stat_values(spec)
            if not sourced(v, known)
        ]

    oid = spec.get("output")
    pdf = proj / "assets" / "pdf" / f"{oid}.pdf"
    if not oid or not pdf.is_file():
        return [
            fail(f"no source PDF at {pdf.relative_to(VIDEO)}: run templated.py fetch")
        ]
    text = pdf_text(pdf)
    known = number_set(text)
    found = [
        fail(f"beat {k}'s stat {fmt(v)} is not in the output's PDF")
        for k, v in stat_values(spec)
        if not sourced(v, known)
    ]
    body = flat(text)
    quotes = [
        (k, b)
        for k, b in enumerate(spec.get("beats", []))
        if b.get("type") == "quote" and b.get("text") and not own_words(b)
    ]
    found += [
        fail(f"beat {k}'s quote is not the PDF's words: {b['text'][:70]!r}")
        for k, b in quotes
        if flat(b["text"]) not in body
    ]
    # a spoken number above ten, or with a fraction, is a claim that needs a source
    found += [
        fail(f"line {n} says {t}, which the output's PDF does not", line["start"])
        for n, line in enumerate(timing["lines"])
        for t in tokens(line["caption"])
        if re.fullmatch(r"\d+(\.\d+)?", t)
        and (float(t) > 10 or "." in t)
        and not sourced(float(t), known)
    ]
    return found


def norm_word(w: str) -> str:
    return re.sub(r"[^a-z0-9']", "", w.lower())


def word_start(timing: dict, line: int, w: str, nth: int = 1) -> float:
    n = 0
    for x in timing["lines"][line]["words"]:
        if norm_word(x["w"]) == norm_word(w):
            n += 1
            if n == nth:
                return x["start"]
    raise ValueError(f'"{w}" ({nth}) not in line {line}')


def check_beats(proj: Path, timing: dict, spec: dict) -> list[dict]:
    beats = [b for b in spec.get("beats", []) if b.get("type") != "close"]
    close = next((b for b in spec.get("beats", []) if b.get("type") == "close"), {})
    lines = timing["lines"]
    found = []

    def cue(b: dict, at) -> float | None:
        if at is None or isinstance(at, (int, float)):
            return at
        if isinstance(at, str):
            return word_start(timing, b["line"], at)
        return word_start(timing, at[0], at[1], at[2] if len(at) > 2 else 1)

    try:
        starts = [
            max(
                0.0,
                (
                    word_start(timing, b["line"], b["from"])
                    if b.get("from")
                    else lines[b["line"]]["start"]
                )
                - LEAD,
            )
            for b in beats
        ]
    except (ValueError, IndexError, KeyError) as e:
        return [
            {
                "level": "fail",
                "at": None,
                "detail": f"a beat's line or `from` does not resolve: {e}",
            }
        ]
    closing = (
        max(0.0, lines[close["line"]]["start"] - LEAD)
        if close.get("line") is not None
        else lines[-1]["end"] + 0.6
    )
    ends = starts[1:] + [closing]
    for k, b in enumerate(beats):
        t0, t1 = starts[k], ends[k] - OUT_GAP
        hold = t1 - t0
        if hold < MIN_HOLD_S:
            found.append(
                {
                    "level": "fail" if hold < MIN_HOLD_FAIL_S else "warn",
                    "at": round(t0, 2),
                    "detail": f"beat {k} ({b.get('type')}) is on screen {hold:.1f} s",
                }
            )
        cues = [("at", b.get("at"))] + [
            (f"item {i} at", it.get("at"))
            for i, it in enumerate(b.get("items", []) or [])
        ]
        cues += [
            (f"focus {i} at", f.get("at"))
            for i, f in enumerate(b.get("focus", []) or [])
        ]
        if (
            isinstance(b.get("at"), list)
            and b["at"]
            and not isinstance(b["at"][0], (int, float))
            and b.get("type") == "people"
        ):
            cues = [(f"person {i} at", a) for i, a in enumerate(b["at"])]
        for name, at in cues:
            try:
                t = cue(b, at)
            except (ValueError, IndexError) as e:
                found.append(
                    {
                        "level": "fail",
                        "at": round(t0, 2),
                        "detail": f"beat {k} {name} does not resolve: {e}",
                    }
                )
                continue
            if t is not None and t > t1 - CUE_MARGIN_S:
                found.append(
                    {
                        "level": "fail",
                        "at": round(t, 2),
                        "detail": f"beat {k} ({b.get('type')}) {name} lands {t1 - t:.1f} s before the beat clears",
                    }
                )
    return found


def check_frames(proj: Path, timing: dict, vid: str) -> list[dict]:
    drafts = sorted((OUT / vid).glob(f"{vid}*-draft.mp4"))
    if not drafts:
        return [
            {
                "level": "fail",
                "at": None,
                "detail": f"no draft in out/{vid}/: run video.py render",
            }
        ]
    spans = [(line["start"] + 0.3, line["end"]) for line in timing["lines"]]
    found = []
    for draft in drafts:
        w, h = map(
            int,
            subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=width,height",
                    "-of",
                    "csv=p=0",
                    str(draft),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            .stdout.strip()
            .split(","),
        )
        sw = 160
        sh = round(h * sw / w / 2) * 2
        raw = subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                str(draft),
                "-vf",
                f"fps={FPS},scale={sw}:{sh},format=gray",
                "-f",
                "rawvideo",
                "-",
            ],
            capture_output=True,
            check=True,
        ).stdout
        frames = np.frombuffer(raw, np.uint8).reshape(-1, sh, sw)
        # the caption band is the bottom of the frame and is lit whenever a line plays
        top = (
            frames[:, : int(sh * (0.7 if h > w else 0.78)), :]
            .reshape(len(frames), -1)
            .astype(np.float32)
        )
        std = top.std(axis=1)
        blanks = [
            i / FPS
            for i in range(len(std))
            if std[i] < BLANK_STD and any(a <= i / FPS <= b for a, b in spans)
        ]
        # one finding per run of blank frames
        run_start = None
        for k, t in enumerate(blanks):
            if run_start is None:
                run_start = t
            if k + 1 == len(blanks) or blanks[k + 1] - t > 1.5 / FPS:
                if t + 1 / FPS - run_start >= BLANK_MIN_S:
                    found.append(
                        {
                            "level": "fail",
                            "at": run_start,
                            "detail": f"{draft.name}: nothing on screen from {run_start:.2f} to {t + 1 / FPS:.2f} s while a line plays",
                        }
                    )
                run_start = None
    return found


CHECKS = {
    "levels": lambda p, t, s, v: check_levels(p, t),
    "tails": lambda p, t, s, v: check_tails(p, t),
    "transcript": lambda p, t, s, v: check_transcript(p, t),
    "phrases": lambda p, t, s, v: check_phrases(p, t, s),
    "sources": lambda p, t, s, v: check_sources(p, t, s),
    "beats": lambda p, t, s, v: check_beats(p, t, s),
    "frames": lambda p, t, s, v: check_frames(p, t, v),
}


def review(vid: str, offline: bool) -> dict:
    proj = VIDEO / vid
    timing = json.loads((proj / "timing.json").read_text())
    spec = json.loads((proj / "spec.json").read_text())
    checks = {}
    for name, run in CHECKS.items():
        if name == "transcript" and offline:
            checks[name] = {"ran": False, "findings": []}
            continue
        checks[name] = {"ran": True, "findings": run(proj, timing, spec, vid)}
    failed = [
        n for n, c in checks.items() if any(f["level"] == "fail" for f in c["findings"])
    ]
    return {
        "id": vid,
        "pass": not failed and all(c["ran"] for c in checks.values()),
        "failed": failed,
        "inputs": {
            name: sha(path)
            for name, path in {
                "spec.json": proj / "spec.json",
                "timing.json": proj / "timing.json",
                "script": VIDEO / "scripts" / f"{vid}.md",
                "voice.wav": proj / "assets" / "voice.wav",
                "mix.wav": proj / "assets" / "mix.wav",
            }.items()
        },
        "checks": checks,
    }


def report(r: dict) -> None:
    for name, c in r["checks"].items():
        if not c["ran"]:
            print(f"{name}: skipped")
            continue
        fails = [f for f in c["findings"] if f["level"] == "fail"]
        warns = [f for f in c["findings"] if f["level"] == "warn"]
        print(
            f"{name}: {'FAIL' if fails else 'ok'}"
            + (f" ({len(warns)} warning(s))" if warns else "")
        )
        for f in fails + warns:
            at = f"{f['at']:6.2f}s " if isinstance(f["at"], (int, float)) else ""
            print(f"  {f['level']}: {at}{f['detail']}")
    print(
        "PASS"
        if r["pass"]
        else "FAIL"
        + (f": {', '.join(r['failed'])}" if r["failed"] else ": a check was skipped")
    )


@app.command()
def main(
    vid: Annotated[str, typer.Argument()] = "",
    offline: Annotated[
        bool, typer.Option(help="skip the transcript, which calls ElevenLabs")
    ] = False,
    corpus: Annotated[
        bool, typer.Option(help="every committed video, offline, one line each")
    ] = False,
) -> None:
    if corpus:
        ids = sorted(p.parent.name for p in VIDEO.glob("slop-*/spec.json"))
        for v in ids:
            if not (VIDEO / v / "assets" / "mix.wav").is_file():
                print(f"{v}: no assets")
                continue
            r = review(v, offline=True)
            counts = {
                n: sum(f["level"] == "fail" for f in c["findings"])
                for n, c in r["checks"].items()
                if c["ran"]
            }
            print(f"{v}: " + " ".join(f"{n}={k}" for n, k in counts.items()))
        return
    if not vid:
        raise typer.BadParameter("give a video id, or --corpus")
    r = review(vid, offline)
    out = OUT / vid / "review.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(r, indent=1))
    report(r)
    print(out)
    raise typer.Exit(0 if r["pass"] else 1)


if __name__ == "__main__":
    app()
