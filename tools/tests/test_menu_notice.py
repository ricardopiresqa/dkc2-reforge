"""Source-contract checks for the title menu's temporary 2P notice."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_two_player_selection_shows_notice_and_restores_start_prompt():
    menu = (ROOT / "main/menu.lua").read_text(encoding="utf-8")
    branch_start = menu.index("elseif M.selection == 2 then")
    branch_end = menu.index("elseif M.selection == 3 then", branch_start)
    two_player_branch = menu[branch_start:branch_end]

    assert 'text = "2 JOGADORES: EM BREVE"' in two_player_branch
    assert "M.notice_timer = 2" in two_player_branch
    assert 'msg.post("#prompt_label", "enable")' in two_player_branch

    update_start = menu.index("function M.update(dt)")
    start_start = menu.index("function M.on_start()", update_start)
    notice_update = menu[update_start:start_start]
    assert 'if M.notice_timer > 0 then' in notice_update
    assert 'text = "APERTE START"' in notice_update

    game = (ROOT / "main/game.lua").read_text(encoding="utf-8")
    title_start = game.index("if current_phase == M.PHASE.TITLE then")
    select_start = game.index("elseif current_phase == M.PHASE.LEVEL_SELECT then", title_start)
    title_flow = game[title_start:select_start]
    assert "menu.on_start()" in title_flow
    assert "menu.update(dt)" in title_flow

    collection = (ROOT / "main/main.collection").read_text(encoding="utf-8")
    assert 'id: \\"prompt_label\\"' in collection
