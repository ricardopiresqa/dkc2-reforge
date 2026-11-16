local M = {}
local save_manager = require("main.save_manager")

local function _get_map_key(level_id)
  local map = {
    level_1_1 = "1-1",
    level_1_2 = "1-2",
    level_1_3 = "1-3",
    level_1_4 = "1-4",
    level_1_5 = "1-5",
    level_forest = "F-1",
    test_water = "T-1",
    level_2_1 = "2-1",
    level_2_2 = "2-2",
    level_2_3 = "2-3",
    level_2_4 = "2-4",
    level_2_5 = "2-5",
    level_3_1 = "3-1",
    level_3_2 = "3-2",
    level_3_3 = "3-3",
    level_3_4 = "3-4",
    level_3_5 = "3-5",
    level_4_1 = "4-1",
    level_4_2 = "4-2",
    level_4_3 = "4-3",
    level_4_4 = "4-4",
    level_4_5 = "4-5",
    level_5_1 = "5-1",
    level_5_2 = "5-2",
    level_5_3 = "5-3",
    level_5_4 = "5-4",
    level_5_5 = "5-5",
    boss_krow   = "B-1",
    boss_kleaver = "B-2",
    boss_zing    = "B-3",
    boss_kreep   = "B-4",
    boss_krool1  = "B-5",
    boss_krool2  = "B-6",
    level_6_1 = "6-1",
    level_6_2 = "6-2",
    level_6_3 = "6-3",
    level_6_4 = "6-4",
    level_6_5 = "6-5",
  }
  return map[level_id] or level_id
end

local function _update_lock_states()
  for _, level in ipairs(M.levels) do
    if level.id == "level_1_1" then
      level.locked = false
    elseif level.id == "level_1_2" then
      level.locked = not save_manager.is_level_completed("1-1")
    elseif level.id == "level_1_3" then
      level.locked = not save_manager.is_level_completed("1-2")
    elseif level.id == "level_1_4" then
      level.locked = not save_manager.is_level_completed("1-3")
    elseif level.id == "level_1_5" then
      level.locked = not save_manager.is_level_completed("1-4")
    elseif level.id == "level_forest" then
      level.locked = not save_manager.is_level_completed("1-2")
    elseif level.id == "level_2_1" then
      level.locked = not save_manager.is_level_completed("1-1")
    elseif level.id == "level_2_2" then
      level.locked = not save_manager.is_level_completed("2-1")
    elseif level.id == "level_2_3" then
      level.locked = not save_manager.is_level_completed("2-2")
    elseif level.id == "level_2_4" then
      level.locked = not save_manager.is_level_completed("2-3")
    elseif level.id == "level_2_5" then
      level.locked = not save_manager.is_level_completed("2-4")
    elseif level.id == "level_3_1" then
      level.locked = not save_manager.is_level_completed("2-2")
    elseif level.id == "level_3_2" then
      level.locked = not save_manager.is_level_completed("3-1")
    elseif level.id == "level_3_3" then
      level.locked = not save_manager.is_level_completed("3-2")
    elseif level.id == "level_3_4" then
      level.locked = not save_manager.is_level_completed("3-3")
    elseif level.id == "level_3_5" then
      level.locked = not save_manager.is_level_completed("3-4")
    elseif level.id == "level_4_1" then
      level.locked = not save_manager.is_level_completed("B-1")
    elseif level.id == "level_4_2" then
      level.locked = not save_manager.is_level_completed("4-1")
    elseif level.id == "level_4_3" then
      level.locked = not save_manager.is_level_completed("4-2")
    elseif level.id == "level_4_4" then
      level.locked = not save_manager.is_level_completed("4-3")
    elseif level.id == "level_4_5" then
      level.locked = not save_manager.is_level_completed("4-4")
    elseif level.id == "level_5_1" then
      level.locked = not (save_manager.is_level_completed("2-5") and save_manager.is_level_completed("3-5") and save_manager.is_level_completed("4-5"))
    elseif level.id == "level_5_2" then
      level.locked = not save_manager.is_level_completed("5-1")
    elseif level.id == "level_5_3" then
      level.locked = not save_manager.is_level_completed("5-2")
    elseif level.id == "level_5_4" then
      level.locked = not save_manager.is_level_completed("5-3")
    elseif level.id == "level_5_5" then
      level.locked = not save_manager.is_level_completed("5-4")
    elseif level.id == "boss_krow" then
      level.locked = not (save_manager.is_level_completed("1-5") and save_manager.has_dk_coin("1-5"))
    elseif level.id == "boss_kleaver" then
      level.locked = not save_manager.is_level_completed("2-5")
    elseif level.id == "boss_zing" then
      level.locked = not save_manager.is_level_completed("3-5")
    elseif level.id == "boss_kreep" then
      level.locked = not save_manager.is_level_completed("4-5")
    elseif level.id == "boss_krool1" then
      level.locked = not (save_manager.is_level_completed("5-4") and save_manager.is_level_completed("B-4"))
    elseif level.id == "boss_krool2" then
      level.locked = not save_manager.is_level_completed("B-5")
    elseif level.id == "level_6_1" then
      level.locked = not (save_manager.is_level_completed("B-1") and save_manager.get_dk_coins() >= 3)
    elseif level.id == "level_6_2" then
      level.locked = not (save_manager.is_level_completed("6-1") and save_manager.get_dk_coins() >= 6)
    elseif level.id == "level_6_3" then
      level.locked = not (save_manager.is_level_completed("6-2") and save_manager.get_dk_coins() >= 9)
    elseif level.id == "level_6_4" then
      level.locked = not (save_manager.is_level_completed("6-3") and save_manager.get_dk_coins() >= 12)
    elseif level.id == "level_6_5" then
      level.locked = not (save_manager.is_level_completed("6-4") and save_manager.get_dk_coins() >= 15)
    end
  end
