import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
REPLAY_PATH = ROOT / "tools/replay-compare/replay_camera_offline.py"
CAPTURE = ROOT / "assets-raw/pirate/reference-camera-kernel.csv"
local_capture = pytest.mark.skipif(not CAPTURE.is_file(),
                                   reason="capturas originais são locais e não distribuídas")


def load_replay():
    pytest.importorskip("lupa")
    spec = importlib.util.spec_from_file_location("replay_camera_offline", REPLAY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_camera_is_source_derived_not_trace_playback():
    source = (ROOT / "main/original_camera.lua").read_text()
    assert "reference-camera.csv" not in source
    assert "reference-gameplay.csv" not in source


def test_camera_comparison_rejects_clock_context_mismatch():
    source = (ROOT / "tools/replay-compare/compare_camera_checkpoints.py").read_text()
    assert "original clock context is missing/different" in source


def test_spring_limit_sign_and_step_clamp():
    lua, camera = load_replay().load_runtime()
    assert camera.check_damping()

    def step(target, position, velocity, new_target):
        axis = lua.table_from({"target": target, "position": position, "velocity": velocity})
        camera.spring(axis, new_target, 96)
        return axis.velocity, axis.position

    assert step(1000, 1000, 300, 1000) == (0, 1000)        # EEB1 zero limit stops the axis
    assert step(1000, 1000, -300, 1100) == (-147, 853)     # (-300 + 100>>4) halved: opposite sign
    assert step(0, 0, 4000, 100000) == (4096, 2048)        # ED92 caps the step, not velocity


@local_capture
def test_camera_replay_matches_original_every_frame():
    report = load_replay().replay()
    assert report["status"] == "PASS", report["failures"][:5]
    assert report["exact_frames"] == report["frames"] == 1033


@local_capture
def test_camera_replay_discriminates_missing_hitstop():
    report = load_replay().replay(hitstop=False)
    frames = {failure["frame"] for failure in report["failures"]}
    assert frames and frames <= set(range(566, 571)) | set(range(938, 946))


def test_camera_profile_uses_original_region_links_and_bounds():
    evidence = [ROOT / "assets-raw/pirate/reference-snapshot-report.json",
                ROOT / "data/original/pirate/camera_profile.lua"]
    if not all(path.is_file() for path in evidence):
        pytest.skip("perfil/evidência derivados da ROM são locais e não distribuídos")
    report = json.loads((ROOT / "assets-raw/pirate/reference-snapshot-report.json").read_text())
    profile = (ROOT / "assets-raw/pirate/camera_profile.lua").read_text()
    assert len(report["camera_regions"]) == 18
    assert "{512,696,360,592,772,1,0,0,2}" in profile
    assert "Soft" not in profile  # actual raw flags and links are preserved verbatim
