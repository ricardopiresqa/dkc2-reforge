--- Desenha o HUD nos labels declarados em main.collection.
--
-- Só escreve num label quando o texto muda, para não recriar a malha de
-- glifos a cada frame.

local hud = require("main.hud")
local player = require("main.player")
local level_loader = require("main.level_loader")

local M = {}

local IDS = {
  "hud_level", "hud_lives", "hud_bananas",
  "hud_coins", "hud_score", "hud_kong", "hud_breath",
}

local last = {}
M.visible = false

local function set(id, text)
  if last[id] == text then return end
  last[id] = text
  label.set_text("#" .. id, text)
end

function M.show()
  M.visible = true
  for _, id in ipairs(IDS) do
    -- Prototype counters/score are not the original transient icon HUD.
    msg.post("#" .. id, level_loader.original_semantics() and "disable" or "enable")
  end
end

function M.hide()
  M.visible = false
  for _, id in ipairs(IDS) do
    msg.post("#" .. id, "disable")
  end
  M.clear_banner()
end

--- Mensagem grande no centro da tela (PAUSED, LEVEL COMPLETE, nome do boss...).
function M.banner(text)
  set("banner_label", text or "")
  msg.post("#banner_label", "enable")
end

function M.clear_banner()
  set("banner_label", "")
  msg.post("#banner_label", "disable")
end

local function kong_text()
  local out = {}
  for _, letter in ipairs({ "K", "O", "N", "G" }) do
    out[#out + 1] = hud.kong_letters[letter] and letter or "-"
  end
  return "KONG " .. table.concat(out)
end

function M.update()
  if not M.visible then return end

  set("hud_level", string.format("%s  %s", level_loader.get_id(), level_loader.get_name()))
  set("hud_lives", string.format("LIVES %d", hud.lives))
  set("hud_bananas", string.format("BANANAS %d", hud.bananas))
  set("hud_coins", string.format("DK COINS %d", hud.dk_coins))
  set("hud_score", string.format("SCORE %d", hud.score))
  set("hud_kong", kong_text())

  local hearts = string.rep("#", math.max(0, player.health))
      .. string.rep(".", math.max(0, 3 - player.health))
  if level_loader.original_semantics() then
    -- semantica original: sem HP numerico nem AIR (invencoes do prototipo)
    set("hud_breath", "")
  elseif hud.is_swimming then
    set("hud_breath", string.format("HP %s   AIR %d%%", hearts,
        math.floor((player.breath or 0) + 0.5)))
  else
    set("hud_breath", string.format("HP %s", hearts))
  end
end

return M
