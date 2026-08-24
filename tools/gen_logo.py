"""Generate the placeholder brand mark (violet tile + gold "TM" monogram).

Placeholder only — replace `static/img/logo.png` and `static/img/pwa/*` with the
real logo, or upload one in the admin (SiteConfig -> Logo / Favicon), which wins
over these files at runtime.

    python tools/gen_logo.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(BASE, "static", "img")
PWA = os.path.join(IMG, "pwa")

TEXT = "TM"
VIOLET_TOP, VIOLET_BOTTOM = (81, 40, 152), (44, 22, 85)
GOLD = (220, 174, 60)

# Pillow needs a real .ttf; the repo only ships woff2 (browser-only). Fall back
# through a few common bold faces, then to Pillow's bitmap default.
FONTS = ["seguibl.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf"]


def _font(size):
    for name in FONTS:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def tile(size, *, radius_ratio=0.22, pad_ratio=0.0, bleed=False):
    """Rounded violet tile with a gold ring and the monogram, centered."""
    s = size * 4  # supersample, then downscale for clean edges
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    pad = int(s * pad_ratio)
    box = (pad, pad, s - pad - 1, s - pad - 1)
    radius = 0 if bleed else int((s - 2 * pad) * radius_ratio)

    # vertical gradient, painted as a clipped strip stack
    grad = Image.new("RGBA", (s, s))
    gd = ImageDraw.Draw(grad)
    for y in range(s):
        t = y / (s - 1)
        gd.line(
            [(0, y), (s, y)],
            fill=tuple(round(a + (b - a) * t) for a, b in zip(VIOLET_TOP, VIOLET_BOTTOM)) + (255,),
        )
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    im.paste(grad, (0, 0), mask)

    ring = int(s * 0.018)
    inset = int((s - 2 * pad) * 0.075) + pad
    d.rounded_rectangle(
        (inset, inset, s - inset - 1, s - inset - 1),
        radius=max(radius - inset + pad, int(radius * 0.6)),
        outline=GOLD + (170,), width=ring,
    )

    f = _font(int((s - 2 * pad) * 0.36))
    l, t, r, b = d.textbbox((0, 0), TEXT, font=f)
    d.text(((s - (r - l)) / 2 - l, (s - (b - t)) / 2 - t), TEXT, font=f, fill=GOLD + (255,))

    return im.resize((size, size), Image.LANCZOS)


def save(im, path, opaque=False):
    if opaque:
        bg = Image.new("RGB", im.size, VIOLET_BOTTOM)
        bg.paste(im, (0, 0), im)
        im = bg
    im.save(path)
    print("wrote", os.path.relpath(path, BASE))


def main():
    os.makedirs(PWA, exist_ok=True)
    save(tile(512), os.path.join(IMG, "logo.png"))
    save(tile(192), os.path.join(PWA, "icon-192.png"))
    save(tile(512), os.path.join(PWA, "icon-512.png"))
    # maskable: full bleed, art inside the 80% safe zone
    save(tile(512, pad_ratio=0.10, bleed=True), os.path.join(PWA, "icon-512-maskable.png"))
    save(tile(180), os.path.join(PWA, "apple-touch-icon.png"), opaque=True)


if __name__ == "__main__":
    main()
