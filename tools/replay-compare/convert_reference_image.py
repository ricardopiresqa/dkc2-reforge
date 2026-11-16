"""Convert a locally captured reference PPM to PNG; never download assets."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[2]
sources = sorted((root / "assets-raw/pirate").glob("reference-*.ppm"))
for source in sources:
    with Image.open(source) as image:
        image.save(source.with_suffix(".png"))
    print(source.with_suffix(".png"))
