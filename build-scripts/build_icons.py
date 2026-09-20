#!/usr/bin/env python3
"""Generate the PWA icon set from assets/images/apple-touch-icon.png.

The source is a 180px two-tone silhouette, so a plain upscale goes soft at
the edges. Upscaling, re-thresholding back to two tones and then downsampling
restores clean antialiased edges at 192 and 512.
"""
from PIL import Image

SRC = "assets/images/apple-touch-icon.png"
ORANGE = (255, 140, 0, 255)
BLACK = (18, 18, 18, 255)


def two_tone(im, size):
    big = im.convert("RGBA").resize((size * 4, size * 4), Image.LANCZOS)
    px = big.load()
    for y in range(big.height):
        for x in range(big.width):
            r, g, b, a = px[x, y]
            # the silhouette is the warm, bright half of the image
            px[x, y] = ORANGE if (r > 110 and g > 45) else BLACK
    return big.resize((size, size), Image.LANCZOS)


def main():
    src = Image.open(SRC)
    for size, name in [(192, "icon-192.png"), (512, "icon-512.png")]:
        out = two_tone(src, size)
        out.save("assets/images/" + name, "PNG", optimize=True)
        print("assets/images/%s  %dx%d" % (name, size, size))

    # Maskable: the same art inset to the 80% safe zone on a full bleed plate,
    # so Android can crop it to any shape without clipping the mech.
    plate = Image.new("RGBA", (512, 512), BLACK)
    art = two_tone(src, 400)
    plate.paste(art, (56, 56), art)
    plate.save("assets/images/icon-maskable-512.png", "PNG", optimize=True)
    print("assets/images/icon-maskable-512.png  512x512 (maskable)")


if __name__ == "__main__":
    main()
