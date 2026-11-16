"""Measure actual captured frames, checking PPM integrity and integer upscale.

Pixel mismatch is evidence, not a fidelity certificate. No aligning/warping
images to hide differences; port is only downscaled by the approved integer4.
"""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
FRAMES = (40, 60, 100, 140, 153, 158, 165, 173, 180)
GAME = ROOT / "dist/pirate-panic-framebuffer-qa/dkc2-reforge"


def ppm_info(path):
    raw = path.read_bytes()
    magic, shape, maximum, payload = raw.split(b"\n", 3)
    assert magic == b"P6" and maximum == b"255"
    width, height = map(int, shape.split())
    expected = width * height * 3
    return {"width": width, "height": height, "payload_bytes": len(payload),
            "expected_payload_bytes": expected, "exact_payload": len(payload) == expected,
            "payload_rows": len(payload) / (width * 3)}


def compare(bundle=None):
    game = (ROOT / bundle / "dkc2-reforge").resolve() if bundle else GAME
    game.relative_to(ROOT / "dist")
    results = []
    for frame in FRAMES:
        reference_path = ROOT / "assets-raw/pirate" / ("reference-frame-%04d.png" % frame)
        port_path = game / ("qa-frame-%04d.png" % frame)
        integrity = ppm_info(reference_path.with_suffix(".ppm"))
        reference = Image.open(reference_path).convert("RGB")
        raw_reference_size = reference.size
        frontend_crop = None
        if reference.size == (256, 239):
            # Explicit Mesen NTSC frontend profile, not image registration.
            reference = reference.crop((0, 7, 256, 231))
            frontend_crop = {"top": 7, "bottom": 8, "source": "explicit portable Snes.Overscan profile"}
        full_port = Image.open(port_path).convert("RGB")
        if reference.size != (256, 224) or full_port.size != (1024, 896):
            raise ValueError("unexpected frame dimensions frame %d: reference=%s port=%s ppm=%s" %
                             (frame, reference.size, full_port.size, integrity))
        port = full_port.resize(reference.size, Image.Resampling.NEAREST)
        exact_scaling = ImageChops.difference(full_port, port.resize(full_port.size, Image.Resampling.NEAREST)).getbbox() is None
        diff = ImageChops.difference(reference, port)
        values = diff.tobytes()
        mismatch = sum(values[i:i + 3] != b"\0\0\0" for i in range(0, len(values), 3))
        out = game / ("comparison-%04d.png" % frame)
        sheet = Image.new("RGB", (768, 224))
        sheet.paste(reference, (0, 0)); sheet.paste(port, (256, 0)); sheet.paste(diff, (512, 0))
        sheet.save(out)
        results.append({"frame": frame, "reference_ppm": integrity,
                        "raw_reference_dimensions": raw_reference_size,
                        "frontend_crop": frontend_crop,
                        "integer_replication_exact": exact_scaling,
                        "pixel_mismatch": mismatch, "pixels_total": 256 * 224,
                        "reference_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
                        "port_sha256": hashlib.sha256(port_path.read_bytes()).hexdigest(),
                        "comparison_sheet": str(out.relative_to(ROOT)),
                        "status": "REFERENCE_INVALID" if not integrity["exact_payload"] else "DIFFERENT"})
    report = {"scope": "actual framebuffers; no alignment or invented reference",
              "status": "NOT_PROVEN", "frames": results}
    (game / "framebuffer-comparison.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    compare(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
