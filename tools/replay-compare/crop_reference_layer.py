"""Extract a layer's raw tilemap window with explicit PPU scroll metadata."""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
frame = int(sys.argv[1]) if len(sys.argv) > 1 else 40
layer = int(sys.argv[2]) if len(sys.argv) > 2 else 0
stage = ROOT / "assets-raw/pirate"
image = Image.open(stage / ("frame-backgrounds/%04d/original_bg%d_01.png" % (frame, layer + 1))).convert("RGBA")
meta = dict(line.split("=", 1) for line in (stage / ("reference-frame-%04d-ppu.txt" % frame)).read_text().splitlines())
prefix = "ppu.layers[%d]." % layer
x = int(meta[prefix + "hscroll"]) % image.width
y = int(meta[prefix + "vscroll"]) % image.height
out = Image.new("RGBA", (256, 239))
pixels = out.load()  # PixelAccess writes (faster than putpixel)
for py in range(out.height):
    for px in range(out.width):
        color = image.getpixel(((x + px) % image.width, (y + py) % image.height))
        assert color is not None
        pixels[px, py] = color
path = stage / ("reference-layer%d-frame-%04d-viewport.png" % (layer + 1, frame))
out.save(path)
print("frame=%d layer=%d scroll=(%d,%d) output=%s" % (frame, layer + 1, x, y, path))
