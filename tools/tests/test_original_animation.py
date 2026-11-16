import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / "tools/replay-compare/export_animation_scripts.py"
spec = importlib.util.spec_from_file_location("animation_export", path)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_original_walk_and_jump_script_opcodes_not_guessed_fps():
    rom_path = module.SOURCE / "Donkey Kong Country 2 (USA V1.0).sfc"
    if not rom_path.is_file():
        pytest.skip("ROM/disassembly local não distribuído")
    rom = rom_path.read_bytes()
    walk = module.script(rom, 3)
    assert walk["start"] == 0x1B62 and walk["status"] == "exported"
    poses = [op for op in walk["code"].values() if op["op"] < 128]
    assert [op["arg"] for op in poses] == list(range(0x3B8, 0x3F8, 4))
    assert all(op["op"] == 2 for op in poses)
    jump = module.script(rom, 6)
    assert jump["start"] == 0x1D17 and jump["flags"] == 0x3000
    assert jump["code"][0x1D17] == {"op": 0x84, "arg": 0xDEC3, "next": 0x1D1A}
    assert any(op["op"] == 0x83 and op["arg"] == 0xD5A6 for op in jump["code"].values())


def test_capture_snapshots_not_driving_production_animation():
    runtime = (ROOT / "main/original_animation.lua").read_text(encoding="utf-8")
    assert 'require("data.original.pirate.animation_scripts")' in runtime
    assert "reference-poses.csv" not in runtime
    # B9D570 translated: on the ground or the floor below under $48 px
    assert "ground_distance(player.pos_x, top, w, h, 0x48)" in runtime and "distance < 0x48" in runtime
    assert "callbacks[0xDA5D] = callbacks[0]" in runtime
    assert "callbacks[0xDFE3] = callbacks[0xE0AA]" in runtime
    game = (ROOT / "main/game.lua").read_text(encoding="utf-8")
    gameplay = game.split("elseif M.phase == M.PHASE.GAMEPLAY then", 1)[1]
    assert gameplay.index("player.update(dt)") < gameplay.index("original_animation.update(player)")


def test_every_exported_script_pose_has_resource():
    import json
    evidence = ROOT / "assets-raw/pirate/animation-script-report.json"
    if not evidence.is_file():
        pytest.skip("evidência derivada da ROM é local e não distribuída")
    report = json.loads(evidence.read_text())
    poses = report["poses"]
    for identity, script in report["scripts"].items():
        assert script["status"] == "exported"
        for pc, instruction in script["code"].items():
            if instruction["op"] < 128:
                assert str(instruction["arg"]) in poses, (identity, hex(int(pc)), hex(instruction["arg"]))


def test_original_audio_does_not_substitute_prototype_sounds():
    source = (ROOT / "main/sound.lua").read_text(encoding="utf-8")
    assert "if original_semantics then return end" in source
    game = (ROOT / "main/game.lua").read_text(encoding="utf-8")
    assert "sound.set_original_semantics(level_loader.original_semantics())" in game
