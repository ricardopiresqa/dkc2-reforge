local M = {}

M.visible = false
M.active = false
M.elapsed = 0
M.best_times = {}
M.selection = 1
M.blink_timer = 0
M.blink_visible = true
M.should_exit = false
M.should_restart = false
M.level_list = {}
M.selected_level = nil

function M.init()
  M.visible = false
  M.active = false
  M.elapsed = 0
  M.best_times = {}
  M.selection = 1
  M.should_exit = false
  M.should_restart = false
  M.selected_level = nil
  msg.post("#ta_header", "disable")
  msg.post("#ta_timer", "disable")
  msg.post("#ta_list", "disable")
  msg.post("#ta_cursor", "disable")
  msg.post("#ta_footer", "disable")
end

function M.show(levels)
  M.level_list = levels or {
    "level_1_1", "level_1_2", "level_2_1", "level_2_2",
    "level_3_1", "level_4_1", "level_5_1",
  }
  M.selection = 1
  M.visible = true
  M.active = false
  M.should_exit = false
  M.should_restart = false
  M.blink_timer = 0
  msg.post("#ta_header", "enable")
  msg.post("#ta_list", "enable")
  msg.post("#ta_footer", "enable")
  M._update_list()
end

function M.hide()
  M.visible = false
  M.active = false
  msg.post("#ta_header", "disable")
  msg.post("#ta_timer", "disable")
  msg.post("#ta_list", "disable")
  msg.post("#ta_cursor", "disable")
  msg.post("#ta_footer", "disable")
end

function M._update_list()
  local lines = {}
  for i, level_id in ipairs(M.level_list) do
    local map_key = _get_map_key(level_id)
    local best = M.best_times[level_id]
    local time_str = best and string.format("%.2f", best) or "--:--"
    local mark = (i == M.selection) and "> " or "  "
    lines[#lines + 1] = mark .. map_key .. "  BEST: " .. time_str
  end
  msg.post("#ta_list", "set_text", { text = table.concat(lines, "\n") })
end

function _get_map_key(level_id)
  local map = {
    level_1_1 = "1-1", level_1_2 = "1-2",
    level_2_1 = "2-1", level_2_2 = "2-2",
    level_3_1 = "3-1", level_4_1 = "4-1",
    level_5_1 = "5-1",
  }
  return map[level_id] or level_id
end

function M.start_level(level_module)
  M.selected_level = level_module
  M.active = true
  M.elapsed = 0
  M.visible = false
  M.hide()
end

function M.update(dt)
  if M.active then
    M.elapsed = M.elapsed + dt
  end
  if not M.visible then return end
  M.blink_timer = M.blink_timer + dt
  if M.blink_timer > 0.5 then
    M.blink_timer = 0
    M.blink_visible = not M.blink_visible
  end
end

function M.on_up()
  if not M.visible or M.active then return end
  M.selection = M.selection - 1
  if M.selection < 1 then M.selection = #M.level_list end
  M._update_cursor()
end

function M.on_down()
  if not M.visible or M.active then return end
  M.selection = M.selection + 1
  if M.selection > #M.level_list then M.selection = 1 end
  M._update_cursor()
end

function M.on_confirm()
  if not M.visible or M.active then return end
  M.should_exit = true
end

--- A selecao e um prefixo na propria lista (label nao aceita reposicionamento).
function M._update_cursor()
  msg.post("#ta_cursor", "disable")
  M._update_list()
end

function M.record_time(level_id)
  if not M.active then return end
  M.active = false
  local prev = M.best_times[level_id]
  if not prev or M.elapsed < prev then
    M.best_times[level_id] = M.elapsed
  end
end

function M.get_time()
  if not M.active then return 0 end
  return M.elapsed
end

return M
