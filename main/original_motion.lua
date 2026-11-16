-- Kong ground velocity in original 8.8 units, not a full player state machine.
-- Limits from the Kong's physics table + $0C/$0E; ease observed against same-ROM RAM trace.
-- DATA_FF0040 = Diddy, DATA_FF012A = Dixie: +$04 held-jump gravity, +$08 jump velocity,
-- +$0C walk and +$0E run maximum (gravity $70 and terminal $0800 are shared).
local M = {}
local TABLES = {
  diddy = { held_gravity = 0x005A, jump = -2104, walk = 0x0240, run = 0x0360 },  -- $F7C8
  dixie = { held_gravity = 0x0048, jump = -1848, walk = 0x0200, run = 0x0300 },  -- $F8C8
}
local kong = TABLES.diddy
M.kong_name = "diddy"
-- Terminal fall speed (the Kong struct's +$0A): $0800, $0100 while Dixie glides.
M.terminal = 0x0800

--- Leader Kong's physics table ("diddy" | "dixie").
function M.set_kong(name)
  kong, M.kong_name, M.terminal = TABLES[name] or TABLES.diddy, TABLES[name] and name or "diddy", 0x0800
end

function M.approach(raw_velocity, target)
  local delta = target - raw_velocity
  if math.abs(delta) < 8 then return target end
  local increment = math.max(1, math.floor(math.abs(delta) / 8))
  return raw_velocity + (delta < 0 and -increment or increment)
end

function M.ground_velocity(pixels_per_second, direction, running)
  local sign = pixels_per_second < 0 and -1 or 1
  local raw = math.floor(math.abs(pixels_per_second) * 256 / 60 + 0.5) * sign
  local maximum = running and kong.run or kong.walk
  return M.approach(raw, direction * maximum) * 60 / 256
end

function M.vertical_velocity(pixels_per_second, holding_jump)
  local sign = pixels_per_second < 0 and -1 or 1
  local raw = math.floor(math.abs(pixels_per_second) * 256 / 60 + 0.5) * sign
  -- Normal gravity $70, held-jump gravity (+$04), terminal $0800.
  local gravity = holding_jump and kong.held_gravity or 0x0070
  return math.min(M.terminal, raw + gravity) * 60 / 256
end

function M.jump_velocity()
  return kong.jump * 60 / 256 -- signed, table +$08
end

function M.check()
  M.set_kong("diddy")
  local speed = 0
  for _, expected in ipairs({72, 135, 190, 238, 280, 317, 349, 377}) do
    speed = M.approach(speed, 0x0240)
    assert(speed == expected, "original observed ground ramp diverged")
  end
  assert(M.approach(569, 576) == 576)
  assert(M.approach(0, -576) == -72)
  assert(M.vertical_velocity(M.jump_velocity(), true) == -2014 * 60 / 256)
  local air_velocity = 135
  for _, expected_raw in ipairs({432, 306, 196, 100, 16, -58}) do
    air_velocity = M.ground_velocity(air_velocity, -1, false)
    local raw = math.floor(math.abs(air_velocity) * 256 / 60 + 0.5)
      * (air_velocity < 0 and -1 or 1)
    assert(raw == expected_raw, "original airborne direction reversal diverged")
  end
  return true
end

return M
