local M = {}

M.items = { "opt_1p", "opt_2p", "opt_options" }
M.selection = 1
M.show_menu = false
M.ready = false  -- set by game.lua once the opening reaches the title screen
M.blink_timer = 0
M.blink_visible = true
M.should_start = false
M.notice_text = ""
M.notice_timer = 0

function M.init()
  M.selection = 1
  M.show_menu = false
  M.blink_timer = 0
  M.blink_visible = true
  M.should_start = false
  M.notice_text = ""
  M.notice_timer = 0
  -- The original title screen (main/opening.lua) replaces the text header.
  msg.post("#title_label", "disable")
  msg.post("#prompt_label", "set_text", { text = "APERTE START" })
  msg.post("#prompt_label", "disable")
  for _, id in ipairs(M.items) do
    msg.post("#" .. id, "disable")
  end
  msg.post("#cursor_label", "disable")
end

function M.update(dt)
  if M.notice_timer > 0 then
    M.notice_timer = M.notice_timer - dt
    if M.notice_timer <= 0 then
      msg.post("#prompt_label", "set_text", { text = "APERTE START" })
    end
    return
  end

  if not M.show_menu and M.ready then
    M.blink_timer = M.blink_timer + dt
    if M.blink_timer > 0.5 then
      M.blink_timer = 0
      M.blink_visible = not M.blink_visible
      if M.blink_visible then
        msg.post("#prompt_label", "enable")
      else
        msg.post("#prompt_label", "disable")
      end
    end
  end
end

function M.on_start()
  if M.show_menu then
    if M.selection == 1 then
      M.exit()
      M.should_start = true
    elseif M.selection == 2 then
      M.exit()
      msg.post("#prompt_label", "enable")
      msg.post("#prompt_label", "set_text", { text = "2 JOGADORES: EM BREVE" })
      M.notice_timer = 2
    elseif M.selection == 3 then
      M.exit()
      msg.post("#prompt_label", "enable")
      msg.post("#prompt_label", "set_text", { text = "OPCOES: EM BREVE" })
      M.notice_timer = 2
    end
    return
  else
    M.show_menu = true
    msg.post("#prompt_label", "disable")
    msg.post("#title_label", "disable")
    for _, id in ipairs(M.items) do
      msg.post("#" .. id, "enable")
    end
    M._update_cursor()
  end
end

function M.on_up()
  if not M.show_menu then return end
  M.selection = M.selection - 1
  if M.selection < 1 then M.selection = #M.items end
  M._update_cursor()
end

function M.on_down()
  if not M.show_menu then return end
  M.selection = M.selection + 1
  if M.selection > #M.items then M.selection = 1 end
  M._update_cursor()
end

local ITEM_TEXT = { "NOVO JOGO", "2 JOGADORES", "OPCOES" }

--- Marca a opcao selecionada com um prefixo.
--
-- O cursor era um label reposicionado por go.set(..., "position", ...), que o
-- Defold nao aceita em componente (so em game object).
function M._update_cursor()
  msg.post("#cursor_label", "disable")
  for i, id in ipairs(M.items) do
    local mark = (i == M.selection) and "> " or "  "
    msg.post("#" .. id, "set_text", { text = mark .. ITEM_TEXT[i] })
  end
end

function M.exit()
  M.show_menu = false
  for _, id in ipairs(M.items) do
    msg.post("#" .. id, "disable")
  end
  msg.post("#cursor_label", "disable")
end

--- Some com tudo do titulo, inclusive o cabecalho e o "PRESS START".
function M.hide()
  M.exit()
  M.notice_timer = 0
  msg.post("#title_label", "disable")
  msg.post("#prompt_label", "disable")
end

return M
