"""Generate static/js/world_map.js — country outlines + Uzbek country names.

The admin analytics dashboard (apps/analytics) draws its Locations choropleth
from this file. It is a generated asset: edit THIS script, not the output.

Run it with the project venv from anywhere; sources are downloaded and cached
under the system temp dir, so a re-run is fast:

    venv\\Scripts\\python.exe tools/gen_world_map.py

Then rebuild the flag sprite, which appends its index to the same file:

    venv\\Scripts\\python.exe tools/gen_flags.py

Sources (both permissively licensed):
  * Geometry — Natural Earth 110m admin-0 countries, public domain.
  * Uzbek country names — Unicode CLDR, Unicode licence. Only uz is shipped:
    Chrome's Intl.DisplayNames covers ru/en but silently answers in English
    for uz, so it is the one locale the browser cannot localize on its own.

Output: Miller cylindrical projection, 1000px wide, Antarctica dropped.
Requires: requests (already a project dependency).
"""
import json
import math
import os
import sys
import tempfile

import requests

GEO_URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
           "master/geojson/ne_110m_admin_0_countries.geojson")
CLDR_URL = ("https://raw.githubusercontent.com/unicode-org/cldr-json/main/"
            "cldr-json/cldr-localenames-full/main/uz/territories.json")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(BASE, "static", "js", "world_map.js")
CACHE = os.path.join(tempfile.gettempdir(), "tagayev-mapdata")

W = 1000.0
K = W / (2 * math.pi)          # radians -> px
LAT_TOP, LAT_BOTTOM = 84.0, -58.0
PREC = 1                        # decimals kept in projected px
MIN_AREA = 0.6                  # px^2 bbox area below which a ring is dropped

# Unrecognised states NE lists separately; ip-api reports their IPs under the
# recognised parent, so merge them there instead of losing the geometry.
FIXUP = {"N. Cyprus": "CY", "Somaliland": "SO"}


def download(url, name):
    """Fetch `url` once, then serve it from the temp cache on later runs."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        print(f"downloading {name} ...")
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        with open(path, "wb") as fh:
            fh.write(response.content)
    return json.load(open(path, encoding="utf-8"))


def miller_y(lat):
    phi = math.radians(max(min(lat, 89.5), -89.5))
    return 1.25 * math.asinh(math.tan(0.8 * phi))


Y_TOP, Y_BOTTOM = miller_y(LAT_TOP), miller_y(LAT_BOTTOM)
H = round((Y_TOP - Y_BOTTOM) * K, 1)


def project(lon, lat):
    x = (math.radians(lon) + math.pi) * K
    y = (Y_TOP - miller_y(lat)) * K
    return round(x, PREC), round(y, PREC)


def ring_path(ring):
    """One closed SVG subpath, plus its bbox area so tiny islands can be cut."""
    pts, prev = [], None
    for lon, lat in ring:
        point = project(lon, lat)
        if point != prev:
            pts.append(point)
            prev = point
    if len(pts) < 3:
        return None, 0.0
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    area = (max(xs) - min(xs)) * (max(ys) - min(ys))
    out = [f"M{pts[0][0]} {pts[0][1]}"]
    for x, y in pts[1:]:
        out.append(f"L{x} {y}")
    out.append("Z")
    return "".join(out), area


def polygons(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    return geom["coordinates"]


def build_paths(data):
    paths = {}
    for feat in data["features"]:
        props = feat["properties"]
        code = props.get("ISO_A2_EH") or ""
        if code in ("-99", ""):
            code = FIXUP.get(props.get("NAME"), "")
        if not code or code == "AQ":
            continue
        rings = []
        for poly in polygons(feat["geometry"]):
            for ring in poly:
                d, area = ring_path(ring)
                if d:
                    rings.append((area, d))
        if not rings:
            continue
        # Always keep the mainland (largest ring); drop only the specks.
        rings.sort(reverse=True)
        kept = [rings[0][1]] + [d for a, d in rings[1:] if a >= MIN_AREA]
        paths[code] = paths.get(code, "") + "".join(kept)
    return paths


def build_uz_names(data):
    territories = data["main"]["uz"]["localeDisplayNames"]["territories"]
    return {
        code: name
        for code, name in territories.items()
        # Skip numeric macro-regions ("001" = World) and CLDR variant keys
        # ("US-alt-short"); only plain ISO 3166-1 alpha-2 codes are useful.
        if len(code) == 2 and code.isalpha()
    }


def main():
    paths = build_paths(download(GEO_URL, "ne_110m_countries.geojson"))
    names = build_uz_names(download(CLDR_URL, "cldr_uz_territories.json"))
    with open(DEST, "w", encoding="utf-8") as fh:
        fh.write(
            "// Generated — do not edit by hand. See tools/gen_world_map.py.\n"
            "// Geometry: Natural Earth 110m admin-0 countries (public domain),\n"
            "//   Miller cylindrical, "
            f"{int(W)}px wide, lat {LAT_BOTTOM}..{LAT_TOP} (Antarctica dropped).\n"
            "// Uzbek country names: Unicode CLDR (Chrome's Intl.DisplayNames\n"
            "//   covers ru/en but falls back to English for uz).\n"
            "// window.FLAG_SPRITE is appended by tools/gen_flags.py — run it after this.\n"
        )
        body = ",".join(f'"{c}":"{d}"' for c, d in sorted(paths.items()))
        fh.write(f"window.WORLD_MAP={{w:{int(W)},h:{H},paths:{{{body}}}}};\n")
        fh.write("window.COUNTRY_NAMES_UZ=" + json.dumps(
            names, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + ";\n")
    print(f"{len(paths)} countries, {len(names)} uz names -> {DEST}")
    print("now run: tools/gen_flags.py")


if __name__ == "__main__":
    sys.exit(main())
