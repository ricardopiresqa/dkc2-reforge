local M = {}

M.visible = false
M.selection = 1
M.should_continue = false
M.should_quit = false
M.blink_timer = 0

local ITEMS = { "continue", "quit" }

function M.init()
  M.visible = false
  M.selection = 1
  M.should_continue = false
  M.should_quit = false
  M.blink_timer = 0
  msg.post("#go_overlay", "disable")
  msg.post("#go_header", "disable")
  msg.post("#go_stats", "disable")
  msg.post("#go_cursor", "disable")
  msg.post("#go_footer", "disable")
  for _, id in ipairs(ITEMS) do
    msg.post("#go_" .. id, "disable")
  end
end

function M.show()
  M.visible = true
  M.selection = 1
  M.should_continue = false
  M.should_quit = false
  M.blink_timer = 0
  msg.post("#go_overlay", "enable")
  msg.post("#go_header", "enable")
  msg.post("#go_stats", "enable")
  msg.post("#go_footer", "enable")
  for _, id in ipairs(ITEMS) do
    msg.post("#go_" .. id, "enable")
  end
  M._update_cursor()
end

function M.hide()
  M.visible = false
  msg.post("#go_overlay", "disable")
  msg.post("#go_header", "disable")
  msg.post("#go_stats", "disable")
  msg.post("#go_cursor", "disable")
  msg.post("#go_footer", "disable")
  for _, id in ipairs(ITEMS) do
    msg.post("#go_" .. id, "disable")
  end
end

function M.update(dt)
  if not M.visible then return end
  M.blink_timer = M.blink_timer + dt
  if M.blink_timer > 0.5 then
    M.blink_timer = 0
  end
end

function M.on_up()
  if not M.visible then return end
  M.selection = M.selection - 1
  if M.selection < 1 then M.selection = #ITEMS end
  M._update_cursor()
end

function M.on_down()
  if not M.visible then return end
  M.selection = M.selection + 1
  if M.selection > #ITEMS then M.selection = 1 end
  M._update_cursor()
end

function M.on_confirm()
  if not M.visible then return end
  if M.selection == 1 then
    M.should_continue = true
  else
    M.should_quit = true
  end
end

local ITEM_TEXT = { "CONTINUE", "QUIT TO TITLE" }

--- Marca a opcao selecionada com um prefixo (label nao aceita reposicionamento).
function M._update_cursor()
  msg.post("#go_cursor", "disable")
  for i, id in ipairs(ITEMS) do
    local mark = (i == M.selection) and "> " or "  "
    msg.post("#go_" .. id, "set_text", { text = mark .. ITEM_TEXT[i] })
  end
end

return M
