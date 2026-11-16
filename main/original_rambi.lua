-- Rambi (animal buddy) and the ship-deck breakable wall into bonus 2.
-- Data: data/original/pirate/rambi.lua (tools/replay-compare/export_rambi.py): original
-- poses, F9 frame lists, DATA_BCB600 boxes; wall spawn fields $42 = 3 (bonus 2),
-- $44 = 4 (return record). Rider pose $211C drawn at Rambi's origin (authored so).
-- APPROXIMATIONS (Rambi's own routines are not translated): stomping the crate frees
-- Rambi; touching Rambi mounts him; mounted, Rambi moves with the Kong's physics, side
-- contacts defeat walkers, the wall breaks under the super charge (below) into bonus 2;
-- the No Animal sign ends the ride; on foot the wall blocks like a solid block.
-- Super charge (animal-route-t7.csv, B9E387): A held while mounted on the ground charges
-- (state $53, the animation rate climbs $100 -> $480 by $0C: 75 frames); releasing it
-- full dashes at vx $700 (state $4F). Only the dash breaks the wall (t4: pushing does
-- not); the Kong then walks through at $180 for 46 frames (state $33) into bonus 2.
-- APPROXIMATION: a dash that meets no wall stops after DASH_FRAMES.
local M = { active = false }
local collision = require("main.collision")
local CHARGE_FRAMES, DASH_SPEED, DASH_FRAMES, ENTER_SPEED, ENTER_FRAMES = 75, 7, 40, 1.5, 46

local data
local rambi
local wall

function M.init(enabled, objects, surface_at)
  M.active, rambi, wall, M.surface_at = false, nil, nil, surface_at
  if not enabled then return end
  local ok, rambi_data = pcall(function() return require("data.original.pirate.rambi") end)
  if not ok then return end
  data = rambi_data
  if not objects then
    local ok_level, level = pcall(function() return require("data.original.pirate.pirate_panic_level") end)
    objects = ok_level and level.objects or {}
  end
  for _, object in ipairs(objects) do
    if object.param == data.wall.param then
      wall = { x = object.x, feet_y = object.feet_y, broken = false }
    end
  end
  M.active = true
end

local function pose_box(pose_id, x, feet, flipped)
  local pose = data.poses[pose_id]
  local hit = pose and pose.box
  if not hit then return nil end
  local left = flipped and x - hit[1] - hit[3] or x + hit[1]
  return left, feet + hit[2], left + hit[3], feet + hit[2] + hit[4]
end

local function overlap(a, b)
  return a[3] >= b[1] and b[3] >= a[1] and b[4] >= a[2] and a[4] >= b[2]
end

--- The crate was stomped at (x, feet): Rambi appears there.
function M.free(x, feet)
  if not M.active or rambi then return end
  rambi = { x = x, feet_y = feet, vy = 0, state = "free", flipped = false, anim = "idle", index = 1, timer = 0 }
end

function M.mounted() return rambi ~= nil and rambi.state == "mounted" end

--- Area change while riding: the Kong arrives on Rambi (animal-route-t9.csv: bonus 2
--- starts with Diddy mounted at its spawn record, x 44 / feet 209).
function M.ride(player)
  if not M.active then return end
  rambi = { x = player.pos_x, feet_y = player.pos_y + 24, vy = 0, state = "mounted",
            flipped = player.direction < 0, anim = "idle", index = 1, timer = 0 }
end

local function play(anim)
  if rambi.anim ~= anim then rambi.anim, rambi.index, rambi.timer = anim, 1, 0 end
end

local function animate()
  local list = data.animations[rambi.anim]
  if not list or #list == 0 then return end
  rambi.timer = rambi.timer - 1
  if rambi.timer <= 0 then
    rambi.index = rambi.index % #list + 1
    rambi.timer = list[rambi.index][1]
    if rambi.anim == "turn" and rambi.index == #list then rambi.anim, rambi.index = "idle", 1 end
  end
end

--- One frame. player: main/player.lua module. Returns "enter_bonus" when the Kong goes
-- through the broken wall.
-- Charge, dash and walk-through: the Kong's position is driven here.
local function drive(player, a_held)
  local dir = rambi.flipped and -1 or 1
  if rambi.entering then
    rambi.entering = rambi.entering - 1
    rambi.x = rambi.x + ENTER_SPEED * dir
  elseif rambi.dash then
    if rambi.dash <= 0 then
      rambi.dash = nil  -- the frame after a hit: the breakable wall check has run
    else
      local x, wall_hit = collision.resolve_x(rambi.x, player.pos_y, 16, 24, DASH_SPEED * dir, player.grounded)
      rambi.x, rambi.dash = x, wall_hit and 0 or rambi.dash - 1
    end
  elseif rambi.charge then
    if not player.grounded then rambi.charge = nil; return false end  -- off a ledge: no charge
    if a_held then rambi.charge = rambi.charge + 1
    else
      rambi.dash, rambi.charge = rambi.charge >= CHARGE_FRAMES and DASH_FRAMES or nil, nil
    end
  elseif a_held and player.grounded then  -- B8C7EB: A on the ground zeroes vx and charges
    rambi.charge = 0
  else
    return false
  end
  player.pos_x, player.vel_x = rambi.x, 0
  return true
end

function M.update(player, a_held)
  if not M.active then return nil end
  local feet = player.pos_y + 24
  local player_box = { player.pos_x - 8, feet - 26, player.pos_x + 8, feet }
  if rambi and rambi.state == "free" then
    rambi.feet_y = rambi.feet_y + rambi.vy
    rambi.vy = math.min(rambi.vy + 0x70 / 256, 8)
    local floor = M.surface_at and M.surface_at(math.floor(rambi.x), math.floor(rambi.feet_y) - 8,
                                                math.floor(rambi.feet_y) + 4)
    if floor and rambi.vy >= 0 then rambi.feet_y, rambi.vy = floor, 0 end
    local l, t, r, b = pose_box(data.animations.idle[1][2], rambi.x, rambi.feet_y, rambi.flipped)
    if l and overlap(player_box, { l, t, r, b }) then rambi.state = "mounted" end
  elseif rambi and rambi.state == "mounted" then
    local driven = drive(player, a_held)
    local flipped = player.direction < 0
    if not driven and flipped ~= rambi.flipped then rambi.flipped = flipped; play("turn") end
    if driven then player.direction = rambi.flipped and -1 or 1 end
    rambi.x, rambi.feet_y = player.pos_x, feet
    if rambi.anim ~= "turn" then
      if not player.grounded then play("jump")
      elseif rambi.dash or rambi.entering or math.abs(player.vel_x) > 1 then play("walk")
      else play("idle") end
    end
  end
  if rambi then animate() end
  if wall then
    local l, t, r, b = pose_box(data.wall.pose, wall.x, wall.feet_y, false)
    local wall_box = { l, t, r, b }
    local reach = player_box
    if rambi and rambi.dash then  -- the level collision stops the dash just short of the wall
      local dir = rambi.flipped and -1 or 1
      reach = { player_box[1] + math.min(0, 8 * dir), player_box[2], player_box[3] + math.max(0, 8 * dir), player_box[4] }
    end
    if not wall.broken and overlap(reach, wall_box) then
      if M.mounted() and rambi.dash then
        wall.broken, rambi.dash, rambi.entering = true, nil, ENTER_FRAMES
        M.sound_request = "break_wall"
        M.break_at = { wall.x, wall.feet_y - 32 }
      elseif player.pos_x < wall.x then
        player.pos_x, player.vel_x = math.min(player.pos_x, l - 9), 0
      else
        player.pos_x, player.vel_x = math.max(player.pos_x, r + 9), 0
      end
    elseif wall.broken and rambi and rambi.entering and rambi.entering <= 0 then
      return "enter_bonus"
    end
  end
  return nil
end

--- The No Animal sign: the ride ends here.
function M.dismount()
  if rambi then rambi.state, rambi = "gone", nil end
end

function M.wall_link() return data and data.wall.dest, data and data.wall.return_record end

--- draw(sprite, left, top, width, height, flipped): wall, Rambi, then the rider.
function M.each_visible(draw)
  if not M.active then return end
  local function pose(pose_id, x, feet, flipped)
    local p = data.poses[pose_id]
    if not p then return end
    local left = flipped and x - (p.width - p.origin_x) + 1 or x - p.origin_x
    draw(p.sprite, left - 1, feet - p.origin_y, p.width, p.height, flipped)
  end
  if wall and not wall.broken then pose(data.wall.pose, wall.x, wall.feet_y, false) end
  if rambi then
    local list = data.animations[rambi.anim]
    local x, feet = math.floor(rambi.x), math.floor(rambi.feet_y)
    pose(list[rambi.index][2], x, feet, rambi.flipped)
    if rambi.state == "mounted" then pose(data.rider, x, feet, rambi.flipped) end
  end
end

return M
