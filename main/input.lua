local bit = require("bit")

local M = {}

local hold = 0
local edge = 0
local prev_hold = 0
local synthetic = nil
local stick_hold = 0  -- left stick directions, kept apart from `hold` (the d-pad's own bits)

M.BIT = {
  B       = 0,
  Y       = 1,
  SELECT  = 2,
  START   = 3,
  UP      = 4,
  DOWN    = 5,
  LEFT    = 6,
  RIGHT   = 7,
  A       = 8,
  X       = 9,
  L       = 10,
  R       = 11,
}

function M.get_hold()
  return hold
end

function M.get_edge()
  return edge
end

function M.hold_bit(b)
  return bit.band(bit.bor(hold, synthetic and 0 or stick_hold), bit.lshift(1, b)) ~= 0
end

function M.edge_bit(b)
  return bit.band(edge, bit.lshift(1, b)) ~= 0
end

--- Inicio do frame: limpa borda consumida; estado anterior persiste ate post_update.
--
-- `hold` NAO e zerado aqui: ele e o estado real das teclas, ligado em
-- `pressed` e desligado em `released`. Zerar por frame fazia `hold_bit`
-- se comportar como borda, e nenhuma tecla ficava pressionada.
function M.update()
  edge = 0
end

-- Xbox (XInput) pad, laid out like the SNES pad by position: A = SNES B (jump), X = Y
-- (run), B = A (team-up), Y = X, LB/RB = L/R, Menu = START, View = SELECT; d-pad and left
-- stick move. The stick only counts past half tilt (no drift on a loose stick).
local STICK = { [hash("stick_up")] = "UP", [hash("stick_down")] = "DOWN", [hash("stick_left")] = "LEFT",
                [hash("stick_right")] = "RIGHT" }
local STICK_ON, STICK_OFF = 0.5, 0.4  -- hysteresis: no repeated edges around the threshold

function M.on_input(action_id, action)
  local stick = action_id and STICK[action_id]
  if stick then
    local mask, value = bit.lshift(1, M.BIT[stick]), action.value or 0
    if value > STICK_ON then
      stick_hold = bit.bor(stick_hold, mask)
    elseif action.released or value < STICK_OFF then
      stick_hold = bit.band(stick_hold, bit.bnot(mask))
    end
    return
  end
  local b = M.name_to_bit[action_id]
  if b then
    if action.pressed then
      hold = bit.bor(hold, bit.lshift(1, b))
    end
    if action.released then
      hold = bit.band(hold, bit.bnot(bit.lshift(1, b)))
    end
  end
end

--- Entrada sintetica (dev_autopilot). `nil` devolve o controle ao teclado.
function M.set_synthetic(mask)
  synthetic = mask
end

function M.post_update()
  if synthetic then
    hold = synthetic
  end
  local held = synthetic and hold or bit.bor(hold, stick_hold)
  edge = bit.band(bit.bxor(held, prev_hold), held)
  -- Input callbacks can precede update(). Keep the last processed frame here.
  prev_hold = held
end

M.name_to_bit = {}
for name, b in pairs(M.BIT) do
  M.name_to_bit[hash(name:lower())] = b
end

return M
