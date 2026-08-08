#!/usr/bin/env python3
"""Compose App Store screenshots, and the web-sized copies the site uses.

    python3 tools/appstore.py ~/Desktop/shots

Reads four window captures, writes two things:

  appstore/*.png   2880x1800, one of the sizes App Store Connect accepts, with a
                   bold Chinese line down the left and the window filling the
                   right and bleeding off the edge.
  assets/shot-*.png  the same captures, resized for the marketing page.

The palette is Achromatic, the same greys as the app and the site, so a
screenshot dropped onto this canvas has no seam: the window's own background is
already this colour.
"""

import sys
import os
import glob

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# --- The canvas -------------------------------------------------------------

W, H = 2880, 1800          # accepted by App Store Connect for macOS
VOID = (16, 16, 16)        # #101010, the app's own background
TEXT = (237, 237, 237)     # #ededed
DIM = (138, 138, 138)      # #8a8a8a

# The window starts here and runs off the right edge. 2880 - 560 = 2320, which
# is 80.5% of the width: the brief asked for at least 80%, and letting it bleed
# rather than fitting it is what stops the composition reading as a slide.
SPLIT = 560
PAD_L = 132
TEXT_W = SPLIT - PAD_L - 44

CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"
CJK_BOLD = 2               # W6. Index 0 is W3, which is too light at this size.
CJK_LIGHT = 0
# Helvetica Neue Bold rather than SF: SF ships as a variable font macOS will not
# hand to Pillow by weight, and Helvetica Neue is the face SF descends from, so
# it sits beside the app's own type without announcing itself as a substitute.
LATIN = "/System/Library/Fonts/HelveticaNeue.ttc"
LATIN_BOLD = 1
MONO = "/System/Library/Fonts/Menlo.ttc"

# --- What each one says -----------------------------------------------------
#
# One sentence each, and the eyebrow above it is the same word the website uses
# for that section. Order is the order they should be uploaded in: the first is
# the only one that appears in search results.

# Five or six characters a line. The column is a fifth of the canvas because the
# window takes the rest, so a long line either shrinks to nothing or runs under
# the screenshot. Short lines are what this layout is for anyway: at this size a
# sentence that needs punctuation is a sentence that needs cutting.
SHOTS = {
    "zh": [
        ("shot-pad",     "调色板", "你的照片\n就是调色盘"),
        ("shot-lucy",    "LUCY",  "每一个数值\n都写给你看"),
        ("shot-regions", "区域",   "蒙版拆得开\n每个都能改"),
        ("shot-batch",   "批量",   "一整个文件夹\n逐张求解"),
    ],
    # Not translations. Chinese fits four or five characters where English needs
    # a dozen, so the English lines are written for the same column rather than
    # rendered from the Chinese and then shrunk to fit.
    "en": [
        ("shot-pad",     "THE PAD",  "Your photo,\nyour palette"),
        ("shot-lucy",    "LUCY",     "Every value,\nwritten down"),
        ("shot-regions", "REGIONS",  "Every mask\ncomes apart"),
        ("shot-batch",   "BATCH",    "Every photo,\nsolved again"),
    ],
}


def line_height(font):
    ascent, descent = font.getmetrics()
    return ascent + descent


def fit(text, max_width, path=CJK, index=CJK_BOLD, start=104, floor=40):
    """Largest size at which every line fits the column.

    Returns the last size that fitted, never a size that did not. The earlier
    version fell through to the floor when nothing fitted, which is how a
    headline ended up running underneath the screenshot: it was drawn at a size
    the column had already rejected.
    """
    size = start
    while size >= floor:
        font = ImageFont.truetype(path, size, index=index)
        if max(font.getbbox(l)[2] for l in text.split("\n")) <= max_width:
            return font
        size -= 2
    raise SystemExit(
        f"“{text.replace(chr(10), ' / ')}” does not fit {max_width}px even at "
        f"{floor}pt. Shorten the line rather than shrinking it further.")


def window(capture):
    """The window out of a macOS capture, without the shadow it came with.

    `screencapture` on a window writes the drop shadow into the alpha channel, and
    that shadow fades to nothing at the very edge of the file rather than stopping,
    so `getbbox()` on the alpha returns the whole image and trims nothing. Cutting
    to the near-opaque pixels instead gets the window itself. Skipping this puts
    two shadows on the canvas and insets the window by a margin nobody chose.
    """
    shot = Image.open(capture)
    if shot.mode != "RGBA":
        return shot.convert("RGBA")
    solid = shot.getchannel("A").point(lambda a: 255 if a > 200 else 0)
    box = solid.getbbox()
    return shot.crop(box) if box else shot


