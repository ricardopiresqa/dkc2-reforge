-- Carry and throw the wooden box and the DK barrel (level objects "wooden_box", "dk_barrel").
-- Measured on route-bot-trace.csv (frames 1072-1230): with Y held, walking into a box on
-- the ground picks it up (animation $0F, 8 frames); it rides at the carry frame's offset
-- (the $8B frames of $10-$18: x +12, y -8 standing, -11/-9 walking, -9 in the air; the
-- route-bot jump shows +12/-9 throughout); 12/-9 when no frame gives one. A carried box
-- touching an enemy breaks and defeats it.
-- Throw (carry-route-t2.csv 1150-1174): releasing Y plays animation $14; B9D8AC holds the
-- Kong for the wind-up (the box follows the $8B offsets), B9D967 lets it go (player
-- .throw_release) at vx $0C00, vy -$0100: vx eases to $0400 by 1/16 a frame, vy +$50.
-- APPROXIMATIONS: it breaks on the first enemy, floor or after 60 frames.
local M = {}

local CARRY_DX, CARRY_DY, PICKUP_FRAMES = 12, -9, 8
local THROW_VX, THROW_VY, SETTLE_VX, GRAVITY, LIFETIME = 0x0C00, -0x0100, 0x0400, 0x50, 60
local held, flying, pickup = nil, {}, 0
-- DK barrel too: route-bot-trace.csv frames 2036-2042 (Diddy carries sprite 424, anim $16).
local CARRIED = { "wooden_box", "dk_barrel" }

--- `taken` (the level-visit taken table): a box still held or flying when the level
--- reloads (death, area change) never broke, so it is released to respawn.
function M.init(taken)
  if taken then
    if held and held.key then taken[held.key] = nil end
    for _, box in ipairs(flying) do if box.key then taken[box.key] = nil end end
  end
  held, flying, pickup = nil, {}, 0
end

function M.carrying() return held ~= nil end

local function overlap(a, b)
  return a[3] >= b[1] and b[3] >= a[1] and b[4] >= a[2] and a[4] >= b[2]
end

local function frame_box(frame, x, feet)
  local left = x - frame.origin_x
  return { left, feet - frame.origin_y, left + frame.width, feet - frame.origin_y + frame.height }
end

--- Enemy hit by a box: returns the walker or nil.
local function hit_walker(walkers, box)
  for _, walker in ipairs(walkers.walkers()) do
    if walker.alive and not walker.defeated then
      local l, t, r, b = walkers.box(walker.pose, bit.rshift(walker.x, 8) - 256, bit.rshift(walker.y, 8) - 256,
                                     bit.band(walker.attributes, 0x4000) ~= 0)
      if l and overlap(box, { l, t, r, b }) then return walker end
    end
  end
  return nil
end

--- One frame. Returns a list of events: { kind = "pickup" | "throw" | "break", x, y, walker }.
function M.update(player, items, walkers, surface_at, y_held)
  local events = {}
  local dir = player.direction < 0 and -1 or 1
  local feet = player.pos_y + 24
  if not held and y_held and player.grounded then
    local reach = { player.pos_x - 14, feet - 24, player.pos_x + 14, feet }
    for _, kind in ipairs(CARRIED) do
      items.each_alive(kind, function(entity)
        if held then return end
        local frame = entity.frames[entity.index]
        if overlap(reach, frame_box(frame, entity.x, entity.feet_y)) then
          items.remove(entity)
          held, pickup = { frame = frame, key = entity.key, item = kind }, PICKUP_FRAMES
          events[#events + 1] = { kind = "pickup" }
        end
      end)
    end
  end
  if held then
    local animation = require("main.original_animation")
    held.x = player.pos_x + (animation.held_dx or CARRY_DX) * dir
    held.feet = feet + (animation.held_dy or CARRY_DY)
    pickup = math.max(0, pickup - 1)
    local walker = hit_walker(walkers, frame_box(held.frame, held.x, held.feet))
    if walker then
      events[#events + 1] = { kind = "break", x = held.x, y = held.feet - 8, feet = held.feet, walker = walker,
                              item = held.item }
      held = nil
    elseif pickup == 0 and not y_held and not held.throwing then
      held.throwing = true
      events[#events + 1] = { kind = "throw_start" }
    -- another animation took over before B9D967 (damage, swap): let go at once
    elseif held.throwing and (player.throw_release or require("main.original_animation").forced ~= 0x14) then
      player.throw_release = nil
      flying[#flying + 1] = { frame = held.frame, key = held.key, item = held.item, x = held.x, feet = held.feet,
                              vx = THROW_VX * dir, vy = THROW_VY, dir = dir, age = 0 }
      held = nil
      events[#events + 1] = { kind = "throw" }
    end
  end
  for i = #flying, 1, -1 do
    local box = flying[i]
    box.vx = box.vx + math.floor((SETTLE_VX * box.dir - box.vx) / 16)
    box.x, box.feet, box.vy, box.age = box.x + box.vx / 256, box.feet + box.vy / 256, box.vy + GRAVITY, box.age + 1
    local walker = hit_walker(walkers, frame_box(box.frame, box.x, box.feet))
    local floor = surface_at and box.vy > 0 and surface_at(math.floor(box.x), math.floor(box.feet) - 4,
                                                           math.floor(box.feet) + 2)
    if walker or floor or box.age >= LIFETIME then
      events[#events + 1] = { kind = "break", x = box.x, y = box.feet - 8, feet = box.feet, walker = walker,
                              item = box.item }
      table.remove(flying, i)
    end
  end
  return events
end

M.hit_walker = hit_walker

function M.picking_up() return held ~= nil and pickup > 0 end

--- draw(sprite, left, top, width, height) for the held and flying boxes.
function M.each_visible(draw)
  local function one(box)
    local f = box.frame
    draw(f.sprite, box.x - f.origin_x - 1, box.feet - f.origin_y, f.width, f.height)
  end
  if held and held.x then one(held) end
  for _, box in ipairs(flying) do one(box) end
end

return M
