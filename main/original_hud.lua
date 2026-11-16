-- DKC2 HUD state (BEC68A per frame): banana counter BEC840 and lives panel BEC70E.
-- BB9210 arms both timers to $78 on area entry. Counts are BCD like the source.
-- Pickups fly to the counter (B5F9D1) and only then raise $096D.
local M = {}

local function bcd_add(value, delta)  -- SED ; ADC on two BCD digits pairs (0-99)
  local decimal = math.floor(value / 16) * 10 + value % 16
  decimal = (decimal + delta) % 100
  return math.floor(decimal / 10) * 16 + decimal % 10
end

function M.init(lives)
  M.target, M.shown = 0, 0            -- $096D, $096B
  M.banana_timer = 0x78               -- $096F
  M.lives_timer, M.lives_slide = 0x78, 0  -- $0973, $0979
  M.flying = {}                       -- $7FD632 list of bananas flying to the counter
  if M.balloon then  -- area changed mid-flight: still a life
    lives = (lives or 4) + 1
    if M.on_life then M.on_life() end
  end
  M.lives = lives or 4                -- $08C0
  M.balloon = nil
end

--- B5F880/B5F899: a pickup re-arms the counter and launches a flying banana from its
-- screen position (clamped to $00-$F0 / $00-$E0), 8.8 velocity $40 - pos*8 per axis,
-- so it reaches the counter icon at (8, 8) after 32 steps.
function M.collect_banana(screen_positions)
  M.banana_timer = 0x3C
  for _, position in ipairs(screen_positions) do
    if #M.flying < 32 then  -- $7FD632 list holds $40 bytes
      local x = math.max(0, math.min(math.floor(position[1]), 0xF0)) * 256
      local y = math.max(0, math.min(math.floor(position[2]), 0xE0)) * 256
      M.flying[#M.flying + 1] = { x = x, y = y, vx = 0x40 - x / 32, vy = 0x40 - y / 32 }
    else
      M.target = bcd_add(M.target, 1)  -- B5F913: list full, count immediately
    end
  end
end

--- B5F9D1: move flying bananas; one arrives when Y crosses $0800 along its velocity
-- (CMP #$0800 ; ROR ; EOR vy ; BMI), adding 1 to the target count ($096D).
function M.move_flying()
  for index = #M.flying, 1, -1 do
    local banana = M.flying[index]
    banana.x, banana.y = banana.x + banana.vx, banana.y + banana.vy
    local arrived = (banana.y >= 0x0800) ~= (banana.vy < 0)
    if arrived then
      table.remove(M.flying, index)
      M.target = bcd_add(M.target, 1)
    end
  end
end

-- Extra life balloon ($178, kabin-route-t3.csv 848-885): touched, it flies in screen space
-- to (212, 40), 1/8 of the way per frame (8.8), and is gone the frame it is there.
-- APPROXIMATIONS: the life is added and the panel re-armed on arrival (the lives count
-- was not logged); the balloon keeps its float animation in flight.
local BALLOON_X, BALLOON_Y = 212, 40

function M.collect_balloon(x, y, frames)
  M.balloon = { x = x * 256, y = y * 256, frames = frames, age = 0 }
end

local function approach(value, target)
  local next_value = value + math.floor((target * 256 - value) / 8)
  if next_value == value then next_value = target * 256 end
  return next_value
end

local function update_balloon()
  local balloon = M.balloon
  if not balloon then return false end
  balloon.age = balloon.age + 1
  balloon.x, balloon.y = approach(balloon.x, BALLOON_X), approach(balloon.y, BALLOON_Y)
  if balloon.x == BALLOON_X * 256 and balloon.y == BALLOON_Y * 256 then
    M.balloon, M.lives = nil, M.lives + 1
    M.lives_timer = 0x3C  -- BEC79E: the panel shows the new count
    if M.on_life then M.on_life() end  -- the game's own count (game.lua)
  end
end

local function update_lives()
  if M.lives_timer == 0 then return end
  local timer = M.lives_timer - 1
  if timer == 0 then                  -- slide out, then hide
    local slide = M.lives_slide - 0x30
    if slide < 0 then slide, M.lives_timer = 0, 0 end
    M.lives_slide = slide
  elseif M.lives_slide < 0x200 then   -- slide in
    M.lives_slide = M.lives_slide + 0x30
  else
    M.lives_timer = M.lives_timer - 1
  end
end

--- Returns true when the counter is drawn this frame.
local function update_bananas(clock)
  if M.target == M.shown then
    if M.banana_timer == 0 then return false end
  else
    if M.banana_timer < 0x8000 then M.banana_timer = 0x3C end
    if M.target > M.shown then
      if M.shown >= 0x99 then M.shown = 0 else M.shown = bcd_add(M.shown, 1) end
    elseif clock % 4 == 0 then
      M.shown = bcd_add(M.shown, -1)
    end
  end
  M.banana_timer = M.banana_timer - 1
  return true
end

--- One BEC68A pass; returns banana_visible, lives_visible.
function M.update(clock)
  update_balloon()
  update_lives()
  M.banana_visible = update_bananas(clock)
  M.lives_visible = M.lives_timer > 0
  M.clock = clock
  return M.banana_visible, M.lives_visible
end

--- Lives panel Y (BEC7BB): (($0979 << 4) + $F000) >> 8 as a signed byte.
function M.lives_y()
  local y = math.floor(((M.lives_slide * 16 + 0xF000) % 65536) / 256)
  return y >= 128 and y - 256 or y
end

--- Digits (BCD) to draw left-to-right; hundreds/tens skipped when zero (BEC8D2).
function M.banana_digits()
  local tens, ones = math.floor(M.shown / 16) % 16, M.shown % 16
  if tens > 0 then return { tens, ones } end
  return { ones }
end

return M
