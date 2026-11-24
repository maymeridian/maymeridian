'''
tools/build.py
Author: maymeridian
Description: Draws the pictures of the profile page: the animated banner and one card per project.
             - The cards take their titles, descriptions, tags and drawings from a copy of the website
               (projects.json and assets/<name>.svg), so the profile and maymeridian.dev say the same thing.
             - Every picture is a self-contained SVG: no script, no web font and nothing fetched from another site.
             - Usage: python tools/build.py <folder of the website>
'''

import json
import random
import re
import sys
import textwrap
from html import escape
from pathlib import Path

# --- LOOK ---

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# The site's colours (style.css)
BACKGROUND = "#07040a"
BORDER = "#33264f"
TEXT = "#ece4e0"
TEXT_DIM = "#9a8f96"
RED_BRIGHT = "#f08a68"
VIOLET_BRIGHT = "#b9a4ff"
TAG = "#c9b48f"

# No web font can be loaded by a picture, so each reader's own monospace face is used
FONT = "ui-monospace, SFMono-Regular, 'JetBrains Mono', Menlo, Consolas, 'Liberation Mono', monospace"
ADVANCE = 0.6  # width of a monospace character as a share of its size, in the widest of those faces

# --- BANNER ---

BANNER = (1200, 380)  # size of the banner's drawing area
STARS = 90  # stars scattered over the banner
SEED = 1048596  # fixes where the stars fall, so a rebuild draws the same sky
TAGLINES = [
    "machine learning, checked against real data",
    "game mods and a VR port rebuilt from a binary",
    "the tools that run a film and TV prop store",
]
TAGLINE_SIZE = 24  # points
TAGLINE_LEFT = 70  # left edge of the title and the taglines
TAGLINE_TIME = 4  # seconds each tagline has, typed and held
TICKER_SIZE = 16  # points
TICKER_GAP = 70  # space between two equations of the ticker
TICKER_TIME = 80  # seconds for the ticker to scroll through all its equations once

# The equations of the ticker, as (text, level) pieces: level -1 is a subscript and 1 a superscript
EQUATIONS = [
    [("iℏ ∂ψ/∂t = Ĥψ", 0)],
    [("G", 0), ("μν", -1), (" + Λg", 0), ("μν", -1), (" = (8πG/c⁴) T", 0), ("μν", -1)],
    [("∇·E = ρ/ε₀", 0)],
    [("r", 0), ("t", -1), (" ≈ R", 0), ("★", -1), ("(M", 0), ("BH", -1), ("/M", 0), ("★", -1), (")", 0), ("1/3", 1)],
    [("L ∝ t", 0), ("−5/3", 1)],
    [("S = k", 0), ("B", -1), (" ln Ω", 0)],
    [("E² = (pc)² + (mc²)²", 0)],
    [("Δx Δp ≥ ℏ/2", 0)],
    [("r", 0), ("s", -1), (" = 2GM/c²", 0)],
]


def stars():
    """Returns the banner's stars: small circles in three groups that twinkle out of step."""
    rng = random.Random(SEED)
    circles = []
    for _ in range(STARS):
        x, y = rng.uniform(10, BANNER[0] - 10), rng.uniform(10, 300)
        radius = rng.choice([0.6, 0.8, 1.0, 1.2, 1.6])
        circles.append(f'<circle class="tw {rng.choice("abc")}" cx="{x:.0f}" cy="{y:.0f}" r="{radius}"/>')
    return "\n    ".join(circles)


