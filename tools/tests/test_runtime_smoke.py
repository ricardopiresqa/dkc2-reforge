"""Validate an observed bounded runtime report, not SNES fidelity."""
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "dist/pirate-panic-art-qa/dkc2-reforge/qa-runtime.json"


@pytest.mark.skipif(not REPORT.exists(), reason="fresh runtime report not generated")
def test_observed_runtime_advances_without_pool_exhaustion():
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    assert data["frames"] == 600
    samples = data["samples"]
    assert len(samples) == 11
    assert all(s["phase"] == 11 and s["health"] > 0 for s in samples)
    assert len({s["state"] for s in samples}) >= 3
    assert samples[-1]["x"] > samples[0]["x"]
    assert all(s["pool_drops"] == 0 for s in samples)
    assert 0 < max(s["sprites"] for s in samples) < 1200


NEW_REPORT = ROOT / "dist/pirate-panic-short-jump/dkc2-reforge/qa-runtime.json"


@pytest.mark.skipif(not NEW_REPORT.exists(), reason="current movement QA not generated")
def test_manual_input_and_original_motion_checks_executed():
    data = json.loads(NEW_REPORT.read_text(encoding="utf-8"))
    assert data["frames"] == 220
    assert data["input_check"] is True
    assert data["qa_version"] == "room-slice-oam-input-v2"
    assert all(s["pool_drops"] == 0 for s in data["samples"])


NATIVE = ROOT / "dist/pirate-panic-native-4x/dkc2-reforge"


@pytest.mark.skipif(not (NATIVE / "qa-runtime.json").exists(), reason="native 4x runtime not generated")
def test_native_viewport_is_measured_and_render_log_is_clean():
    report = json.loads((NATIVE / "qa-runtime.json").read_text(encoding="utf-8"))
    assert report["viewport"] == {"width": 256, "height": 224, "scale": 4,
                                   "window_width": 1024, "window_height": 896}
    assert report["frames"] == 220 and report["input_check"] is True
    assert all(sample["pool_drops"] == 0 for sample in report["samples"])
    log = (NATIVE / "log.txt").read_text(encoding="utf-8")
    assert "ERROR:" not in log


def test_bounded_route_qa_is_not_claimed_as_original_replay():
    source = (ROOT / "main/dev_autopilot.lua").read_text(encoding="utf-8")
    assert 'get_config("dkc2.route_qa", "0")' in source
    assert "frame_index >= #reference.inputs" in source
    assert "bounded-mixed-route-v1" in source
    assert "route_completed" in source
    assert "reference and not route_qa" in source
    assert "QA-only repeated held-jump bursts near decoded collision geometry" in source
    assert "player_x >= 3000 and player_x <= 4200" in source
    assert "tail % 48 < 22" in source
    assert "decoded ship-deck slice ends near source X=3207" in source
    assert "player_x >= 3020 and player_x <= 3070" in source


def test_original_level_cannot_complete_by_crossing_an_unverified_x_marker():
    game = (ROOT / "main/game.lua").read_text(encoding="utf-8")
    start = game.index("-- Prototype levels may use a simple X end marker.")
    block = game[start:game.index("if M.current_boss then", start)]
    assert "if not level_loader.original_semantics()" in block
    assert "header coordinate" in block
    wrapper = (ROOT / "data/levels/level_1_1.lua").read_text(encoding="utf-8")
    assert "original LevelEndGoal collision/state machine is not ported" in wrapper


def test_walk_collision_trace_is_opt_in_and_keeps_source_provenance():
    autopilot = (ROOT / "main/dev_autopilot.lua").read_text(encoding="utf-8")
    collision = (ROOT / "main/collision.lua").read_text(encoding="utf-8")
    assert 'get_config("dkc2.collision_walk_qa", "0")' in autopilot
    assert 'input.set_synthetic(RIGHT) -- walk only' in autopilot
    assert 'kind = kind' in collision and 'source_value = value' in collision
    assert "TRACE_LIMIT = 4096" in collision
    assert "source_step_y(col, pos_y, h, 16)" in collision
    player = (ROOT / "main/player.lua").read_text(encoding="utf-8")
    assert "local dx = landing_hold and 0 or M.vel_x * dt" in player and "current_h, dx, M.grounded)" in player
    assert "local vertical_start_y = step_y or M.pos_y" in (ROOT / "main/player.lua").read_text(encoding="utf-8")


def test_reference_walk_uses_snes_right_bit_not_r_button():
    source = (ROOT / "tools/replay-compare/reference_walk_capture.lua").read_text(encoding="utf-8")
    assert "mask = 128 end -- $4218 bit7 is Right" in source
    assert 'local buttons = { "b", "y", "select", "start", "up", "down", "left", "right"' in source


def test_save_manager_uses_native_defold_tables_with_json_compatibility():
    source = (ROOT / "main/save_manager.lua").read_text(encoding="utf-8")
    assert "if type(raw) == \"table\" then" in source
    assert "elseif type(raw) == \"string\" then" in source
    assert "pcall(sys.save, SAVE_FILE, M.data)" in source
    assert "pcall(sys.save, SAVE_FILE, M.encode(M.data))" not in source
