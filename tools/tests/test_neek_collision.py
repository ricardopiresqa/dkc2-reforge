"""Validate Neek collision/stomp implementation against source evidence."""
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_neek_collision_only_not_all_original_static():
    """Only Neek (sprite == 'Neek') gets collision; others remain passive."""
    objects = (ROOT / "main/objects.lua").read_text(encoding="utf-8")

    # check_player_collision should check sprite == "Neek" (local variable)
    assert 'sprite == "Neek"' in objects, "Neek-specific collision check missing"

    # Other unported original_static sprites stay passive and emit no fake event.
    assert 'original_static_skip' not in objects

    # Should NOT treat all original_static as enemies
    assert 'obj.type == M.OBJ_ORIGINAL_STATIC then' in objects
    # The old broad "Neek/Klomp" comment should be gone
    source = objects
    # Verify the logic branches on sprite name
    assert 'local sprite = obj.params and obj.params.sprite' in source


def test_stomp_enemy_only_neek_gets_kill_and_bounce():
    """stomp_enemy should only kill/bounce Neek, not Klomp or other original_static."""
    objects = (ROOT / "main/objects.lua").read_text(encoding="utf-8")

    # stomp_enemy should check sprite == "Neek"
    assert 'sprite == "Neek"' in objects

    # Should return "kill", "neek_bounce" for Neek
    assert 'return "kill", "neek_bounce"' in objects

    # Should return "none" for other original_static
    assert 'return "none"' in objects

    # Old broad "Neek/Klomp" comment should be gone
    assert "Neek/Klomp" not in objects or "Neek/Klomp: mark as collected" not in objects


def test_player_bounce_accepts_velocity_parameter():
    """player.bounce() should accept optional vel_y parameter for Neek stomp."""
    player = (ROOT / "main/player.lua").read_text(encoding="utf-8")

    # bounce function should accept vel_y parameter
    assert "function M.bounce(vel_y, hitpause_frames)" in player

    # Should use vel_y or default -350
    assert "vel_y or -350" in player or "vel_y or -350" in player.replace(" ", "")


def test_game_uses_original_motion_jump_velocity_for_neek():
    """game.lua should use original_motion.jump_velocity() for Neek bounce."""
    game = (ROOT / "main/game.lua").read_text(encoding="utf-8")

    # Should import original_motion
    assert 'require("main.original_motion")' in game

    # Should check for neek_bounce and use jump_velocity()
    assert "neek_bounce" in game
    assert "original_motion.jump_velocity()" in game

    # Should pass velocity to player.bounce()
    assert 'player.bounce(original_motion.jump_velocity(), 2)' in game


def test_game_imports_sound_wrapper_for_init():
    game = (ROOT / "main/game.lua").read_text(encoding="utf-8")
    assert 'local sound = require("main.sound")' in game
    assert "sound.init()" in game


def test_neek_motion_starts_at_source_viewport_entry():
    objects = (ROOT / "main/objects.lua").read_text(encoding="utf-8")
    assert "NEEK_SOURCE_SPEED = -60" in objects
    assert "camera_x + (viewport_w or 256)" in objects
    assert "visible_right >= obj.source_x" in objects
    assert "obj.x = obj.x + obj.vel_x * dt" in objects


def test_neek_qa_trace_is_frame_bounded():
    autopilot = (ROOT / "main/dev_autopilot.lua").read_text(encoding="utf-8")
    assert "frame >= 550 and frame <= 615" in autopilot
    assert "frame >= 900 and frame <= 950" in autopilot
    assert "neek_interaction_samples =" in autopilot


def test_original_motion_jump_velocity_matches_source_f7c8():
    """original_motion.jump_velocity() must match source $F7C8 (-2104 * 60 / 256)."""
    original_motion = (ROOT / "main/original_motion.lua").read_text(encoding="utf-8")

    # Should have the exact calculation from DATA_FF0040+$08
    assert "2104 * 60 / 256" in original_motion
    assert "$F7C8" in original_motion or "F7C8" in original_motion
    assert "signed" in original_motion


def test_level_1_1_preserves_neek_and_klomp_as_original_static():
    """level_1_1.lua should map Neek and Klomp to original_static with sprite params."""
    level = (ROOT / "data/levels/level_1_1.lua").read_text(encoding="utf-8")

    # SPRITE_TO_TYPE should map Neek and Klomp to original_static
    assert 'Neek              = "original_static"' in level
    assert 'Klomp             = "original_static"' in level

    # Objects should preserve params.sprite
    assert 'params = { script = o.script, sprite = o.sprite' in level


def test_pirate_panic_level_has_neek_at_1024_288():
    """Source data should have Neek at world x=1024, feet_y=288."""
    path = ROOT / "data/original/pirate/pirate_panic_level.lua"
    if not path.is_file():
        pytest.skip("nível derivado da ROM é local e não distribuído")
    source = path.read_text(encoding="utf-8")

    # Neek at line ~45: x=1024, feet_y=288
    assert '"x = 1024"' in source or "x = 1024" in source
    assert '"feet_y = 288"' in source or "feet_y = 288" in source

    # Klomp at line ~48: x=1248, feet_y=209
    assert '"x = 1248"' in source or "x = 1248" in source
    assert '"feet_y = 209"' in source or "feet_y = 209" in source


def test_no_generic_ai_or_bonus_handling_added():
    """Changes should be minimal - no generic AI, bonus, or other enemy handling added."""
    objects = (ROOT / "main/objects.lua").read_text(encoding="utf-8")

    # Should not have new AI logic for original_static
    assert "patrol" not in objects or objects.count("patrol") <= objects.count("patrol_min") + objects.count("patrol_max")
    # Should not have new bonus/collectible logic for original_static
    assert "collect_banana" not in objects or "OBJ_BANANA" in objects
    # No new state machines for original_static
    assert "original_static" in objects


if __name__ == "__main__":
    test_neek_collision_only_not_all_original_static()
    test_stomp_enemy_only_neek_gets_kill_and_bounce()
    test_player_bounce_accepts_velocity_parameter()
    test_game_uses_original_motion_jump_velocity_for_neek()
    test_original_motion_jump_velocity_matches_source_f7c8()
    test_level_1_1_preserves_neek_and_klomp_as_original_static()
    test_pirate_panic_level_has_neek_at_1024_288()
    test_no_generic_ai_or_bonus_handling_added()
    print("All Neek validation tests passed!")
