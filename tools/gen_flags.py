"""Build static/img/flags.png — one vertical sprite of every country flag.

Flag emoji do not render on Windows (Chrome draws nothing), so the admin
analytics dashboard shows real flag images instead. This script downloads one
small PNG per country from flagcdn.com (public-domain flag artwork), stacks
them into a single sprite, and appends the per-code row index to
static/js/world_map.js as `window.FLAG_SPRITE`.

Run AFTER tools/gen_world_map.py — this reads the country list from its output
and writes to the end of the same file:

    venv\\Scripts\\python.exe tools/gen_world_map.py
    venv\\Scripts\\python.exe tools/gen_flags.py

Downloads are cached under the system temp dir, so a re-run is fast.
Requires: requests + Pillow (both already project dependencies).
"""
import io
import json
import os
import sys
import tempfile

import requests
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_JS = os.path.join(BASE, "static", "js", "world_map.js")
SPRITE = os.path.join(BASE, "static", "img", "flags.png")
CACHE = os.path.join(tempfile.gettempdir(), "tagayev-flags")

# 40x30 cells: the dashboard renders them at 20x15, so this is the 2x asset.
CELL_W, CELL_H = 40, 30
MARKER = "\nwindow.FLAG_SPRITE="


def codes_from_map_js():
    """Every ISO-2 code the dashboard can show (the CLDR name list)."""
    src = io.open(MAP_JS, encoding="utf-8").read()
    anchor = "window.COUNTRY_NAMES_UZ="
    if anchor not in src:
        sys.exit("world_map.js has no COUNTRY_NAMES_UZ — run gen_world_map.py first.")
    start = src.index(anchor) + len(anchor)
    return sorted(json.loads(src[start:src.rindex(";")]))


def flag_image(code):
    """One 40x30 RGBA tile, or None if flagcdn has no artwork for the code."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, code.lower() + ".png")
    if not os.path.exists(path):
        response = requests.get(f"https://flagcdn.com/w40/{code.lower()}.png",
                                timeout=30)
        if response.status_code != 200:
            return None
        with open(path, "wb") as fh:
            fh.write(response.content)
    return Image.open(path).convert("RGBA").resize((CELL_W, CELL_H), Image.LANCZOS)


def main():
    tiles, kept = [], []
    for code in codes_from_map_js():
        try:
            tile = flag_image(code)
        except Exception as exc:            # network hiccup: skip, not fatal
            print(f"skip {code}: {exc}")
            continue
        if tile is None:
            continue
        tiles.append(tile)
        kept.append(code)

    sheet = Image.new("RGBA", (CELL_W, CELL_H * len(tiles)), (0, 0, 0, 0))
    for row, tile in enumerate(tiles):
        sheet.paste(tile, (0, row * CELL_H))
    os.makedirs(os.path.dirname(SPRITE), exist_ok=True)
    sheet.save(SPRITE, optimize=True)

    index = {code: row for row, code in enumerate(kept)}
    src = io.open(MAP_JS, encoding="utf-8").read()
    if MARKER in src:                        # drop a previous run's line
        src = src[:src.index(MARKER) + 1]
    with io.open(MAP_JS, "w", encoding="utf-8") as fh:
        fh.write(src)
        fh.write("window.FLAG_SPRITE={w:%d,h:%d,index:%s};\n" % (
            CELL_W, CELL_H,
            json.dumps(index, sort_keys=True, separators=(",", ":"))))
    print(f"{len(kept)} flags -> {SPRITE} ({os.path.getsize(SPRITE)} bytes)")


if __name__ == "__main__":
    sys.exit(main())
