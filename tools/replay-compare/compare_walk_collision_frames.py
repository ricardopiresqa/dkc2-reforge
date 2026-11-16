"""Pair original SNES walk frames with the closest port wall-contact frame.

Only visible-screen cropping and approved integer4 downscale are applied; no
translation, registration, or tolerance adjustment is made.
"""
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
PORT = ROOT / "dist/pirate-panic-walk-collision-qa4/dkc2-reforge"
STAGE = ROOT / "assets-raw/pirate"


def compare():
    manifest = json.loads((PORT / "qa-captures.json").read_text(encoding="utf-8"))
    contacts = [item for item in manifest["captures"] if item.get("metadata")]
    pairs = []
    for item in contacts:
        meta = item["metadata"]
        world_x = meta.get("x", 0)
        source_raw_x = world_x + 256
        refs = sorted(STAGE.glob("reference-walk-v5-x*.png"),
                      key=lambda p: abs(int(p.stem.rsplit("x", 1)[1]) - source_raw_x))
        if not refs: continue
        reference_path = refs[0]
        source_x = int(reference_path.stem.rsplit("x", 1)[1])
        original_raw = Image.open(reference_path).convert("RGB")
        original = original_raw.crop((0, 7, 256, 231))
        port_raw = Image.open(PORT / item["file"]).convert("RGB")
        if port_raw.size != (1024, 896): continue
        port = port_raw.resize((256, 224), Image.Resampling.NEAREST)
        diff = ImageChops.difference(original, port)
        out = Image.new("RGB", (768, 250), "#151515")
        out.paste(original, (0, 26)); out.paste(port, (256, 26)); out.paste(diff, (512, 26))
        draw = ImageDraw.Draw(out)
        draw.text((4, 5), "SNES rawX=%d" % source_x, fill="white")
        draw.text((260, 5), "PORT worldX=%.1f" % world_x, fill="white")
        draw.text((516, 5), "pixel-diff; no alignment", fill="white")
        path = PORT / ("walk-contact-%05d.png" % round(world_x))
        out.save(path)
        diff_bytes = diff.tobytes()
        mismatch = sum(diff_bytes[i:i+3] != b"\0\0\0" for i in range(0,len(diff_bytes),3))
        pairs.append({"source_frame": source_x, "port_frame": item["frame"],
                      "port_x": world_x, "source_minus_port_x": source_x-source_raw_x,
                      "source_image": str(reference_path.relative_to(ROOT)),
                      "port_image": item["file"], "comparison": str(path.relative_to(ROOT)),
                      "visible_pixels_different": mismatch})
    report = {"scope":"same input-vector opening then right-only tail; actual capture pairs, no image registration",
              "pairs":pairs}
    (PORT / "walk-collision-comparisons.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    compare()
