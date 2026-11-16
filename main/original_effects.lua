-- Short-lived original effects: burst (anim $168), smoke puff (anim $1BB) and barrel
-- shards (sprites $60/$64, anims $2A4/$2A5).
-- Data: data/original/pirate/effects.lua (tools/replay-compare/export_effects.py).
-- Timing from the F9 scripts; the smoke drifts down 1 px every 2 frames
-- (route-bot-trace.csv, frame 1230). Positions in port pixels.
local M = {}

-- Shards (route-bot-trace.csv frames 1230/2042; goal-route-t6.csv frame 4938): four
-- pieces per break, vx +2/-1/-2/+1 px, vy -1216/-1472/-1216/-1600 (8.8), gravity $40;
-- gone 78 frames later (goal-route-t6.csv: 4938 -> 5016).
local SHARDS = { { "shard_a", 2, -1216 }, { "shard_a", -1, -1472 }, { "shard_b", -2, -1216 }, { "shard_b", 1, -1600 } }
local SHARD_GRAVITY, SHARD_LIFE = 0x40 / 256, 78

local data
local live = {}

function M.init()
  live = {}
  if data == nil then
    local ok, effects = pcall(function() return require("data.original.pirate.effects") end)
    data = ok and effects or false
  end
end

--- kind: "burst" | "smoke" | "smoke_rise" (the cannon's: rises 1 px per frame,
--- cannon-route-t1.csv) ; x, y: effect origin.
function M.spawn(kind, x, y)
  local frames = data and data[kind == "smoke_rise" and "smoke" or kind]
  if not frames then return end
  live[#live + 1] = { kind = kind, frames = frames, x = x, y = y, index = 1, timer = frames[1].frames, age = 0 }
  return live[#live]
end

--- The four barrel shards flying from (x, y).
function M.spawn_shards(x, y)
  for _, shard in ipairs(SHARDS) do
    local effect = M.spawn(shard[1], x, y)
    if effect then effect.vx, effect.vy, effect.loop = shard[2], shard[3] / 256, true end
  end
end

--- Break effect at the impact: burst + smoke puff, plus the shards for wooden barrels and
--- boxes (APPROXIMATION: shards measured on the box and the DK barrel only; star barrel,
--- animal crate and Klobber assumed the same). `shards` false: no shards (the bonus wall).
function M.spawn_break(x, y, shards)
  M.spawn("burst", x, y)
  M.spawn("smoke", x - 4, y + 4)
  if shards ~= false then M.spawn_shards(x, y) end
end

function M.update(frozen)
  if frozen then return end
  for i = #live, 1, -1 do
    local effect = live[i]
    effect.age = effect.age + 1
    if effect.kind == "smoke" and effect.age % 2 == 0 then effect.y = effect.y + 1 end
    if effect.kind == "smoke_rise" then effect.y = effect.y - 1 end
    if effect.vx then
      effect.x, effect.y, effect.vy = effect.x + effect.vx, effect.y + effect.vy, effect.vy + SHARD_GRAVITY
    end
    effect.timer = effect.timer - 1
    if effect.loop and effect.age >= SHARD_LIFE then
      table.remove(live, i)
    elseif effect.timer <= 0 then
      effect.index = effect.index + 1
      if effect.index > #effect.frames and effect.loop then
        effect.index, effect.timer = 1, effect.frames[1].frames
      elseif effect.index > #effect.frames then
        table.remove(live, i)
      else
        effect.timer = effect.frames[effect.index].frames
      end
    end
  end
end

function M.each_visible(draw)
  for _, effect in ipairs(live) do
    local frame = effect.frames[effect.index]
    draw(frame.sprite, effect.x - frame.origin_x, effect.y - frame.origin_y, frame.width, frame.height)
  end
end

return M