def taglines():
    """Returns the taglines, each wiped in from the left behind a caret, one after another in a loop."""
    loop = TAGLINE_TIME * len(TAGLINES)
    share = 1 / len(TAGLINES)
    # the wipe takes 40% of a tagline's time, the line is held until 90% and cleared at the end
    times = f"0;{0.4 * share:.4f};{0.9 * share:.4f};{share:.4f};1"
    parts = []
    for number, line in enumerate(TAGLINES):
        width = round(len(line) * TAGLINE_SIZE * ADVANCE)
        timing = f'dur="{loop}s" begin="{number * TAGLINE_TIME}s" repeatCount="indefinite"'
        right = TAGLINE_LEFT + width + 6
        parts.append(
            f'''<clipPath id="line-{number}"><rect x="{TAGLINE_LEFT}" y="182" width="0" height="36">
      <animate attributeName="width" values="0;{width + 4};{width + 4};0;0" keyTimes="{times}" {timing}/>
    </rect></clipPath>
    <text x="{TAGLINE_LEFT}" y="208" font-size="{TAGLINE_SIZE}" fill="{TEXT}" textLength="{width}" lengthAdjust="spacingAndGlyphs" clip-path="url(#line-{number})">{escape(line)}</text>
    <rect class="caret" x="{TAGLINE_LEFT}" y="186" width="11" height="26" fill="{RED_BRIGHT}" opacity="0">
      <animate attributeName="x" values="{TAGLINE_LEFT};{right};{right};{TAGLINE_LEFT};{TAGLINE_LEFT}" keyTimes="{times}" {timing}/>
      <animate attributeName="opacity" values="1;1;1;0;0" keyTimes="{times}" {timing}/>
    </rect>'''
        )
    return "\n    ".join(parts)


def ticker():
    """Returns the equations laid out in a row twice over, and the length of one row for the loop."""
    small = round(TICKER_SIZE * 0.7)
    row, x = [], 0
    for pieces in EQUATIONS:
        spans, level = [], 0
        for text, to in pieces:
            # a subscript sits 5 below the line and a superscript 7 above it; dy moves from the last piece
            shift = {0: 0, -1: 5, 1: -7}[to] - {0: 0, -1: 5, 1: -7}[level]
            size = TICKER_SIZE if to == 0 else small
            spans.append(f'<tspan dy="{shift}" font-size="{size}">{escape(text)}</tspan>')
            level = to
        row.append((x, "".join(spans)))
        x += round(sum(len(t) * (TICKER_SIZE if lv == 0 else small) * ADVANCE for t, lv in pieces)) + TICKER_GAP
    texts = [f'<text x="{at + offset}" y="346">{spans}</text>' for offset in (0, x) for at, spans in row]
    return "\n      ".join(texts), x


