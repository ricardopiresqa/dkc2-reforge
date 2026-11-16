"""Checks for the exact approved native-source upload staging, not runtime screenshots."""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/delivery/screenshot-native-source.json"


@pytest.mark.skipif(not REPORT.exists() or not (ROOT / "tools/native-build-screenshot").is_dir(),
                    reason="approved screenshot source not staged")
def test_native_upload_inputs_are_pinned_licensed_and_not_game_data():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["source_commit"] == "5f3098e3bfc37e8f26bde9428436b4d4499d1d50"
    assert report["license"] == "MIT" and report["budget_brl"] == 0
    stage = ROOT / "tools/native-build-screenshot"
    assert (stage / "main.collection").read_text() == 'name: "ScreenshotQA"\n'
    assert (stage / "empty.input_binding").read_bytes() == b""
    for item in report["native_source_files"]:
        path = Path(item["path"])
        assert path.parts[0] == "screenshot" or path.name == "LICENSE.md"
        assert path.suffix.lower() not in (".sfc", ".smc", ".png", ".wav", ".der")
        assert "roms" not in path.parts and "assets-raw" not in path.parts
        assert hashlib.sha256((stage / path).read_bytes()).hexdigest() == item["sha256"]


def test_capture_is_game_framebuffer_and_opt_in():
    script = (ROOT / "main/qa_capture.lua").read_text(encoding="utf-8")
    assert '"dkc2.capture_qa", "0"' in script
    assert "screenshot.png(function" in script
    assert "empty QA framebuffer capture" in script
    assert "io.open(filename" in script
    assert "collision_walk_qa" in script
    assert 'event.kind == "source_wall" or event.kind == "legacy_grid_wall"' in script
    assert "max_collision_captures = 12" in script
    assert "camera_x = camera.pos_x" in script and "camera_y = camera.pos_y" in script
    assert "for index = #events, 1, -1 do" in script
    assert "event.frame < frame - 1" in script
    assert "/tools" in (ROOT / ".defignore").read_text()
    ignore = (ROOT / ".defignore").read_text(encoding="utf-8")
    assert "/assets-raw" in ignore and "/roms" in ignore
    assert "/samples" in ignore
    assert "/manifest.private.der" in ignore
    assert "/dkc2_save.dat" in ignore
    for module in (ROOT / "main/original_animation.lua", ROOT / "main/original_camera.lua",
                   ROOT / "main/dev_autopilot.lua", ROOT / "data/levels/level_1_1.lua"):
        text = module.read_text(encoding="utf-8")
        assert 'require("assets-raw.' not in text


def test_rom_derived_runtime_data_is_available_locally():
    runtime_data = ROOT / "data/original/pirate"
    if not runtime_data.is_dir():
        pytest.skip("dados derivados da ROM são locais e não distribuídos")
    for name in ("pirate_panic_level.lua", "render_info.lua", "camera_profile.lua",
                 "animation_scripts.lua", "reference_inputs.lua"):
        assert (runtime_data / name).is_file(), name
    assert 'require("data.original.pirate.animation_scripts")' in (ROOT / "main/original_animation.lua").read_text(encoding="utf-8")
    assert 'require("data.original.pirate.reference_inputs")' in (ROOT / "main/dev_autopilot.lua").read_text(encoding="utf-8")
