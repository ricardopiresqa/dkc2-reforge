import csv
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"
TRACE = STAGE / "reference-hud-trace.csv"
local_capture = pytest.mark.skipif(not TRACE.is_file() or not (ROOT / "assets/images/pirate/hud/original_hud_digit_0.png").is_file(),
                                   reason="capturas e sprites derivados da ROM são locais e não distribuídos")


def hud_module():
    lupa = pytest.importorskip("lupa.luajit21")
    lua = lupa.LuaRuntime()
    lua.execute("jit.off()")
    return lua.eval("dofile([[%s]])" % (ROOT / "main/original_hud.lua"))


def trace():
    with TRACE.open(newline="") as handle:
        return list(csv.DictReader(handle))


@local_capture
def test_pickup_flight_and_hud_match_capture_every_frame():
    """Original route -> per-animation box -> pickup -> flying banana -> HUD, no injected events."""
    lupa = pytest.importorskip("lupa.luajit21")
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    lua.execute("jit.off()")
    lua.execute('package.preload["data.original.pirate.bananas"] = function() return dofile([[%s]]) end'
                % (ROOT / "data/original/pirate/bananas.lua"))
    bananas = lua.eval("dofile([[%s]])" % (ROOT / "main/original_bananas.lua"))
    hud = lua.eval("dofile([[%s]])" % (ROOT / "main/original_hud.lua"))
    bananas.init(True)
    hud.init(4)

    def rows_of(name):
        with (STAGE / name).open(newline="") as handle:
            return list(csv.DictReader(handle))

    gameplay, poses, camera, rows = (rows_of("reference-gameplay.csv"), rows_of("reference-poses.csv"),
                                     rows_of("reference-camera.csv"), trace())
    assert len(rows) == 401
    for frame, row in enumerate(rows):
        if frame:
            hud.update(int(row["clock"]))   # BEC68A, then the actors' pickups
            x, feet = int(gameplay[frame]["x_raw"]) - 256, int(gameplay[frame]["y_raw"]) - 256
            box = bananas.player_box(int(poses[frame]["animation_id"]),
                                     bool(int(poses[frame]["flags"]) & 0x4000), x, feet)
            count, positions = bananas.collect(*box)
            if count:  # screen position against the camera before this frame's update
                cam_x, cam_y = int(camera[frame - 1]["camera_x_raw"]) - 256, int(camera[frame - 1]["camera_y_raw"]) - 256
                hud.collect_banana(lua.table_from([lua.table_from([p[1] - cam_x, p[2] - cam_y])
                                                   for p in positions.values()]))
            hud.move_flying()
        state = (hud.target, hud.shown, hud.banana_timer, hud.lives_timer, hud.lives_slide, hud.lives)
        expected = tuple(int(row[key]) for key in ("banana_target", "banana_shown", "banana_timer",
                                                   "lives_timer", "lives_slide", "lives"))
        assert state == expected, (frame, state, expected)


@local_capture
def test_hud_sprites_match_original_screens():
    np = pytest.importorskip("numpy")
    from PIL import Image

    hud = hud_module()
    banana = [np.asarray(Image.open(ROOT / ("assets/images/pirate/banana/original_banana_%d.png" % i)).convert("RGBA")).astype(int)
              for i in range(8)]
    digit = [np.asarray(Image.open(ROOT / ("assets/images/pirate/hud/original_hud_digit_%d.png" % i)).convert("RGBA")).astype(int)
             for i in range(10)]
    head = np.asarray(Image.open(ROOT / "assets/images/pirate/hud/original_hud_diddy_head.png").convert("RGBA")).astype(int)
    rows = trace()

    def score(frame, lag):
        screen = np.asarray(Image.open(STAGE / ("reference-frame-%04d.png" % frame)).convert("RGB"))[7:231].astype(int)
        row, stats = rows[frame - lag], [0, 0]

        def put(sprite, x, y):  # displayed row = OAM Y
            for yy in range(sprite.shape[0]):
                for xx in range(sprite.shape[1]):
                    if sprite[yy, xx, 3] and 0 <= x + xx < 256 and 0 <= y + yy < 224:
                        stats[0] += 1
                        stats[1] += int(np.abs(sprite[yy, xx, :3] - screen[y + yy, x + xx]).max() <= 8)

        if int(row["banana_timer"]):
            put(banana[int(row["clock"]) // 4 % 8], 8, 8)
            put(digit[int(row["banana_shown"]) % 16], 0x18, 8)
        if int(row["lives_timer"]):
            hud.lives_slide = int(row["lives_slide"])
            put(digit[int(row["lives"])], 0xE4, hud.lives_y())
            put(head, 212 - 7, hud.lives_y() + 16 - 14)
        return stats

    for frame in (40, 60, 140):  # frames with the HUD on screen
        opaque, matched = max((score(frame, lag) for lag in range(1, 7)), key=lambda s: s[1])
        assert opaque > 80 and matched == opaque, (frame, opaque, matched)
