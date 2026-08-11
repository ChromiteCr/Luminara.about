#!/usr/bin/env python3
"""Fit a window capture into an exact canvas, for App Store Connect.

    python3 tools/review_shot.py ~/Pictures/截屏图像/截屏2026-08-09\\ 09.54.39.png \\
        review/plan-1280x800.png

The subscription review screenshot has to be one fixed size, and a macOS window
is never that size. Scaling the file itself would either letterbox it with white
or distort it, so the window is scaled to fit and centred on the app's own black
instead. Nothing is added, removed or retouched: what a reviewer sees is the
capture, at a smaller size, on the background it already had.

Default output is 1280x800, the size App Store Connect takes for a Mac
subscription. Pass --size WxH for anything else.
"""

import argparse
import os

from PIL import Image, ImageFilter

VOID = (16, 16, 16)        # #101010, the app's own background
MARGIN = 24                # breathing room, so the window is not wall to wall


def window(path):
    """The window out of a macOS capture, without the shadow it came with.

    `screencapture` writes the drop shadow into the alpha channel, and that
    shadow fades to nothing at the very edge of the file rather than stopping,
    so `getbbox()` on the alpha returns the whole image and trims nothing.
    Cutting to the near-opaque pixels gets the window itself. Skipping this puts
    two shadows on the canvas and insets the window by a margin nobody chose.
    """
    shot = Image.open(path)
    if shot.mode != "RGBA":
        return shot.convert("RGBA")
    solid = shot.getchannel("A").point(lambda a: 255 if a > 200 else 0)
    box = solid.getbbox()
    return shot.crop(box) if box else shot


def fit(shot, size, margin=MARGIN):
    w, h = size
    canvas = Image.new("RGB", size, VOID)

    # Never enlarged. A capture smaller than the canvas is a capture taken at 1x,
    # and blowing it up to fill the frame turns crisp text into a soft mess that
    # reads, correctly, as a doctored image.
    scale = min((w - margin * 2) / shot.width, (h - margin * 2) / shot.height, 1.0)
    shot = shot.resize(
        (round(shot.width * scale), round(shot.height * scale)), Image.LANCZOS)

    x = (w - shot.width) // 2
    y = (h - shot.height) // 2

    # A soft shadow built from the window's own alpha, so it follows the rounded
    # corners the capture already has rather than boxing them.
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    silhouette = Image.new("RGBA", shot.size, (0, 0, 0, 150))
    silhouette.putalpha(shot.getchannel("A").point(lambda a: int(a * 0.5)))
    shadow.paste(silhouette, (x, y + 14), silhouette)
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))

    canvas.paste(shadow, (0, 0), shadow)
    canvas.paste(shot, (x, y), shot)
    return canvas, scale


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture")
    ap.add_argument("out", nargs="?", default="review/plan-1280x800.png")
    ap.add_argument("--size", default="1280x800")
    ap.add_argument("--margin", type=int, default=MARGIN)
    args = ap.parse_args()

    w, h = (int(n) for n in args.size.lower().split("x"))
    shot = window(args.capture)
    canvas, scale = fit(shot, (w, h), args.margin)

    directory = os.path.dirname(args.out)
    if directory:
        os.makedirs(directory, exist_ok=True)
    canvas.save(args.out, "PNG")
    print(f"{args.out}  {w}x{h}  window {shot.width}x{shot.height} at {scale:.3f}  "
          f"{os.path.getsize(args.out)//1024} KB")


if __name__ == "__main__":
    main()
