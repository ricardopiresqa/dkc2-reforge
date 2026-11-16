import csv
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"
FRAMES = ROOT / "assets/images/pirate/banana"
local_capture = pytest.mark.skipif(
    not (STAGE / "reference-wram.bin").is_file() or not (ROOT / "data/original/pirate/bananas.lua").is_file()
    or not (FRAMES / "original_banana_0.png").is_file(),
    reason="capturas, disasm e dados derivados da ROM são locais e não distribuídos")


def exporter():
    spec = importlib.util.spec_from_file_location("export_bananas", ROOT / "tools/replay-compare/export_bananas.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bananas_module():
    lupa = pytest.importorskip("lupa.luajit21")
    lua = lupa.LuaRuntime()
    lua.execute("jit.off()")
    lua.execute('package.preload["data.original.pirate.bananas"] = function() return dofile([[%s]]) end'
                % (ROOT / "data/original/pirate/bananas.lua"))
    module = lua.eval("dofile([[%s]])" % (ROOT / "main/original_bananas.lua"))
    module.init(True)
    return module


def rows(name):
    with (STAGE / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


@local_capture
def test_formations_match_the_games_own_wram_list():
    module = exporter()
    check = module.check_wram(module.groups(module.asm()))
    assert check["columns"] == 148 and check["differences_are_cleared_bits"]
    assert [index for index, _, _ in check["differing_columns"]] == [51, 54]  # collected in the trace


@local_capture
def test_original_route_collects_exactly_the_bananas_the_game_cleared():
    module = bananas_module()
    poses, taken = rows("reference-poses.csv"), []
    for frame, row in enumerate(rows("reference-gameplay.csv")):
        x, feet = int(row["x_raw"]) - 256, int(row["y_raw"]) - 256
        box = module.player_box(int(poses[frame]["animation_id"]), bool(int(poses[frame]["flags"]) & 0x4000), x, feet)
        result = module.collect(*box)  # (count, positions)
        if (result[0] if isinstance(result, tuple) else result) > 0:
            taken.append(frame)
    # reference-hud-trace.csv: the HUD timer re-arms on exactly these pickup frames
    assert taken == [197, 206] and module.remaining() == 95


@local_capture
def test_spin_frames_and_positions_match_original_screens():
    np = pytest.importorskip("numpy")
    from PIL import Image

    module = bananas_module()
    sprites = [np.asarray(Image.open(FRAMES / ("original_banana_%d.png" % i)).convert("RGBA")).astype(int)
               for i in range(8)]
    camera, poses = rows("reference-camera.csv"), rows("reference-poses.csv")

    def score(frame, lag):
        screen = np.asarray(Image.open(STAGE / ("reference-frame-%04d.png" % frame)).convert("RGB"))[7:231].astype(int)
        cam_x, cam_y = int(camera[frame - lag]["camera_x_raw"]) - 256, int(camera[frame - lag]["camera_y_raw"]) - 256
        stats = [0, 0]

        def draw(spin, x, y):
            sprite = sprites[spin]
            for yy in range(16):
                for xx in range(16):
                    sx, sy = x - cam_x + xx, y - cam_y + yy
                    if 0 <= sx < 256 and 0 <= sy < 224 and sprite[yy, xx, 3]:
                        stats[0] += 1
                        stats[1] += int(np.abs(sprite[yy, xx, :3] - screen[sy, sx]).max() <= 8)

        module.each_visible(int(poses[frame - lag]["game_counter"]), draw)
        return stats

    # Screenshots lag the RAM capture by a variable 1-6 frames (see test_bg2_hdma).
    for frame in (40, 100, 153, 180):
        opaque, matched = max((score(frame, lag) for lag in range(1, 7)), key=lambda s: s[1])
        assert opaque > 100 and matched >= 0.97 * opaque, (frame, opaque, matched)