end

M.levels = {
  { id = "level_1_1", name = "1-1 JUNGLE HIJINKS", locked = false },
  { id = "level_1_2", name = "1-2 KROCK'S QUARRY", locked = false },
  { id = "level_1_3", name = "1-3 LOCKJAW'S LOCKER", locked = true },
  { id = "level_1_4", name = "1-4 TOPSAIL TROUBLE", locked = true },
  { id = "level_1_5", name = "1-5 KROW'S NEST APPROACH", locked = true },
  { id = "test_water", name = "T-1 WATER TEST", locked = false },
  { id = "level_forest", name = "F-1 KREMWOOD FOREST", locked = true },
  { id = "level_2_1", name = "2-1 CROCODILE CAULDRON", locked = true },
  { id = "level_2_2", name = "2-2 KREMTOWN", locked = true },
  { id = "level_2_3", name = "2-3 RICKETY RIDE", locked = true },
  { id = "level_2_4", name = "2-4 SLIPPERY SLOPE", locked = true },
  { id = "level_2_5", name = "2-5 BELOW THE BELT", locked = true },
  { id = "level_3_1", name = "3-1 WEB WOODS", locked = true },
  { id = "level_3_2", name = "3-2 SPIDERS' WEB", locked = true },
  { id = "level_3_3", name = "3-3 KREMLING QUARRY", locked = true },
  { id = "level_3_4", name = "3-4 SWAMPY SLOG", locked = true },
  { id = "level_3_5", name = "3-5 CAVE DWELLERS", locked = true },
  { id = "level_4_1", name = "4-1 SHIPWRECK COVE", locked = true },
  { id = "level_4_2", name = "4-2 KANNON'S ALLEY", locked = true },
  { id = "level_4_3", name = "4-3 LOOPY LIGHTHOUSE", locked = true },
  { id = "level_4_4", name = "4-4 TIDAL TROUBLE", locked = true },
  { id = "level_4_5", name = "4-5 GANGPLANK GULCH", locked = true },
  { id = "level_5_1", name = "5-1 SKULL'S ROCK", locked = true },
  { id = "level_5_2", name = "5-2 KREMLATOA KLIFF", locked = true },
  { id = "level_5_3", name = "5-3 POISONOUS PEAK", locked = true },
  { id = "level_5_4", name = "5-4 DIRE DIKES", locked = true },
  { id = "level_5_5", name = "5-5 KREMLING'S END", locked = true },
  { id = "boss_krow",   name = "B-1 KROW'S NEST",       locked = true },
  { id = "boss_kleaver", name = "B-2 KLEAVER'S RAID",    locked = true },
  { id = "boss_zing",    name = "B-3 KING ZING'S HIVE",  locked = true },
  { id = "boss_kreep",   name = "B-4 KREEP'S KEEP",      locked = true },
  { id = "boss_krool1",  name = "B-5 K.ROOL'S SHOWDOWN", locked = true },
  { id = "boss_krool2",  name = "B-6 K.ROOL'S REVENGE",  locked = true },
  { id = "level_6_1",    name = "6-1 KREMLING KRUSADE",  locked = true },
  { id = "level_6_2",    name = "6-2 ABYSSAL ABYSS",     locked = true },
  { id = "level_6_3",    name = "6-3 CAVERN OF CHAOS",   locked = true },
  { id = "level_6_4",    name = "6-4 TOWERING TROUBLE",  locked = true },
  { id = "level_6_5",    name = "6-5 THE FINAL FRONTIER",locked = true },
}

