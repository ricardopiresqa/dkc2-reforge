import csv
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "assets-raw/pirate"
STRIPS = ROOT / "assets/images/pirate/background/bg2"
local_capture = pytest.mark.skipif(
    not (STAGE / "reference-wram.bin").is_file() or not (STRIPS / "original_bg2_line_150.png").is_file(),
    reason="capturas originais e faixas derivadas da ROM são locais e não distribuídas")


def rows(name):
    with (STAGE / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def replay_tables():
    """Run main/original_bg2.lua over the captured trace; yield the module after each frame."""
    lupa = pytest.importorskip("lupa.luajit21")
    lua = lupa.LuaRuntime()
    lua.execute("jit.off()")
    module = lua.eval("dofile([[%s]])" % (ROOT / "main/original_bg2.lua"))
    camera, poses = rows("reference-camera.csv"), rows("reference-poses.csv")
    for frame in range(len(camera)):
        module.update(int(camera[frame]["camera_x_raw"]), int(poses[frame]["game_counter"]))
        yield frame, module, camera[frame]


@local_capture
def test_bg2_table_matches_register_and_wram_snapshot():
    matched = checked = 0
    for frame, module, camera in replay_tables():
        if frame >= 5:  # first frames still carry pre-trace INC state
            checked += 1
            # Scanline 224 (sea line 120) is the last HDMA write before V-blank.
            matched += (module.word(0x801C + 2 * 120) & 0x3FF) == int(camera["bg2_hscroll"])
    assert matched == checked == 1029
    wram = (STAGE / "reference-wram.bin").read_bytes()  # captured on the trace's last frame
    assert all((module.word(0x8000 + offset) & 0xFF) == wram[0x8000 + offset] for offset in range(0x12, 0x13A))


@local_capture
def test_coldata_gradient_starts_at_sea_line_112():
    spec = importlib.util.spec_from_file_location("strips", ROOT / "tools/replay-compare/export_bg2_strips.py")
    assert spec is not None and spec.loader is not None
    strips = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strips)
    table = strips.coldata_table()
    assert all(row == (0, 0, 0) for row in table[:112])
    assert table[112] == (0, 12, 0) and table[119] == (0, 13, 0)


@local_capture
def test_baked_strips_match_original_screen_with_scanline_scroll():
    np = pytest.importorskip("numpy")
    from PIL import Image

    frame = 153  # most open sea in the captured screenshots
    history = {index: [module.line_h(y) for y in range(224)]
               for index, module, _ in replay_tables() if frame - 6 <= index <= frame}
    screen = np.asarray(Image.open(STAGE / ("reference-frame-%04d.png" % frame)).convert("RGB"))[7:231].astype(int)
    strip = {}
    for index, (top, bottom) in enumerate(((0, 24), (24, 48), (48, 104))):
        image = np.asarray(Image.open(STRIPS / ("original_bg2_band_%d.png" % index)).convert("RGBA")).astype(int)
        for y in range(top, bottom):
            strip[y] = image[y - top]
    for y in range(104, 224):
        strip[y] = np.asarray(Image.open(STRIPS / ("original_bg2_line_%03d.png" % y)).convert("RGBA")).astype(int)[0]

    def matches(y, h):
        line = np.roll(strip[y], -h, axis=0)
        close = np.abs(line[:, :3] - screen[y]).max(axis=1) <= 8
        return int((close & (line[:, 3] > 0)).sum())

    # Mesen screenshots lag the RAM capture by a variable 1-6 frames; take it from the sky.
    lag = max(range(7), key=lambda l: sum(matches(y, history[frame - l][y]) for y in range(104)))
    predicted = history[frame - lag]
    visible = good = 0
    for y in range(104, 224):
        best = max(matches(y, h) for h in range(256))
        if best >= 100:  # row not hidden by the deck/sprites
            visible += 1
            good += max(matches(y, (predicted[y] + d) % 256) for d in (-1, 0, 1)) >= best - 2
    assert visible >= 60 and good == visible
