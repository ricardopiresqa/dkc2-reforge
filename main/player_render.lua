--- Glifo de debug do player (herdado da fase sem sprites).
--
-- Desde que `main.renderer` desenha o player com sprite de verdade, este modulo
-- so mantem o label antigo escondido. Ligue `M.debug = true` para trazer a letra
-- de estado de volta por cima do sprite -- util para inspecionar a state machine.

local player = require("main.player")

local M = {}

M.debug = false
M.visible = false

local LABEL = "/player_visual#player_label"

local STATE_LABELS = {
  [player.STATE.IDLE]            = "O",
  [player.STATE.RUN]             = "D",
  [player.STATE.JUMP]            = "J",
  [player.STATE.FALL]            = "F",
  [player.STATE.ROLL]            = "@",
  [player.STATE.CROUCH]          = "U",
  [player.STATE.SKID]            = "S",
  [player.STATE.CLIMB]           = "C",
  [player.STATE.SWIM]            = "W",
  [player.STATE.BARREL]          = "B",
  [player.STATE.DAMAGE]          = "X",
  [player.STATE.DEATH]           = "*",
  [player.STATE.RAMBI_RIDING]    = "R",
  [player.STATE.ENGUARDE_RIDING] = "E",
  [player.STATE.MOUNTED]         = "M",
}

function M.spawn()
  M.visible = true
  if M.debug then
    msg.post(LABEL, "enable")
  else
    msg.post(LABEL, "disable")
  end
end

function M.update(dt, camera)
  if not (M.visible and M.debug) then return end
  label.set_text(LABEL, STATE_LABELS[player.state] or "?")
  go.set_position(
    vmath.vector3(player.pos_x - camera.pos_x, player.pos_y - camera.pos_y + 40, 0.5),
    "/player_visual")
end

function M.destroy()
  M.visible = false
  msg.post(LABEL, "disable")
end

return M
