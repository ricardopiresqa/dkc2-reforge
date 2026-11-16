-- ShipDeck camera translated from B5E4ED/E5EC/E73B/E652/E7B7/E9EA/ED62/EEB1.
-- Units follow the source: 1/256 px words, actor coordinates offset by +256.
-- Open deltas: EF89 fast-Y spring parameters, EE6B shake, $0D4E/$6E/$B8 gates.
local M = { status = "disabled" }
local profile = require("data.original.pirate.camera_profile")
local function clamp(x, low, high) return math.max(low, math.min(x, high)) end

-- Per-level DP words captured from WRAM ($0AEA/$0AEC/$0AEE/$0AF0/$0AF2/$0AF4).
local LOOK_LEFT, LOOK_RIGHT, LOOK_ADJUST = 0x8000, 0x3800, 0
local FLOOR_OFFSET, FLOOR_ADJUST, RISE_MARGIN = 0x9C00, 0, 0x0800
local VIEW_W, VIEW_H = 0x100, 0xE0

-- DATA_B5E612/DATA_B5E76B: identical 32-entry triangle tables of whole pixels.
local function wave(index)
  index = index % 32
  return (index < 16 and index or 31 - index) * 256
end

local function damp(value, shift)
  -- EF13/EF29 skip residuals in [-32, 31]; shifted results keep magnitude >= 8.
  if value >= -32 and value < 32 then return value end
  local result = math.floor(value / (2 ^ shift))
  if value < 0 then return math.min(-8, result) end
  return math.max(8, result)
end

function M.spring(axis, target, acceleration_cap, gain_shift)
  local difference = target - axis.target
  local previous_error = axis.target - axis.position
  -- EEB1 decrements X/Y before the ROR loops: parameter4 means FOUR shifts.
  local acceleration = clamp(math.floor((target - axis.position) / (2 ^ (gain_shift or 4))), -acceleration_cap, acceleration_cap)
  local limit = difference + damp(previous_error, 4)
  local velocity = axis.velocity + acceleration
  if limit == 0 then velocity = 0
  elseif velocity * limit < 0 then velocity = math.floor(velocity / 2)
  elseif math.abs(velocity) > math.abs(limit) then velocity = limit end
  axis.velocity = velocity
  -- ED92/EDFC clamp only the integrated step (velocity + shake) to +/-$0800.
  axis.position = axis.position + clamp(velocity, -2048, 2048)
  axis.target = target
end

-- Region rows: {8D28 x_low, 8E28 x_high, 8F28 y_low, 9028 y_high, 9128 flags|right<<8,
-- 9228 left links, 9328 up links, 9428 down links, index}; offsets are index*2.
local regions = profile.regions
local function row(offset) return regions[offset / 2 + 1] end
local function x_low(n) return row(n)[1] end
local function x_high(n) return row(n)[2] end
local function y_low(n) return row(n)[3] end
local function y_high(n) return row(n)[4] end
local function flags(n) return row(n)[5] % 256 end
local function right_link(n) return math.floor(row(n)[5] / 256) end
local function links(n, column) local word = row(n)[column]; return word % 256, math.floor(word / 256) end

local function vertical_overlap(n, top)  -- E914/E94D tail: >= $38 rows shared
  local bottom = top + VIEW_H
  local shared = bottom >= y_high(n) and y_high(n) - top or bottom - y_low(n)
  return shared >= 0x38
end

local function horizontal_overlap(n, left)  -- E97E/E9B0 tail: >= $40 columns shared
  local right = left + VIEW_W
  local shared = right >= x_high(n) and x_high(n) - left or right - x_low(n)
  return shared >= 0x40
end

local function qualifies(link, test)
  if link == 0 then return nil end
  local n = link * 2
  if flags(n) % 256 >= 0x80 or math.floor(flags(n) / 0x20) % 2 == 1 then return nil end
  return test(n) and n or nil
end

local function next_right(n)  -- ED10: region after the right link must list n as left link
  local link = right_link(n)
  if link == 0 or link + 2 > #regions then return nil end
  local candidate = (link + 1) * 2
  local a, b = links(candidate, 6)
  if a == n / 2 or b == n / 2 then return candidate end
end