M.selection = 1
M.visible = false
M.blink_timer = 0
M.blink_visible = true
M.should_load = false
M.should_back = false
M.should_scrapbook = false
M.should_time_attack = false
M.selected_level = nil

local LABEL_IDS = {
  "ls_item_1", "ls_item_2", "ls_item_3", "ls_item_4", "ls_item_5",
  "ls_item_6", "ls_item_7", "ls_item_8", "ls_item_9", "ls_item_10",
  "ls_item_11", "ls_item_12", "ls_item_13", "ls_item_14", "ls_item_15",
  "ls_item_16", "ls_item_17", "ls_item_18", "ls_item_19", "ls_item_20",
  "ls_item_21", "ls_item_22", "ls_item_23", "ls_item_24", "ls_item_25",
  "ls_item_26", "ls_item_27", "ls_item_28", "ls_item_29", "ls_item_30",
  "ls_item_31", "ls_item_32", "ls_item_33", "ls_item_34", "ls_item_35",
  "ls_item_36", "ls_item_37", "ls_item_38",
}

function M.init()
  M.selection = 1
  M.visible = false
  M.blink_timer = 0
  M.blink_visible = true
  M.should_load = false
  M.should_back = false
  M.should_scrapbook = false
  M.should_time_attack = false
  M.selected_level = nil
  msg.post("#level_select_header", "disable")
  msg.post("#ls_cursor", "disable")
  for _, id in ipairs(LABEL_IDS) do
    msg.post("#" .. id, "disable")
  end
end

function M.show()
  _update_lock_states()
  M.selection = 1
  M.visible = true
  M.should_load = false
  M.should_back = false
  M.should_scrapbook = false
  M.should_time_attack = false
  M.selected_level = nil
  M.blink_timer = 0
  M.blink_visible = true

  M.scroll = 0
  msg.post("#level_select_header", "enable")
  msg.post("#ls_cursor", "disable")   -- a selecao agora e um prefixo no texto
  M._update_cursor()
end

function M.hide()
  M.visible = false
  msg.post("#level_select_header", "disable")
  msg.post("#ls_cursor", "disable")
  for _, id in ipairs(LABEL_IDS) do
    msg.post("#" .. id, "disable")
  end
end

function M.update(dt)
  if not M.visible then return end
  M.blink_timer = M.blink_timer + dt
  if M.blink_timer > 0.5 then
    M.blink_timer = 0
    M.blink_visible = not M.blink_visible
    if M.blink_visible then
      msg.post("#level_select_header", "enable")
    else
      msg.post("#level_select_header", "disable")
    end
  end
end

function M.on_up()
  if not M.visible then return end
  M.selection = M.selection - 1
  if M.selection < 1 then M.selection = #M.levels end
  M._update_cursor()
end

function M.on_down()
  if not M.visible then return end
  M.selection = M.selection + 1
  if M.selection > #M.levels then M.selection = 1 end
  M._update_cursor()
end

function M.on_confirm()
  if not M.visible then return end
  local level = M.levels[M.selection]
  if level and not level.locked then
    M.selected_level = level.id
    M.should_load = true
  end
end

function M.on_back()
  if not M.visible then return end
  M.should_back = true
end

-- Quantas linhas cabem na tela. Existem 38 labels, mas so as primeiras 24 ficam
-- dentro do viewport (y 540 -> 80, passo 20); as demais tem y negativo. Por isso
-- a lista rola uma janela em vez de tentar mostrar tudo de uma vez.
local VISIBLE_ROWS = 24
M.scroll = 0

--- Reescreve os labels visiveis a partir de M.scroll, marcando a selecao.
--
-- O cursor era um label reposicionado com go.set(..., "position", ...), que o
-- Defold nao aceita em componente. Agora ele e um prefixo no texto da linha.
function M._render()
  for i, id in ipairs(LABEL_IDS) do
    local level = M.levels[M.scroll + i]
    if i <= VISIBLE_ROWS and level then
      local mark = (M.scroll + i == M.selection) and "> " or "  "
      local lock = level.locked and "  [LOCKED]" or ""
      msg.post("#" .. id, "set_text", { text = mark .. level.name .. lock })
      msg.post("#" .. id, "enable")
    else
      msg.post("#" .. id, "disable")
    end
  end
end

--- Mantem a selecao dentro da janela visivel e redesenha.
function M._update_cursor()
  local max_scroll = math.max(0, #M.levels - VISIBLE_ROWS)
  if M.selection <= M.scroll then
    M.scroll = M.selection - 1
  elseif M.selection > M.scroll + VISIBLE_ROWS then
    M.scroll = M.selection - VISIBLE_ROWS
  end
  M.scroll = math.max(0, math.min(M.scroll, max_scroll))
  M._render()
end

return M
