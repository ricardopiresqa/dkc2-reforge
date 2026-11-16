-- Pirate Panic banana formations (B5F10B layout, B5F5BD/B5F637 OAM, B5F79A collision).
-- Positions come from data.original.pirate.bananas (source coordinates, top-left of a
-- 16x16 sprite); the port's world is source - 256. Only groups whose type bit is set in
-- $0D30 (= 1 after B5F10B) are drawn and collectable.
local bit = require("bit")
local M = { active = false }

local SOURCE_OFFSET = 256
local VISIBLE_TYPES = 1  -- $0D30
local list, taken = {}, {}

-- Literal require(...) so bob's static scan bundles the generated modules; subareas
-- have their own formations (the warp room's banana "!", PiratePanic_Warp.bin).
local LOADERS = {
  main = function() return require("data.original.pirate.bananas") end,
  warp = function() return require("data.original.pirate.bananas_warp") end,
  bonus_1 = function() return require("data.original.pirate.bananas_bonus_1") end,
}

function M.init(enabled, area)
  M.active, list, taken = false, {}, {}
  local loader = LOADERS[area or "main"]
  if not enabled or not loader then return end
  local ok, data = pcall(loader)
  if not ok or type(data) ~= "table" then return end
  list, M.active = data, true
end

--- Spin frame (0-7) from B5F637: P = ((clock>>1)*4 + gx + gy) >> 2; frame = P>>1 + col + row.
function M.frame(banana, clock)
  local phase = math.floor((math.floor(clock / 2) * 4 + banana.gx + banana.gy) / 4) % 65536
  return (math.floor(phase / 2) + banana.col + banana.row) % 8
end

--- Collect every banana whose 16x16 cell overlaps the hitbox (port coordinates).
-- B5F79A clears the column-mask bit; the cell test includes one extra 8 px column and
-- row, i.e. the whole 16x16 sprite. Returns the count and the world top-left of each.
function M.collect(left, top, width, height)
  if not M.active then return 0, {} end
  local count, positions = 0, {}
  for index, banana in ipairs(list) do
    if not taken[index] and bit.band(banana.type_bit, VISIBLE_TYPES) ~= 0 then
      local x, y = banana.x - SOURCE_OFFSET, banana.y - SOURCE_OFFSET
      if left < x + 16 and left + width > x and top < y + 16 and top + height > y then
        taken[index] = true
        count = count + 1
        positions[count] = { x, y }
      end
    end
  end
  return count, positions
end

-- Player box read by B5F739 from $09B3 (left, top, right, bottom relative to the
-- actor's x and feet), per original animation id, facing right. Values captured in
-- reference-banana-box.csv; the ROM clipping table behind them is not decoded yet.
local BOXES = {
  [1] = { -9, -34, 9, -3 }, [2] = { -7, -31, 7, -3 }, [3] = { -7, -34, 11, -3 },
  [5] = { -8, -26, 12, -2 }, [6] = { -8, -26, 12, -2 }, [7] = { -8, -26, 12, -2 },
  [8] = { -8, -26, 12, -2 },
}

--- Returns left, top, width, height of the banana-collection box (port coordinates).
function M.player_box(animation_id, facing_left, x, feet_y)
  local box = BOXES[animation_id] or BOXES[1]
  local left, right = box[1], box[3]
  if facing_left then left, right = -box[3], -box[1] end
  return x + left, feet_y + box[2], right - left, box[4] - box[2]
end

--- Calls draw(frame, x, y) with port world top-left for each visible banana.
function M.each_visible(clock, draw)
  if not M.active then return end
  for index, banana in ipairs(list) do
    if not taken[index] and bit.band(banana.type_bit, VISIBLE_TYPES) ~= 0 then
      draw(M.frame(banana, clock), banana.x - SOURCE_OFFSET, banana.y - SOURCE_OFFSET)
    end
  end
end

function M.remaining()
  local count = 0
  for index in ipairs(list) do
    if not taken[index] then count = count + 1 end
  end
  return count
end

return M