def compose(capture, eyebrow, headline, out):
    canvas = Image.new("RGB", (W, H), VOID)
    shot = window(capture)

    # Scaled to fill the column exactly, flush to the right edge.
    #
    # Fitting by height and letting it bleed looked better and was wrong: this
    # app puts its most interesting panel down the right side, so any overhang
    # crops the one thing the screenshot is of. The window's rounded corners are
    # what stop a flush edge reading as a mistake.
    target_w = W - SPLIT
    scale = target_w / shot.width
    target_h = int(shot.height * scale)
    shot = shot.resize((target_w, target_h), Image.LANCZOS)
    y = (H - target_h) // 2

    # A soft drop shadow, built from the window's own alpha so it follows the
    # rounded corners a macOS capture already has rather than boxing them.
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    silhouette = Image.new("RGBA", shot.size, (0, 0, 0, 150))
    silhouette.putalpha(shot.getchannel("A").point(lambda a: int(a * 0.55)))
    shadow.paste(silhouette, (SPLIT, y + 26), silhouette)
    shadow = shadow.filter(ImageFilter.GaussianBlur(38))
    canvas.paste(shadow, (0, 0), shadow)
    canvas.paste(shot, (SPLIT, y), shot)

    draw = ImageDraw.Draw(canvas)

    if headline.isascii():
        head_font = fit(headline, TEXT_W, LATIN, LATIN_BOLD)
    else:
        head_font = fit(headline, TEXT_W, CJK, CJK_BOLD)

    # Menlo for a Latin eyebrow, because mono is the site's label voice. It has
    # no CJK glyphs though, so a Chinese eyebrow set in it comes out as a row of
    # tofu, which is exactly what happened the first time. Chinese falls back to
    # the light weight of the headline face, which reads as a label beside W6.
    if eyebrow.isascii():
        eye_font = ImageFont.truetype(MONO, 30, index=1)
    else:
        eye_font = ImageFont.truetype(CJK, 30, index=CJK_LIGHT)

    lines = headline.split("\n")
    lead = int(line_height(head_font) * 1.16)
    block = lead * len(lines)
    top = (H - block) // 2

    # The eyebrow sits above the headline in mono with wide tracking, the same
    # label style the app and the website use. Spaced by hand because Pillow has
    # no letter-spacing.
    tracked = " ".join(eyebrow)
    draw.text((PAD_L, top - 88), tracked, font=eye_font, fill=DIM)

    for i, line in enumerate(lines):
        draw.text((PAD_L, top + i * lead), line, font=head_font, fill=TEXT)

    canvas.save(out, "PNG")
    return canvas.size, head_font.size


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "."
    lang = sys.argv[2] if len(sys.argv) > 2 else "zh"
    if lang not in SHOTS:
        raise SystemExit(f"language must be one of {sorted(SHOTS)}")

    out_dir = os.path.join("appstore", lang)
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs("assets", exist_ok=True)

    missing = []
    for name, eyebrow, headline in SHOTS[lang]:
        found = (glob.glob(os.path.join(src, name + ".*"))
                 or glob.glob(os.path.join(src, name.replace("shot-", "") + ".*")))
        if not found:
            missing.append(name)
            continue
        capture = found[0]

        out = os.path.join(out_dir, name + ".png")
        size, pt = compose(capture, eyebrow, headline, out)
        print(f"{out}  {size[0]}x{size[1]}  headline {pt}pt")

        # The site takes its pictures from the English run only: the page is in
        # English, and a Chinese interface under English prose would read as a
        # screenshot of some other program.
        if lang != "en":
            continue

        # The capture itself, not the composed canvas: the page already has the
        # words in HTML, where they are selectable and translate.
        web = window(capture).convert("RGB")
        web.thumbnail((1600, 1600), Image.LANCZOS)
        # JPEG, not PNG. These are photographs of an interface, and PNG holds a
        # dark gradient-heavy screenshot at about four times the size for a
        # difference nobody sees at page width. Progressive so a slow connection
        # gets the whole frame early rather than the top third.
        web_out = os.path.join("assets", name + ".jpg")
        web.save(web_out, "JPEG", quality=88, optimize=True, progressive=True)
        print(f"{web_out}  {web.width}x{web.height}  "
              f"{os.path.getsize(web_out)//1024} KB")

    if missing:
        print("\nnot found in " + src + ":")
        for name in missing:
            print("  " + name + ".png")


if __name__ == "__main__":
    main()
