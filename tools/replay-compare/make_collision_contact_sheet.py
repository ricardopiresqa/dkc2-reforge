"""Create a QA-only sheet of screenshots taken on distinct wall contacts."""
import json
from pathlib import Path
import sys
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[2]
bundle = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dist/pirate-panic-walk-collision-qa4")
folder = root / bundle / "dkc2-reforge"
manifest = json.loads((folder / "qa-captures.json").read_text())
items = [item for item in manifest["captures"] if item.get("metadata")]
cell_w, cell_h, columns = 384, 336, 3
rows = (len(items) + columns - 1) // columns
sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "#171717")
draw = ImageDraw.Draw(sheet)
for index, item in enumerate(items):
    image = Image.open(folder / item["file"]).convert("RGB")
    image.thumbnail((cell_w, cell_h - 28), Image.Resampling.NEAREST)
    x, y = (index % columns) * cell_w, (index // columns) * cell_h
    sheet.paste(image, (x, y + 24))
    meta = item["metadata"]
    draw.text((x + 4, y + 4), "%s x=%.1f y=%.1f floor=%s" %
              (item["file"], meta["x"], meta["y"], meta["surface_y"]), fill="white")
sheet.save(folder / "collision-contact-sheet.png")
print("collision sites=%d sheet=%s" % (len(items), folder / "collision-contact-sheet.png"))
