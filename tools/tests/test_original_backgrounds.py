import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("backgrounds", ROOT / "tools/replay-compare/export_original_backgrounds.py")
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_snes_bitplanes_2bpp_and_4bpp():
    data = bytearray(32)
    data[0] = 0x80
    data[1] = 0x40
    data[16] = 0x20
    data[17] = 0x10
    assert module.tile_pixels(data, 0, 2)[0][:4] == [1, 2, 0, 0]
    assert module.tile_pixels(data, 0, 4)[0][:4] == [1, 2, 4, 8]
    assert module.tile_pixels(data, 32, 4) == module.tile_pixels(data, 0, 4)


def test_map_palette_flip_and_zero_transparency():
    vram = bytearray(65536)
    cgram = bytearray(512)
    vram[4096] = 0x80
    word = 0x4000 | 0x0400
    vram[:2] = word.to_bytes(2, "little")
    cgram[34:36] = (31).to_bytes(2, "little")
    metadata = {"ppu.layers[1].doubleWidth": "false", "ppu.layers[1].doubleHeight": "false",
                "ppu.layers[1].tilemapAddress": "0", "ppu.layers[1].chrAddress": "2048",
                "ppu.layers[1].largeTiles": "false"}
    image = module.render_layer(vram, cgram, metadata, 1, 4)
    assert image.getpixel((7, 0)) == (255, 0, 0, 255)
    assert image.getpixel((0, 0)) == (0, 0, 0, 0)


def test_palette_and_ppu_snapshot_are_frame_scoped():
    import json
    evidence = [ROOT / "assets-raw/pirate/diddy-palette-verification.json",
                ROOT / "assets-raw/pirate/ppu-snapshot-difference.json",
                ROOT / "assets-raw/pirate/backgrounds/source-report.json"]
    if not all(path.is_file() for path in evidence):
        pytest.skip("evidência derivada da ROM é local e não distribuída")
    palette = json.loads((ROOT / "assets-raw/pirate/diddy-palette-verification.json").read_text())
    assert all(frame["top_cgram_matches"][0]["exact"]
               and frame["top_cgram_matches"][0]["start_index"] == 145
               for frame in palette["frames"])
    snapshots = json.loads((ROOT / "assets-raw/pirate/ppu-snapshot-difference.json").read_text())
    assert snapshots["vram_changed_bytes"] == 7665
    assert snapshots["cgram_changed_bytes"] == 83
    source = json.loads((ROOT / "assets-raw/pirate/backgrounds/source-report.json").read_text())
    assert source["bg2_map"]["full_bytes_match_vram_offset"] == 47104
    assert source["bg2_gfx"]["full_bytes_match_vram_offset"] == 49152
    assert source["bg3_map"]["full_bytes_match_vram_offset"] == -1


def test_unverified_late_snapshot_bg3_is_not_rendered_in_original_mode():
    renderer = (ROOT / "main/renderer.lua").read_text(encoding="utf-8")
    start = renderer.index("local function draw_original_rigging")
    end = renderer.index("-- Cache da faixa visivel", start)
    block = renderer[start:end]
    assert 'draw("original_bg3"' not in block
    # Only the source-assembled, VRAM-verified rigging map may be drawn (test_bg3_rigging.py).
    assert 'draw("original_bg3_rigging"' in block
