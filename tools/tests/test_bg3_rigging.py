import csv
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"
DISASM = ROOT / "tools/vendor/DKC2-disasm/DKC2/Tilemaps/Layer3_ShipDeck.bin"
local_capture = pytest.mark.skipif(not (STAGE / "reference-frame-0040-vram.bin").is_file() or not DISASM.is_file(),
                                   reason="capturas/disasm originais são locais e não distribuídos")

spec = importlib.util.spec_from_file_location("export_bg3_rigging", ROOT / "tools/replay-compare/export_bg3_rigging.py")
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def camera_rows():
    with (STAGE / "reference-camera.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


@local_capture
def test_bg3_scroll_registers_match_every_frame():
    rows = camera_rows()
    for frame in range(1, len(rows)):
        previous = rows[frame - 1]
        expected = (int(rows[frame]["bg3_hscroll"]), int(rows[frame]["bg3_vscroll"]))
        assert module.bg3_scroll(int(previous["camera_x_raw"]), int(previous["camera_y_raw"])) == expected, frame


@local_capture
def test_bg3_map_matches_captured_vram_tilemap():
    checks = module.verify(module.tile_words())
    assert len(checks) == 9 and all(check["cells"] == 780 and check["mismatched"] == 0 for check in checks)


@local_capture
def test_bg3_pixels_match_original_screens():
    from PIL import Image

    rig_image = Image.open(ROOT / "assets/images/pirate/background/original_bg3_rigging_p1.png").convert("RGBA")
    rig = rig_image.load()  # keep rig_image alive: PixelAccess does not own the image
    rows = camera_rows()

    def compare(frame, lag):
        screen_image = Image.open(STAGE / ("reference-frame-%04d.png" % frame)).convert("RGB")
        screen = screen_image.load()
        map_x, map_y = module.map_origin(int(rows[frame - lag]["camera_x_raw"]), int(rows[frame - lag]["camera_y_raw"]))
        opaque = matched = 0
        for sy in range(224):
            for sx in range(256):
                pixel = rig[(map_x + sx) % 1280, (map_y + sy) % 512]
                if pixel[3]:
                    opaque += 1
                    observed = screen[sx, sy + 7]  # explicit Mesen NTSC overscan crop
                    matched += max(abs(a - b) for a, b in zip(pixel[:3], observed)) <= 8
        return opaque, matched

    # Mesen screenshots lag the RAM capture by a variable 1-6 frames (see test_bg2_hdma).
    for frame in (40, 60, 100, 173, 180):
        opaque, matched = max((compare(frame, lag) for lag in range(1, 7)), key=lambda r: r[1])
        assert opaque > 150 and matched == opaque, (frame, opaque, matched)
