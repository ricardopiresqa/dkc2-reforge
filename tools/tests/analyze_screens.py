"""Localiza a regiao do jogo no screenshot (varredura de diversidade de cor)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from PIL import Image  # noqa: E402


def main(p):
    im = Image.open(p).convert("RGB")
    w, h = im.size
    px = im.load()
    print("%s %dx%d" % (os.path.basename(p), w, h))
    best = []
    step = 160
    for y0 in range(0, h, step):
        for x0 in range(0, w, step):
            seen = set()
            for y in range(y0, min(y0 + step, h), 4):
                for x in range(x0, min(x0 + step, w), 4):
                    seen.add(px[x, y])
            best.append((len(seen), x0, y0))
    best.sort(reverse=True)
    print("regioes mais coloridas (diversidade, x, y):")
    for n, x0, y0 in best[:8]:
        print("  %5d  x=%4d y=%4d" % (n, x0, y0))
    # recorta a regiao rica e descreve
    n, x0, y0 = best[0]
    crop = im.crop((x0, y0, min(x0 + step * 3, w), min(y0 + step * 3, h)))
    cs = crop.getcolors(maxcolors=1 << 20) or []
    print("recorte x=%d y=%d -> %dx%d cores=%d" % (x0, y0, crop.width,
                                                   crop.height, len(cs)))
    q = crop.load()
    for yy in range(0, crop.height, 24):
        row = []
        for xx in range(0, crop.width, 24):
            r, g, b = q[xx, yy]
            row.append("%02x%02x%02x" % (r, g, b))
        print("  " + " ".join(row))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