def banner():
    """Returns the banner: the name over a field of stars, a star falling into a black hole, and the ticker."""
    width, height = BANNER
    equations, loop = ticker()
    title_width = 540  # the name is spaced out to this width, whatever face draws it
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="maymeridian: machine learning, game mods and reverse engineering. A star is pulled into a black hole beside the name.">
  <defs>
    <clipPath id="frame"><rect width="{width}" height="{height}" rx="14"/></clipPath>
    <radialGradient id="cloud-red"><stop offset="0" stop-color="#d2583c" stop-opacity="0.22"/><stop offset="1" stop-color="#d2583c" stop-opacity="0"/></radialGradient>
    <radialGradient id="cloud-violet"><stop offset="0" stop-color="#8b6cf0" stop-opacity="0.2"/><stop offset="1" stop-color="#8b6cf0" stop-opacity="0"/></radialGradient>
    <linearGradient id="disk" x1="0" x2="1">
      <stop offset="0" stop-color="#8b6cf0" stop-opacity="0.2"/><stop offset="0.3" stop-color="#d2583c"/>
      <stop offset="0.5" stop-color="#fff0d8"/><stop offset="0.7" stop-color="#d2583c"/>
      <stop offset="1" stop-color="#8b6cf0" stop-opacity="0.2"/>
    </linearGradient>
    <linearGradient id="stream" x1="0" x2="1">
      <stop offset="0" stop-color="#fff5e1"/><stop offset="0.6" stop-color="#f08a68"/>
      <stop offset="1" stop-color="#d2583c" stop-opacity="0.6"/>
    </linearGradient>
    <radialGradient id="star">
      <stop offset="0" stop-color="#fffaf0"/><stop offset="0.35" stop-color="#ffd2a8" stop-opacity="0.8"/>
      <stop offset="1" stop-color="#f08a68" stop-opacity="0"/>
    </radialGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="4" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <style>
    text {{ font-family: {FONT}; }}
    .tw {{ fill: #fff; animation: twinkle 5s ease-in-out infinite; }}
    .tw.b {{ animation-duration: 7s; animation-delay: -3s; }}
    .tw.c {{ animation-duration: 11s; animation-delay: -6s; }}
    @keyframes twinkle {{ 0%, 100% {{ opacity: 0.2; }} 50% {{ opacity: 0.85; }} }}
    .debris {{ stroke-dasharray: 30 16; animation: fall 1.6s linear infinite; }}
    @keyframes fall {{ to {{ stroke-dashoffset: -46; }} }}
    .disk {{ animation: flare 6s ease-in-out infinite; }}
    @keyframes flare {{ 0%, 100% {{ opacity: 0.78; }} 50% {{ opacity: 1; }} }}
    .victim {{ animation: stretch 6s ease-in-out infinite; transform-origin: 150px 122px; transform-box: view-box; }}
    @keyframes stretch {{ 0%, 100% {{ transform: rotate(-20deg) scale(1, 1); }} 50% {{ transform: rotate(-20deg) scale(1.18, 0.86); }} }}
    .caret {{ animation: blink 0.9s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ fill-opacity: 0; }} }}
    .ticker {{ animation: scroll {TICKER_TIME}s linear infinite; }}
    @keyframes scroll {{ to {{ transform: translateX(-{loop}px); }} }}
    @media (prefers-reduced-motion: reduce) {{ .tw, .debris, .disk, .victim, .ticker {{ animation: none; }} }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{width}" height="{height}" fill="{BACKGROUND}"/>
    <ellipse cx="110" cy="20" rx="520" ry="230" fill="url(#cloud-red)"/>
    <ellipse cx="1090" cy="120" rx="480" ry="260" fill="url(#cloud-violet)"/>
    <ellipse cx="420" cy="400" rx="560" ry="200" fill="url(#cloud-violet)"/>
    {stars()}

    <!-- a tidal disruption event: the star on the left is pulled into a stream that feeds the disk -->
    <g transform="translate(610 42) scale(1.05)">
      <g transform="rotate(-12 400 125)">
        <path d="M335 125 A65 50 0 0 1 465 125" fill="none" stroke="#f08a68" stroke-width="6" opacity="0.45" filter="url(#glow)"/>
        <path class="debris" d="M150 95 C 230 60, 330 55, 430 95 S 420 150, 380 140" fill="none" stroke="url(#stream)" stroke-width="5" stroke-linecap="round" filter="url(#glow)"/>
        <path d="M150 95 C 230 75, 320 72, 420 102" fill="none" stroke="#fff5e1" stroke-width="1.2" opacity="0.7"/>
        <ellipse class="disk" cx="400" cy="125" rx="120" ry="24" fill="none" stroke="url(#disk)" stroke-width="10" filter="url(#glow)"/>
        <circle cx="400" cy="125" r="40" fill="#000" stroke="#ffd7aa" stroke-width="1.5" filter="url(#glow)"/>
        <path class="disk" d="M280 125 A120 24 0 0 0 520 125" fill="none" stroke="url(#disk)" stroke-width="10" filter="url(#glow)"/>
      </g>
      <ellipse class="victim" cx="150" cy="122" rx="30" ry="18" fill="url(#star)" transform="rotate(-20 150 122)"/>
    </g>

    <text x="{TAGLINE_LEFT}" y="150" font-size="68" fill="{RED_BRIGHT}" textLength="{title_width}" lengthAdjust="spacing">MAYMERIDIAN</text>
    {taglines()}
    <text x="{TAGLINE_LEFT}" y="262" font-size="17" fill="{VIOLET_BRIGHT}">maymeridian.dev →</text>

    <path d="M0 318 H{width} M0 364 H{width}" stroke="{BORDER}"/>
    <g fill="{TEXT_DIM}" opacity="0.75" font-size="{TICKER_SIZE}">
      <g class="ticker">
      {equations}
      </g>
    </g>
  </g>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="14" fill="none" stroke="{BORDER}"/>
</svg>
'''


# --- CARDS ---

CARD_WIDTH = 600  # the width of a card and of the site's drawings
ART_HEIGHT = 240  # the height of the site's drawings
CARD_HEIGHT = 486  # a full card: the drawing, a title, up to five lines and the tags
SMALL_HEIGHT = 312  # a small card: the drawing and the name
MARGIN = 28  # space left and right of a card's text
TITLE_SIZE = 25  # points
BODY_SIZE = 18  # points
BODY_PITCH = 26  # distance between two lines of the description
TAG_SIZE = 14  # points
NAME_SIZE = 34  # points, on a small card


def drawing(site, project):
    """Returns the inside of the project's drawing on the site, without its outer <svg> element."""
    name = re.sub(r"\?.*", "", project["image"])
    source = (site / name).read_text(encoding="utf-8")
    return re.search(r"<svg[^>]*>(.*)</svg>", source, flags=re.S).group(1).strip()


def tags(project, baseline):
    """Returns the project's tags as outlined labels in a row; "private" takes the violet of the site."""
    parts, x = [], MARGIN
    for tag in project["tags"]:
        width = round(len(tag) * TAG_SIZE * ADVANCE)
        colour = VIOLET_BRIGHT if tag == "private" else TAG
        if x + width + 18 > CARD_WIDTH - MARGIN:
            break
        parts.append(
            f'<rect x="{x}" y="{baseline - 17}" width="{width + 18}" height="24" fill="none" stroke="{colour}" stroke-opacity="0.6"/>'
            f'<text x="{x + 9}" y="{baseline}" font-size="{TAG_SIZE}" fill="{colour}" textLength="{width}" lengthAdjust="spacingAndGlyphs">{escape(tag)}</text>'
        )
        x += width + 18 + 8
    return "\n  ".join(parts)


def frame(height, label, inside):
    """Returns a card of the given height around its contents, with the site's dark panel and border."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_WIDTH} {height}" role="img" aria-label="{escape(label)}" font-family="{FONT}">
  <rect width="{CARD_WIDTH}" height="{height}" fill="{BACKGROUND}"/>
  {inside}
  <rect x="0.5" y="0.5" width="{CARD_WIDTH - 1}" height="{height - 1}" fill="none" stroke="{BORDER}"/>
</svg>
'''


def art(site, project):
    """Returns the project's drawing placed at the top of a card, with a rule under it."""
    return (
        f'<svg width="{CARD_WIDTH}" height="{ART_HEIGHT}" viewBox="0 0 {CARD_WIDTH} {ART_HEIGHT}">{drawing(site, project)}</svg>\n'
        f'  <path d="M0 {ART_HEIGHT} H{CARD_WIDTH}" stroke="{BORDER}"/>'
    )


def card(site, project):
    """Returns a full card: the drawing, the title, the description wrapped to the card, and the tags."""
    per_line = int((CARD_WIDTH - 2 * MARGIN) / (BODY_SIZE * ADVANCE))
    lines = textwrap.wrap(project["description"], per_line)
    body = "\n  ".join(
        f'<text x="{MARGIN}" y="{ART_HEIGHT + 82 + number * BODY_PITCH}" font-size="{BODY_SIZE}" fill="{TEXT_DIM}">{escape(line)}</text>'
        for number, line in enumerate(lines)
    )
    inside = f'''{art(site, project)}
  <text x="{MARGIN}" y="{ART_HEIGHT + 44}" font-size="{TITLE_SIZE}" font-weight="600" fill="{TEXT}">{escape(project["title"])}</text>
  {body}
  {tags(project, CARD_HEIGHT - 26)}'''
    return frame(CARD_HEIGHT, f'{project["title"]}: {project["description"]}', inside)


def small_card(site, project):
    """Returns a small card: the drawing with the project's name under it."""
    inside = f'''{art(site, project)}
  <text x="{CARD_WIDTH / 2:.0f}" y="{ART_HEIGHT + 47}" font-size="{NAME_SIZE}" font-weight="600" fill="{TEXT}" text-anchor="middle">{escape(project["title"])}</text>'''
    return frame(SMALL_HEIGHT, project["title"], inside)


# --- COMMAND LINE ---

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    site = Path(sys.argv[1])

    # 1. The banner
    (ASSETS / "cards").mkdir(parents=True, exist_ok=True)
    (ASSETS / "header.svg").write_text(banner(), encoding="utf-8", newline="\n")
    print("assets/header.svg")

    # 2. A card per project: full cards for the public groups, small ones for the store's own tools
    for project in json.loads((site / "projects.json").read_text(encoding="utf-8")):
        name = Path(project["link"]).name
        draw = small_card if project.get("group") == "propabilia" else card
        (ASSETS / "cards" / f"{name}.svg").write_text(draw(site, project), encoding="utf-8", newline="\n")
        print(f"assets/cards/{name}.svg")