local function neighbour_bounds(bc, left, top)
  if bc == 0 then return x_low(0), x_high(0), y_low(0), y_high(0) end
  local function to_left(n) return x_high(n) >= left and vertical_overlap(n, top) end
  local function to_right(n) return left + VIEW_W >= x_low(n) and vertical_overlap(n, top) end
  local function to_up(n) return y_high(n) >= top and horizontal_overlap(n, left) end
  local function to_down(n) return top + VIEW_H >= y_low(n) and horizontal_overlap(n, left) end
  local function pair(n, column, test)
    local a, b = links(n, column)
    return qualifies(a, test) or qualifies(b, test)
  end
  local function right_of(n)
    local found = qualifies(right_link(n), to_right)
    if found then return found end
    local after = next_right(n)
    return after and qualifies(after / 2, to_right) or nil
  end
  -- E810/E843/E882/E8BA: use a neighbour, or its neighbour when still beyond it.
  local n, deeper = pair(bc, 6, to_left), nil
  if n and left < x_low(n) then deeper = pair(n, 6, to_left) end
  local aa = x_low(deeper or n or bc)
  n, deeper = right_of(bc), nil
  if n and x_high(n) - VIEW_W < left then deeper = right_of(n) end
  local ac = x_high(deeper or n or bc)
  n, deeper = pair(bc, 7, to_up), nil
  if n and top < y_low(n) then deeper = pair(n, 7, to_up) end
  local ae = y_low(deeper or n or bc)
  n, deeper = pair(bc, 8, to_down), nil
  if n and y_high(n) - VIEW_H < top then deeper = pair(n, 8, to_down) end
  return aa, ac, ae, y_high(deeper or n or bc)
end

local function search_region(last, x, y)  -- ED2C linear search from the last row
  local n = last + 2
  repeat n = n - 2 until n == 0 or x >= x_low(n)
  while n > 0 and x >= x_high(n) do n = n - 2 end
  while n > 0 do
    if y < y_low(n) or y >= y_high(n) or x >= x_high(n) then n = n - 2 else break end
  end
  return n
end

