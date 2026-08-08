#!/usr/bin/env python3
"""Two vertical announcement images, one Chinese and one English.

    python3 tools/teaser.py

Writes teaser/coming-zh.png and teaser/coming-en.png at 1080x1920, the shape a
phone shows full screen.

The background is the icon's spectrum, cropped and blurred past recognition.
That band is the only colour in the icon, and the only colour on the marketing
site, so a teaser built out of it says what the product is before a word is
read: an interface with no colour in it, and light coming through something.
"""

import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

W, H = 1080, 1920
MARGIN = 96

VOID = (16, 16, 16)        # #101010, the app's own background
TEXT = (237, 237, 237)     # #ededed
MUTED = (180, 180, 180)    # #b4b4b4
DIM = (138, 138, 138)      # #8a8a8a
HAIRLINE = (49, 49, 49)    # #313131

CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"
CJK_BOLD, CJK_LIGHT = 2, 0
LATIN = "/System/Library/Fonts/HelveticaNeue.ttc"
LATIN_BOLD, LATIN_MEDIUM = 1, 10
MONO = "/System/Library/Fonts/Menlo.ttc"

ICON = "assets/icon-256.png"
ICON_LARGE = "/tmp/icon-1024-rounded.png"

# Where the spectrum sits in a 1024 icon: the band under the hat's brim. Taken
# by eye from the artwork rather than computed, because "the colourful part" is
# not something a threshold finds without also finding the star.
SPECTRUM = (240, 620, 800, 800)

CARDS = [
    ("coming-en", "en", "COMING SOON", "Create\nyour own style.",
     "Luminara", "Colour grading for macOS"),
    ("coming-zh", "zh", "即将上线", "创建\n你自己的风格",
     "Luminara", "macOS 调色工具"),
]


def fonts(lang):
    if lang == "zh":
        return CJK, CJK_BOLD, CJK, CJK_LIGHT
    return LATIN, LATIN_BOLD, LATIN, LATIN_MEDIUM


def fit(text, max_width, path, index, start=170, floor=48):
    size = start
    while size >= floor:
        font = ImageFont.truetype(path, size, index=index)
        if max(font.getbbox(l)[2] for l in text.split("\n")) <= max_width:
            return font
        size -= 2
    raise SystemExit(f"“{text}” will not fit {max_width}px")


def backdrop():
    """The spectrum, enlarged until it stops being a picture of anything.

    **Masked radially, and that is the whole difference between light and a
    pasted rectangle.** A blurred crop dropped onto the canvas still has four
    straight edges however soft its insides are, and the eye finds them
    immediately. Fading it on a circle leaves nothing to find.
    """
    band = Image.open(ICON_LARGE).convert("RGB").crop(SPECTRUM)

    # Stretched to more than cover the canvas, on both axes independently.
    #
    # Keeping the band's aspect ratio left its own top edge lying across the
    # picture, because the radial mask was still bright where the artwork
    # stopped. A blurred field of colour has no detail left to distort, so the
    # honest fix is to have no boundary anywhere inside the frame.
    wide = band.resize((int(W * 2.6), int(H * 1.5)), Image.LANCZOS)
    wide = wide.filter(ImageFilter.GaussianBlur(150))
    # Blur averages the spectrum toward grey, which is the one thing this image
    # cannot be. Put the colour back.
    wide = ImageEnhance.Color(wide).enhance(2.1)

    centre_y = int(H * 0.34)
    glow = Image.new("RGB", (W, H), VOID)
    glow.paste(wide, (-(wide.width - W) // 2, centre_y - wide.height // 2))

    # A circle of light rather than a band of it: bright at the centre, gone well
    # before any edge of the canvas.
    reach = int(W * 1.75)
    falloff = ImageOps.invert(Image.radial_gradient("L")).resize(
        (reach, reach), Image.BICUBIC)
    mask = Image.new("L", (W, H), 0)
    mask.paste(falloff, (W // 2 - reach // 2, centre_y - reach // 2))
    # Squared harder and capped lower than a plain falloff: the point is a bloom
    # with a centre, not an even wash the type has to fight.
    mask = mask.point(lambda v: int((v / 255) ** 2.4 * 165))

    return Image.composite(glow, Image.new("RGB", (W, H), VOID), mask)


def card(name, lang, eyebrow, headline, wordmark, tagline):
    canvas = backdrop()
    draw = ImageDraw.Draw(canvas)

    body, bold, label_path, label_index = fonts(lang)
    column = W - MARGIN * 2

    icon = Image.open(ICON).convert("RGBA").resize((132, 132), Image.LANCZOS)
    canvas.paste(icon, (MARGIN, 190), icon)

    head_font = fit(headline, column, body, bold)
    lines = headline.split("\n")
    ascent, descent = head_font.getmetrics()
    lead = int((ascent + descent) * (1.12 if lang == "zh" else 1.02))

    # Anchored from the bottom, so the two cards agree on where the words sit
    # however tall the headline turns out to be in that language.
    foot_y = H - MARGIN - 150
    head_bottom = foot_y - 150
    top = head_bottom - lead * len(lines)

    if eyebrow.isascii():
        eye_font = ImageFont.truetype(MONO, 30, index=1)
    else:
        eye_font = ImageFont.truetype(CJK, 30, index=CJK_LIGHT)
    draw.text((MARGIN, top - 78), " ".join(eyebrow), font=eye_font, fill=DIM)

    for i, line in enumerate(lines):
        draw.text((MARGIN, top + i * lead), line, font=head_font, fill=TEXT)

    draw.rectangle([MARGIN, foot_y - 56, W - MARGIN, foot_y - 55], fill=HAIRLINE)

    mark = ImageFont.truetype(LATIN, 40, index=LATIN_BOLD)
    draw.text((MARGIN, foot_y - 20), wordmark, font=mark, fill=TEXT)

    tag = ImageFont.truetype(label_path, 30, index=label_index)
    draw.text((MARGIN, foot_y + 40), tagline, font=tag, fill=MUTED)

    out = os.path.join("teaser", name + ".png")
    canvas.save(out, "PNG")
    print(f"{out}  {W}x{H}  headline {head_font.size}pt")


def main():
    os.makedirs("teaser", exist_ok=True)
    for args in CARDS:
        card(*args)


if __name__ == "__main__":
    main()
