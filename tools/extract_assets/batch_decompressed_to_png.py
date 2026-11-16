"""Batch convert decompressed PAC1 files to grayscale PNGs."""
import os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_bpp import parse_bpp_tiles

try:
    from PIL import Image
except ImportError:
    sys.exit('pip install pillow')

IN_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'samples', 'pac1_extracted')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'samples', 'gfx_png')
os.makedirs(OUT_DIR, exist_ok=True)

PAL = [(i * 17, i * 17, i * 17) for i in range(16)]

files = sorted(glob.glob(os.path.join(IN_DIR, '*_decompressed.bin')))
print(f'{len(files)} files to convert')

count = 0
for fpath in files:
    data = open(fpath, 'rb').read()
    if len(data) < 16 or len(data) % 16 != 0:
        continue
    try:
        tiles = parse_bpp_tiles(data, bpp=4)
    except Exception:
        continue
    if not tiles:
        continue

    num = len(tiles)
    cols = min(16, num)
    rows = (num + cols - 1) // cols
    img = Image.new('RGB', (cols * 8, rows * 8))
    px = img.load()

    for ti, tile in enumerate(tiles):
        cx = ti % cols
        cy = ti // cols
        for py in range(8):
            for px_i in range(8):
                v = tile[py * 8 + px_i]
                px[cx * 8 + px_i, cy * 8 + py] = PAL[v] if 0 <= v < 16 else (0, 0, 0)

    base = os.path.basename(fpath).replace('_decompressed.bin', '')
    img.save(os.path.join(OUT_DIR, f'{base}_{num}t.png'))
    count += 1
    if count % 500 == 0:
        print(f'{count}...', flush=True)

print(f'Done: {count} PNGs -> {OUT_DIR}')