local function select_region(bc, x, y)  -- E7DB/EC55
  if bc == 0 then return search_region(2 * (#regions - 1), x, y) end
  local inside_x = x >= x_low(bc) and x < x_high(bc)
  local inside_y = y >= y_low(bc) and y < y_high(bc)
  if inside_x and inside_y then return bc end
  local function spans_x(n) return flags(n) % 0x40 < 0x20 and x >= x_low(n) and x <= x_high(n) end
  local function spans_y(n) return flags(n) % 0x40 < 0x20 and y >= y_low(n) and y <= y_high(n) end
  if not inside_y then
    local a, b = links(bc, y < y_low(bc) and 7 or 8)
    for _, link in ipairs({ a, b }) do
      if link > 0 and spans_x(link * 2) then return link * 2 end
    end
    y = y < y_low(bc) and y_low(bc) or y_high(bc)
  end
  if x < x_low(bc) then
    local a, b = links(bc, 6)
    for _, link in ipairs({ a, b }) do
      if link > 0 and spans_y(link * 2) then return link * 2 end
    end
  elseif x >= x_high(bc) then
    local link = right_link(bc)
    if link > 0 and spans_y(link * 2) then return link * 2 end
    local after = next_right(bc)
    if after and spans_y(after) then return after end
  end
  return bc
end

local function clamp_view(pixel, low, high_edge, span)  -- E9EA/EA0C
  local high = high_edge - span
  if high < 0 then return 0 end
  if high < low then return math.floor((high + low) / 2) end
  if pixel > high then return high end
  if pixel <= low then return low end
  return pixel
end

local function set_pixel(word, pixel) return pixel * 256 + word % 256 end

-- One B5E4ED target pass. actor_x/actor_y are source words; ground is the $000E
-- floor distance in pixels, or nil when the probe found no floor ($8050).
local function targets(actor_x, actor_y, facing_left, ground)
  local clock = M.clock
  local target_x = actor_x - wave(math.floor(clock / 8))
    - ((facing_left and LOOK_LEFT or LOOK_RIGHT) + LOOK_ADJUST)
  target_x = math.max(0, target_x)
  -- E73B: (clock + clock/2 + $1F) >> 2, masked $3E as a WORD offset: /8 entries.
  local focus_y = actor_y - wave(math.floor((clock + math.floor(clock / 2) + 31) / 8))
  local target_y
  if ground then  -- E67E/E6E2: aim at the floor beneath the actor.
    target_y = math.max(0, focus_y + ground * 256 - (FLOOR_OFFSET + FLOOR_ADJUST))
    M.floor_pixel = math.floor(target_y / 256)
  else            -- E68E: rising/high air only lifts the target.
    local candidate = focus_y - 0x3800 - RISE_MARGIN
    if focus_y - 0x3800 < 0 or candidate < 0 then target_y = 0
    elseif math.floor(candidate / 256) < M.floor_pixel then target_y = candidate
    else
      candidate = focus_y - 0xC800
      if candidate < 0 then target_y = 0
      elseif math.floor(candidate / 256) < M.floor_pixel then target_y = M.y.target
      else target_y = candidate end
    end
  end
  -- E7B7: level limits reset the subpixel byte.
  local left, top = math.floor(target_x / 256), math.floor(target_y / 256)
  if x_low(0) >= left then target_x = x_low(0) * 256 elseif profile.x_max < left then target_x = profile.x_max * 256 end
  if y_low(0) >= top then target_y = y_low(0) * 256 elseif profile.y_max < top then target_y = profile.y_max * 256 end
  left, top = math.floor(target_x / 256), math.floor(target_y / 256)
  M.region = select_region(M.region or 0, math.floor(actor_x / 256), math.floor(actor_y / 256))
  local aa, ac, ae, b0 = neighbour_bounds(M.region, left, top)
  local clamped_x, clamped_y = clamp_view(left, aa, ac, VIEW_W), clamp_view(top, ae, b0, VIEW_H)
  if clamped_x ~= left then target_x = set_pixel(target_x, clamped_x) end
  if clamped_y ~= top then target_y = set_pixel(target_y, clamped_y) end
  return target_x, target_y
end

local function clamp_position(axis, maximum, floor_zero)  -- EDDE/EE48: subpixel kept
  if floor_zero and axis.position < 0 then axis.position = 0 end  -- EE44 BPL (X only)
  local pixel = math.floor(axis.position / 256)
  if pixel < 256 then axis.position = set_pixel(axis.position, 256)
  elseif pixel > maximum then axis.position = set_pixel(axis.position, maximum) end
end

local function source_words(x, y)
  return math.floor((x + 256) * 256), math.floor((y + 256) * 256)
end

function M.init(clock, x, y, facing_left, ground)
  M.clock, M.region, M.floor_pixel = clock, 0, 0
  M.y = { position = 0, velocity = 0, target = 0 }
  local actor_x, actor_y = source_words(x, y)
  local target_x, target_y = targets(actor_x, actor_y, facing_left, ground or 0)
  M.x = { position = target_x, velocity = 0, target = target_x }
  M.y = { position = target_y, velocity = 0, target = target_y }
  M.status = "source pipeline; EF89 fast-Y, EE6B shake and $0D4E/$6E/$B8 gates open"
  return math.floor(target_x / 256) - 256, math.floor(target_y / 256) - 256
end

-- frozen mirrors $0A36 bit $80 (hit-stop): ED62 returns after the target pass.
function M.update(x, y, facing_left, ground, frozen)
  M.clock = (M.clock + 1) % 65536
  local actor_x, actor_y = source_words(x, y)
  local target_x, target_y = targets(actor_x, actor_y, facing_left, ground)
  if frozen then
    -- E4ED still copies the new targets into $A2/$A6 for the next spring pass.
    M.x.target, M.y.target = target_x, target_y
    return math.floor(M.x.position / 256) - 256, math.floor(M.y.position / 256) - 256
  end
  -- ED92 runs the Y axis (EF89 base parameters) before the X axis (EEB1).
  M.spring(M.y, target_y, 64, 5)
  clamp_position(M.y, profile.y_max)
  M.spring(M.x, target_x, 96)
  clamp_position(M.x, profile.x_max, true)
  return math.floor(M.x.position / 256) - 256, math.floor(M.y.position / 256) - 256
end

function M.snapshot()
  return { clock = M.clock, status = M.status, region = M.region and M.region / 2,
           x_position = M.x and M.x.position, x_target = M.x and M.x.target,
           x_velocity = M.x and M.x.velocity,
           y_position = M.y and M.y.position, y_target = M.y and M.y.target,
           y_velocity = M.y and M.y.velocity }
end

function M.check_damping()
  assert(damp(-169, 4) == -11, "negative spring damping must preserve larger residual")
  assert(damp(-100, 4) == -8, "small negative spring damping must floor at -8")
  assert(damp(169, 4) == 10, "positive spring damping changed before cap")
  assert(damp(-12, 4) == -12 and damp(12, 4) == 12, "small residual damping must remain unchanged")
  assert(damp(-32, 4) == -32 and damp(32, 4) == 8, "EF13/EF29 skip window is [-32, 31]")
  return true
end

return M
