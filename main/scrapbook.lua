local M = {}
local save_manager = require("main.save_manager")

M.visible = false
M.selection = 1
M.blink_timer = 0
M.blink_visible = true
M.should_exit = false
M.pages = { "stats", "dk_coins", "bosses" }
M.current_page = 1

local LABEL_IDS = {
  "sb_stat_1", "sb_stat_2", "sb_stat_3", "sb_stat_4", "sb_stat_5",
}

function M.init()
  M.visible = false
  M.selection = 1
  M.current_page = 1
  M.blink_timer = 0
  M.blink_visible = true
  M.should_exit = false
  msg.post("#sb_header", "disable")
  msg.post("#sb_content", "disable")
  msg.post("#sb_cursor", "disable")
  msg.post("#sb_footer", "disable")
  for _, id in ipairs(LABEL_IDS) do
    msg.post("#" .. id, "disable")
  end
end

function M.show()
  M.visible = true
  M.selection = 1
  M.current_page = 1
  M.blink_timer = 0
  M.should_exit = false
  msg.post("#sb_header", "enable")
  msg.post("#sb_content", "enable")
  msg.post("#sb_cursor", "enable")
  msg.post("#sb_footer", "enable")
  M._update_page()
end

function M.hide()
  M.visible = false
  msg.post("#sb_header", "disable")
  msg.post("#sb_content", "disable")
  msg.post("#sb_cursor", "disable")
  msg.post("#sb_footer", "disable")
  for _, id in ipairs(LABEL_IDS) do
    msg.post("#" .. id, "disable")
  end
end

local function _world_coin_count(world)
  local count = 0
  for i = 1, 5 do
    local level_id = world .. "-" .. i
    if save_manager.has_dk_coin(level_id) then count = count + 1 end
  end
  return count
end

function M._update_page()
  if M.current_page == 1 then
    -- Stats page
    local lives = save_manager.get_lives()
    local bananas = save_manager.get_bananas()
    local dk_coins = save_manager.get_dk_coins()
    local score = save_manager.get_score()
    local completed = 0
    for i = 1, 30 do
      if save_manager.is_level_completed(tostring(i)) then completed = completed + 1 end
    end
    msg.post("#sb_content", "enable")
    msg.post("#sb_content", "set_text", { text =
      "LIVES: " .. lives .. "\n" ..
      "BANANAS: " .. bananas .. "\n" ..
      "DK COINS: " .. dk_coins .. "\n" ..
      "SCORE: " .. score .. "\n" ..
      "LEVELS COMPLETE: " .. completed })
  elseif M.current_page == 2 then
    -- DK Coins page
    msg.post("#sb_content", "enable")
    msg.post("#sb_content", "set_text", { text =
      "=== DK COINS COLLECTED ===\n" ..
      "World 1: " .. _world_coin_count(1) .. "/5\n" ..
      "World 2: " .. _world_coin_count(2) .. "/5\n" ..
      "World 3: " .. _world_coin_count(3) .. "/5\n" ..
      "World 4: " .. _world_coin_count(4) .. "/5\n" ..
      "World 5: " .. _world_coin_count(5) .. "/5\n" ..
      "Lost World: " .. _world_coin_count(6) .. "/5" })
  elseif M.current_page == 3 then
    -- Bosses page
    local boss_status = {}
    for _, boss_id in ipairs({"B-1", "B-2", "B-3", "B-4", "B-5", "B-6"}) do
      local done = save_manager.is_level_completed(boss_id)
      boss_status[#boss_status + 1] = boss_id .. ": " .. (done and "DEFEATED" or "PENDING")
    end
    msg.post("#sb_content", "enable")
    msg.post("#sb_content", "set_text", { text = "=== BOSS STATUS ===\n" .. table.concat(boss_status, "\n") })
  end
end

function M.update(dt)
  if not M.visible then return end
  M.blink_timer = M.blink_timer + dt
  if M.blink_timer > 0.5 then
    M.blink_timer = 0
    M.blink_visible = not M.blink_visible
    if M.blink_visible then
      msg.post("#sb_footer", "enable")
    else
      msg.post("#sb_footer", "disable")
    end
  end
end

function M.on_up()
  if not M.visible then return end
  M.current_page = M.current_page - 1
  if M.current_page < 1 then M.current_page = #M.pages end
  M._update_page()
end

function M.on_down()
  if not M.visible then return end
  M.current_page = M.current_page + 1
  if M.current_page > #M.pages then M.current_page = 1 end
  M._update_page()
end

function M.on_confirm()
  if not M.visible then return end
  M.should_exit = true
end

return M
